"""
Pydantic schemas shared across the AquaScan AI backend.

These schemas define the contract between the frontend and backend.

The same response structure is used for:
    - Simulation Mode
    - Real AI Mode

The detector can therefore be replaced without changing
the frontend API contract.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ============================================================
# ENUM-LIKE TYPES
# ============================================================

Severity = Literal[
    "High",
    "Medium",
    "Low",
]

ConfidenceBand = Literal[
    "High",
    "Medium",
    "Low",
]

LocationStatus = Literal[
    "geotagged",
    "simulated",
    "unavailable",
    "estimated",
]

LocationSource = Literal[
    "GeoTIFF",
    "XTF Navigation",
    "Live Navigation",
    "External Geospatial Metadata",
    "Simulation",
    "Unknown",
    "synthetic_demo_ocean",
    "estimated_demo_location",
]

ProcessingMode = Literal[
    "simulation",
    "real",
]


# ============================================================
# BOUNDING BOX
# ============================================================

class BoundingBox(BaseModel):
    """
    Bounding box in the coordinate system used by the
    displayed/model image.

    Float values are used because model/tile transformations
    can result in non-integer coordinates.
    """

    x: float = Field(
        ge=0.0
    )

    y: float = Field(
        ge=0.0
    )

    width: float = Field(
        ge=0.0
    )

    height: float = Field(
        ge=0.0
    )


# ============================================================
from typing import Optional


class SegmentationResult(BaseModel):
    """
    Result returned by U-Net segmentation.
    """

    status: str = "completed"

    mask_url: Optional[str] = None

    overlay_url: Optional[str] = None

    width: int = 0

    height: int = 0

    coverage_pct: float = 0.0

    threshold: float = 0.5



# ============================================================


# ============================================================
# SEAFLOOR / VERIFICATION
# ============================================================

class SeafloorAssessment(BaseModel):
    artificial_pct: float = Field(
        ge=0.0,
        le=100.0,
    )

    natural_pct: float = Field(
        ge=0.0,
        le=100.0,
    )

    note: str = ""


# ============================================================
# LOCATION
# ============================================================

class DetectionLocation(BaseModel):
    """
    Geographic information associated with one detection.

    Latitude/longitude remain optional because PNG/JPG input
    may not contain geographic metadata.
    """

    latitude: Optional[float] = Field(
        default=None,
        ge=-90.0,
        le=90.0,
    )

    longitude: Optional[float] = Field(
        default=None,
        ge=-180.0,
        le=180.0,
    )

    status: LocationStatus = "unavailable"

    source: Optional[LocationSource] = None

    reason: Optional[str] = None


# ============================================================
# DETECTION
# ============================================================

class Detection(BaseModel):
    """
    One detected sonar target.
    """

    id: str

    class_id: Optional[int] = None

    class_name: str

    # Primary detection confidence
    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    confidence_band: ConfidenceBand

    # Separate confidence components
    model_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    verification_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    final_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    # Bounding box
    bbox: BoundingBox

    system_score: Optional[float] = None

    classification_type: Optional[str] = None

    priority: Optional[str] = None

    input_type: Optional[str] = None

    analysis_id: Optional[str] = None

    # --------------------------------------------------------
    # Geographic result
    # --------------------------------------------------------

    latitude: Optional[float] = Field(
        default=None,
        ge=-90.0,
        le=90.0,
    )

    longitude: Optional[float] = Field(
        default=None,
        ge=-180.0,
        le=180.0,
    )

    location_status: LocationStatus = (
        "unavailable"
    )

    location_source: Optional[LocationSource] = (
        None
    )

    location_reason: Optional[str] = None

    # --------------------------------------------------------
    # Risk
    # --------------------------------------------------------

    severity: Severity

    seafloor_assessment: SeafloorAssessment

    # --------------------------------------------------------
    # Segmentation
    # --------------------------------------------------------

    segmentation: Optional[
            SegmentationResult
        ] = None

    # --------------------------------------------------------
    # Sonar metadata
    # --------------------------------------------------------

    ping_id: Optional[int] = None

    timestamp: Optional[str] = None

    # --------------------------------------------------------
    # Tile information
    # --------------------------------------------------------

    tile_id: Optional[str] = None

    tile_offset_x: Optional[float] = None

    tile_offset_y: Optional[float] = None

    # Bounding box mapped back to the original raster.
    # Format:
    # [x1, y1, x2, y2]
    original_bbox: Optional[List[float]] = None

    # --------------------------------------------------------
    # Simulation indicator
    # --------------------------------------------------------

    is_simulated_location: bool = False


# ============================================================
# ANALYSIS RESULT
# ============================================================

class AnalysisResult(BaseModel):
    """
    Complete result of one analysis request.
    """

    analysis_id: str

    # Example:
    # completed / failed
    status: str

    processing_mode: ProcessingMode

    input_type: str

    file_format: str

    filename: str

    # Dimensions of the displayed/source image
    image_width: int

    image_height: int

    # Browser/display preview
    preview_image_url: Optional[str] = None

    # All detections
    detections: List[Detection] = Field(
        default_factory=list
    )

    # --------------------------------------------------------
    # Input metadata
    # --------------------------------------------------------

    navigation_available: bool = False

    georeferencing_available: bool = False

    geotagging_available: bool = False

    location_source: Optional[LocationSource] = None

    # --------------------------------------------------------
    # Processing information
    # --------------------------------------------------------

    processing_time: Optional[float] = None

    tile_count: Optional[int] = None

    created_at: str

    note: str = ""


# ============================================================
# HEALTH
# ============================================================

class HealthResponse(BaseModel):
    status: str

    mode: ProcessingMode

    detector: str

    version: str


# ============================================================
# SYSTEM STATUS
# ============================================================

class SystemStatusResponse(BaseModel):
    backend_api: str

    detection_engine: str

    model_status: str = "Unknown"

    classes: int = 0

    segmentation_engine: str = "Unknown"

    geolocation: str

    database: str

    map_service: str

    processing_mode: ProcessingMode