import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { evaluateCsv } from "../api";

export default function UploadPage() {
  const [name, setName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!file || !name.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const run = await evaluateCsv(file, name.trim());
      navigate(`/runs/${run.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <h1>Upload a run</h1>
      <p className="page-subtitle">
        CSV with <code>prompt</code>, <code>context</code> (optional), and{" "}
        <code>response</code> columns. Each row is scored on faithfulness, format
        compliance, and safety — this calls the Anthropic API once per judge per
        row, so larger CSVs take longer.
      </p>

      <form className="card" onSubmit={handleSubmit} style={{ maxWidth: 480 }}>
        <div className="field">
          <label htmlFor="run-name">Run name</label>
          <input
            id="run-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. v2 - after prompt fix"
            required
          />
        </div>

        <div className="field">
          <label htmlFor="run-file">CSV file</label>
          <input
            id="run-file"
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            required
          />
        </div>

        {error && <div className="error-banner">{error}</div>}

        <button className="btn primary" type="submit" disabled={busy || !file}>
          {busy ? "Scoring…" : "Evaluate"}
        </button>
      </form>
    </div>
  );
}
