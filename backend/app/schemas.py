from datetime import datetime

from pydantic import BaseModel


class ItemOut(BaseModel):
    id: int
    prompt: str
    context: str
    response: str

    faithfulness_score: int
    faithfulness_rationale: str
    faithfulness_confidence: str

    format_score: int
    format_rationale: str
    format_confidence: str

    safety_score: int
    safety_rationale: str
    safety_confidence: str

    class Config:
        from_attributes = True


class DimensionAggregate(BaseModel):
    average: float
    color: str  # "green" | "yellow" | "red"


class RunAggregate(BaseModel):
    faithfulness: DimensionAggregate
    format: DimensionAggregate
    safety: DimensionAggregate


class RunSummary(BaseModel):
    id: int
    name: str
    created_at: datetime
    item_count: int
    aggregate: RunAggregate


class RunDetailOut(BaseModel):
    id: int
    name: str
    created_at: datetime
    aggregate: RunAggregate
    items: list[ItemOut]


class CompareOut(BaseModel):
    run_a: RunSummary
    run_b: RunSummary
