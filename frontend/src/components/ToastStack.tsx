import { CheckCircle2, AlertTriangle, Info, X } from "lucide-react";
import type { ToastMessage } from "../types";

const ICONS = {
  success: CheckCircle2,
  error: AlertTriangle,
  info: Info,
};

const STYLES = {
  success: "border-sonar-green/30 bg-sonar-green/10 text-sonar-green",
  error: "border-sonar-coral/30 bg-sonar-coral/10 text-sonar-coral",
  info: "border-signal-cyan/30 bg-signal-cyan/10 text-signal-cyan",
};

export default function ToastStack({
  toasts,
  onDismiss,
}: {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}) {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 w-80">
      {toasts.map((t) => {
        const Icon = ICONS[t.type];
        return (
          <div
            key={t.id}
            className={`flex items-start gap-2.5 rounded-lg border px-4 py-3 text-sm shadow-panel backdrop-blur-md bg-abyss-900/95 ${STYLES[t.type]}`}
          >
            <Icon className="h-4 w-4 mt-0.5 shrink-0" strokeWidth={2} />
            <p className="flex-1 text-slate-200">{t.message}</p>
            <button onClick={() => onDismiss(t.id)} className="text-slate-500 hover:text-slate-300">
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
