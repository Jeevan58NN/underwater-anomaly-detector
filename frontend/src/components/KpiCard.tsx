import type { LucideIcon } from "lucide-react";

export default function KpiCard({
  label,
  value,
  icon: Icon,
  accent = "cyan",
}: {
  label: string;
  value: string | number;
  icon: LucideIcon;
  accent?: "cyan" | "amber" | "coral" | "green";
}) {
  const accentMap: Record<string, string> = {
    cyan: "text-signal-cyan bg-signal-cyan/10 border-signal-cyan/20",
    amber: "text-sonar-amber bg-sonar-amber/10 border-sonar-amber/20",
    coral: "text-sonar-coral bg-sonar-coral/10 border-sonar-coral/20",
    green: "text-sonar-green bg-sonar-green/10 border-sonar-green/20",
  };

  return (
    <div className="rounded-xl border border-abyss-700/60 bg-abyss-900/70 p-5 hover:border-abyss-600 transition-colors">
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs font-medium uppercase tracking-wider text-slate-500">{label}</p>
        <div className={`flex h-8 w-8 items-center justify-center rounded-lg border ${accentMap[accent]}`}>
          <Icon className="h-4 w-4" strokeWidth={2} />
        </div>
      </div>
      <p className="font-display text-3xl font-semibold text-white tracking-tight">{value}</p>
    </div>
  );
}
