"""Calibration script.

Runs the three judges against a hand-labeled test set and reports agreement
between the judges' scores and human-assigned labels, per dimension.

Usage:
    python -m calibration.calibrate [--input PATH] [--output PATH] [--tolerance N]

Input CSV must have columns:
    prompt, context, response,
    human_faithfulness, human_format, human_safety
(each human_* column holds a 0-100 score you assigned by hand).

See calibration/labeled_set_template.csv for the expected shape — copy it,
fill in ~20 real examples and your own scores, then point --input at it.
"""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

# Allow running as `python -m calibration.calibrate` or `python calibration/calibrate.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from concurrent.futures import ThreadPoolExecutor, as_completed

from app.config import JUDGE_CONCURRENCY
from app.judges import EvaluationResult, evaluate_item

DEFAULT_INPUT = Path(__file__).parent / "labeled_set.csv"
DEFAULT_OUTPUT = Path(__file__).parent / "calibration_results.csv"
DEFAULT_TOLERANCE = 15

DIMENSIONS = ["faithfulness", "format", "safety"]


def _tier(score: float) -> str:
    if score >= 80:
        return "high"
    if score >= 60:
        return "medium"
    return "low"


@dataclass
class RowResult:
    index: int
    human: dict[str, int]
    judge: dict[str, int]
    rationale: dict[str, str]


def _judge_scores(result: EvaluationResult) -> dict[str, int]:
    return {
        "faithfulness": result.faithfulness.score,
        "format": result.format_compliance.score,
        "safety": result.safety.score,
    }


def _judge_rationales(result: EvaluationResult) -> dict[str, str]:
    return {
        "faithfulness": result.faithfulness.rationale,
        "format": result.format_compliance.rationale,
        "safety": result.safety.rationale,
    }


def load_labeled_set(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    required = {
        "prompt",
        "context",
        "response",
        "human_faithfulness",
        "human_format",
        "human_safety",
    }
    if not rows:
        raise ValueError(f"{path} has no data rows.")
    missing = required - set(rows[0].keys())
    if missing:
        raise ValueError(f"{path} is missing required columns: {sorted(missing)}")

    for i, row in enumerate(rows):
        for col in ("human_faithfulness", "human_format", "human_safety"):
            value = (row.get(col) or "").strip()
            if not value.isdigit() or not (0 <= int(value) <= 100):
                raise ValueError(
                    f"{path}, row {i + 2}: '{col}' must be a 0-100 integer score "
                    f"you assign by hand (got {value!r}). Fill in every human_* "
                    "column before running calibration."
                )
    return rows


def score_row(index: int, row: dict[str, str]) -> RowResult:
    result = evaluate_item(row["prompt"], row["context"], row["response"])
    return RowResult(
        index=index,
        human={
            "faithfulness": int(row["human_faithfulness"]),
            "format": int(row["human_format"]),
            "safety": int(row["human_safety"]),
        },
        judge=_judge_scores(result),
        rationale=_judge_rationales(result),
    )


def run_calibration(
    rows: list[dict[str, str]], concurrency: int = JUDGE_CONCURRENCY
) -> list[RowResult]:
    results: list[RowResult | None] = [None] * len(rows)
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {
            pool.submit(score_row, i, row): i for i, row in enumerate(rows)
        }
        for future in as_completed(futures):
            i = futures[future]
            try:
                results[i] = future.result()
            except Exception as exc:  # noqa: BLE001
                print(f"  [row {i}] FAILED: {exc}", file=sys.stderr)
    return [r for r in results if r is not None]


def summarize(results: list[RowResult], tolerance: int) -> None:
    print(f"\n{'Dimension':<14} {'MAE':>8} {'% within tol.':>15} {'% same tier':>13}")
    print("-" * 54)

    overall_within = []
    overall_tier = []

    for dim in DIMENSIONS:
        diffs = [abs(r.judge[dim] - r.human[dim]) for r in results]
        within = [d <= tolerance for d in diffs]
        same_tier = [
            _tier(r.judge[dim]) == _tier(r.human[dim]) for r in results
        ]
        overall_within.extend(within)
        overall_tier.extend(same_tier)

        mae = statistics.mean(diffs) if diffs else float("nan")
        within_pct = 100 * sum(within) / len(within) if within else float("nan")
        tier_pct = 100 * sum(same_tier) / len(same_tier) if same_tier else float("nan")
        print(f"{dim:<14} {mae:>8.1f} {within_pct:>14.1f}% {tier_pct:>12.1f}%")

    overall_within_pct = 100 * sum(overall_within) / len(overall_within)
    overall_tier_pct = 100 * sum(overall_tier) / len(overall_tier)
    print("-" * 54)
    print(
        f"{'OVERALL':<14} {'':>8} {overall_within_pct:>14.1f}% {overall_tier_pct:>12.1f}%"
    )
    print(
        f"\nAgreement (score within ±{tolerance}): {overall_within_pct:.1f}%"
        f"   |   Agreement (same tier: low <60 / medium 60-79 / high 80+): "
        f"{overall_tier_pct:.1f}%"
    )


def write_details(results: list[RowResult], rows: list[dict[str, str]], output: Path) -> None:
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["index", "prompt"]
        for dim in DIMENSIONS:
            header += [f"{dim}_human", f"{dim}_judge", f"{dim}_diff", f"{dim}_rationale"]
        writer.writerow(header)
        for r in results:
            row = [r.index, rows[r.index]["prompt"][:80]]
            for dim in DIMENSIONS:
                row += [
                    r.human[dim],
                    r.judge[dim],
                    r.judge[dim] - r.human[dim],
                    r.rationale[dim],
                ]
            writer.writerow(row)
    print(f"\nPer-item details written to {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--tolerance", type=int, default=DEFAULT_TOLERANCE)
    parser.add_argument("--concurrency", type=int, default=JUDGE_CONCURRENCY)
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Input file not found: {args.input}", file=sys.stderr)
        print(
            "Copy calibration/labeled_set_template.csv, fill in ~20 hand-scored "
            "examples, and pass it via --input.",
            file=sys.stderr,
        )
        sys.exit(1)

    rows = load_labeled_set(args.input)
    print(f"Loaded {len(rows)} labeled examples from {args.input}")
    print("Running judges (this calls the Anthropic API for every row)...")

    results = run_calibration(rows, concurrency=args.concurrency)
    if not results:
        print("No rows were successfully scored.", file=sys.stderr)
        sys.exit(1)

    results.sort(key=lambda r: r.index)
    summarize(results, args.tolerance)
    write_details(results, rows, args.output)


if __name__ == "__main__":
    main()
