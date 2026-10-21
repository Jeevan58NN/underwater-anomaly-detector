from __future__ import annotations

import os

from .image_loader import load_standard_image
from .sonar_log_parser import parse_sonar_log
from .geotiff_reader import load_geotiff


# File formats supported by the application
SONAR_LOG_EXTENSIONS = {".xtf", ".jsf"}
GEOTIFF_EXTENSIONS = {".tif", ".tiff"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def route_input(
    file_path: str,
    ext: str,
    extract_dir: str,
):
    """
    Route an uploaded sonar file to the correct input processor.

    Supported inputs:
        .xtf / .jsf   -> sonar log parser
        .tif / .tiff  -> GeoTIFF reader
        .png/.jpg/... -> standard image loader

    Returns:
        A standardized input object produced by the selected loader.
    """

    if not file_path:
        raise ValueError("Input file path is empty.")

    if not os.path.isfile(file_path):
        raise FileNotFoundError(
            f"Input file does not exist: {file_path}"
        )

    # Normalize extension.
    # If ext is not supplied correctly, derive it from file_path.
    normalized_ext = (ext or "").strip().lower()

    if not normalized_ext:
        normalized_ext = os.path.splitext(file_path)[1].lower()

    # ---------------------------------------------------------
    # XTF / JSF sonar logs
    # ---------------------------------------------------------
    if normalized_ext in SONAR_LOG_EXTENSIONS:

        return parse_sonar_log(
            file_path,
            extract_dir,
        )

    # ---------------------------------------------------------
    # GeoTIFF / TIFF
    # ---------------------------------------------------------
    if normalized_ext in GEOTIFF_EXTENSIONS:

        return load_geotiff(
            file_path,
            extract_dir,
        )

    # ---------------------------------------------------------
    # Normal sonar images
    # ---------------------------------------------------------
    if normalized_ext in IMAGE_EXTENSIONS:

        return load_standard_image(
            file_path
        )

    # ---------------------------------------------------------
    # Unsupported format
    # ---------------------------------------------------------
    supported = sorted(
        SONAR_LOG_EXTENSIONS
        | GEOTIFF_EXTENSIONS
        | IMAGE_EXTENSIONS
    )

    raise ValueError(
        f"Unsupported input format: {normalized_ext or 'unknown'}. "
        f"Supported formats: {', '.join(supported)}"
    )