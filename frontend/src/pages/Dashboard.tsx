import { useNavigate } from "react-router-dom";
import { Radar, Crosshair, ShieldAlert, Gauge, ArrowRight, FileText } from "lucide-react";
import { PageHeader } from "../components/PageHeader";
import KpiCard from "../components/KpiCard";
import UploadDropzone from "../components/UploadDropzone";
import { useAppData } from "../hooks/AppDataContext";
import { useToast } from "../hooks/useToast";
import ToastStack from "../components/ToastStack";

const PIPELINE_STAGES = [
  "Sonar Image",
  "Preprocessing",
  "AI Detection",
  "Confidence Filtering",
  "Geotagging",
  "Report",
];

export default function Dashboard() {
  const navigate = useNavigate();
  const { detections, reportsCount } = useAppData();
  const { toasts, dismissToast } = useToast();

  const totalDetections = detections.length;
  const artificialDetections = detections.filter(d => d.classification_type === "artificial").length;
  const naturalDetections = detections.filter(d => d.classification_type === "natural").length;
  const highPriorityDetections = detections.filter(d => d.severity === "High").length;

  function handleFile(file: File) {
    navigate("/sonar-analysis", { state: { pendingFile: file } });
  }

  return (
    <div>
      <PageHeader
        title="Underwater Anomaly Detection"
        subtitle="Analyze Side-Scan Sonar imagery for potential marine debris"
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
        <KpiCard label="Total Detections" value={totalDetections} icon={Radar} accent="cyan" />
        <KpiCard label="Artificial Objects" value={artificialDetections} icon={Crosshair} accent="amber" />
        <KpiCard label="Natural Objects" value={naturalDetections} icon={ShieldAlert} accent="green" />
        <KpiCard label="High Priority" value={highPriorityDetections} icon={Gauge} accent="coral" />
        <KpiCard label="Reports Generated" value={reportsCount} icon={FileText} accent="cyan" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <p className="text-sm font-medium text-slate-300 mb-3">Start a New Analysis</p>
          <UploadDropzone onFileSelected={handleFile} />
        </div>

        <div className="rounded-xl border border-abyss-700/60 bg-abyss-900/70 p-5">
          <p className="text-sm font-medium text-slate-300 mb-4">Detection Pipeline</p>
          <div className="space-y-0">
            {PIPELINE_STAGES.map((stage, idx) => (
              <div key={stage} className="flex items-center gap-3">
                <div className="flex flex-col items-center">
                  <div className="h-2 w-2 rounded-full bg-signal-cyan/70" />
                  {idx < PIPELINE_STAGES.length - 1 && (
                    <div className="w-px h-6 bg-abyss-700" />
                  )}
                </div>
                <p className="text-sm text-slate-400 font-mono -mt-0.5">{stage}</p>
              </div>
            ))}
          </div>
          <div className="mt-5 pt-4 border-t border-abyss-700/60 space-y-1.5 text-xs font-mono">
            <p className="text-slate-400">
              Active Model: <span className="text-sonar-green font-semibold">SonarDeNet Detector (best.pt)</span>
            </p>
            <p className="text-slate-500">
              Pipeline Status: <span className="text-signal-cyan font-semibold">Operational / Real AI Mode</span>
            </p>
          </div>
        </div>
      </div>

      <button
        onClick={() => navigate("/sonar-analysis")}
        className="mt-6 inline-flex items-center gap-1.5 text-sm text-signal-cyan hover:text-signal-teal transition-colors"
      >
        Go to Sonar Analysis <ArrowRight className="h-3.5 w-3.5" />
      </button>

      <ToastStack toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
