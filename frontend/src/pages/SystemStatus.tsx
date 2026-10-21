import { useEffect, useState } from "react";
import { PageHeader } from "../components/PageHeader";
import { useAppData } from "../hooks/AppDataContext";
import { getSystemStatus } from "../services/api";
import type { SystemStatusResponse } from "../types";

const ROWS: { key: keyof SystemStatusResponse; label: string }[] = [
  { key: "backend_api", label: "Backend API" },
  { key: "detection_engine", label: "Detection Engine" },
  { key: "model_status", label: "Model Status" },
  { key: "classes", label: "Classes" },
  { key: "geolocation", label: "Geolocation" },
  { key: "database", label: "Database" },
  { key: "map_service", label: "Map Service" },
];

function statusColor(value: string) {
  if (value === "Online" || value === "Loaded") return "text-sonar-green";
  if (value === "Prototype" || value === "Simulation") return "text-sonar-amber";
  return "text-slate-400";
}

export default function SystemStatus() {
  const { backendOnline, health } = useAppData();
  const [status, setStatus] = useState<SystemStatusResponse | null>(null);

  useEffect(() => {
    getSystemStatus()
      .then(setStatus)
      .catch(() => setStatus(null));
  }, [backendOnline]);

  const fallback: SystemStatusResponse = {
    backend_api: backendOnline ? "Online" : "Offline",
    detection_engine: "Prototype",
    model_status: "Offline",
    classes: 0,
    geolocation: "Simulation",
    database: "Local Storage",
    map_service: "Online",
    processing_mode: "real",
  };

  const data = status ?? fallback;

  return (
    <div>
      <PageHeader title="System Status" subtitle="Live status of AquaScan AI backend components" />

      <div className="rounded-xl border border-abyss-700/60 bg-abyss-900/70 divide-y divide-abyss-800/60">
        {ROWS.map(({ key, label }) => (
          <div key={key} className="flex items-center justify-between px-5 py-4">
            <p className="text-sm text-slate-300">{label}</p>
            <p className={`text-sm font-mono font-medium flex items-center gap-2 ${statusColor(String(data[key]))}`}>
              <span className="h-1.5 w-1.5 rounded-full bg-current" />
              {data[key]}
            </p>
          </div>
        ))}
      </div>

      <div className="mt-6 rounded-xl border border-sonar-amber/30 bg-sonar-amber/5 p-5">
        <p className="text-xs uppercase tracking-wider text-slate-500 mb-1">Processing Mode</p>
        <p className="font-display text-lg font-semibold text-sonar-amber">{data.processing_mode}</p>
      </div>

      {health && (
        <div className="mt-4 text-xs font-mono text-slate-600">
          Detector: SonarDeNet · Backend version: {health.version}
        </div>
      )}
    </div>
  );
}
