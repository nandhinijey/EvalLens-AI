import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getFlaggedItems, getRun, type Item } from "../api";
import ConfidenceTag from "../components/ConfidenceTag";

type SortKey = "faithfulness" | "format" | "safety";

const DIMENSIONS: { key: SortKey; label: string }[] = [
  { key: "faithfulness", label: "Faithfulness" },
  { key: "format", label: "Format compliance" },
  { key: "safety", label: "Safety / PII" },
];

function scoreClass(score: number, threshold: number) {
  if (score < threshold) return "status-badge red";
  if (score < threshold + 15) return "status-badge yellow";
  return "status-badge green";
}

function DimensionCell({
  score,
  rationale,
  confidence,
  threshold,
}: {
  score: number;
  rationale: string;
  confidence: "high" | "low";
  threshold: number;
}) {
  return (
    <td className="score-cell">
      <span className={scoreClass(score, threshold)} style={{ marginBottom: 4 }}>
        <span className="dot" />
        {score}
      </span>
      <div className="rationale" style={{ marginTop: 4, fontSize: "0.82rem" }}>
        {rationale}
      </div>
      <ConfidenceTag confidence={confidence} />
    </td>
  );
}

export default function FlaggedItemsPage() {
  const { id } = useParams();
  const runId = Number(id);
  const [runName, setRunName] = useState<string>("");
  const [items, setItems] = useState<Item[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [threshold, setThreshold] = useState(70);
  const [sortBy, setSortBy] = useState<SortKey>("faithfulness");
  const [order, setOrder] = useState<"asc" | "desc">("asc");

  useEffect(() => {
    getRun(runId)
      .then((run) => setRunName(run.name))
      .catch(() => {});
  }, [runId]);

  useEffect(() => {
    if (!runId) return;
    getFlaggedItems(runId, { threshold, sortBy, order })
      .then(setItems)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, [runId, threshold, sortBy, order]);

  function toggleSort(key: SortKey) {
    if (sortBy === key) {
      setOrder(order === "asc" ? "desc" : "asc");
    } else {
      setSortBy(key);
      setOrder("asc");
    }
  }

  return (
    <div>
      <h1>Flagged items{runName ? ` — ${runName}` : ""}</h1>
      <p className="page-subtitle">
        Items scoring below the threshold on any dimension. Sort by a column to
        find the worst offenders first. <Link to={`/runs/${runId}`}>Back to run overview</Link>
      </p>

      <div className="field" style={{ maxWidth: 220 }}>
        <label htmlFor="threshold">Flag threshold (below this score on any dimension)</label>
        <input
          id="threshold"
          type="number"
          min={0}
          max={100}
          value={threshold}
          onChange={(e) => setThreshold(Number(e.target.value))}
        />
      </div>

      {error && <div className="error-banner">{error}</div>}

      {items === null && !error && <p>Loading…</p>}

      {items?.length === 0 && (
        <div className="empty-state">Nothing flagged — every item scored at or above {threshold} on all three dimensions.</div>
      )}

      {items && items.length > 0 && (
        <div style={{ overflowX: "auto" }}>
          <table>
            <thead>
              <tr>
                <th>Prompt</th>
                <th>Response</th>
                {DIMENSIONS.map((d) => (
                  <th
                    key={d.key}
                    className="sortable"
                    onClick={() => toggleSort(d.key)}
                  >
                    {d.label} {sortBy === d.key ? (order === "asc" ? "▲" : "▼") : ""}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td className="rationale" title={item.prompt}>
                    {item.prompt.length > 120 ? `${item.prompt.slice(0, 120)}…` : item.prompt}
                  </td>
                  <td className="rationale" title={item.response}>
                    {item.response.length > 120 ? `${item.response.slice(0, 120)}…` : item.response}
                  </td>
                  <DimensionCell
                    score={item.faithfulness_score}
                    rationale={item.faithfulness_rationale}
                    confidence={item.faithfulness_confidence}
                    threshold={threshold}
                  />
                  <DimensionCell
                    score={item.format_score}
                    rationale={item.format_rationale}
                    confidence={item.format_confidence}
                    threshold={threshold}
                  />
                  <DimensionCell
                    score={item.safety_score}
                    rationale={item.safety_rationale}
                    confidence={item.safety_confidence}
                    threshold={threshold}
                  />
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
