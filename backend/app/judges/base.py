"""Shared plumbing for the LLM-as-judge evaluators.

Each judge module (faithfulness, format_compliance, safety) builds a
system/user prompt and calls `call_judge`, which handles the Claude API
call, structured-JSON parsing, and retries on malformed/failed responses.
"""

from __future__ import annotations

import functools
import logging
import time
from typing import Literal

import anthropic
from pydantic import BaseModel, Field

from app.config import ANTHROPIC_MODEL, MAX_JUDGE_RETRIES

logger = logging.getLogger("trustlens.judges")


class JudgeResult(BaseModel):
    score: int = Field(ge=0, le=100, description="0 (worst) to 100 (best)")
    rationale: str = Field(description="One-sentence justification for the score")
    confidence: Literal["high", "low"] = Field(
        description="How confident the judge is in this score"
    )


@functools.lru_cache(maxsize=1)
def get_client() -> anthropic.Anthropic:
    # Reads ANTHROPIC_API_KEY (or an `ant auth login` profile) from the environment.
    return anthropic.Anthropic()


def call_judge(
    system_prompt: str,
    user_prompt: str,
    *,
    max_retries: int = MAX_JUDGE_RETRIES,
    max_tokens: int = 500,
) -> JudgeResult:
    """Call Claude for a single judge verdict, retrying on malformed/failed output.

    Uses structured outputs (`output_format`) so the model is constrained to the
    JudgeResult schema; retries handle transient API errors, refusals, or any
    response that fails Pydantic validation.
    """
    client = get_client()
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            response = client.messages.parse(
                model=ANTHROPIC_MODEL,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                output_format=JudgeResult,
            )
            if response.stop_reason == "refusal":
                raise ValueError("Judge model refused to score this item")
            if response.parsed_output is None:
                raise ValueError("Judge response did not parse into the expected schema")
            return response.parsed_output
        except Exception as exc:  # noqa: BLE001 - deliberately broad: any failure should retry
            last_error = exc
            logger.warning(
                "Judge call failed (attempt %d/%d): %s", attempt, max_retries, exc
            )
            if attempt < max_retries:
                time.sleep(min(2 ** (attempt - 1), 8))

    # All retries exhausted — surface a low-confidence result rather than
    # crashing the whole batch over one bad row.
    return JudgeResult(
        score=50,
        rationale=f"Judge call failed after {max_retries} attempts: {last_error}",
        confidence="low",
    )
