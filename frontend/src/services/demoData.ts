import type { AnalysisResult } from "../types";

/**
 * Demo Mode data — used when the real dataset/backend isn't reachable,
 * or when the user just wants to see the flow without uploading anything.
 * This mirrors exactly what /api/analyze would return for a real upload,
 * so switching from Demo Mode to a live backend requires no UI changes.
 */
export const MOCK_ANALYSIS: AnalysisResult = {
  analysis_id: "SCAN-DEMO123",
  status: "simulation",
  processing_mode: "simulation",
  input_type: "IMAGE",
  file_format: ".png",
  filename: "demo_sonar_scan.png",
  image_width: 1280,
  image_height: 720,
  navigation_available: false,
  geotagging_available: false,
  created_at: new Date().toISOString(),
  note: "All detections are SIMULATED for prototype purposes.",
  detections: [
    {
      id: "DET-001",
      class_name: "Pipe",
      confidence: 0.94,
      confidence_band: "High",
      bbox: { x: 420, y: 250, width: 210, height: 100 },
      latitude: 13.0827,
      longitude: 80.2707,
      severity: "High",
      seafloor_assessment: { artificial_pct: 92.5, natural_pct: 7.5, note: "" },
      is_simulated_location: true,
      location_status: "simulated",
    },
    {
      id: "DET-9F2B1C",
      class_name: "Ghost Net",
      confidence: 0.74,
      confidence_band: "Medium",
      bbox: { x: 740, y: 190, width: 280, height: 160 },
      latitude: 13.08272,
      longitude: 80.27068,
      severity: "Medium",
      seafloor_assessment: { artificial_pct: 78.0, natural_pct: 22.0, note: "" },
      is_simulated_location: true,
      location_status: "simulated",
    },
  ],
};

/** Generates a placeholder sonar-style image as a data URL (no asset files needed). */
export function generatePlaceholderSonarImage(width = 1280, height = 720): string {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  if (!ctx) return "";

  const gradient = ctx.createLinearGradient(0, 0, 0, height);
  gradient.addColorStop(0, "#040c14");
  gradient.addColorStop(1, "#0a1c29");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, width, height);

  ctx.strokeStyle = "rgba(34,211,238,0.15)";
  for (let y = 0; y < height; y += 18) {
    ctx.beginPath();
    let px = 0;
    ctx.moveTo(0, y);
    while (px < width) {
      const wobble = Math.sin((px + y) * 0.02) * 4;
      ctx.lineTo(px, y + wobble);
      px += 8;
    }
    ctx.stroke();
  }

  ctx.fillStyle = "rgba(148,163,184,0.6)";
  ctx.font = "20px monospace";
  ctx.fillText("DEMO SONAR IMAGE — SIMULATED", 24, 36);

  return canvas.toDataURL("image/png");
}
