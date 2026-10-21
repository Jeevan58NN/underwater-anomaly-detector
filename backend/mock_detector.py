"""
mock_detector.py

Simulation-mode detection engine for AquaScan AI.

IMPORTANT:
    MockDetector is used ONLY for Simulation Mode.

It generates deterministic demo detections so that the same
input image produces the same detections each time.

This module is responsible ONLY for detection.

It does NOT perform:
    - geotagging
    - segmentation
    - verification
    - map conversion

Those operations are handled by the main analysis pipeline.
"""

from __future__ import annotations

import hashlib

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


# ============================================================
# DEMO CLASSES
# ============================================================

PROTOTYPE_CLASSES = [
    "Ghost Net",
    "Pipe",
    "Cylinder",
    "Shipwreck",
    "Unknown Anomaly",
]


# ============================================================
# RAW DETECTION
# ============================================================

@dataclass
class RawDetection:
    """
    Standard detection output shared between simulation
    and real detection engines.

    bbox format:

        {
            "x": left,
            "y": top,
            "width": width,
            "height": height
        }

    Coordinates are relative to the image/tile passed to
    the detector.
    """

    class_name: str

    confidence: float

    bbox: dict

    # Optional sonar geometry fields.
    #
    # These are retained for future XTF/live-sonar support.
    # They are NOT used for GeoTIFF geotagging.
    relative_angle: float = 0.0

    sonar_range: float = 0.0


# ============================================================
# DETECTOR INTERFACE
# ============================================================

class Detector(ABC):
    """
    Common interface for every detection engine.

    Simulation:
        MockDetector

    Real:
        Eventually:
            DualStreamDetector
            (SonarDeNet + YOLO11)
    """

    @abstractmethod
    def predict(
        self,
        image_path: str,
        image_width: int,
        image_height: int,
    ) -> List[RawDetection]:
        """
        Run detection on one image/tile.
        """
        raise NotImplementedError


# ============================================================
# MOCK DETECTOR
# ============================================================

class MockDetector(Detector):
    """
    Deterministic simulation detector.

    The detections are generated from a hash of the input
    file path, so the same input produces the same result.

    This makes the frontend and backend demonstrations
    repeatable.
    """

    name = "MockDetector"

    def predict(
        self,
        image_path: str,
        image_width: int,
        image_height: int,
    ) -> List[RawDetection]:

        if image_width <= 0:
            raise ValueError(
                "image_width must be greater than zero."
            )

        if image_height <= 0:
            raise ValueError(
                "image_height must be greater than zero."
            )

        # ----------------------------------------------------
        # Deterministic seed
        # ----------------------------------------------------

        seed = self._seed_from_file(
            image_path
        )

        rng_state = seed

        # ----------------------------------------------------
        # Lightweight deterministic pseudo-random generator
        # ----------------------------------------------------

        def next_val(
            lo: float,
            hi: float,
        ) -> float:

            nonlocal rng_state

            rng_state = (
                1103515245 * rng_state
                + 12345
            ) & 0x7FFFFFFF

            fraction = (
                rng_state
                / 0x7FFFFFFF
            )

            return (
                lo
                + fraction
                * (hi - lo)
            )

        # ----------------------------------------------------
        # Number of demo detections
        # ----------------------------------------------------

        num_detections = (
            2
            if seed % 3 != 0
            else 3
        )

        detections: List[
            RawDetection
        ] = []

        # ----------------------------------------------------
        # Generate detections
        # ----------------------------------------------------

        for i in range(
            num_detections
        ):

            class_index = (
                seed
                + i * 7
            ) % len(
                PROTOTYPE_CLASSES
            )

            class_name = (
                PROTOTYPE_CLASSES[
                    class_index
                ]
            )

            confidence = round(
                next_val(
                    0.62,
                    0.97,
                ),
                2,
            )

            # ------------------------------------------------
            # Bounding box dimensions
            # ------------------------------------------------

            max_box_width = max(
                41,
                min(
                    240,
                    image_width - 20,
                ),
            )

            max_box_height = max(
                41,
                min(
                    160,
                    image_height - 20,
                ),
            )

            min_box_width = min(
                90,
                max_box_width,
            )

            min_box_height = min(
                60,
                max_box_height,
            )

            box_width = int(
                next_val(
                    min_box_width,
                    max_box_width,
                )
            )

            box_height = int(
                next_val(
                    min_box_height,
                    max_box_height,
                )
            )

            # ------------------------------------------------
            # Bounding box position
            # ------------------------------------------------

            max_x = max(
                0,
                image_width
                - box_width,
            )

            max_y = max(
                0,
                image_height
                - box_height,
            )

            x = int(
                next_val(
                    0,
                    max_x,
                )
            )

            y = int(
                next_val(
                    0,
                    max_y,
                )
            )

            # ------------------------------------------------
            # Optional sonar geometry
            # ------------------------------------------------
            #
            # These values are ONLY retained as demo metadata.
            #
            # They must NOT be interpreted as actual sonar
            # measurements for GeoTIFF geotagging.
            # ------------------------------------------------

            relative_angle = next_val(
                0,
                360,
            )

            sonar_range = next_val(
                15,
                80,
            )

            detections.append(
                RawDetection(
                    class_name=class_name,

                    confidence=confidence,

                    bbox={
                        "x": x,
                        "y": y,
                        "width": box_width,
                        "height": box_height,
                    },

                    relative_angle=(
                        relative_angle
                    ),

                    sonar_range=(
                        sonar_range
                    ),
                )
            )

        return detections

    # ========================================================
    # SEED
    # ========================================================

    @staticmethod
    def _seed_from_file(
        image_path: str,
    ) -> int:
        """
        Generate a deterministic seed from the image path.

        This is intentionally deterministic so the demo is
        repeatable.
        """

        path_string = str(
            image_path
        )

        digest = hashlib.md5(
            path_string.encode(
                "utf-8"
            )
        ).hexdigest()

        return int(
            digest[:8],
            16,
        )


# ============================================================
# SHARED HELPERS
# ============================================================

def confidence_band(
    confidence: float,
) -> str:
    """
    Convert confidence into a simple display band.
    """

    percentage = (
        float(confidence)
        * 100.0
    )

    if percentage >= 90:
        return "High"

    if percentage >= 70:
        return "Medium"

    return "Low"


def severity_for(
    confidence: float,
    class_name: str,
) -> str:
    """
    Prototype severity rule.

    This is a UI/prioritization helper, not a certified
    maritime risk assessment.
    """

    if (
        class_name in (
            "Pipe",
            "Shipwreck",
        )
        and confidence >= 0.85
    ):
        return "High"

    return confidence_band(
        confidence
    )


def seafloor_assessment_for(
    seed_value: int,
) -> dict:
    """
    Simulation-only natural/artificial estimate.

    This is NOT a trained classifier.

    Real Mode should eventually receive its verification
    result from the actual verification pipeline.
    """

    artificial = (
        60
        + (
            int(seed_value)
            % 35
        )
    )

    artificial = float(
        artificial
    )

    natural = (
        100.0
        - artificial
    )

    return {
        "artificial_pct": artificial,
        "natural_pct": natural,
        "note": (
            "Simulation estimate — "
            "not derived from a trained classifier."
        ),
    }


# ============================================================
# IMPORTANT
# ============================================================
#
# There is intentionally NO geotag_detection() function here.
#
# Geotagging belongs to:
#
#     backend/geotagging.py
#
# and is called by:
#
#     backend/pipeline/analysis_pipeline.py
#
# This keeps detection and geolocation independent.
# ============================================================