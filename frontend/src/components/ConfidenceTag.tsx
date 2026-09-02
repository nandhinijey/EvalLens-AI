export default function ConfidenceTag({ confidence }: { confidence: "high" | "low" }) {
  return (
    <span className={`confidence-tag ${confidence}`}>
      {confidence === "low" ? "⚠ low confidence" : "high confidence"}
    </span>
  );
}
