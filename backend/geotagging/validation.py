from __future__ import annotations
import math
from typing import Sequence, Tuple

BBox = Tuple[float, float, float, float]

def _validate_bbox(bbox: Sequence[float]) -> BBox:
    """
    Validate a bounding box. Expected format: (x1, y1, x2, y2)
    """
    if bbox is None or len(bbox) != 4:
        raise ValueError("Bounding box must contain exactly (x1, y1, x2, y2).")
    x1, y1, x2, y2 = (float(val) for val in bbox)
    if x2 < x1 or y2 < y1:
        raise ValueError(f"Invalid bounding box boundaries: {bbox}")
    return x1, y1, x2, y2

def _validate_lat_lon(latitude: float, longitude: float) -> None:
    """
    Validate WGS84 latitude and longitude values.
    """
    if not math.isfinite(latitude) or not math.isfinite(longitude):
        raise ValueError(f"Latitude/Longitude must be finite. Got: ({latitude}, {longitude})")
    if not -90.0 <= latitude <= 90.0:
        raise ValueError(f"Latitude out of range [-90, 90]: {latitude}")
    if not -180.0 <= longitude <= 180.0:
        raise ValueError(f"Longitude out of range [-180, 180]: {longitude}")
