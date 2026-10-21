from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np


class SWNetSegmentation:
    """
    SW-Net segmentation adapter.

    Responsibility:
        - validate SW-Net configuration
        - crop the detector's bounding-box region
        - prepare the crop for SW-Net
        - run the real SW-Net model once it is connected
        - return segmentation information

    This module does NOT:
        - perform object detection
        - perform geotagging
        - calculate latitude/longitude
        - decide geographic coordinates

    Current status:
        The actual trained SW-Net network architecture is not
        connected yet. Therefore Real Mode segmentation fails
        explicitly instead of returning a fake mask/polygon.
    """

    def __init__(
        self,
        weights_path: str,
    ):
        self.weights_path = (
            str(weights_path).strip()
            if weights_path
            else ""
        )

        self.model = None
        self.model_loaded = False

        self._load_model()

    # ========================================================
    # MODEL LOADING
    # ========================================================

    def _load_model(self) -> None:
        """
        Validate the configured checkpoint.

        IMPORTANT:
            A checkpoint existing on disk is NOT considered
            a loaded model until the actual SW-Net architecture
            is instantiated and its weights are loaded.
        """

        if not self.weights_path:

            print(
                "SW-Net weights are not configured."
            )

            self.model_loaded = False

            return

        if not os.path.isfile(
            self.weights_path
        ):

            print(
                "SW-Net weights file not found: "
                f"{self.weights_path}"
            )

            self.model_loaded = False

            return

        print(
            "SW-Net checkpoint found: "
            f"{self.weights_path}"
        )

        print(
            "SW-Net model architecture is not "
            "connected yet."
        )

        # IMPORTANT:
        # Do not set model_loaded=True here.
        #
        # Once your actual SW-Net architecture is implemented,
        # this section will become approximately:
        #
        #     self.model = SWNet(...)
        #     checkpoint = torch.load(...)
        #     self.model.load_state_dict(...)
        #     self.model.eval()
        #     self.model_loaded = True

        self.model_loaded = False

    # ========================================================
    # BOUNDING BOX
    # ========================================================

    @staticmethod
    def _parse_bbox(
        bbox: Dict[str, Any],
    ) -> Tuple[
        int,
        int,
        int,
        int,
    ]:
        """
        Convert bbox into integer pixel coordinates.

        Accepted format:

            {
                "x": ...,
                "y": ...,
                "width": ...,
                "height": ...
            }

        Returns:

            x1, y1, x2, y2
        """

        if not isinstance(
            bbox,
            dict,
        ):
            raise ValueError(
                "SW-Net bbox must be a dictionary."
            )

        required = (
            "x",
            "y",
            "width",
            "height",
        )

        if not all(
            key in bbox
            for key in required
        ):
            raise ValueError(
                "SW-Net bbox must contain "
                "x, y, width and height."
            )

        x = float(
            bbox["x"]
        )

        y = float(
            bbox["y"]
        )

        width = float(
            bbox["width"]
        )

        height = float(
            bbox["height"]
        )

        if width <= 0 or height <= 0:
            raise ValueError(
                "SW-Net bbox width and height "
                "must be greater than zero."
            )

        x1 = int(
            round(x)
        )

        y1 = int(
            round(y)
        )

        x2 = int(
            round(x + width)
        )

        y2 = int(
            round(y + height)
        )

        return (
            x1,
            y1,
            x2,
            y2,
        )

    # ========================================================
    # CROP DETECTION
    # ========================================================

    @staticmethod
    def _crop_detection(
        image_path: str,
        bbox: Dict[str, Any],
    ) -> Tuple[
        np.ndarray,
        Tuple[int, int, int, int],
    ]:
        """
        Crop the detector's region from the image.

        Returns:
            crop,
            clipped bbox
        """

        if not image_path:
            raise ValueError(
                "Image path is empty."
            )

        image = cv2.imread(
            image_path,
            cv2.IMREAD_COLOR,
        )

        if image is None:
            raise ValueError(
                f"Could not read image: "
                f"{image_path}"
            )

        image_height, image_width = (
            image.shape[:2]
        )

        x1, y1, x2, y2 = (
            SWNetSegmentation._parse_bbox(
                bbox
            )
        )

        # ----------------------------------------------------
        # Clip bbox to actual image boundaries
        # ----------------------------------------------------

        x1 = max(
            0,
            min(
                x1,
                image_width - 1,
            ),
        )

        y1 = max(
            0,
            min(
                y1,
                image_height - 1,
            ),
        )

        x2 = max(
            x1 + 1,
            min(
                x2,
                image_width,
            ),
        )

        y2 = max(
            y1 + 1,
            min(
                y2,
                image_height,
            ),
        )

        crop = image[
            y1:y2,
            x1:x2,
        ]

        if crop.size == 0:
            raise RuntimeError(
                "The detection crop is empty."
            )

        return (
            crop,
            (
                x1,
                y1,
                x2,
                y2,
            ),
        )

    # ========================================================
    # REAL SW-NET INFERENCE
    # ========================================================

    def _run_model(
        self,
        crop: np.ndarray,
    ) -> np.ndarray:
        """
        Run the actual SW-Net model.

        This function intentionally raises until the actual
        trained SW-Net architecture has been connected.
        """

        if not self.model_loaded:
            raise RuntimeError(
                "SW-Net inference is not available. "
                "The trained SW-Net architecture and checkpoint "
                "have not been connected to the backend yet."
            )

        if crop is None or crop.size == 0:
            raise ValueError(
                "SW-Net received an empty crop."
            )

        # ====================================================
        # REAL MODEL CODE WILL GO HERE
        # ====================================================
        #
        # Example final flow:
        #
        # tensor = preprocess_for_swnet(crop)
        #
        # with torch.no_grad():
        #     logits = self.model(tensor)
        #
        # probability = torch.sigmoid(logits)
        #
        # mask = (
        #     probability >= 0.5
        # ).cpu().numpy()
        #
        # return mask
        #
        # ====================================================

        raise RuntimeError(
            "SW-Net model inference is not implemented yet."
        )

    # ========================================================
    # PUBLIC SEGMENT FUNCTION
    # ========================================================

    def segment(
        self,
        image_path: str,
        bbox: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Segment the region identified by the detector.

        Input:
            image_path
            detector bbox

        Conceptual flow:

            image
              ↓
            bbox
              ↓
            crop
              ↓
            SW-Net
              ↓
            pixel mask
        """

        # ----------------------------------------------------
        # Crop detector region first.
        # ----------------------------------------------------

        crop, clipped_bbox = (
            self._crop_detection(
                image_path,
                bbox,
            )
        )

        # ----------------------------------------------------
        # Run actual SW-Net model
        # ----------------------------------------------------

        mask = self._run_model(
            crop
        )

        # ----------------------------------------------------
        # Validate returned mask
        # ----------------------------------------------------

        if mask is None:
            raise RuntimeError(
                "SW-Net returned no segmentation mask."
            )

        mask = np.asarray(
            mask
        )

        if mask.size == 0:
            raise RuntimeError(
                "SW-Net returned an empty segmentation mask."
            )

        return {
            "available": True,

            "method": "SW-Net",

            "mask": mask,

            "crop_bbox": {
                "x": clipped_bbox[0],
                "y": clipped_bbox[1],
                "width": (
                    clipped_bbox[2]
                    - clipped_bbox[0]
                ),
                "height": (
                    clipped_bbox[3]
                    - clipped_bbox[1]
                ),
            },
        }