import type { ScoreColor } from "../api";

const LABELS: Record<ScoreColor, string> = {
  green: "Healthy",
  yellow: "Needs review",
  red: "Critical",
};

export default function StatusBadge({ color }: { color: ScoreColor }) {
  return (
    <span className={`status-badge ${color}`}>
      <span className="dot" />
      {LABELS[color]}
    </span>
  );
}
