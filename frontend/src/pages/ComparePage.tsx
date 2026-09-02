import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  LabelList,
} from "recharts";
import { compareRuns, listRuns, type CompareResult, type RunSummary } from "../api";

const SERIES_1 = "var(--series-1)";
const SERIES_2 = "var(--series-2)";

function RunSelect({
  runs,
  value,
  onChange,
  label,
}: {
  runs: RunSummary[];
  value: number | "";
  onChange: (v: number | "") => void;
  label: string;
}) {
  return (
    <div className="field" style={{ minWidth: 240 }}>
      <label>{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value ? Number(e.target.value) : "")}
      >
        <option value="">Select a run…</option>
        {runs.map((r) => (
          <option key={r.id} value={r.id}>
            {r.name}
          </option>
        ))}
      </select>
    </div>
  );
}

function CustomLegend({ nameA, nameB }: { nameA: string; nameB: string }) {
  return (
    <div className="legend-row">
      <span className="legend-swatch">
        <span className="swatch" style={{ background: SERIES_1 }} />
        {nameA}
      </span>
      <span className="legend-swatch">
        <span className="swatch" style={{ background: SERIES_2 }} />
        {nameB}
      </span>
    </div>
  );
}

export default function ComparePage() {
  const [params, setParams] = useSearchParams();
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [runA, setRunA] = useState<number | "">(params.get("a") ? Number(params.get("a")) : "");
  const [runB, setRunB] = useState<number | "">(params.get("b") ? Number(params.get("b")) : "");
  const [result, setResult] = useState<CompareResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listRuns().then(setRuns).catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  useEffect(() => {
    const next = new URLSearchParams();
    if (runA) next.set("a", String(runA));
    if (runB) next.set("b", String(runB));
    setParams(next, { replace: true });

    if (!runA || !runB) {
      setResult(null);
      return;
    }
    if (runA === runB) {
      setError("Pick two different runs to compare.");
      setResult(null);
      return;
    }
    setError(null);
    compareRuns(runA, runB)
      .then(setResult)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runA, runB]);

  const chartData = useMemo(() => {
    if (!result) return [];
    const { run_a, run_b } = result;
    return [
      {
        dimension: "Faithfulness",
        runA: run_a.aggregate.faithfulness.average,
        runB: run_b.aggregate.faithfulness.average,
      },
      {
        dimension: "Format",
        runA: run_a.aggregate.format.average,
        runB: run_b.aggregate.format.average,
      },
      {
        dimension: "Safety",
        runA: run_a.aggregate.safety.average,
        runB: run_b.aggregate.safety.average,
      },
    ];
  }, [result]);

  return (
    <div>
      <h1>Compare runs</h1>
      <p className="page-subtitle">
        Side-by-side aggregate scores per dimension — the "before/after" view for
        a prompt or model change.
      </p>

      <div className="compare-select-row">
        <RunSelect runs={runs} value={runA} onChange={setRunA} label="Run A" />
        <RunSelect runs={runs} value={runB} onChange={setRunB} label="Run B" />
      </div>

      {error && <div className="error-banner">{error}</div>}

      {result && (
        <div className="card">
          <h2>
            {result.run_a.name} vs. {result.run_b.name}
          </h2>
          <div className="viz-root" style={{ width: "100%", height: 340 }}>
            <ResponsiveContainer>
              <BarChart data={chartData} margin={{ top: 24, right: 16, left: 0, bottom: 0 }} barGap={4} barCategoryGap="28%">
                <CartesianGrid stroke="var(--gridline)" vertical={false} />
                <XAxis
                  dataKey="dimension"
                  axisLine={{ stroke: "var(--baseline)" }}
                  tickLine={false}
                  tick={{ fill: "var(--text-secondary)", fontSize: 13 }}
                />
                <YAxis
                  domain={[0, 100]}
                  ticks={[0, 20, 40, 60, 80, 100]}
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: "var(--text-muted)", fontSize: 12 }}
                />
                <Tooltip
                  cursor={{ fill: "var(--surface-2)" }}
                  contentStyle={{
                    background: "var(--surface)",
                    border: "1px solid var(--border)",
                    borderRadius: 8,
                    fontSize: 13,
                    color: "var(--text-primary)",
                  }}
                  labelStyle={{ color: "var(--text-primary)", fontWeight: 600 }}
                />
                <Legend content={<CustomLegend nameA={result.run_a.name} nameB={result.run_b.name} />} />
                <Bar dataKey="runA" name={result.run_a.name} fill={SERIES_1} radius={[4, 4, 0, 0]} maxBarSize={24}>
                  <LabelList dataKey="runA" position="top" fill="var(--text-secondary)" fontSize={12} />
                </Bar>
                <Bar dataKey="runB" name={result.run_b.name} fill={SERIES_2} radius={[4, 4, 0, 0]} maxBarSize={24}>
                  <LabelList dataKey="runB" position="top" fill="var(--text-secondary)" fontSize={12} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
