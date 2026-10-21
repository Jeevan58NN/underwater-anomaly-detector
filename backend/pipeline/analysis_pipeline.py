from __future__ import annotations
from segmentation.unet import UNetSegmentation
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

from schemas import (
    AnalysisResult,
    Detection,
    BoundingBox,
    SeafloorAssessment,
)

from detectors.mock_detector import MockDetector

from segmentation.swnet import (
    SWNetSegmentation,
)

from verification import (
    verify_detection,
)

from geotagging import (
    geotag_detection,
)

from ingestion.input_router import (
    route_input,
)

from ingestion.tiling import (
    generate_tiles,
)

from preprocessing import (
    preprocess_sss_image,
)


# ============================================================
# MODEL CACHE
# ============================================================

mock_detector = MockDetector()





UNET_MODEL_PATH = os.getenv(
    "UNET_MODEL_PATH",
    "weights/unet_best.pth",
).strip()

UNET_THRESHOLD = float(
    os.getenv(
        "UNET_THRESHOLD",
        "0.5",
    )
)

try:
    unet_segmentation = UNetSegmentation(
        checkpoint_path=UNET_MODEL_PATH,
        threshold=UNET_THRESHOLD,
    )

except Exception as exc:
    print(
        "[WARNING] U-Net unavailable:",
        exc,
    )
    unet_segmentation = None










# ============================================================
# SW-NET CONFIGURATION
# ============================================================

swnet_path = os.getenv(
    "SWNET_MODEL_PATH",
    "",
).strip()

try:
    swnet_segmentation = SWNetSegmentation(
        swnet_path
    )
except Exception:
    swnet_segmentation = None


# ============================================================
# TILE CONFIGURATION
# ============================================================

TILE_SIZE = int(
    os.getenv(
        "TILE_SIZE",
        "512",
    )
)

TILE_OVERLAP = int(
    os.getenv(
        "TILE_OVERLAP",
        "64",
    )
)

MAX_TILES = int(
    os.getenv(
        "MAX_TILES_PER_ANALYSIS",
        "20",
    )
)


# ============================================================
# HELPERS
# ============================================================

def _now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def confidence_band(
    confidence: float,
) -> str:

    pct = float(confidence) * 100.0

    if pct >= 90:
        return "High"

    if pct >= 70:
        return "Medium"

    return "Low"


def severity_for(
    confidence: float,
    class_name: str,
) -> str:

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


def _get_value(
    obj: Any,
    key: str,
    default: Any = None,
) -> Any:
    """
    Safely retrieve a value from either
    a dictionary or an object.
    """

    if isinstance(obj, dict):
        return obj.get(
            key,
            default,
        )

    return getattr(
        obj,
        key,
        default,
    )


def _bbox_to_xyxy(
    bbox: Any,
) -> Optional[
    Tuple[
        float,
        float,
        float,
        float,
    ]
]:
    """
    Convert supported bounding-box formats
    into x1, y1, x2, y2.
    """

    if bbox is None:
        return None

    # --------------------------------------------------------
    # Dictionary: x/y/width/height
    # --------------------------------------------------------

    if isinstance(
        bbox,
        dict,
    ):

        if all(
            key in bbox
            for key in (
                "x",
                "y",
                "width",
                "height",
            )
        ):

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

            return (
                x,
                y,
                x + width,
                y + height,
            )

        # ----------------------------------------------------
        # Dictionary: x1/y1/x2/y2
        # ----------------------------------------------------

        if all(
            key in bbox
            for key in (
                "x1",
                "y1",
                "x2",
                "y2",
            )
        ):

            return (
                float(
                    bbox["x1"]
                ),
                float(
                    bbox["y1"]
                ),
                float(
                    bbox["x2"]
                ),
                float(
                    bbox["y2"]
                ),
            )

    # --------------------------------------------------------
    # List / tuple
    # --------------------------------------------------------

    if isinstance(
        bbox,
        (
            list,
            tuple,
        ),
    ):

        if len(bbox) == 4:

            return tuple(
                float(value)
                for value in bbox
            )

    return None


def _raw_detection_bbox(
    detection: Any,
) -> Optional[
    Tuple[
        float,
        float,
        float,
        float,
    ]
]:
    return _bbox_to_xyxy(
        _get_value(
            detection,
            "bbox",
        )
    )


def _create_detection_id() -> str:
    return (
        "DET-"
        + str(
            uuid.uuid4()
        )[:6].upper()
    )


def _get_image_size(
    image_path: str,
) -> Tuple[int, int]:

    try:

        with Image.open(
            image_path
        ) as image:

            return (
                image.width,
                image.height,
            )

    except Exception:

        return (
            1280,
            720,
        )


# ============================================================
# PREVIEW URL BUILDER
# ============================================================

def _build_preview_url(
    survey: Any,
    file_path: str,
    extract_dir: str,
) -> Optional[str]:
    """
    Build a browser-accessible URL for the image/preview.

    Priority:

    1. Generated preview inside the analysis directory
       -> /previews/...

    2. Preview inside uploads directory
       -> /uploads/...

    3. Normal uploaded JPG/PNG/etc.
       -> /uploads/<filename>

    Returns None only when no valid path is available.
    """

    preview_path = getattr(
        survey,
        "preview_image_path",
        None,
    )

    extract_root = Path(
        extract_dir
    ).resolve()

    upload_root = Path(
        "uploads"
    ).resolve()

    # --------------------------------------------------------
    # Case 1: explicit generated preview
    # --------------------------------------------------------

    if preview_path:

        preview_path_obj = Path(
            preview_path
        ).resolve()

        # Preview lives inside this analysis folder.
        try:

            relative_path = (
                preview_path_obj
                .relative_to(
                    extract_root
                )
            )

            return (
                "/previews/"
                + relative_path.as_posix()
            )

        except ValueError:
            pass

        # ----------------------------------------------------
        # Preview lives somewhere inside uploads.
        # ----------------------------------------------------

        try:

            relative_path = (
                preview_path_obj
                .relative_to(
                    upload_root
                )
            )

            return (
                "/uploads/"
                + relative_path.as_posix()
            )

        except ValueError:
            pass

    # --------------------------------------------------------
    # Case 2: normal uploaded image
    # --------------------------------------------------------

    file_path_obj = Path(
        file_path
    )

    filename = file_path_obj.name

    if filename:

        return (
            "/uploads/"
            + filename
        )

    return None


# ============================================================
# PREPARE INPUTS
# ============================================================

def _prepare_inputs(
    survey: Any,
    extract_dir: str,
) -> List[
    Dict[str, Any]
]:
    """
    Convert survey data into model inputs.

    GeoTIFF:
        Raster -> overlapping tiles.

    Standard image:
        One image -> one model input.

    XTF/JSF:
        Extracted sonar image -> model input.
    """

    input_type = (
        str(
            getattr(
                survey,
                "input_type",
                "",
            )
            or ""
        )
        .upper()
    )

    # --------------------------------------------------------
    # GeoTIFF
    # --------------------------------------------------------

    if input_type == "GEOTIFF":

        original_file = getattr(
            survey,
            "original_file",
            None,
        )

        if not original_file:

            raise ValueError(
                "Original GeoTIFF path is unavailable."
            )

        tile_dir = os.path.join(
            extract_dir,
            "tiles",
        )

        tiles = generate_tiles(
            file_path=original_file,
            output_dir=tile_dir,
            tile_size=TILE_SIZE,
            overlap=TILE_OVERLAP,
        )

        if MAX_TILES > 0:

            tiles = tiles[
                :MAX_TILES
            ]

        return [
            {
                "image_path": tile.image_path,
                "tile": tile,
            }
            for tile in tiles
        ]

    # --------------------------------------------------------
    # Standard image / XTF-generated image
    # --------------------------------------------------------

    image_path = getattr(
        survey,
        "image_path",
        None,
    )

    if not image_path:

        raise ValueError(
            "No image is available for model inference."
        )

    return [
        {
            "image_path": image_path,
            "tile": None,
        }
    ]


# ============================================================
# PREPROCESSING
# ============================================================

def _prepare_model_image(
    image_path: str,
    output_dir: str,
    index: int,
    mode: str,
) -> str:
    """
    Prepare an image for model inference.
    """

    if mode == "simulation":
        return image_path

    os.makedirs(
        output_dir,
        exist_ok=True,
    )

    output_path = os.path.join(
        output_dir,
        f"processed_{index:05d}.png",
    )

    try:

        return preprocess_sss_image(
            image_path,
            output_path,
        )

    except Exception as exc:

        print(
            "[WARNING] Preprocessing failed "
            f"for {image_path}: {exc}"
        )

        # Use original image as fallback.
        return image_path


# ============================================================
# IOU
# ============================================================

def _calculate_iou(
    box_a,
    box_b,
) -> float:

    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    ix1 = max(
        ax1,
        bx1,
    )

    iy1 = max(
        ay1,
        by1,
    )

    ix2 = min(
        ax2,
        bx2,
    )

    iy2 = min(
        ay2,
        by2,
    )

    intersection_width = max(
        0.0,
        ix2 - ix1,
    )

    intersection_height = max(
        0.0,
        iy2 - iy1,
    )

    intersection_area = (
        intersection_width
        * intersection_height
    )

    area_a = (
        max(
            0.0,
            ax2 - ax1,
        )
        * max(
            0.0,
            ay2 - ay1,
        )
    )

    area_b = (
        max(
            0.0,
            bx2 - bx1,
        )
        * max(
            0.0,
            by2 - by1,
        )
    )

    union = (
        area_a
        + area_b
        - intersection_area
    )

    if union <= 0:
        return 0.0

    return (
        intersection_area
        / union
    )


# ============================================================
# DUPLICATE MERGING
# ============================================================

def _merge_duplicate_detections(
    detections: List[
        Dict[str, Any]
    ],
    iou_threshold: float = 0.5,
) -> List[
    Dict[str, Any]
]:
    """
    Remove duplicate detections caused by
    overlapping GeoTIFF tiles.
    """

    if not detections:
        return []

    ordered = sorted(
        detections,
        key=lambda item: float(
            item.get(
                "confidence",
                0.0,
            )
        ),
        reverse=True,
    )

    kept = []

    for candidate in ordered:

        candidate_box = (
            candidate.get(
                "original_bbox"
            )
        )

        if candidate_box is None:

            kept.append(
                candidate
            )

            continue

        is_duplicate = False

        for existing in kept:

            existing_box = (
                existing.get(
                    "original_bbox"
                )
            )

            if existing_box is None:
                continue

            if (
                candidate.get(
                    "class_name"
                )
                != existing.get(
                    "class_name"
                )
            ):
                continue

            if (
                _calculate_iou(
                    candidate_box,
                    existing_box,
                )
                >= iou_threshold
            ):

                is_duplicate = True
                break

        if not is_duplicate:

            kept.append(
                candidate
            )

    return kept


# ============================================================
# MAIN ANALYSIS PIPELINE
# ============================================================

def run_analysis(
    file_path: str,
    ext: str,
    analysis_id: str,
    mode: str,
    extract_dir: str,
    detector: Any,
) -> AnalysisResult:
    """
    Main AquaScan analysis pipeline.

    Flow:

        Input
          ↓
        Ingestion
          ↓
        Tiles/images
          ↓
        Preprocessing
          ↓
        Detector
          ↓
        Verification
          ↓
        Segmentation
          ↓
        Geotagging
          ↓
        Duplicate merging
          ↓
        Final result

    detector is supplied by main.py.

    Simulation:
        MockDetector

    Real:
        YOLODetector

    Future:
        DualStreamDetector
    """

    mode = (
        mode
        or "simulation"
    ).strip().lower()

    if mode not in {
        "simulation",
        "real",
    }:

        raise ValueError(
            "Mode must be 'simulation' or 'real'."
        )

    if detector is None:

        raise RuntimeError(
            "No detector was supplied to the analysis pipeline."
        )

    # ========================================================
    # 1. INGESTION
    # ========================================================

    survey = route_input(
        file_path,
        ext,
        extract_dir,
    )

    # ========================================================
    # 2. INPUT PREPARATION
    # ========================================================

    model_inputs = _prepare_inputs(
        survey,
        extract_dir,
    )

    if not model_inputs:

        raise RuntimeError(
            "No model inputs were generated."
        )

    # ========================================================
    # 3. PROCESS INPUTS
    # ========================================================

    intermediate_results = []

    processed_dir = os.path.join(
        extract_dir,
        "processed",
    )

    os.makedirs(
        processed_dir,
        exist_ok=True,
    )

    for input_index, item in enumerate(
        model_inputs
    ):

        image_path = item[
            "image_path"
        ]

        tile = item[
            "tile"
        ]

        # ----------------------------------------------------
        # Image dimensions
        # ----------------------------------------------------

        image_width, image_height = (
            _get_image_size(
                image_path
            )
        )

        # ----------------------------------------------------
        # Preprocessing
        # ----------------------------------------------------

        eval_path = _prepare_model_image(
            image_path=image_path,
            output_dir=processed_dir,
            index=input_index,
            mode=mode,
        )

        eval_width, eval_height = (
            _get_image_size(
                eval_path
            )
        )

        # ----------------------------------------------------
        # Detection
        # ----------------------------------------------------

        raw_detections = detector.predict(
            eval_path,
            eval_width,
            eval_height,
        )

        # ----------------------------------------------------
        # Process detections
        # ----------------------------------------------------

        for detection_index, raw in enumerate(
            raw_detections
        ):

            bbox = _raw_detection_bbox(
                raw
            )

            if bbox is None:

                print(
                    "[WARNING] Detector returned "
                    "an invalid bounding box."
                )

                continue

            x1, y1, x2, y2 = bbox

            # ------------------------------------------------
            # Tile coordinates
            # ------------------------------------------------

            tile_bbox = (
                x1,
                y1,
                x2,
                y2,
            )

            # ------------------------------------------------
            # Original raster coordinates
            # ------------------------------------------------

            if tile is not None:

                original_bbox = (
                    tile.offset_x + x1,
                    tile.offset_y + y1,
                    tile.offset_x + x2,
                    tile.offset_y + y2,
                )

                tile_offset_x = float(
                    tile.offset_x
                )

                tile_offset_y = float(
                    tile.offset_y
                )

                tile_id = (
                    tile.tile_id
                )

            else:

                original_bbox = (
                    tile_bbox
                )

                tile_offset_x = 0.0
                tile_offset_y = 0.0
                tile_id = None

            # ------------------------------------------------
            # Geotagging proxy
            # ------------------------------------------------

            detection_proxy = {
                "bbox": {
                    "x1": tile_bbox[0],
                    "y1": tile_bbox[1],
                    "x2": tile_bbox[2],
                    "y2": tile_bbox[3],
                }
            }

            # ------------------------------------------------
            # Geotagging
            # ------------------------------------------------

            try:

                location = geotag_detection(
                    detection=detection_proxy,
                    survey=survey,
                    tile=tile,
                    processing_mode=mode,
                    analysis_id=analysis_id,
                    detection_index=detection_index,
                )

            except Exception as exc:

                print(
                    "[WARNING] Geotagging failed: "
                    f"{exc}"
                )

                location = {
                    "location_status": "unavailable",
                    "latitude": None,
                    "longitude": None,
                    "location_source": None,
                    "reason": str(exc),
                }

            # ------------------------------------------------
            # Class and confidence
            # ------------------------------------------------

            class_id = _get_value(
                raw,
                "class_id",
                None,
            )

            class_name = str(
                _get_value(
                    raw,
                    "class_name",
                    "Unknown",
                )
            )

            if class_id is None:
                from verification.classifier import CLASS_NAMES
                reverse_mapping = {v.lower(): k for k, v in CLASS_NAMES.items()}
                class_id = reverse_mapping.get(class_name.lower(), None)

            confidence = float(
                _get_value(
                    raw,
                    "confidence",
                    0.0,
                )
            )

            # ------------------------------------------------
            # Verification
            # ------------------------------------------------

            seed_value = (
                int(
                    confidence
                    * 1000
                )
                + detection_index
                + input_index
            )

            verification = verify_detection(
                class_name,
                {
                    "x": x1,
                    "y": y1,
                    "width": x2 - x1,
                    "height": y2 - y1,
                },
                mode,
                seed_value,
            )

            # ------------------------------------------------
            # Segmentation
            # ------------------------------------------------
            unet_result = None

            if (
    mode == "real"
    and unet_segmentation is not None
):
                try:
                    unet_result = (
            unet_segmentation.segment(
                image_path=eval_path,
                output_dir=processed_dir,
            )
        )
                except Exception as exc:
                    print(
            "[WARNING] U-Net segmentation failed:",
            exc,
        )
                    unet_result = None




            








            segmentation = None

            

            if (
                mode == "real"
                and swnet_segmentation
                and getattr(
                    swnet_segmentation,
                    "model_loaded",
                    False,
                )
            ):

                try:

                    segmentation = (
                        swnet_segmentation.segment(
                            eval_path,
                            {
                                "x": x1,
                                "y": y1,
                                "width": (
                                    x2 - x1
                                ),
                                "height": (
                                    y2 - y1
                                ),
                            },
                        )
                    )

                except Exception as exc:

                    print(
                        "[WARNING] SW-Net failed: "
                        f"{exc}"
                    )

            # ------------------------------------------------
            # Classification, scoring, and priority
            # ------------------------------------------------

            from verification.classifier import get_classification_type, get_priority
            from confidence.scoring import calculate_system_score

            classification_type = get_classification_type(class_name)
            priority = get_priority(class_name, confidence)

            has_seg = segmentation is not None and isinstance(segmentation, dict) and segmentation.get("available", False)
            system_score = calculate_system_score(
                model_confidence=confidence,
                class_name=class_name,
                has_segmentation=has_seg,
                has_shadow=False
            )

            # ------------------------------------------------
            # Location
            # ------------------------------------------------

            location_status = location.get(
                "location_status",
                "unavailable",
            )

            latitude = location.get(
                "latitude"
            )

            longitude = location.get(
                "longitude"
            )

            location_source = location.get(
                "location_source"
            )

            location_reason = location.get(
                "reason"
            )

            # ------------------------------------------------
            # Intermediate record
            # ------------------------------------------------

            intermediate_results.append(
                {
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": confidence,
                    "tile_bbox": tile_bbox,
                    "original_bbox": original_bbox,
                    "tile_id": tile_id,
                    "tile_offset_x": tile_offset_x,
                    "tile_offset_y": tile_offset_y,
                    "location": location,
                    "location_status": location_status,
                    "latitude": latitude,
                    "longitude": longitude,
                    "location_source": location_source,
                    "location_reason": location_reason,
                    "verification": verification,
                    "segmentation": segmentation,
                    "system_score": system_score,
                    "classification_type": classification_type,
                    "priority": priority,
                }
            )

    # ========================================================
    # 4. MERGE TILE DUPLICATES
    # ========================================================

    merged_results = (
        _merge_duplicate_detections(
            intermediate_results
        )
    )

    # ========================================================
    # 5. BUILD API DETECTIONS
    # ========================================================

    detections: List[
        Detection
    ] = []

    for item in merged_results:

        class_id = item.get("class_id")

        class_name = item[
            "class_name"
        ]

        confidence = item[
            "confidence"
        ]

        tile_bbox = item[
            "tile_bbox"
        ]

        original_bbox = item[
            "original_bbox"
        ]

        location = item[
            "location"
        ]

        verification = item[
            "verification"
        ]

        segmentation = item[
            "segmentation"
        ]

        system_score = item.get("system_score")

        classification_type = item.get("classification_type")

        priority = item.get("priority")

        tx1, ty1, tx2, ty2 = (
            tile_bbox
        )

        location_status = item.get(
            "location_status",
            "unavailable",
        )

        latitude = item.get(
            "latitude"
        )

        longitude = item.get(
            "longitude"
        )

        location_source = item.get(
            "location_source"
        )

        location_reason = item.get(
            "location_reason"
        )

        artificial_pct = float(
            verification.get(
                "artificial_pct",
                0.0,
            )
        )

        verification_score = (
            artificial_pct / 100.0
        )

        detection = Detection(
            id=_create_detection_id(),

            class_id=class_id,

            class_name=class_name,

            confidence=confidence,

            confidence_band=confidence_band(
                confidence
            ),

            model_confidence=confidence,

            verification_score=(
                verification_score
            ),

            system_score=system_score,

            final_confidence=confidence,

            classification_type=classification_type,

            priority=priority,

            bbox=BoundingBox(
                x=float(tx1),
                y=float(ty1),
                width=float(
                    tx2 - tx1
                ),
                height=float(
                    ty2 - ty1
                ),
            ),

            latitude=latitude,

            longitude=longitude,

            severity=priority,

            seafloor_assessment=(
                SeafloorAssessment(
                    **verification
                )
            ),

            segmentation=segmentation,

            location_status=(
                location_status
            ),

            location_source=(
                location_source
            ),

            location_reason=(
                location_reason
            ),

            ping_id=(
                survey.ping_metadata[0].get(
                    "ping_id"
                )
                if getattr(
                    survey,
                    "ping_metadata",
                    None,
                )
                else None
            ),

            timestamp=(
                survey.ping_metadata[0].get(
                    "timestamp"
                )
                if getattr(
                    survey,
                    "ping_metadata",
                    None,
                )
                else None
            ),

            tile_id=item.get(
                "tile_id"
            ),

            tile_offset_x=item.get(
                "tile_offset_x"
            ),

            tile_offset_y=item.get(
                "tile_offset_y"
            ),

            original_bbox=[
                float(value)
                for value in original_bbox
            ],

            is_simulated_location=(
                location_status
                == "simulated" or location_status == "estimated"
            ),

            input_type=survey.input_type,

            analysis_id=analysis_id,
        )

        detections.append(
            detection
        )

    # ========================================================
    # 6. PREVIEW URL
    # ========================================================

    preview_url = _build_preview_url(
        survey=survey,
        file_path=file_path,
        extract_dir=extract_dir,
    )

    print(
        "[AquaScan] Preview URL:",
        preview_url,
    )

    # ========================================================
    # 7. LOCATION CAPABILITY
    # ========================================================

    has_georeferencing = (
        getattr(
            survey,
            "has_georeferencing",
            lambda: False,
        )()
    )

    has_navigation = (
        getattr(
            survey,
            "has_navigation",
            lambda: False,
        )()
    )

    geotagging_available = (
        has_georeferencing
        or has_navigation
        or mode == "simulation"
    )

    navigation_available = bool(
        getattr(
            survey,
            "navigation_available",
            False,
        )
    )

    # ========================================================
    # 8. FINAL LOCATION SOURCE
    # ========================================================

    if has_georeferencing:

        final_location_source = (
            "GeoTIFF"
        )

    elif has_navigation:

        final_location_source = (
            "XTF Navigation"
        )

    elif mode == "simulation":

        final_location_source = (
            "Simulation"
        )

    else:

        final_location_source = None

    # ========================================================
    # 9. FINAL RESULT
    # ========================================================

    result = AnalysisResult(

        analysis_id=analysis_id,

        status="completed",

        processing_mode=mode,

        input_type=survey.input_type,

        file_format=survey.file_format,

        filename=os.path.basename(
            file_path
        ),

        image_width=(
            getattr(
                survey,
                "raster_width",
                None,
            )
            or _get_image_size(
                survey.image_path
            )[0]
        ),

        image_height=(
            getattr(
                survey,
                "raster_height",
                None,
            )
            or _get_image_size(
                survey.image_path
            )[1]
        ),

        preview_image_url=preview_url,

        detections=detections,

        navigation_available=(
            navigation_available
        ),

        georeferencing_available=(
            has_georeferencing
        ),

        geotagging_available=(
            geotagging_available
        ),

        location_source=(
            final_location_source
        ),

        processing_time=None,

        tile_count=(
            len(model_inputs)
            if (
                str(
                    survey.input_type
                ).upper()
                == "GEOTIFF"
            )
            else 1
        ),

        created_at=_now_iso(),

        note=(
            f"Processed in {mode} mode."
        ),
    )

    return result