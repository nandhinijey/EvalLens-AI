import logging
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from app.config import CORS_ORIGINS, FLAG_THRESHOLD, JUDGE_CONCURRENCY
from app.csv_utils import CSVValidationError, parse_csv
from app.db import get_session, init_db
from app.judges import evaluate_item
from app.models import Item, Run
from app.schemas import (
    CompareOut,
    DimensionAggregate,
    ItemOut,
    RunAggregate,
    RunDetailOut,
    RunSummary,
)
from app.thresholds import score_color

logger = logging.getLogger("trustlens.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="TrustLens API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _aggregate(items: list[Item]) -> RunAggregate:
    def dim(scores: list[int]) -> DimensionAggregate:
        avg = statistics.mean(scores) if scores else 0.0
        return DimensionAggregate(average=round(avg, 1), color=score_color(avg))

    return RunAggregate(
        faithfulness=dim([i.faithfulness_score for i in items]),
        format=dim([i.format_score for i in items]),
        safety=dim([i.safety_score for i in items]),
    )


def _run_summary(run: Run, items: list[Item]) -> RunSummary:
    return RunSummary(
        id=run.id,
        name=run.name,
        created_at=run.created_at,
        item_count=len(items),
        aggregate=_aggregate(items),
    )


def _score_one_row(row: dict[str, str]) -> Item:
    result = evaluate_item(row["prompt"], row["context"], row["response"])
    return Item(
        run_id=0,  # set after the parent Run is persisted
        prompt=row["prompt"],
        context=row["context"],
        response=row["response"],
        faithfulness_score=result.faithfulness.score,
        faithfulness_rationale=result.faithfulness.rationale,
        faithfulness_confidence=result.faithfulness.confidence,
        format_score=result.format_compliance.score,
        format_rationale=result.format_compliance.rationale,
        format_confidence=result.format_compliance.confidence,
        safety_score=result.safety.score,
        safety_rationale=result.safety.rationale,
        safety_confidence=result.safety.confidence,
    )


@app.post("/evaluate", response_model=RunDetailOut)
async def evaluate(
    file: UploadFile = File(...),
    name: str = Form(...),
    session: Session = Depends(get_session),
):
    """Accept a CSV of prompt/context/response rows, run all three judges on
    each row, persist the results as a new Run, and return it."""
    raw_bytes = await file.read()
    try:
        rows = parse_csv(raw_bytes)
    except CSVValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Score every row concurrently — each row makes up to 3 sequential judge
    # calls internally, so this bounds total wall-clock time to roughly
    # (rows / JUDGE_CONCURRENCY) judge calls rather than 3 * rows.
    items_by_index: dict[int, Item] = {}
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=JUDGE_CONCURRENCY) as pool:
        futures = {pool.submit(_score_one_row, row): i for i, row in enumerate(rows)}
        for future in as_completed(futures):
            i = futures[future]
            try:
                items_by_index[i] = future.result()
            except Exception as exc:  # noqa: BLE001
                logger.exception("Row %d failed to score", i)
                errors.append(f"row {i}: {exc}")

    if not items_by_index:
        raise HTTPException(
            status_code=502,
            detail=f"All rows failed to score. First error: {errors[0] if errors else 'unknown'}",
        )

    run = Run(name=name)
    session.add(run)
    session.commit()
    session.refresh(run)

    ordered_items = [items_by_index[i] for i in sorted(items_by_index)]
    for item in ordered_items:
        item.run_id = run.id
        session.add(item)
    session.commit()

    for item in ordered_items:
        session.refresh(item)

    return RunDetailOut(
        id=run.id,
        name=run.name,
        created_at=run.created_at,
        aggregate=_aggregate(ordered_items),
        items=[ItemOut.model_validate(i) for i in ordered_items],
    )


@app.get("/runs", response_model=list[RunSummary])
def list_runs(session: Session = Depends(get_session)):
    runs = session.exec(select(Run).order_by(Run.created_at.desc())).all()
    out = []
    for run in runs:
        items = session.exec(select(Item).where(Item.run_id == run.id)).all()
        out.append(_run_summary(run, items))
    return out


def _get_run_or_404(run_id: int, session: Session) -> Run:
    run = session.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return run


@app.get("/runs/{run_id}", response_model=RunDetailOut)
def get_run(run_id: int, session: Session = Depends(get_session)):
    run = _get_run_or_404(run_id, session)
    items = session.exec(select(Item).where(Item.run_id == run_id)).all()
    return RunDetailOut(
        id=run.id,
        name=run.name,
        created_at=run.created_at,
        aggregate=_aggregate(items),
        items=[ItemOut.model_validate(i) for i in items],
    )


@app.delete("/runs/{run_id}", status_code=204)
def delete_run(run_id: int, session: Session = Depends(get_session)):
    run = _get_run_or_404(run_id, session)
    session.delete(run)
    session.commit()


SORTABLE_FIELDS = {
    "faithfulness": Item.faithfulness_score,
    "format": Item.format_score,
    "safety": Item.safety_score,
}


@app.get("/runs/{run_id}/flagged", response_model=list[ItemOut])
def get_flagged_items(
    run_id: int,
    threshold: int = Query(FLAG_THRESHOLD, ge=0, le=100),
    sort_by: str = Query("faithfulness", pattern="^(faithfulness|format|safety)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    session: Session = Depends(get_session),
):
    """Items scoring below `threshold` on any of the three dimensions."""
    _get_run_or_404(run_id, session)

    column = SORTABLE_FIELDS[sort_by]
    stmt = (
        select(Item)
        .where(Item.run_id == run_id)
        .where(
            (Item.faithfulness_score < threshold)
            | (Item.format_score < threshold)
            | (Item.safety_score < threshold)
        )
        .order_by(column.desc() if order == "desc" else column.asc())
    )
    items = session.exec(stmt).all()
    return [ItemOut.model_validate(i) for i in items]


@app.get("/compare", response_model=CompareOut)
def compare_runs(
    run_a: int = Query(...),
    run_b: int = Query(...),
    session: Session = Depends(get_session),
):
    a = _get_run_or_404(run_a, session)
    b = _get_run_or_404(run_b, session)
    items_a = session.exec(select(Item).where(Item.run_id == run_a)).all()
    items_b = session.exec(select(Item).where(Item.run_id == run_b)).all()
    return CompareOut(
        run_a=_run_summary(a, items_a),
        run_b=_run_summary(b, items_b),
    )


@app.get("/health")
def health():
    return {"status": "ok"}
