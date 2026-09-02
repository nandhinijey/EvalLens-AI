# TrustLens

LLM output evaluation & guardrails tool. Upload a CSV of prompt/context/response
triples, score every row on **faithfulness**, **format compliance**, and
**safety/PII leakage** with Claude-as-judge, and compare runs (e.g. an old
prompt vs. a new one) side by side.

## Project layout

```
backend/
  app/
    judges/              faithfulness.py, format_compliance.py, safety.py, base.py
    models.py             SQLModel: Run, Item
    main.py                FastAPI app (/evaluate, /runs, /compare, ...)
  calibration/
    calibrate.py           agreement-with-human-labels report
    labeled_set_template.csv
  demo_data/
    bad_run.csv / improved_run.csv    before/after showcase data
frontend/
  src/pages/               Upload, Runs list, Run Overview, Flagged Items, Compare
```

## 1. Backend setup

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in ANTHROPIC_API_KEY
```

Run the API:

```bash
uvicorn app.main:app --reload
```

API docs at `http://localhost:8000/docs`. SQLite database is created
automatically at `backend/trustlens.db` on first run.

## 2. Judge calibration

Before trusting the judges, sanity-check them against your own labels:

```bash
cd backend
cp calibration/labeled_set_template.csv calibration/labeled_set.csv
# open labeled_set.csv and fill in human_faithfulness / human_format / human_safety (0-100)
python -m calibration.calibrate
```

Prints per-dimension mean absolute error and agreement % (score within a
tolerance band, and same low/60/medium/80/high tier as your label), plus a
per-item CSV in `calibration/calibration_results.csv`. See
`backend/calibration/README.md` for details.

## 3. Frontend setup

```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_URL defaults to http://localhost:8000
npm run dev
```

Open `http://localhost:5173`.

## 4. Try the before/after demo

`backend/demo_data/` has two CSVs with identical prompts — one with
deliberately bad responses (hallucinated facts, broken JSON, leaked PII/SSNs)
and one with corrected responses. Upload both from the Upload page (e.g. named
"v1 - before fix" and "v2 - after fix"), then open **Compare** and pick both
runs — faithfulness, format compliance, and safety all jump from red to
green. See `backend/demo_data/README.md`.

## Deploying

- **Backend**: any host that runs `uvicorn app.main:app` works (Render,
  Fly.io, Railway, etc.). Set `ANTHROPIC_API_KEY`, and `DATABASE_URL` if you
  want persistent storage beyond the container's local disk (e.g. a managed
  Postgres — swap `sqlite:///...` for a `postgresql://...` URL; SQLModel/
  SQLAlchemy handles the rest). Set `CORS_ORIGINS` to your deployed frontend
  URL.
- **Frontend**: `npm run build` produces a static `dist/` — deploy to
  Vercel, Netlify, or serve it from the backend host. Set `VITE_API_URL` to
  the deployed backend URL at build time.

## Data model

- **Run**: `id`, `name`, `created_at`
- **Item**: `id`, `run_id`, `prompt`, `context`, `response`, plus per
  dimension (`faithfulness` / `format` / `safety`): `*_score` (0-100),
  `*_rationale`, `*_confidence` (`high`/`low`)

## Config (env vars, all optional with sane defaults)

See `backend/.env.example` — model choice, DB URL, flag/color thresholds,
judge retry count and concurrency, CORS origins.
