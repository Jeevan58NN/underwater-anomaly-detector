import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import type { AnalysisResult, Detection, HealthResponse } from "../types";
import { getDetections, getHealth } from "../services/api";
import { MOCK_ANALYSIS } from "../services/demoData";

interface AppDataContextValue {
  currentAnalysis: AnalysisResult | null;
  setCurrentAnalysis: (a: AnalysisResult | null) => void;
  detections: Detection[];
  addDetections: (d: Detection[]) => void;
  refreshDetections: () => Promise<void>;
  backendOnline: boolean;
  health: HealthResponse | null;
  loadDemo: () => void;
  isDemo: boolean;
  reportsCount: number;
  incrementReportsCount: () => void;
}

const AppDataContext = createContext<AppDataContextValue | undefined>(undefined);

export function AppDataProvider({ children }: { children: ReactNode }) {
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisResult | null>(null);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [backendOnline, setBackendOnline] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isDemo, setIsDemo] = useState(false);
  const [reportsCount, setReportsCount] = useState(0);

  const incrementReportsCount = useCallback(() => {
    setReportsCount((prev) => prev + 1);
  }, []);

  const checkHealth = useCallback(async () => {
    try {
      const h = await getHealth();
      setHealth(h);
      setBackendOnline(true);
    } catch {
      setBackendOnline(false);
      setHealth(null);
    }
  }, []);

  const refreshDetections = useCallback(async () => {
    try {
      const d = await getDetections();
      setDetections(d);
    } catch {
      // silently keep local state — health check surfaces connectivity issues
    }
  }, []);

  useEffect(() => {
    checkHealth();
    refreshDetections();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, [checkHealth, refreshDetections]);

  const addDetections = useCallback((d: Detection[]) => {
    setDetections((prev) => {
      const existingIds = new Set(prev.map((p) => p.id));
      const merged = [...prev, ...d.filter((x) => !existingIds.has(x.id))];
      return merged;
    });
  }, []);

  const loadDemo = useCallback(() => {
    setCurrentAnalysis(MOCK_ANALYSIS);
    addDetections(MOCK_ANALYSIS.detections);
    setIsDemo(true);
  }, [addDetections]);

  return (
    <AppDataContext.Provider
      value={{
        currentAnalysis,
        setCurrentAnalysis,
        detections,
        addDetections,
        refreshDetections,
        backendOnline,
        health,
        loadDemo,
        isDemo,
        reportsCount,
        incrementReportsCount,
      }}
    >
      {children}
    </AppDataContext.Provider>
  );
}

export function useAppData() {
  const ctx = useContext(AppDataContext);
  if (!ctx) throw new Error("useAppData must be used within AppDataProvider");
  return ctx;
}
