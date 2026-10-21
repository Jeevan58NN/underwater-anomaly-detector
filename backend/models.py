"""
Pydantic models shared across the AquaScan AI backend.

These schemas define the contract between the frontend and backend.
They are intentionally identical whether the detections come from the
MockDetector (today) or a real YOLO / segmentation model (future) —
see mock_detector.py for the swappable Detector interface.
"""
from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field

Severity = Literal["High", "Medium", "Low"]
ConfidenceBand = Literal["High", "Medium", "Low"]
LocationStatus = Literal["geotagged", "simulated", "unavailable"]

class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int

class SeafloorAssessment(BaseModel):
    artificial_pct: float
    natural_pct: float
    note: str

class Detection(BaseModel):
    id: str
    class_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_band: ConfidenceBand
    model_confidence: Optional[float] = None
    verification_score: Optional[float] = None
    final_confidence: Optional[float] = None
    bbox: BoundingBox
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    severity: Severity
    seafloor_assessment: SeafloorAssessment
    segmentation: Optional[str] = None
    location_status: LocationStatus = "unavailable"
    location_source: Optional[str] = None
    ping_id: Optional[int] = None
    timestamp: Optional[str] = None
    is_simulated_location: bool = True

class AnalysisResult(BaseModel):
    analysis_id: str
    status: str
    processing_mode: str
    input_type: str
    file_format: str
    filename: str
    image_width: int
    image_height: int
    preview_image_url: Optional[str] = None
    detections: List[Detection]
    navigation_available: bool = False
    geotagging_available: bool = False
    processing_time: Optional[float] = None
    created_at: str
    note: str = ""


class HealthResponse(BaseModel):
    status: str
    mode: str
    detector: str
    version: str


class SystemStatusResponse(BaseModel):
    backend_api: str
    detection_engine: str
    geolocation: str
    database: str
    map_service: str
    processing_mode: str
