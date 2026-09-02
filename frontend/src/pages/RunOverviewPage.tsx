import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getRun, type RunDetail } from "../api";
import DimensionCard from "../components/DimensionCard";

export default function RunOverviewPage() {
  const { id } = useParams();
  const [run, setRun] = useState<RunDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getRun(Number(id))
      .then(setRun)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, [id]);

  if (error) return <div className="error-banner">{error}</div>;
  if (!run) return <p>Loading…</p>;

  return (
    <div>
      <h1>{run.name}</h1>
      <p className="page-subtitle">
        {run.items.length} item{run.items.length === 1 ? "" : "s"} · created{" "}
        {new Date(run.created_at).toLocaleString()}
      </p>

      <h2>Aggregate scores</h2>
      <div className="card-grid" style={{ marginBottom: 28 }}>
        <DimensionCard label="Faithfulness" aggregate={run.aggregate.faithfulness} />
        <DimensionCard label="Format compliance" aggregate={run.aggregate.format} />
        <DimensionCard label="Safety / PII" aggregate={run.aggregate.safety} />
      </div>

      <div style={{ display: "flex", gap: 10 }}>
        <Link className="btn primary" to={`/runs/${run.id}/flagged`}>
          View flagged items
        </Link>
        <Link className="btn" to={`/compare?a=${run.id}`}>
          Compare against another run
        </Link>
      </div>
    </div>
  );
}
