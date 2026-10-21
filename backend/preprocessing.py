from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

import cv2
import numpy as np


def preprocess_sss_image(
    image_path: str,
    output_path: str,
) -> str:
    """
    Preprocess one Side-Scan Sonar image/tile.

    Pipeline:
        1. Load grayscale sonar image
        2. Speckle/noise reduction
        3. CLAHE contrast enhancement
        4. Intensity normalization
        5. Save processed image

    IMPORTANT:
        The output keeps the SAME width and height as the input.
        No resize, crop, or padding is performed here.

        This is important because model bounding-box coordinates
        can then be mapped directly back to the original tile.
    """

    if not image_path:
        raise ValueError(
            "Input image path is empty."
        )

    input_path = Path(
        image_path
    )

    if not input_path.is_file():
        raise FileNotFoundError(
            f"Input image not found: {input_path}"
        )

    output_file = Path(
        output_path
    )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # 1. Read SSS image
    # --------------------------------------------------------

    image = cv2.imread(
        str(input_path),
        cv2.IMREAD_GRAYSCALE,
    )

    if image is None:
        raise ValueError(
            f"Could not read SSS image: {input_path}"
        )

    original_height, original_width = (
        image.shape[:2]
    )

    # --------------------------------------------------------
    # 2. Speckle / noise reduction
    # --------------------------------------------------------
    #
    # Gaussian blur is retained as a lightweight baseline
    # filter for the prototype.
    #
    # Later, this can be replaced with a more sonar-specific
    # filter such as Lee/SRAD without changing the pipeline API.
    # --------------------------------------------------------

    filtered = cv2.GaussianBlur(
        image,
        (5, 5),
        0,
    )

    # --------------------------------------------------------
    # 3. CLAHE
    # --------------------------------------------------------

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    enhanced = clahe.apply(
        filtered
    )

    # --------------------------------------------------------
    # 4. Intensity normalization
    # --------------------------------------------------------
    #
    # Normalize using percentile clipping to reduce the effect
    # of extreme sonar intensity values.
    #
    # The result remains uint8 [0,255].
    # --------------------------------------------------------

    enhanced_float = (
        enhanced.astype(
            np.float32
        )
    )

    low = np.percentile(
        enhanced_float,
        2,
    )

    high = np.percentile(
        enhanced_float,
        98,
    )

    if high > low:

        normalized = (
            enhanced_float - low
        ) / (
            high - low
        )

        normalized = (
            normalized * 255.0
        )

    else:

        normalized = enhanced_float

    normalized = np.clip(
        normalized,
        0,
        255,
    ).astype(
        np.uint8
    )

    # --------------------------------------------------------
    # 5. Safety check:
    # output dimensions must equal input dimensions
    # --------------------------------------------------------

    if normalized.shape != (
        original_height,
        original_width,
    ):
        raise RuntimeError(
            "Preprocessing unexpectedly changed "
            "the image dimensions. "
            f"Input={image.shape}, "
            f"Output={normalized.shape}"
        )

    # --------------------------------------------------------
    # 6. Save
    # --------------------------------------------------------

    success = cv2.imwrite(
        str(output_file),
        normalized,
    )

    if not success:
        raise RuntimeError(
            f"Failed to save preprocessed image: "
            f"{output_file}"
        )

    return str(
        output_file
    )


def get_preprocessing_info(
    image_path: str,
) -> Dict[str, Any]:
    """
    Return metadata describing the preprocessing behaviour.

    This is useful for logging/debugging and later for keeping
    track of coordinate transformations.

    Since the current preprocessing does not resize/crop/pad,
    the spatial transform is identity.
    """

    image = cv2.imread(
        str(image_path),
        cv2.IMREAD_GRAYSCALE,
    )

    if image is None:
        raise ValueError(
            f"Could not read image: {image_path}"
        )

    height, width = (
        image.shape[:2]
    )

    return {
        "input_width": width,
        "input_height": height,

        "output_width": width,
        "output_height": height,

        "resized": False,
        "cropped": False,
        "padded": False,

        # Identity mapping:
        #
        # model_x = original_x
        # model_y = original_y
        #
        "scale_x": 1.0,
        "scale_y": 1.0,

        "offset_x": 0.0,
        "offset_y": 0.0,
    }