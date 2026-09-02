from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Run(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=_utcnow)

    items: list["Item"] = Relationship(
        back_populates="run", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="run.id", index=True)

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

    run: Optional[Run] = Relationship(back_populates="items")
