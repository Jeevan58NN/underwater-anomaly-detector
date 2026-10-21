from __future__ import annotations
from typing import Tuple
import rasterio
from pyproj import Transformer
from .validation import _validate_lat_lon

def tile_point_to_original(
    x: float,
    y: float,
    tile_offset_x: float,
    tile_offset_y: float,
) -> Tuple[float, float]:
    """
    Map point from tile-relative pixels to original GeoTIFF pixels.
    """
    return float(tile_offset_x) + float(x), float(tile_offset_y) + float(y)

def pixel_to_projected(
    geo_tiff_path: str,
    pixel_x: float,
    pixel_y: float,
) -> Tuple[float, float]:
    """
    Map GeoTIFF pixel columns/rows to the projected spatial CRS coordinates.
    """
    with rasterio.open(geo_tiff_path) as src:
        if not (0 <= pixel_x < src.width and 0 <= pixel_y < src.height):
            raise ValueError(
                f"Pixel ({pixel_x}, {pixel_y}) lies outside GeoTIFF bounds: {src.width}x{src.height}"
            )
        projected_x, projected_y = rasterio.transform.xy(
            src.transform,
            pixel_y,
            pixel_x,
            offset="center"
        )
        return float(projected_x), float(projected_y)

def projected_to_latlon(
    geo_tiff_path: str,
    projected_x: float,
    projected_y: float,
) -> Tuple[float, float]:
    """
    Map projected coordinates to WGS84 latitude/longitude.
    """
    with rasterio.open(geo_tiff_path) as src:
        if src.crs is None:
            raise ValueError("GeoTIFF does not contain a spatial Coordinate Reference System (CRS).")
        
        transformer = Transformer.from_crs(
            src.crs,
            "EPSG:4326",
            always_xy=True
        )
        longitude, latitude = transformer.transform(projected_x, projected_y)

    latitude = float(latitude)
    longitude = float(longitude)
    _validate_lat_lon(latitude, longitude)
    return latitude, longitude
