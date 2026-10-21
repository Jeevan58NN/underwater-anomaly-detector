import type {
  AnalysisResult,
  Detection,
  HealthResponse,
  SystemStatusResponse,
} from "../types";

export const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;

    try {
      const body = await res.json();

      if (body?.detail) {
        detail = body.detail;
      }
    } catch {
      // Keep the default error message.
    }

    throw new ApiError(detail);
  }

  return res.json() as Promise<T>;
}

async function safeFetch<T>(
  input: RequestInfo,
  init?: RequestInit
): Promise<T> {
  try {
    const res = await fetch(input, init);
    return await handleResponse<T>(res);
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }

    throw new ApiError(
      "Unable to connect to analysis server. Please check that the FastAPI backend is running."
    );
  }
}

/**
 * Convert a backend-relative asset URL into a browser-ready URL.
 *
 * Examples:
 *   "/uploads/SCAN-123.jpg"
 *      -> "http://localhost:8000/uploads/SCAN-123.jpg"
 *
 *   "/previews/SCAN-123/SCAN-123_preview.png"
 *      -> "http://localhost:8000/previews/SCAN-123/SCAN-123_preview.png"
 *
 * Absolute URLs are returned unchanged.
 */
export function getAssetUrl(
  assetPath: string | null | undefined
): string | null {
  if (!assetPath) {
    return null;
  }

  const trimmed = assetPath.trim();

  if (!trimmed) {
    return null;
  }

  // Already an absolute URL.
  if (
    trimmed.startsWith("http://") ||
    trimmed.startsWith("https://") ||
    trimmed.startsWith("blob:") ||
    trimmed.startsWith("data:")
  ) {
    return trimmed;
  }

  // Backend returned a relative URL such as:
  // /previews/SCAN-123/preview.png
  if (trimmed.startsWith("/")) {
    return `${API_BASE}${trimmed}`;
  }

  // Backend returned something without a leading slash.
  return `${API_BASE}/${trimmed}`;
}

export async function getHealth(): Promise<HealthResponse> {
  return safeFetch<HealthResponse>(
    `${API_BASE}/api/health`
  );
}

export async function getSystemStatus(): Promise<SystemStatusResponse> {
  return safeFetch<SystemStatusResponse>(
    `${API_BASE}/api/system-status`
  );
}

export async function analyzeFile(
  file: File,
  mode: "simulation" | "real" = "simulation"
): Promise<AnalysisResult> {
  const formData = new FormData();

  formData.append("image", file);
  formData.append("mode", mode);

  return safeFetch<AnalysisResult>(
    `${API_BASE}/api/analyze`,
    {
      method: "POST",
      body: formData,
    }
  );
}

export async function getDetections(): Promise<Detection[]> {
  return safeFetch<Detection[]>(
    `${API_BASE}/api/detections`
  );
}

export async function getDetection(
  id: string
): Promise<Detection> {
  return safeFetch<Detection>(
    `${API_BASE}/api/detections/${encodeURIComponent(id)}`
  );
}

async function downloadFile(
  url: string,
  filename: string
): Promise<void> {
  try {
    const res = await fetch(url);

    if (!res.ok) {
      throw new ApiError(
        "Unable to download report. Please check the backend connection."
      );
    }

    const blob = await res.blob();

    const objectUrl =
      window.URL.createObjectURL(blob);

    const link =
      document.createElement("a");

    link.href = objectUrl;
    link.download = filename;

    document.body.appendChild(link);
    link.click();
    link.remove();

    window.URL.revokeObjectURL(objectUrl);
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }

    throw new ApiError(
      "Unable to download report. Please check the backend connection."
    );
  }
}

export async function downloadCSV(): Promise<void> {
  return downloadFile(
    `${API_BASE}/api/reports/csv`,
    "aquascan_report.csv"
  );
}

export async function downloadJSON(): Promise<void> {
  return downloadFile(
    `${API_BASE}/api/reports/json`,
    "aquascan_report.json"
  );
}

export { ApiError };



export interface SegmentationResult {
  segmentation_id: string;
  status: string;
  mask_url: string | null;
  overlay_url: string | null;
  width: number;
  height: number;
  coverage_pct: number;
  threshold: number;
}

export async function segmentFile(
  file: File
): Promise<SegmentationResult> {
  const formData = new FormData();

  formData.append("image", file);

  return safeFetch<SegmentationResult>(
    `${API_BASE}/api/segment`,
    {
      method: "POST",
      body: formData,
    }
  );
}