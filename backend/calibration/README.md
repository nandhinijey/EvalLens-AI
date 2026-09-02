# Judge Calibration

`labeled_set_template.csv` has 20 pre-built prompt/context/response examples
spanning faithful/unfaithful, valid/invalid-format, and safe/unsafe cases.

1. Copy it: `cp labeled_set_template.csv labeled_set.csv`
2. Open `labeled_set.csv` and fill in `human_faithfulness`, `human_format`,
   and `human_safety` with your own 0-100 scores for each row (or swap in
   your own examples entirely — the columns just need to stay the same).
3. Run the calibration script from `backend/`:

   ```bash
   python -m calibration.calibrate
   ```

This calls all three judges against every row and prints an agreement
report (mean absolute error, % of items within a tolerance band, % landing
in the same low/medium/high tier as your label) plus a per-item breakdown
written to `calibration_results.csv`.

Useful flags: `--input`, `--output`, `--tolerance` (default 15 points),
`--concurrency` (default from `JUDGE_CONCURRENCY` env var, 5).
