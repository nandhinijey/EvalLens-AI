"""Faithfulness / hallucination judge.

Scores whether a response only states things supported by the provided
context. Pure LLM-as-judge — there's no reliable rule-based check for
hallucination.
"""

from app.judges.base import JudgeResult, call_judge

SYSTEM_PROMPT = """\
You are a strict fact-checking judge. You evaluate whether an AI assistant's \
response is faithful to a provided context — i.e. whether every factual claim \
in the response is supported by the context, with no fabricated or \
unsupported information (hallucination).

Score from 0 to 100:
- 100: every claim in the response is directly supported by the context.
- 50-99: mostly supported, with minor unsupported details or embellishments.
- 1-49: significant unsupported or fabricated claims mixed with some \
supported content.
- 0: the response is largely or entirely unsupported by the context, or \
contradicts it.

If the context is empty or missing, judge whether the response makes claims \
that would require external, unverifiable knowledge (score lower) versus \
staying appropriately general or declining to speculate (score higher).

Set confidence to "low" if the context is ambiguous, the claims are hard to \
verify, or the response is borderline; otherwise "high".

Respond only with the structured score, a one-sentence rationale, and your \
confidence."""

USER_PROMPT_TEMPLATE = """\
CONTEXT:
{context}

RESPONSE TO EVALUATE:
{response}

Evaluate whether the response is faithful to the context."""


def evaluate_faithfulness(context: str, response: str) -> JudgeResult:
    user_prompt = USER_PROMPT_TEMPLATE.format(
        context=context.strip() or "(no context provided)",
        response=response.strip() or "(empty response)",
    )
    return call_judge(SYSTEM_PROMPT, user_prompt)
