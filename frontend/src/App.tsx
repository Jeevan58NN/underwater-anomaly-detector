import { Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import SonarAnalysis from "./pages/SonarAnalysis";
import Detections from "./pages/Detections";
import MapView from "./pages/MapView";
import Reports from "./pages/Reports";
import SystemStatus from "./pages/SystemStatus";
import { AppDataProvider } from "./hooks/AppDataContext";

export default function App() {
  return (
    <AppDataProvider>
      <div className="flex min-h-screen bg-sonar-grid bg-[length:36px_36px]">
        <Sidebar />
        <main className="flex-1 px-6 md:px-10 py-8 max-w-[1400px]">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/sonar-analysis" element={<SonarAnalysis />} />
            <Route path="/detections" element={<Detections />} />
            <Route path="/map" element={<MapView />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/system-status" element={<SystemStatus />} />
          </Routes>
        </main>
      </div>
    </AppDataProvider>
  );
}
