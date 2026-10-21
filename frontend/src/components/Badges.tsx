import type { Severity } from "../types";

const SEVERITY_STYLE: Record<Severity, string> = {
  High: "bg-sonar-coral/10 text-sonar-coral border-sonar-coral/30",
  Medium: "bg-sonar-amber/10 text-sonar-amber border-sonar-amber/30",
  Low: "bg-sonar-green/10 text-sonar-green border-sonar-green/30",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${SEVERITY_STYLE[severity]}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {severity}
    </span>
  );
}

export function PrototypeBadge({ label = "Prototype / Simulated Detection" }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-sonar-amber/30 bg-sonar-amber/10 px-2.5 py-1 text-xs font-medium text-sonar-amber font-mono">
      ⚠ {label}
    </span>
  );
}
