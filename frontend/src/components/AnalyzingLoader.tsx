import { useEffect, useState } from "react";
import { Loader2, Check } from "lucide-react";

const STAGES = [
  "Preprocessing sonar image",
  "Searching for anomalies",
  "Calculating confidence",
  "Preparing report",
];

export default function AnalyzingLoader() {
  const [activeStage, setActiveStage] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStage((s) => Math.min(s + 1, STAGES.length - 1));
    }, 550);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="rounded-xl border border-abyss-700/60 bg-abyss-900/70 p-8">
      <div className="flex items-center gap-2 mb-6">
        <Loader2 className="h-4 w-4 text-signal-cyan animate-spin" />
        <p className="font-display text-sm font-semibold text-white tracking-tight">
          Analyzing Sonar Data...
        </p>
      </div>
      <div className="space-y-3">
        {STAGES.map((stage, idx) => {
          const done = idx < activeStage;
          const active = idx === activeStage;
          return (
            <div key={stage} className="flex items-center gap-3">
              <div
                className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[10px] ${
                  done
                    ? "bg-sonar-green/20 border-sonar-green/40 text-sonar-green"
                    : active
                    ? "border-signal-cyan/60 text-signal-cyan"
                    : "border-abyss-600 text-slate-600"
                }`}
              >
                {done ? <Check className="h-3 w-3" /> : idx + 1}
              </div>
              <p
                className={`text-sm font-mono ${
                  done ? "text-slate-400" : active ? "text-slate-100" : "text-slate-600"
                }`}
              >
                {stage}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
