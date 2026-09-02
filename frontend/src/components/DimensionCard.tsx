import type { DimensionAggregate } from "../api";
import StatusBadge from "./StatusBadge";

export default function DimensionCard({
  label,
  aggregate,
}: {
  label: string;
  aggregate: DimensionAggregate;
}) {
  return (
    <div className="card stat-tile">
      <span className="stat-label">{label}</span>
      <span className="stat-value">{aggregate.average.toFixed(1)}</span>
      <StatusBadge color={aggregate.color} />
    </div>
  );
}
