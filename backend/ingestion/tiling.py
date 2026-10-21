from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
import rasterio
from PIL import Image


@dataclass
class SonarTile:
    """
    Represents one model-ready tile extracted from a sonar raster.

    Coordinates:
        offset_x / offset_y:
            Top-left position of the tile in the original raster.

        width / height:
            Actual tile dimensions.

        image_path:
            PNG file used by the AI model.

    The original GeoTIFF remains the authoritative source
    for geographic calculations.
    """

    tile_id: str
    image_path: str

    offset_x: int
    offset_y: int

    width: int
    height: int

    original_width: int
    original_height: int


def _normalize_band(
    band: np.ndarray,
) -> np.ndarray:
    """
    Convert a raster band to uint8 for model/display use.

    Percentile stretching reduces the effect of extreme
    intensity values.
    """

    band = band.astype(np.float32)

    finite = np.isfinite(band)

    if not np.any(finite):
        return np.zeros(
            band.shape,
            dtype=np.uint8,
        )

    valid = band[finite]

    low = np.percentile(
        valid,
        2,
    )

    high = np.percentile(
        valid,
        98,
    )

    if high <= low:
        low = float(valid.min())
        high = float(valid.max())

    if high <= low:
        return np.zeros(
            band.shape,
            dtype=np.uint8,
        )

    normalized = (
        (band - low)
        / (high - low)
        * 255.0
    )

    normalized = np.clip(
        normalized,
        0,
        255,
    )

    return normalized.astype(
        np.uint8
    )


def _raster_to_rgb(
    data: np.ndarray,
) -> np.ndarray:
    """
    Convert raster data into an RGB uint8 image.

    Supported:
        1 band -> grayscale converted to RGB
        3+ bands -> first three bands used as RGB
    """

    if data.ndim != 3:
        raise ValueError(
            "Expected raster data with shape "
            "(bands, height, width)."
        )

    bands = data.shape[0]

    if bands >= 3:

        r = _normalize_band(data[0])
        g = _normalize_band(data[1])
        b = _normalize_band(data[2])

        return np.stack(
            [r, g, b],
            axis=-1,
        )

    if bands == 1:

        gray = _normalize_band(
            data[0]
        )

        return np.stack(
            [gray, gray, gray],
            axis=-1,
        )

    raise ValueError(
        f"Unsupported number of raster bands: {bands}"
    )


def generate_tiles(
    file_path: str,
    output_dir: str,
    tile_size: int = 512,
    overlap: int = 64,
) -> List[SonarTile]:
    """
    Split a large GeoTIFF into overlapping tiles.

    Example:

        tile_size = 512
        overlap = 64

    means adjacent tiles overlap by 64 pixels.

    IMPORTANT:
    Every tile stores its original raster offset.
    This allows model detections to be mapped back to
    the original GeoTIFF before geotagging.
    """

    if not file_path:
        raise ValueError(
            "Input raster path is empty."
        )

    source_path = Path(file_path)

    if not source_path.exists():
        raise FileNotFoundError(
            f"Raster file not found: {source_path}"
        )

    if tile_size <= 0:
        raise ValueError(
            "tile_size must be greater than zero."
        )

    if overlap < 0:
        raise ValueError(
            "overlap cannot be negative."
        )

    if overlap >= tile_size:
        raise ValueError(
            "overlap must be smaller than tile_size."
        )

    output_path = Path(
        output_dir
    )

    output_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    stride = tile_size - overlap

    tiles: List[SonarTile] = []

    try:
        src = rasterio.open(
            source_path
        )
    except Exception as exc:
        raise ValueError(
            f"Unable to open raster: {source_path}"
        ) from exc

    with src:

        raster_width = src.width
        raster_height = src.height

        tile_number = 0

        # ----------------------------------------------------
        # Iterate through raster
        # ----------------------------------------------------

        y_positions = list(
            range(
                0,
                max(
                    raster_height - tile_size,
                    0
                ) + 1,
                stride,
            )
        )

        x_positions = list(
            range(
                0,
                max(
                    raster_width - tile_size,
                    0
                ) + 1,
                stride,
            )
        )

        # ----------------------------------------------------
        # Ensure the last row/column is covered
        # ----------------------------------------------------

        if not y_positions:
            y_positions = [0]
        elif (
            y_positions[-1] + tile_size
            < raster_height
        ):
            y_positions.append(
                raster_height - tile_size
            )

        if not x_positions:
            x_positions = [0]
        elif (
            x_positions[-1] + tile_size
            < raster_width
        ):
            x_positions.append(
                raster_width - tile_size
            )

        # ----------------------------------------------------
        # Create tiles
        # ----------------------------------------------------

        for y in y_positions:

            for x in x_positions:

                remaining_width = (
                    raster_width - x
                )

                remaining_height = (
                    raster_height - y
                )

                width = min(
                    tile_size,
                    remaining_width,
                )

                height = min(
                    tile_size,
                    remaining_height,
                )

                window = rasterio.windows.Window(
                    x,
                    y,
                    width,
                    height,
                )

                data = src.read(
                    window=window
                )

                rgb = _raster_to_rgb(
                    data
                )

                tile_number += 1

                tile_id = (
                    f"tile_{tile_number:05d}"
                )

                tile_path = (
                    output_path
                    / f"{tile_id}.png"
                )

                Image.fromarray(
                    rgb,
                    mode="RGB",
                ).save(
                    tile_path,
                    format="PNG",
                )

                tiles.append(
                    SonarTile(
                        tile_id=tile_id,
                        image_path=str(
                            tile_path
                        ),

                        offset_x=int(x),
                        offset_y=int(y),

                        width=int(width),
                        height=int(height),

                        original_width=int(
                            raster_width
                        ),
                        original_height=int(
                            raster_height
                        ),
                    )
                )

    return tiles


def tile_bbox_to_original(
    bbox: Tuple[float, float, float, float],
    tile: SonarTile,
) -> Tuple[float, float, float, float]:
    """
    Convert a bounding box from tile coordinates
    into original GeoTIFF pixel coordinates.

    bbox format:
        (x1, y1, x2, y2)

    Tile coordinates:
        origin = top-left of tile

    Original coordinates:
        origin = top-left of full raster
    """

    if len(bbox) != 4:
        raise ValueError(
            "Bounding box must contain "
            "(x1, y1, x2, y2)."
        )

    x1, y1, x2, y2 = bbox

    original_x1 = (
        tile.offset_x + x1
    )

    original_y1 = (
        tile.offset_y + y1
    )

    original_x2 = (
        tile.offset_x + x2
    )

    original_y2 = (
        tile.offset_y + y2
    )

    return (
        original_x1,
        original_y1,
        original_x2,
        original_y2,
    )


def tile_point_to_original(
    x: float,
    y: float,
    tile: SonarTile,
) -> Tuple[float, float]:
    """
    Convert a point from tile coordinates
    to original GeoTIFF pixel coordinates.
    """

    return (
        tile.offset_x + x,
        tile.offset_y + y,
    )