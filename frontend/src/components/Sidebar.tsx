import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Radar,
  Crosshair,
  Map as MapIcon,
  FileBarChart,
  Activity,
  Waves,
} from "lucide-react";
import { useAppData } from "../hooks/AppDataContext";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/sonar-analysis", label: "Sonar Analysis", icon: Radar },
  { to: "/detections", label: "Detections", icon: Crosshair },
  { to: "/map", label: "Map", icon: MapIcon },
  { to: "/reports", label: "Reports", icon: FileBarChart },
  { to: "/system-status", label: "System Status", icon: Activity },
];

export default function Sidebar() {
  const { backendOnline } = useAppData();

  return (
    <aside className="hidden md:flex md:flex-col w-64 shrink-0 h-screen sticky top-0 border-r border-abyss-700/60 bg-abyss-900/80 backdrop-blur-sm">
      <div className="flex items-center gap-2.5 px-6 py-6">
        <div className="relative flex h-9 w-9 items-center justify-center rounded-lg bg-signal-cyan/10 border border-signal-cyan/30">
          <Waves className="h-5 w-5 text-signal-cyan" strokeWidth={2} />
        </div>
        <div>
          <p className="font-display font-semibold text-lg leading-none text-white tracking-tight">
            AquaScan <span className="text-signal-cyan">AI</span>
          </p>
        </div>
      </div>

      <nav className="flex-1 px-3 py-2 space-y-1">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-signal-cyan/10 text-signal-cyan border border-signal-cyan/20"
                  : "text-slate-400 border border-transparent hover:text-slate-100 hover:bg-abyss-800/80"
              }`
            }
          >
            <Icon className="h-4 w-4" strokeWidth={2} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-4 py-5 border-t border-abyss-700/60 space-y-2">
        <p className="text-[11px] uppercase tracking-wider text-slate-500 font-mono">
          Prototype Mode
        </p>
        <div className="flex items-center gap-2 text-xs font-mono">
          <span
            className={`h-2 w-2 rounded-full ${
              backendOnline ? "bg-sonar-green animate-pulseSlow" : "bg-sonar-coral"
            }`}
          />
          <span className={backendOnline ? "text-sonar-green" : "text-sonar-coral"}>
            {backendOnline ? "Backend Connected" : "Backend Unreachable"}
          </span>
        </div>
      </div>
    </aside>
  );
}
