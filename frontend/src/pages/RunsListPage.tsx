import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { deleteRun, listRuns, type RunSummary } from "../api";
import StatusBadge from "../components/StatusBadge";

export default function RunsListPage() {
  const [runs, setRuns] = useState<RunSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setRuns(await listRuns());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleDelete(id: number) {
    if (!confirm("Delete this run? This cannot be undone.")) return;
    await deleteRun(id);
    load();
  }

  return (
    <div>
      <h1>Runs</h1>
      <p className="page-subtitle">
        Every CSV you've evaluated, with an at-a-glance score per dimension.
      </p>

      {error && <div className="error-banner">{error}</div>}

      {runs === null && !error && <p>Loading…</p>}

      {runs?.length === 0 && (
        <div className="empty-state">
          <p>No runs yet.</p>
          <p style={{ marginTop: 8 }}>
            <Link to="/upload" className="btn primary">
              Upload your first CSV
            </Link>
          </p>
        </div>
      )}

      {runs?.map((run) => (
        <div className="run-list-item" key={run.id}>
          <div>
            <div style={{ fontWeight: 600 }}>{run.name}</div>
            <div className="run-meta">
              {run.item_count} item{run.item_count === 1 ? "" : "s"} ·{" "}
              {new Date(run.created_at).toLocaleString()}
            </div>
            <div className="badge-row" style={{ marginTop: 8 }}>
              <StatusBadge color={run.aggregate.faithfulness.color} />
              <StatusBadge color={run.aggregate.format.color} />
              <StatusBadge color={run.aggregate.safety.color} />
            </div>
          </div>
          <div className="run-actions">
            <Link className="btn" to={`/runs/${run.id}`}>
              View
            </Link>
            <Link className="btn" to={`/runs/${run.id}/flagged`}>
              Flagged items
            </Link>
            <button className="btn" onClick={() => handleDelete(run.id)}>
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
