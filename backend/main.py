from __future__ import annotations

from segmentation.unet import UNetSegmentation

import os
import time
import uuid

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from detectors.mock_detector import MockDetector
from detectors.yolo_detector import YOLODetector

from schemas import (
    AnalysisResult,
    Detection,
    HealthResponse,
    SystemStatusResponse,
)

from pipeline.analysis_pipeline import run_analysis


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

APP_VERSION = "1.1.0"

UPLOAD_DIR = Path(
    os.getenv(
        "UPLOAD_DIR",
        "uploads",
    )
)

EXTRACT_DIR = (
    UPLOAD_DIR / "extracted"
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

EXTRACT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# PROCESSING MODE
# ============================================================

PROCESSING_MODE = (
    os.getenv(
        "PROCESSING_MODE",
        "real",
    )
    .strip()
    .lower()
)

if PROCESSING_MODE not in {
    "simulation",
    "real",
}:
    PROCESSING_MODE = "real"


# ============================================================
# MODEL CONFIGURATION
# ============================================================

YOLO11_MODEL_PATH = (
    os.getenv(
        "YOLO11_MODEL_PATH",
        "weights/best.pt",
    )
    .strip()
)

YOLO11_CONFIDENCE = float(
    os.getenv(
        "YOLO11_CONFIDENCE_THRESHOLD",
        "0.25",
    )
)

YOLO11_IMAGE_SIZE = int(
    os.getenv(
        "YOLO11_IMAGE_SIZE",
        "640",
    )
)

SWNET_MODEL_PATH = (
    os.getenv(
        "SWNET_MODEL_PATH",
        "",
    )
    .strip()
)


# ============================================================
# U-NET SEGMENTATION CONFIGURATION
# ============================================================

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

unet_segmentation: Optional[
    UNetSegmentation
] = None

try:
    unet_segmentation = UNetSegmentation(
        checkpoint_path=UNET_MODEL_PATH,
        threshold=UNET_THRESHOLD,
    )

    print(
        "[AquaScan] U-Net model loaded successfully: "
        f"{UNET_MODEL_PATH}"
    )

except Exception as exc:
    print(
        "[AquaScan] WARNING: U-Net could not be loaded: "
        f"{exc}"
    )

    unet_segmentation = None


# ============================================================
# UPLOAD CONFIGURATION
# ============================================================

ALLOWED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".xtf",
    ".jsf",
}

MAX_FILE_SIZE_BYTES = int(
    os.getenv(
        "MAX_UPLOAD_SIZE",
        str(500 * 1024 * 1024),
    )
)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="AquaScan AI Backend",
    version=APP_VERSION,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STATIC FILES
# ============================================================

app.mount(
    "/previews",
    StaticFiles(
        directory=str(EXTRACT_DIR),
    ),
    name="previews",
)

app.mount(
    "/uploads",
    StaticFiles(
        directory=str(UPLOAD_DIR),
    ),
    name="uploads",
)


# ============================================================
# RESULT STORES
# ============================================================

DETECTIONS_STORE: Dict[
    str,
    Detection,
] = {}

ANALYSES_STORE: Dict[
    str,
    AnalysisResult,
] = {}


# ============================================================
# MODEL INITIALIZATION
# ============================================================

mock_detector = MockDetector()

yolo_detector: Optional[
    YOLODetector
] = None

try:
    yolo_detector = YOLODetector(
        model_path=YOLO11_MODEL_PATH,
        confidence_threshold=YOLO11_CONFIDENCE,
        image_size=YOLO11_IMAGE_SIZE,
    )

    print(
        "[AquaScan] YOLO11 model loaded successfully:"
        f" {YOLO11_MODEL_PATH}"
    )

except Exception as exc:
    print(
        "[AquaScan] WARNING: YOLO11 model could not be loaded:"
        f" {exc}"
    )

    yolo_detector = None


# ============================================================
# HELPERS
# ============================================================

def _now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def _validate_mode(
    mode: Optional[str],
) -> str:
    """
    Resolve request processing mode.

    If no mode is provided, use PROCESSING_MODE.
    """

    actual_mode = (
        mode
        if mode is not None
        else PROCESSING_MODE
    )

    actual_mode = (
        actual_mode
        .strip()
        .lower()
    )

    if actual_mode not in {
        "simulation",
        "real",
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid mode. Use "
                "'simulation' or 'real'."
            ),
        )

    return actual_mode


def _validate_extension(
    filename: str,
) -> str:
    """
    Validate and return a normalized extension.
    """

    ext = Path(
        filename
    ).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{ext}'. "
                "Allowed formats: "
                "PNG, JPG, JPEG, TIFF, "
                "XTF, JSF."
            ),
        )

    return ext


def _real_mode_configuration_error() -> Optional[str]:
    """
    Validate the current Real Mode.

    Current working detection model:
        YOLO11

    U-Net is handled independently by the
    segmentation endpoint/module.
    """

    if (
        yolo_detector is None
        or not Path(
            YOLO11_MODEL_PATH
        ).is_file()
    ):

        return (
            "Real AI model is not configured."
        )

    return None


async def _save_upload(
    upload: UploadFile,
    destination: Path,
) -> None:
    """
    Save upload in 1 MB chunks so large sonar files
    don't get loaded completely into RAM.
    """

    total_bytes = 0

    try:

        with destination.open(
            "wb"
        ) as output:

            while True:

                chunk = await upload.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                total_bytes += len(
                    chunk
                )

                if (
                    total_bytes
                    > MAX_FILE_SIZE_BYTES
                ):
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "File too large. "
                            f"Maximum allowed size is "
                            f"{MAX_FILE_SIZE_BYTES} bytes."
                        ),
                    )

                output.write(
                    chunk
                )

    finally:

        await upload.close()

    if total_bytes == 0:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )


def _get_active_detector(
    mode: str,
):
    """
    Return the detector appropriate for the request mode.
    """

    if mode == "simulation":
        return mock_detector

    if (
        yolo_detector is None
        or not Path(
            YOLO11_MODEL_PATH
        ).is_file()
    ):
        raise HTTPException(
            status_code=503,
            detail=(
                "Real AI model is not configured."
            ),
        )

    return yolo_detector


# ============================================================
# HEALTH
# ============================================================

@app.get(
    "/api/health",
    response_model=HealthResponse,
)
def health():

    if yolo_detector is not None:

        detector_name = "YOLO11"

    else:

        detector_name = (
            "YOLO11 - Not Configured"
        )

    return HealthResponse(
        status="online",
        mode=PROCESSING_MODE,
        detector=detector_name,
        version=APP_VERSION,
    )


# ============================================================
# SYSTEM STATUS
# ============================================================

@app.get(
    "/api/system-status",
    response_model=SystemStatusResponse,
)
def system_status():

    if yolo_detector is not None:

        detection_engine = "YOLO11"
        model_status = "Loaded"

    else:

        detection_engine = (
            "Not configured"
        )

        model_status = "Not loaded"

    # --------------------------------------------------------
    # U-NET STATUS
    # --------------------------------------------------------

    if (
        unet_segmentation is not None
        and getattr(
            unet_segmentation,
            "model_loaded",
            False,
        )
    ):

        segmentation_engine = (
            "U-Net"
        )

    elif SWNET_MODEL_PATH:

        segmentation_engine = (
            "SW-Net"
        )

    else:

        segmentation_engine = (
            "Not configured"
        )

    geolocation = (
        "Metadata + estimated fallback"
    )

    return SystemStatusResponse(
        backend_api="Online",

        detection_engine=(
            detection_engine
        ),

        model_status=(
            model_status
        ),

        classes=4,

        segmentation_engine=(
            segmentation_engine
        ),

        geolocation=(
            geolocation
        ),

        database="Local Storage",

        map_service="Online",

        processing_mode=(
            PROCESSING_MODE
        ),
    )


# ============================================================
# ANALYZE
# ============================================================

@app.post(
    "/api/analyze",
    response_model=AnalysisResult,
)
async def analyze(
    image: UploadFile = File(...),
    mode: Optional[str] = Form(None),
):
    """
    Main analysis endpoint.

    Supported inputs:

        PNG/JPG/JPEG
            -> standard image
            -> AI detection

        TIFF/GeoTIFF
            -> GeoTIFF ingestion
            -> tiles
            -> AI detection
            -> geotagging if georeferencing exists

        XTF
            -> sonar parser
            -> SSS extraction
            -> navigation extraction
            -> AI detection
            -> geotagging when sufficient navigation exists

        JSF
            -> parser adapter
    """

    start_time = time.time()

    # --------------------------------------------------------
    # Validate filename
    # --------------------------------------------------------

    if not image.filename:

        raise HTTPException(
            status_code=400,
            detail="No file selected.",
        )

    # --------------------------------------------------------
    # Resolve mode
    # --------------------------------------------------------

    actual_mode = _validate_mode(
        mode
    )

    # --------------------------------------------------------
    # Validate extension
    # --------------------------------------------------------

    ext = _validate_extension(
        image.filename
    )

    # --------------------------------------------------------
    # Validate Real Mode
    # --------------------------------------------------------

    if actual_mode == "real":

        configuration_error = (
            _real_mode_configuration_error()
        )

        if configuration_error:

            raise HTTPException(
                status_code=503,
                detail=configuration_error,
            )

    # --------------------------------------------------------
    # Select detector
    # --------------------------------------------------------

    detector = _get_active_detector(
        actual_mode
    )

    # --------------------------------------------------------
    # Create analysis ID
    # --------------------------------------------------------

    analysis_id = (
        "SCAN-"
        + str(
            uuid.uuid4()
        )[:8]
        .upper()
    )

    # --------------------------------------------------------
    # Save uploaded file
    # --------------------------------------------------------

    saved_name = (
        analysis_id + ext
    )

    saved_path = (
        UPLOAD_DIR / saved_name
    )

    await _save_upload(
        image,
        saved_path,
    )

    # --------------------------------------------------------
    # Extraction directory
    # --------------------------------------------------------

    analysis_extract_dir = (
        EXTRACT_DIR
        / analysis_id
    )

    analysis_extract_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # RUN PIPELINE
    # --------------------------------------------------------

    try:

        result = run_analysis(
            file_path=str(
                saved_path
            ),

            ext=ext,

            analysis_id=analysis_id,

            mode=actual_mode,

            extract_dir=str(
                analysis_extract_dir
            ),

            detector=detector,
        )

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except NotImplementedError as exc:

        raise HTTPException(
            status_code=501,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:

        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except HTTPException:

        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Analysis failed: "
                f"{exc}"
            ),
        ) from exc

    # --------------------------------------------------------
    # Server metadata
    # --------------------------------------------------------

    result.processing_time = (
        time.time()
        - start_time
    )

    result.filename = (
        image.filename
    )

    # --------------------------------------------------------
    # Store results
    # --------------------------------------------------------

    ANALYSES_STORE[
        analysis_id
    ] = result

    for detection in (
        result.detections
    ):

        DETECTIONS_STORE[
            detection.id
        ] = detection

    return result


# ============================================================
# DETECTIONS
# ============================================================

@app.get(
    "/api/detections",
    response_model=List[Detection],
)
def get_detections():

    return list(
        DETECTIONS_STORE.values()
    )


@app.get(
    "/api/detections/{detection_id}",
    response_model=Detection,
)
def get_detection(
    detection_id: str,
):

    detection = (
        DETECTIONS_STORE.get(
            detection_id
        )
    )

    if detection is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Detection "
                f"'{detection_id}' "
                "not found."
            ),
        )

    return detection


# ============================================================
# REPORTS
# ============================================================

from report_generator import (
    build_csv,
    build_json,
)


@app.get(
    "/api/reports/csv"
)
def get_csv_report():

    csv_data = build_csv(
        list(
            DETECTIONS_STORE.values()
        )
    )

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition":
                "attachment; "
                "filename=aquascan_report.csv"
        },
    )


@app.get(
    "/api/reports/json"
)
def get_json_report():

    json_data = build_json(
        list(
            DETECTIONS_STORE.values()
        )
    )

    return Response(
        content=json_data,
        media_type="application/json",
        headers={
            "Content-Disposition":
                "attachment; "
                "filename=aquascan_report.json"
        },
    )


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "message": (
            "AquaScan AI backend running. "
            "See /docs for API."
        )
    }


# ============================================================
# U-NET SEGMENTATION
# ============================================================

@app.post("/api/segment")
async def segment_image(
    image: UploadFile = File(...),
):
    """
    Run the trained U-Net model independently.

    Input:
        JPG / JPEG / PNG / TIFF

    Output:
        segmentation mask
        segmentation overlay
        image dimensions
        segmentation coverage
    """

    # --------------------------------------------------------
    # Check U-Net
    # --------------------------------------------------------

    if (
        unet_segmentation is None
        or not getattr(
            unet_segmentation,
            "model_loaded",
            False,
        )
    ):

        raise HTTPException(
            status_code=503,
            detail=(
                "U-Net segmentation model "
                "is not available. "
                "Check UNET_MODEL_PATH "
                "and unet_best.pth."
            ),
        )

    # --------------------------------------------------------
    # Check uploaded file
    # --------------------------------------------------------

    if not image.filename:

        raise HTTPException(
            status_code=400,
            detail="No file selected.",
        )

    # --------------------------------------------------------
    # Supported segmentation formats
    # --------------------------------------------------------

    allowed_segmentation_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".tif",
        ".tiff",
    }

    ext = Path(
        image.filename
    ).suffix.lower()

    if (
        ext
        not in allowed_segmentation_extensions
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported segmentation input. "
                "Use JPG, JPEG, PNG or TIFF."
            ),
        )

    # --------------------------------------------------------
    # Create segmentation ID
    # --------------------------------------------------------

    segmentation_id = (
        "SEG-"
        + str(
            uuid.uuid4()
        )[:8]
        .upper()
    )

    # --------------------------------------------------------
    # Create segmentation output directory
    # --------------------------------------------------------

    segmentation_dir = (
        EXTRACT_DIR
        / segmentation_id
    )

    segmentation_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Save uploaded image
    # --------------------------------------------------------

    input_path = (
        UPLOAD_DIR
        / f"{segmentation_id}{ext}"
    )

    await _save_upload(
        image,
        input_path,
    )

    # --------------------------------------------------------
    # Run U-Net
    # --------------------------------------------------------

    try:

        result = (
            unet_segmentation.segment(
                image_path=str(
                    input_path
                ),
                output_dir=str(
                    segmentation_dir
                ),
            )
        )

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "U-Net segmentation failed: "
                f"{exc}"
            ),
        ) from exc

    except Exception as exc:

        print(
            "[AquaScan] U-Net segmentation error:",
            exc,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "U-Net segmentation failed."
            ),
        ) from exc

    # --------------------------------------------------------
    # Validate generated files
    # --------------------------------------------------------

    mask_path = Path(
        result["mask_path"]
    ).resolve()

    overlay_path = Path(
        result["overlay_path"]
    ).resolve()

    extract_root = (
        EXTRACT_DIR.resolve()
    )

    if not mask_path.is_file():

        raise HTTPException(
            status_code=500,
            detail=(
                "U-Net completed but "
                "the segmentation mask "
                "was not generated."
            ),
        )

    if not overlay_path.is_file():

        raise HTTPException(
            status_code=500,
            detail=(
                "U-Net completed but "
                "the segmentation overlay "
                "was not generated."
            ),
        )

    # --------------------------------------------------------
    # Convert filesystem paths to
    # browser-accessible URLs
    # --------------------------------------------------------

    try:

        relative_mask = (
            mask_path.relative_to(
                extract_root
            )
        )

        relative_overlay = (
            overlay_path.relative_to(
                extract_root
            )
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Segmentation output path "
                "is outside the configured "
                "preview directory."
            ),
        ) from exc

    # --------------------------------------------------------
    # Return segmentation result
    # --------------------------------------------------------

    return {
        "segmentation_id": (
            segmentation_id
        ),

        "status": "completed",

        "mask_url": (
            "/previews/"
            + relative_mask.as_posix()
        ),

        "overlay_url": (
            "/previews/"
            + relative_overlay.as_posix()
        ),

        "width": int(
            result["width"]
        ),

        "height": int(
            result["height"]
        ),

        "coverage_pct": float(
            result["coverage_pct"]
        ),

        "threshold": float(
            result["threshold"]
        ),
    }