import type { ConfidenceBand } from "../types";

const BAND_COLOR: Record<ConfidenceBand, string> = {
  High: "bg-sonar-green",
  Medium: "bg-sonar-amber",
  Low: "bg-sonar-coral",
};

export default function ConfidenceBar({
  confidence,
  band,
}: {
  confidence: number;
  band: ConfidenceBand;
}) {
  const pct = Math.round(confidence * 100);
  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-1 text-xs font-mono">
        <span className="text-slate-400">{band} confidence</span>
        <span className="text-slate-300">{pct}%</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-abyss-700/80 overflow-hidden">
        <div
          className={`h-full rounded-full ${BAND_COLOR[band]} transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
