"""Format compliance judge.

Rule-based checks handle the clear-cut case (the prompt asks for JSON and we
can just try to parse it). Everything else — free-form structural
instructions like "respond with three bullet points" or "include a summary
and a list of action items" — falls through to an LLM judge.
"""

import json
import re

from app.judges.base import JudgeResult, call_judge

_JSON_HINT_RE = re.compile(r"\bjson\b", re.IGNORECASE)
_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)

SYSTEM_PROMPT = """\
You are a meticulous QA judge. You evaluate whether an AI assistant's \
response follows the structure and formatting instructions implied by the \
prompt — e.g. required fields, a requested list/table format, a length \
constraint, a specific section structure, or an explicitly requested \
schema.

Score from 0 to 100:
- 100: the response fully complies with every structural instruction in \
the prompt.
- 50-99: mostly compliant, with minor formatting deviations.
- 1-49: significant structural deviations — missing required sections/ \
fields, wrong format entirely for parts of the response.
- 0: the response ignores the requested structure entirely.

If the prompt does not specify any particular structure, score 100 with \
high confidence (there is nothing to violate).

Set confidence to "low" if the formatting instructions in the prompt are \
ambiguous or only implicit; otherwise "high".

Respond only with the structured score, a one-sentence rationale, and your \
confidence."""

USER_PROMPT_TEMPLATE = """\
PROMPT (may imply a required structure/format):
{prompt}

RESPONSE TO EVALUATE:
{response}

Evaluate whether the response follows the structure/format implied by the \
prompt."""


def _strip_code_fence(text: str) -> str:
    return _CODE_FENCE_RE.sub("", text.strip()).strip()


def _rule_based_json_check(response: str) -> JudgeResult | None:
    """If the response looks like it's meant to be JSON, validate it directly."""
    candidate = _strip_code_fence(response)
    if not candidate or candidate[0] not in "{[":
        return None
    try:
        json.loads(candidate)
    except json.JSONDecodeError as exc:
        return JudgeResult(
            score=0,
            rationale=f"Response is not valid JSON: {exc}",
            confidence="high",
        )
    return JudgeResult(
        score=100,
        rationale="Response is valid, well-formed JSON.",
        confidence="high",
    )


def evaluate_format_compliance(prompt: str, response: str) -> JudgeResult:
    response = response.strip()
    prompt = prompt.strip()

    # Rule-based pass: only applies when the response is (or attempts to be) JSON.
    if response[:1] in "{[" or _JSON_HINT_RE.search(prompt or ""):
        rule_result = _rule_based_json_check(response)
        if rule_result is not None:
            return rule_result

    # Looser cases (bullet points, sections, prose structure) go to the LLM judge.
    user_prompt = USER_PROMPT_TEMPLATE.format(
        prompt=prompt or "(no prompt provided)",
        response=response or "(empty response)",
    )
    return call_judge(SYSTEM_PROMPT, user_prompt)
