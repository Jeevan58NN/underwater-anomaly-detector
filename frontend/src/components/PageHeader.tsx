import { Sparkles } from "lucide-react";

export function PageHeader({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-6">
      <div>
        <h1 className="font-display text-2xl font-semibold text-white tracking-tight">{title}</h1>
        <p className="text-sm text-slate-500 mt-1">{subtitle}</p>
      </div>
      {children && <div className="flex items-center gap-2">{children}</div>}
    </div>
  );
}

export function DemoModeButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-2 rounded-lg border border-signal-teal/30 bg-signal-teal/10 px-4 py-2 text-sm font-medium text-signal-teal hover:bg-signal-teal/20 transition-colors"
    >
      <Sparkles className="h-4 w-4" />
      Demo Mode
    </button>
  );
}
