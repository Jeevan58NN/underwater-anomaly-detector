from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class RawDetection:
    """
    Standard output returned by every detector.

    bbox uses image/tile coordinates:

        {
            "x": left,
            "y": top,
            "width": width,
            "height": height
        }

    The bounding box is always relative to the image/tile
    passed to Detector.predict().

    Geotagging is handled separately by the analysis pipeline.
    """

    class_name: str

    confidence: float

    bbox: Dict[str, float]

    # Optional sonar geometry information.
    #
    # These fields are retained for future XTF/live-sonar
    # processing. They are NOT used for GeoTIFF geotagging.
    relative_angle: float = 0.0

    sonar_range: float = 0.0


class Detector(ABC):
    """
    Common interface for all detection engines.

    Current:
        MockDetector
        SonarDeNetDetector

    Future:
        DualStreamDetector
            ├── SonarDeNet
            └── YOLO11
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Human-readable detector name.
        """
        raise NotImplementedError

    @abstractmethod
    def predict(
        self,
        image_path: str,
        image_width: int,
        image_height: int,
    ) -> List[RawDetection]:
        """
        Run inference on one image/tile.

        Parameters
        ----------
        image_path:
            Path to the image/tile.

        image_width:
            Width of the image/tile in pixels.

        image_height:
            Height of the image/tile in pixels.

        Returns
        -------
        List[RawDetection]
            Zero or more detections.
        """
        raise NotImplementedError