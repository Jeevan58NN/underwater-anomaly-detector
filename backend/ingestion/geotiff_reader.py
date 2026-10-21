from __future__ import annotations

from pathlib import Path
from typing import Optional

import os

import numpy as np
import rasterio
from PIL import Image

from .image_loader import SonarSurvey


# Maximum dimension for the browser/display preview.
# The original GeoTIFF is NEVER modified.
MAX_PREVIEW_SIZE = 2048


def _normalize_band(band: np.ndarray) -> np.ndarray:
    """
    Convert a raster band to uint8 using percentile stretching.

    This is only for creating a display/AI preview.
    The original GeoTIFF remains unchanged.
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


def _create_preview(
    src: rasterio.io.DatasetReader,
    preview_path: Path,
) -> None:
    """
    Create a browser-friendly PNG preview from the GeoTIFF.

    The preview is downsampled so a very large sonar raster
    does not need to be loaded at full resolution.
    """

    scale = max(
        src.width / MAX_PREVIEW_SIZE,
        src.height / MAX_PREVIEW_SIZE,
        1.0,
    )

    preview_width = max(
        1,
        int(src.width / scale),
    )

    preview_height = max(
        1,
        int(src.height / scale),
    )

    # --------------------------------------------------------
    # Read a downsampled version of the raster.
    # --------------------------------------------------------

    if src.count >= 3:
        # Use the first three bands as RGB.
        data = src.read(
            [1, 2, 3],
            out_shape=(
                3,
                preview_height,
                preview_width,
            ),
            resampling=rasterio.enums.Resampling.bilinear,
        )

        r = _normalize_band(data[0])
        g = _normalize_band(data[1])
        b = _normalize_band(data[2])

        preview = np.stack(
            [r, g, b],
            axis=-1,
        )

    else:
        # Single-band sonar raster.
        data = src.read(
            1,
            out_shape=(
                preview_height,
                preview_width,
            ),
            resampling=rasterio.enums.Resampling.bilinear,
        )

        gray = _normalize_band(data)

        # Convert grayscale to RGB for frontend compatibility.
        preview = np.stack(
            [gray, gray, gray],
            axis=-1,
        )

    Image.fromarray(
        preview,
        mode="RGB",
    ).save(
        preview_path,
        format="PNG",
        optimize=True,
    )


def load_geotiff(
    file_path: str,
    extract_dir: str,
) -> SonarSurvey:
    """
    Read a GeoTIFF and convert it into the common SonarSurvey object.

    The GeoTIFF remains the authoritative geographic source.

    Returned data includes:
        - original GeoTIFF path
        - browser-friendly PNG preview
        - CRS
        - affine transform
        - geographic bounds
        - raster resolution
        - image dimensions
        - georeferencing status
    """

    if not file_path:
        raise ValueError(
            "GeoTIFF file path is empty."
        )

    source_path = Path(file_path)

    if not source_path.is_file():
        raise FileNotFoundError(
            f"GeoTIFF file not found: {file_path}"
        )

    extract_path = Path(
        extract_dir
    )

    extract_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Open GeoTIFF
    # --------------------------------------------------------

    try:
        src = rasterio.open(
            source_path
        )
    except Exception as exc:
        raise ValueError(
            f"Unable to read GeoTIFF: {file_path}"
        ) from exc

    with src:

        # ----------------------------------------------------
        # Geographic metadata
        # ----------------------------------------------------

        crs_string: Optional[str]

        if src.crs is not None:
            crs_string = src.crs.to_string()
        else:
            crs_string = None

        transform = src.transform

        has_valid_transform = (
            transform is not None
            and crs_string is not None
        )

        # ----------------------------------------------------
        # Save PNG preview
        # ----------------------------------------------------

        preview_name = (
            source_path.stem
            + "_preview.png"
        )

        preview_path = (
            extract_path
            / preview_name
        )

        try:
            _create_preview(
                src,
                preview_path,
            )
        except Exception as exc:
            raise RuntimeError(
                "Failed to create GeoTIFF preview."
            ) from exc

        # ----------------------------------------------------
        # Prepare common SonarSurvey object
        # ----------------------------------------------------

        return SonarSurvey(
    input_type="GEOTIFF",
    file_format=source_path.suffix.replace(".", "").upper(),

    original_file=str(source_path),

    image_path=str(preview_path),
    preview_image_path=str(preview_path),

    navigation_available=False,

    navigation=[],
    ping_metadata=[],

    sonar_metadata={
        "width": src.width,
        "height": src.height,
        "bands": src.count,
        "dtype": [
            str(dtype)
            for dtype in src.dtypes
        ],
        "driver": src.driver,
    },

    crs=crs_string,

    geo_transform=(
        list(transform)
        if transform is not None
        else None
    ),

    geo_bounds=[
        src.bounds.left,
        src.bounds.bottom,
        src.bounds.right,
        src.bounds.top,
    ],

    pixel_size=[
        abs(src.res[0]),
        abs(src.res[1]),
    ],

    location_status=(
        "geotagged"
        if has_valid_transform
        else "unavailable"
    ),

    location_source=(
        "GeoTIFF"
        if has_valid_transform
        else None
    ),

    georeferencing_available=has_valid_transform,

    raster_width=src.width,
    raster_height=src.height,
    raster_bands=src.count,
)
           