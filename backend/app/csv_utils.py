import csv
import io

REQUIRED_COLUMNS = {"prompt", "response"}


class CSVValidationError(ValueError):
    pass


def parse_csv(raw_bytes: bytes) -> list[dict[str, str]]:
    """Parse an uploaded CSV into prompt/context/response rows.

    `context` is optional (defaults to empty string) since not every eval
    row needs grounding context to check format/safety.
    """
    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CSVValidationError(f"Could not decode file as UTF-8: {exc}") from exc

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise CSVValidationError("CSV file is empty.")

    columns = {c.strip().lower() for c in reader.fieldnames}
    missing = REQUIRED_COLUMNS - columns
    if missing:
        raise CSVValidationError(
            f"CSV is missing required column(s): {sorted(missing)}. "
            f"Expected columns: prompt, context (optional), response."
        )

    normalized_fieldnames = {c: c.strip().lower() for c in reader.fieldnames}

    rows: list[dict[str, str]] = []
    for raw_row in reader:
        row = {normalized_fieldnames[k]: (v or "") for k, v in raw_row.items() if k}
        rows.append(
            {
                "prompt": row.get("prompt", ""),
                "context": row.get("context", ""),
                "response": row.get("response", ""),
            }
        )

    if not rows:
        raise CSVValidationError("CSV has a header but no data rows.")

    return rows
