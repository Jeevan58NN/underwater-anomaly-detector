from __future__ import annotations

import os
from typing import List

from .base import Detector, RawDetection


class SonarDeNetDetector(Detector):
    """
    SonarDeNet detector adapter.

    Current status:
        This class is an adapter/interface for the real
        SonarDeNet model.

    The actual model implementation is not included here yet.

    Therefore:
        - weights are validated
        - model availability is tracked
        - inference fails clearly instead of returning
          fabricated detections

    Later, when the actual SonarDeNet implementation is ready,
    only this adapter needs to be connected to it.
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
    # Detector name
    # ========================================================

    @property
    def name(self) -> str:
        return "SonarDeNet"

    # ========================================================
    # Model loading
    # ========================================================

    def _load_model(self) -> None:
        """
        Validate the configured weight file.

        IMPORTANT:
        A file existing on disk does not automatically mean
        SonarDeNet has been loaded.

        The actual SonarDeNet architecture/loading code needs
        to be connected once the trained implementation is
        available.
        """

        if not self.weights_path:

            self.model_loaded = False

            print(
                "SonarDeNet weights are not configured."
            )

            return

        if not os.path.isfile(
            self.weights_path
        ):

            self.model_loaded = False

            print(
                "SonarDeNet weights file not found: "
                f"{self.weights_path}"
            )

            return

        # ----------------------------------------------------
        # IMPORTANT
        # ----------------------------------------------------
        #
        # Do NOT set model_loaded=True here.
        #
        # The previous code did that simply because the file
        # existed, even though no model was actually loaded.
        #
        # We will set it to True only after the real model
        # object is instantiated successfully.
        # ----------------------------------------------------

        print(
            "SonarDeNet weight file found:"
            f" {self.weights_path}"
        )

        print(
            "SonarDeNet model implementation is "
            "not connected yet."
        )

        self.model_loaded = False

    # ========================================================
    # Prediction
    # ========================================================

    def predict(
        self,
        image_path: str,
        image_width: int,
        image_height: int,
    ) -> List[RawDetection]:
        """
        Run SonarDeNet inference.

        This currently raises an explicit error because the
        actual trained SonarDeNet implementation has not been
        connected yet.

        It intentionally does NOT return [] because an empty
        result could be mistaken for:
            "The model detected nothing."

        Instead:
            "The model is not implemented/configured yet."
        """

        if not self.model_loaded:

            raise RuntimeError(
                "SonarDeNet inference is not available. "
                "The backend adapter exists, but the actual "
                "trained SonarDeNet model has not been connected yet."
            )

        if not image_path:

            raise ValueError(
                "Image path is empty."
            )

        if image_width <= 0:

            raise ValueError(
                "image_width must be greater than zero."
            )

        if image_height <= 0:

            raise ValueError(
                "image_height must be greater than zero."
            )

        # ----------------------------------------------------
        # REAL MODEL INFERENCE WILL GO HERE
        # ----------------------------------------------------

        # Example final structure:
        #
        # outputs = self.model(image)
        #
        # detections = ...
        #
        # return [
        #     RawDetection(
        #         class_name=...,
        #         confidence=...,
        #         bbox={
        #             "x": ...,
        #             "y": ...,
        #             "width": ...,
        #             "height": ...
        #         },
        #     )
        # ]

        raise RuntimeError(
            "SonarDeNet prediction is not implemented yet."
        )