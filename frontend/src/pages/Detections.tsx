import { useMemo, useState } from "react";
import { Search, Crosshair, MapPin } from "lucide-react";
import { PageHeader } from "../components/PageHeader";
import { SeverityBadge } from "../components/Badges";
import ConfidenceBar from "../components/ConfidenceBar";
import EmptyState from "../components/EmptyState";
import { useAppData } from "../hooks/AppDataContext";
import type { Severity } from "../types";

export default function Detections() {
  const { detections } = useAppData();
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("All Types");
  const [confidenceFilter, setConfidenceFilter] = useState("All Confidence");
  const [severityFilter, setSeverityFilter] = useState<"All Severity" | Severity>("All Severity");

  const objectTypes = useMemo(
    () => ["All Types", ...Array.from(new Set(detections.map((d) => d.class_name)))],
    [detections]
  );

  const filtered = detections.filter((d) => {
    const matchesSearch =
      search.trim() === "" ||
      d.class_name.toLowerCase().includes(search.toLowerCase()) ||
      d.id.toLowerCase().includes(search.toLowerCase());
    const matchesType = typeFilter === "All Types" || d.class_name === typeFilter;
    const matchesConfidence =
      confidenceFilter === "All Confidence" || d.confidence_band === confidenceFilter;
    const matchesSeverity = severityFilter === "All Severity" || d.severity === severityFilter;
    return matchesSearch && matchesType && matchesConfidence && matchesSeverity;
  });

  return (
    <div>
      <PageHeader title="All Detections" subtitle="Browse, search, and filter every detected anomaly" />

      <div className="flex flex-col md:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by object type or detection ID..."
            className="w-full rounded-lg border border-abyss-700 bg-abyss-900/70 pl-9 pr-3 py-2.5 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-signal-cyan/50"
          />
        </div>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="rounded-lg border border-abyss-700 bg-abyss-900/70 px-3 py-2.5 text-sm text-slate-300 focus:outline-none focus:border-signal-cyan/50"
        >
          {objectTypes.map((t) => (
            <option key={t}>{t}</option>
          ))}
        </select>
        <select
          value={confidenceFilter}
          onChange={(e) => setConfidenceFilter(e.target.value)}
          className="rounded-lg border border-abyss-700 bg-abyss-900/70 px-3 py-2.5 text-sm text-slate-300 focus:outline-none focus:border-signal-cyan/50"
        >
          <option>All Confidence</option>
          <option>High</option>
          <option>Medium</option>
          <option>Low</option>
        </select>
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value as "All Severity" | Severity)}
          className="rounded-lg border border-abyss-700 bg-abyss-900/70 px-3 py-2.5 text-sm text-slate-300 focus:outline-none focus:border-signal-cyan/50"
        >
          <option>All Severity</option>
          <option>High</option>
          <option>Medium</option>
          <option>Low</option>
        </select>
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon={Crosshair}
          title="No detections yet"
          description="Run a sonar analysis from the Sonar Analysis page to populate this list."
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((d) => (
            <div key={d.id} className="rounded-xl border border-abyss-700/60 bg-abyss-900/70 p-4 hover:border-abyss-600 transition-colors">
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs font-mono text-slate-600">{d.id}</p>
                <SeverityBadge severity={d.severity} />
              </div>
              <p className="font-display text-base font-semibold text-slate-100 mb-3">{d.class_name}</p>
              <ConfidenceBar confidence={d.confidence} band={d.confidence_band} />
              <div className="flex items-center gap-1.5 mt-3 text-[11px] text-slate-600 font-mono">
                <MapPin className="h-3 w-3" />
                {d.latitude !== null && d.longitude !== null
                  ? `${d.latitude.toFixed(4)}, ${d.longitude.toFixed(4)} (${d.location_status === "estimated" ? "Estimated Location" : d.location_status})`
                  : "Location unavailable"}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
