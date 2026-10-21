from __future__ import annotations
import math
from typing import Sequence, Tuple
from .validation import _validate_bbox, _validate_lat_lon

def get_bbox_center(bbox: Sequence[float]) -> Tuple[float, float]:
    """
    Calculate center point of a bounding box.
    """
    x1, y1, x2, y2 = _validate_bbox(bbox)
    return (x1 + x2) / 2.0, (y1 + y2) / 2.0

def calculate_target_position(
    sonar_lat: float,
    sonar_lon: float,
    heading: float,
    sonar_range: float,
    relative_angle: float,
) -> Tuple[float, float]:
    """
    Geodesic destination calculation from a sonar position, heading, and bearing offsets.
    """
    true_bearing = (heading + relative_angle) % 360
    earth_radius = 6378137.0
    lat_rad = math.radians(sonar_lat)
    lon_rad = math.radians(sonar_lon)
    bearing_rad = math.radians(true_bearing)
    angular_distance = sonar_range / earth_radius

    target_lat_rad = math.asin(
        math.sin(lat_rad) * math.cos(angular_distance)
        + math.cos(lat_rad) * math.sin(angular_distance) * math.cos(bearing_rad)
    )
    target_lon_rad = lon_rad + math.atan2(
        math.sin(bearing_rad) * math.sin(angular_distance) * math.cos(lat_rad),
        math.cos(angular_distance) - math.sin(lat_rad) * math.sin(target_lat_rad)
    )

    target_lat = math.degrees(target_lat_rad)
    target_lon = math.degrees(target_lon_rad)
    _validate_lat_lon(target_lat, target_lon)

    return target_lat, target_lon
