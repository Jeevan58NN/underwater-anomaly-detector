import { FileDown, FileJson, FileBarChart } from "lucide-react";
import { PageHeader } from "../components/PageHeader";
import { SeverityBadge } from "../components/Badges";
import EmptyState from "../components/EmptyState";
import ToastStack from "../components/ToastStack";
import { useToast } from "../hooks/useToast";
import { useAppData } from "../hooks/AppDataContext";
import { downloadCSV, downloadJSON } from "../services/api";

export default function Reports() {
  const { detections, incrementReportsCount } = useAppData();
  const { toasts, pushToast, dismissToast } = useToast();

  async function handleDownload(kind: "csv" | "json") {
    try {
      if (kind === "csv") {
        await downloadCSV();
      } else {
        await downloadJSON();
      }
      incrementReportsCount();
      pushToast("success", `${kind.toUpperCase()} report downloaded.`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Download failed.";
      pushToast("error", message);
    }
  }

  return (
    <div>
      <PageHeader title="Anomaly Reports" subtitle="Export detection results for offline review">
        <button
          onClick={() => handleDownload("csv")}
          className="inline-flex items-center gap-2 rounded-lg border border-abyss-700 bg-abyss-900/70 px-4 py-2 text-sm font-medium text-slate-200 hover:border-signal-cyan/40 transition-colors"
        >
          <FileDown className="h-4 w-4" /> Download CSV
        </button>
        <button
          onClick={() => handleDownload("json")}
          className="inline-flex items-center gap-2 rounded-lg bg-signal-cyan px-4 py-2 text-sm font-semibold text-abyss-950 hover:bg-signal-teal transition-colors"
        >
          <FileJson className="h-4 w-4" /> Download JSON
        </button>
      </PageHeader>

      {detections.length === 0 ? (
        <EmptyState
          icon={FileBarChart}
          title="No detections to report"
          description="Reports are generated from analyzed detections. Run a sonar scan first."
        />
      ) : (
        <div className="rounded-xl border border-abyss-700/60 bg-abyss-900/70 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-abyss-700/60 text-left text-xs uppercase tracking-wider text-slate-500">
                <th className="px-4 py-3 font-medium">ID</th>
                <th className="px-4 py-3 font-medium">Object</th>
                <th className="px-4 py-3 font-medium text-right">Confidence</th>
                <th className="px-4 py-3 font-medium text-right">Latitude</th>
                <th className="px-4 py-3 font-medium text-right">Longitude</th>
                <th className="px-4 py-3 font-medium">Severity</th>
              </tr>
            </thead>
            <tbody>
              {detections.map((d) => (
                <tr key={d.id} className="border-b border-abyss-800/60 last:border-0 hover:bg-abyss-800/40">
                  <td className="px-4 py-3 font-mono text-xs text-slate-500">{d.id}</td>
                  <td className="px-4 py-3 text-slate-200">{d.class_name}</td>
                  <td className="px-4 py-3 text-right font-mono text-slate-300">{Math.round(d.confidence * 100)}%</td>
                  <td className="px-4 py-3 text-right font-mono text-slate-400">
                    {d.latitude !== null ? d.latitude.toFixed(4) : "-"}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-slate-400">
                    {d.longitude !== null ? d.longitude.toFixed(4) : "-"}
                  </td>
                  <td className="px-4 py-3">
                    <SeverityBadge severity={d.severity} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <ToastStack toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
