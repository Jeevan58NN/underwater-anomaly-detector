from __future__ import annotations

import os
from typing import Optional, Dict, Any, List


class SonarSurvey:
    """
    Common internal representation of any sonar input.

    Supported input sources:
        - PNG / JPG / JPEG
        - TIFF / GeoTIFF
        - XTF / JSF

    The object keeps the sonar image separate from
    navigation/geospatial information so that the same
    analysis pipeline can work with all input types.
    """

    def __init__(
        self,
        input_type: str,
        file_format: str,
        image_path: str,
        navigation: Optional[List[Dict[str, Any]]] = None,
        ping_metadata: Optional[List[Dict[str, Any]]] = None,
        sonar_metadata: Optional[Dict[str, Any]] = None,
        original_file: Optional[str] = None,
        preview_image_path: Optional[str] = None,
        navigation_available: bool = False,
        crs: Optional[str] = None,
        geo_transform: Optional[list] = None,
        geo_bounds: Optional[list] = None,
        pixel_size: Optional[list] = None,
        location_status: str = "unavailable",
        location_source: Optional[str] = None,
        georeferencing_available: bool = False,
        raster_width: Optional[int] = None,
        raster_height: Optional[int] = None,
        raster_bands: Optional[int] = None,
    ):
        # ----------------------------------------------------
        # Basic input information
        # ----------------------------------------------------

        self.input_type = input_type
        self.file_format = file_format
        self.image_path = image_path

        # Original source file.
        # For GeoTIFF this must remain the authoritative
        # source for geographic calculations.
        self.original_file = (
            original_file
            if original_file
            else image_path
        )

        # Browser/model friendly preview image.
        self.preview_image_path = (
            preview_image_path
            if preview_image_path
            else image_path
        )

        # ----------------------------------------------------
        # Sonar / navigation metadata
        # ----------------------------------------------------

        self.navigation = (
            navigation
            if navigation is not None
            else []
        )

        self.ping_metadata = (
            ping_metadata
            if ping_metadata is not None
            else []
        )

        self.sonar_metadata = (
            sonar_metadata
            if sonar_metadata is not None
            else {}
        )

        # True ONLY when actual navigation records exist
        # or an explicitly valid navigation source was provided.
        self.navigation_available = bool(
            navigation_available
        )

        # ----------------------------------------------------
        # Geographic reference information
        # ----------------------------------------------------

        self.crs = crs

        # Stored as a serializable list.
        #
        # For GeoTIFF this represents the affine transform:
        #
        # pixel(row, col) -> projected X/Y
        #
        self.geo_transform = (
            geo_transform
            if geo_transform is not None
            else None
        )

        # [left, bottom, right, top]
        self.geo_bounds = (
            geo_bounds
            if geo_bounds is not None
            else None
        )

        # [x_resolution, y_resolution]
        self.pixel_size = (
            pixel_size
            if pixel_size is not None
            else None
        )

        # True means the raster/file contains enough
        # geospatial reference information for a coordinate
        # transformation to be attempted.
        self.georeferencing_available = bool(
            georeferencing_available
        )

        # ----------------------------------------------------
        # Location information
        # ----------------------------------------------------

        self.location_status = (
            location_status
            if location_status
            else "unavailable"
        )

        self.location_source = location_source

        # ----------------------------------------------------
        # Raster information
        # ----------------------------------------------------

        self.raster_width = raster_width
        self.raster_height = raster_height
        self.raster_bands = raster_bands

    # ========================================================
    # Convenience helpers
    # ========================================================

    def has_navigation(self) -> bool:
        """
        Return True only when real navigation data are available.
        """
        return self.navigation_available and bool(
            self.navigation
        )

    def has_georeferencing(self) -> bool:
        """
        Return True when the input has usable georeferencing.
        """
        return (
            self.georeferencing_available
            and self.crs is not None
            and self.geo_transform is not None
        )

    def has_location_information(self) -> bool:
        """
        Return True when some location source is available.
        This can be:
            - GeoTIFF georeferencing
            - XTF navigation
            - Live navigation
            - another supported source
        """
        return (
            self.has_navigation()
            or self.has_georeferencing()
            or self.location_status == "geotagged"
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the survey object into a JSON-friendly dictionary.
        """

        return {
            "input_type": self.input_type,
            "file_format": self.file_format,
            "image_path": self.image_path,
            "original_file": self.original_file,
            "preview_image_path": self.preview_image_path,

            "navigation_available":
                self.navigation_available,

            "navigation": self.navigation,
            "ping_metadata": self.ping_metadata,
            "sonar_metadata": self.sonar_metadata,

            "crs": self.crs,
            "geo_transform": self.geo_transform,
            "geo_bounds": self.geo_bounds,
            "pixel_size": self.pixel_size,

            "georeferencing_available":
                self.georeferencing_available,

            "location_status":
                self.location_status,

            "location_source":
                self.location_source,

            "raster_width":
                self.raster_width,

            "raster_height":
                self.raster_height,

            "raster_bands":
                self.raster_bands,
        }


# ============================================================
# Standard image loader
# ============================================================

def load_standard_image(
    file_path: str
) -> SonarSurvey:
    """
    Load a normal image file such as:

        PNG
        JPG
        JPEG

    No geographic information is assumed.

    Therefore:
        navigation_available = False
        georeferencing_available = False
        location_status = unavailable
    """

    if not file_path:
        raise ValueError(
            "Image file path is empty."
        )

    if not os.path.isfile(file_path):
        raise FileNotFoundError(
            f"Image file not found: {file_path}"
        )

    ext = os.path.splitext(
        file_path
    )[1].lower()

    supported_extensions = {
        ".png",
        ".jpg",
        ".jpeg",
        ".tif",
        ".tiff",
    }

    if ext not in supported_extensions:
        raise ValueError(
            f"Unsupported image format: {ext}"
        )

    return SonarSurvey(
        input_type="IMAGE",

        file_format=ext
            .replace(".", "")
            .upper(),

        image_path=file_path,

        navigation=[],
        ping_metadata=[],
        sonar_metadata={},

        original_file=file_path,
        preview_image_path=file_path,

        navigation_available=False,

        crs=None,
        geo_transform=None,
        geo_bounds=None,
        pixel_size=None,

        location_status="unavailable",
        location_source=None,

        georeferencing_available=False,

        raster_width=None,
        raster_height=None,
        raster_bands=None,
    )