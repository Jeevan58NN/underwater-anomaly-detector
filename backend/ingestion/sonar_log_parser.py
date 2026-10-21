from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image

from .image_loader import SonarSurvey


# ============================================================
# OPTIONAL XTF LIBRARY
# ============================================================
#
# We try to import pyxtf.
#
# If it is not installed, XTF parsing will return a clear
# configuration error instead of generating fake sonar/GPS data.
#
try:
    import pyxtf  # type: ignore

    PYXTF_AVAILABLE = True

except ImportError:

    pyxtf = None
    PYXTF_AVAILABLE = False


# ============================================================
# HELPERS
# ============================================================

def _ensure_directory(
    directory: str,
) -> Path:
    """
    Create extraction/output directory if required.
    """

    path = Path(directory)

    path.mkdir(
        parents=True,
        exist_ok=True,
    )

    return path


def _find_navigation_fields(
    record: Any,
) -> Optional[Dict[str, Any]]:
    """
    Try to extract common navigation fields from an XTF
    navigation record.

    XTF files can differ in the fields they expose, so this
    function uses safe attribute/dictionary access.

    Returns None if latitude/longitude cannot be obtained.
    """

    def get_value(
        name: str,
    ):
        if isinstance(
            record,
            dict,
        ):
            return record.get(name)

        return getattr(
            record,
            name,
            None,
        )

    latitude = (
        get_value("latitude")
        if get_value("latitude") is not None
        else get_value("Latitude")
    )

    longitude = (
        get_value("longitude")
        if get_value("longitude") is not None
        else get_value("Longitude")
    )

    if latitude is None or longitude is None:
        return None

    try:
        latitude = float(latitude)
        longitude = float(longitude)

    except (TypeError, ValueError):
        return None

    # Basic geographic validation
    if not (
        -90.0 <= latitude <= 90.0
        and
        -180.0 <= longitude <= 180.0
    ):
        return None

    timestamp = (
        get_value("timestamp")
        if get_value("timestamp") is not None
        else get_value("Timestamp")
    )

    heading = (
        get_value("heading")
        if get_value("heading") is not None
        else get_value("Heading")
    )

    try:
        if heading is not None:
            heading = float(heading)
    except (TypeError, ValueError):
        heading = None

    return {
        "timestamp": timestamp,
        "latitude": latitude,
        "longitude": longitude,
        "heading": heading,
    }


# ============================================================
# XTF PARSER
# ============================================================

def _parse_xtf(
    file_path: str,
    extract_dir: str,
) -> SonarSurvey:
    """
    Parse an XTF sonar log.

    This function intentionally does NOT fabricate data.

    A complete XTF implementation needs to:
        1. Read sonar ping records
        2. Extract PORT / STBD acoustic data
        3. Build an SSS image
        4. Extract timestamps
        5. Extract navigation
        6. Preserve ping-to-navigation association

    The exact pyxtf API can vary by package/version, so this
    module keeps that implementation isolated from the rest
    of the application.
    """

    if not PYXTF_AVAILABLE:

        raise RuntimeError(
            "XTF support requires the 'pyxtf' package. "
            "Install it with: pip install pyxtf"
        )

    # --------------------------------------------------------
    # Verify source file
    # --------------------------------------------------------

    source_path = Path(file_path)

    if not source_path.is_file():
        raise FileNotFoundError(
            f"XTF file not found: {source_path}"
        )

    output_dir = _ensure_directory(
        extract_dir
    )

    # --------------------------------------------------------
    # IMPORTANT
    # --------------------------------------------------------
    #
    # We do not create a fake image or fake navigation.
    #
    # Instead, attempt to use pyxtf.
    #
    # The actual API differs between releases, so we inspect
    # available parser functionality rather than assuming a
    # particular function exists.
    # --------------------------------------------------------

    parser_candidates = [
        getattr(
            pyxtf,
            "xtf_read",
            None,
        ),

        getattr(
            pyxtf,
            "read",
            None,
        ),
    ]

    parser = next(
        (
            candidate
            for candidate in parser_candidates
            if callable(candidate)
        ),
        None,
    )

    if parser is None:

        raise RuntimeError(
            "pyxtf is installed, but this version does not "
            "expose a supported XTF reader through the "
            "configured adapter. "
            "XTF-specific parser integration must be configured "
            "for the installed pyxtf version."
        )

    # --------------------------------------------------------
    # Attempt to open/read the XTF
    # --------------------------------------------------------

    try:

        xtf_data = parser(
            str(source_path)
        )

    except Exception as exc:

        raise RuntimeError(
            f"Failed to parse XTF file: {source_path.name}. "
            f"Parser error: {exc}"
        ) from exc

    # --------------------------------------------------------
    # Normalize parser output
    # --------------------------------------------------------

    if xtf_data is None:

        raise RuntimeError(
            "XTF parser returned no data."
        )

    # --------------------------------------------------------
    # Navigation extraction
    # --------------------------------------------------------

    navigation: List[
        Dict[str, Any]
    ] = []

    ping_metadata: List[
        Dict[str, Any]
    ] = []

    sonar_metadata: Dict[
        str,
        Any
    ] = {}

    # --------------------------------------------------------
    # NOTE:
    #
    # pyxtf output structures can differ. We intentionally
    # inspect common containers but do not fabricate records.
    # --------------------------------------------------------

    records = []

    if isinstance(
        xtf_data,
        dict,
    ):

        records = (
            xtf_data.get("navigation")
            or xtf_data.get("nav")
            or xtf_data.get("records")
            or []
        )

        sonar_metadata = (
            xtf_data.get("metadata")
            or {}
        )

    elif isinstance(
        xtf_data,
        (list, tuple),
    ):

        records = list(
            xtf_data
        )

    # --------------------------------------------------------
    # Extract valid navigation records
    # --------------------------------------------------------

    for record in records:

        nav = _find_navigation_fields(
            record
        )

        if nav is not None:

            navigation.append(
                nav
            )

    # --------------------------------------------------------
    # Extract ping metadata when available
    # --------------------------------------------------------

    if isinstance(
        xtf_data,
        dict,
    ):

        raw_pings = (
            xtf_data.get("pings")
            or xtf_data.get("ping_metadata")
            or []
        )

        for index, ping in enumerate(
            raw_pings
        ):

            if isinstance(
                ping,
                dict,
            ):

                ping_id = (
                    ping.get("ping_id")
                    if ping.get("ping_id") is not None
                    else index
                )

                timestamp = ping.get(
                    "timestamp"
                )

                ping_metadata.append(
                    {
                        "ping_id": ping_id,
                        "timestamp": timestamp,
                    }
                )

    # --------------------------------------------------------
    # SSS image extraction
    # --------------------------------------------------------
    #
    # This is deliberately kept as a strict validation point.
    #
    # If the installed parser does not provide the sonar
    # channel data in a supported representation, we raise a
    # clear error rather than create a fake image.
    # --------------------------------------------------------

    sonar_image = None

    if isinstance(
        xtf_data,
        dict,
    ):

        sonar_image = (
            xtf_data.get("image")
            or xtf_data.get("sss_image")
            or xtf_data.get("sonar_image")
        )

    if sonar_image is None:

        raise RuntimeError(
            "XTF file was opened successfully, but the current "
            "XTF adapter did not obtain a Side-Scan Sonar image. "
            "The parser must be configured to extract PORT/STBD "
            "sonar channels before this file can enter the AI pipeline."
        )

    # --------------------------------------------------------
    # Save extracted sonar image
    # --------------------------------------------------------

    preview_path = (
        output_dir
        /
        f"preview_{source_path.stem}.png"
    )

    try:

        if isinstance(
            sonar_image,
            Image.Image,
        ):

            image = (
                sonar_image
                .convert("RGB")
            )

        else:

            # NumPy arrays and compatible image objects
            # can be converted through PIL.
            image = Image.fromarray(
                sonar_image
            ).convert(
                "RGB"
            )

        image.save(
            preview_path,
            format="PNG",
        )

    except Exception as exc:

        raise RuntimeError(
            "Failed to convert extracted XTF sonar "
            "data into a PNG preview."
        ) from exc

    # --------------------------------------------------------
    # Final navigation status
    # --------------------------------------------------------

    navigation_available = (
        len(navigation) > 0
    )

    if navigation_available:

        location_status = (
            "geotagged"
        )

        location_source = (
            "XTF Navigation"
        )

    else:

        location_status = (
            "unavailable"
        )

        location_source = None

    # --------------------------------------------------------
    # Return standardized survey
    # --------------------------------------------------------

    return SonarSurvey(
        input_type="SONAR_LOG",

        file_format=source_path.suffix
            .replace(".", "")
            .upper(),

        original_file=str(
            source_path
        ),

        image_path=str(
            preview_path
        ),

        preview_image_path=str(
            preview_path
        ),

        navigation_available=(
            navigation_available
        ),

        navigation=navigation,

        ping_metadata=(
            ping_metadata
        ),

        sonar_metadata=(
            sonar_metadata
        ),

        crs=None,

        geo_transform=None,

        geo_bounds=None,

        pixel_size=None,

        location_status=(
            location_status
        ),

        location_source=(
            location_source
        ),

        georeferencing_available=False,

        raster_width=image.width,

        raster_height=image.height,

        raster_bands=3,
    )


# ============================================================
# JSF
# ============================================================

def _parse_jsf(
    file_path: str,
    extract_dir: str,
) -> SonarSurvey:
    """
    JSF support is intentionally explicit.

    We do not pretend that XTF parsing automatically supports
    JSF.
    """

    raise NotImplementedError(
        "JSF parsing is not implemented yet. "
        "Use XTF or add a dedicated JSF parser adapter."
    )


# ============================================================
# PUBLIC ENTRY POINT
# ============================================================

def parse_sonar_log(
    file_path: str,
    extract_dir: str,
) -> SonarSurvey:
    """
    Parse supported sonar log formats.

    Supported:
        .xtf
        .jsf (explicitly reported as unsupported until a parser
              is added)

    No fake image or fake navigation data are generated.
    """

    if not file_path:
        raise ValueError(
            "Sonar log path is empty."
        )

    source_path = Path(
        file_path
    )

    if not source_path.is_file():
        raise FileNotFoundError(
            f"Sonar log not found: {source_path}"
        )

    ext = (
        source_path.suffix
        .lower()
    )

    if ext == ".xtf":

        return _parse_xtf(
            str(source_path),
            extract_dir,
        )

    if ext == ".jsf":

        return _parse_jsf(
            str(source_path),
            extract_dir,
        )

    raise ValueError(
        f"Unsupported sonar log format: {ext}"
    )