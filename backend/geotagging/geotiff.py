from __future__ import annotations
from typing import Any, Dict, Sequence
from .geometry import get_bbox_center
from .coordinate_transform import (
    tile_point_to_original,
    pixel_to_projected,
    projected_to_latlon,
)

def geotag_geotiff_detection(
    geo_tiff_path: str,
    bbox: Sequence[float],
    tile_offset_x: float = 0.0,
    tile_offset_y: float = 0.0,
) -> Dict[str, Any]:
    """
    Map a tile-relative bbox to geographical WGS84 coordinates using GeoTIFF transformations.
    """
    if not geo_tiff_path:
        raise ValueError("GeoTIFF path is empty.")
    
    # 1. Bounding box center in tile
    center_x, center_y = get_bbox_center(bbox)
    
    # 2. Map tile pixels to original full raster pixels
    original_x, original_y = tile_point_to_original(
        center_x, center_y, tile_offset_x, tile_offset_y
    )
    
    # 3. Map pixels to projected CRS coordinates
    projected_x, projected_y = pixel_to_projected(
        geo_tiff_path, original_x, original_y
    )
    
    # 4. Map projected coordinates to latitude / longitude
    latitude, longitude = projected_to_latlon(
        geo_tiff_path, projected_x, projected_y
    )
    
    return {
        "latitude": latitude,
        "longitude": longitude,
        "location_status": "geotagged",
        "location_source": "GeoTIFF",
        "tile_center": {"x": center_x, "y": center_y},
        "original_pixel": {"x": original_x, "y": original_y},
        "projected_coordinate": {"x": projected_x, "y": projected_y},
    }
