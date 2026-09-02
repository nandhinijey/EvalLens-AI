# Demo Showcase Data

Two CSVs with the *same* prompts/contexts, deliberately scored to produce a
compelling before/after story in the Run Comparison view:

- **`bad_run.csv`** — responses that hallucinate facts not in the context,
  ignore requested JSON formats, and leak PII (emails, SSNs) that shouldn't
  be in a customer-facing reply.
- **`improved_run.csv`** — the same 8 scenarios with corrected responses:
  faithful to context, properly formatted, and PII-free.

## Try it

1. Start the backend (`uvicorn app.main:app --reload` from `backend/`).
2. Upload `bad_run.csv` via `POST /evaluate` (or the frontend's upload
   screen) as a run named e.g. "v1 - before fix".
3. Upload `improved_run.csv` as a run named e.g. "v2 - after fix".
4. Open the Run Comparison view and compare the two — faithfulness, format
   compliance, and safety should all jump from red/yellow into the green.
