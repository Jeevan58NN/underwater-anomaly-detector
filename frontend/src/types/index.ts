export type ConfidenceBand = "High" | "Medium" | "Low";
export type Severity = "High" | "Medium" | "Low";

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface SeafloorAssessment {
  artificial_pct: number;
  natural_pct: number;
  note: string;
}

export interface Detection {
  id: string;
  class_name: string;
  confidence: number;
  confidence_band: ConfidenceBand;
  model_confidence?: number;
  verification_score?: number;
  final_confidence?: number;
  bbox: BoundingBox;
  latitude: number | null;
  longitude: number | null;
  severity: Severity;
  seafloor_assessment: SeafloorAssessment;
  segmentation?: string;
  location_status: "geotagged" | "simulated" | "unavailable" | "estimated";
  location_source?: string;
  ping_id?: number;
  timestamp?: string;
  is_simulated_location: boolean;
  class_id?: number;
  system_score?: number | null;
  classification_type?: "artificial" | "natural" | "unknown";
  priority?: string;
  input_type?: string;
  analysis_id?: string;
}

export interface AnalysisResult {
  analysis_id: string;
  status: string;
  processing_mode: string;
  input_type: string;
  file_format: string;
  filename: string;
  image_width: number;
  image_height: number;
  preview_image_url?: string;
  detections: Detection[];
  navigation_available: boolean;
  geotagging_available: boolean;
  processing_time?: number;
  created_at: string;
  note: string;
}

export interface HealthResponse {
  status: string;
  mode: string;
  detector: string;
  version: string;
}

export interface SystemStatusResponse {
  backend_api: string;
  detection_engine: string;
  model_status: string;
  classes: number;
  geolocation: string;
  database: string;
  map_service: string;
  processing_mode: string;
}

export interface ToastMessage {
  id: string;
  type: "success" | "error" | "info";
  message: string;
}
