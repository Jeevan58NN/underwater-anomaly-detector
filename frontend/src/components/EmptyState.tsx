import type { LucideIcon } from "lucide-react";

export default function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center text-center rounded-xl border border-dashed border-abyss-700 bg-abyss-900/40 py-16 px-6">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-abyss-800 border border-abyss-700 mb-4">
        <Icon className="h-5 w-5 text-slate-500" strokeWidth={2} />
      </div>
      <p className="font-display text-base font-semibold text-slate-200">{title}</p>
      <p className="text-sm text-slate-500 mt-1 max-w-sm">{description}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
