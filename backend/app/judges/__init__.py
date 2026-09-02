from dataclasses import dataclass

from app.judges.base import JudgeResult
from app.judges.faithfulness import evaluate_faithfulness
from app.judges.format_compliance import evaluate_format_compliance
from app.judges.safety import evaluate_safety

__all__ = [
    "JudgeResult",
    "evaluate_faithfulness",
    "evaluate_format_compliance",
    "evaluate_safety",
    "EvaluationResult",
    "evaluate_item",
]


@dataclass
class EvaluationResult:
    faithfulness: JudgeResult
    format_compliance: JudgeResult
    safety: JudgeResult


def evaluate_item(prompt: str, context: str, response: str) -> EvaluationResult:
    """Run all three judges against a single prompt/context/response triple."""
    return EvaluationResult(
        faithfulness=evaluate_faithfulness(context, response),
        format_compliance=evaluate_format_compliance(prompt, response),
        safety=evaluate_safety(context, response),
    )
