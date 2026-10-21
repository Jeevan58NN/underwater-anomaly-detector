from __future__ import annotations

import csv
import io
import json
from typing import List

from schemas import Detection


def build_csv(
    detections: List[Detection],
) -> str:
    """
    Build a CSV anomaly report matching the contract of 20 columns:
    Detection ID, Class, Class ID, Model Confidence, System Score, Classification,
    Artificial %, Natural %, Bounding X, Bounding Y, Bounding Width, Bounding Height,
    Latitude, Longitude, Location Status, Location Source, Priority, Input Type,
    Analysis ID, Timestamp.
    """

    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow(
        [
            "Detection ID",
            "Class",
            "Class ID",
            "Model Confidence",
            "System Score",
            "Classification",
            "Artificial %",
            "Natural %",
            "Bounding X",
            "Bounding Y",
            "Bounding Width",
            "Bounding Height",
            "Latitude",
            "Longitude",
            "Location Status",
            "Location Source",
            "Priority",
            "Input Type",
            "Analysis ID",
            "Timestamp",
        ]
    )

    for detection in detections:
        # Format latitude/longitude
        latitude = (
            f"{detection.latitude:.8f}"
            if detection.latitude is not None
            else ""
        )
        longitude = (
            f"{detection.longitude:.8f}"
            if detection.longitude is not None
            else ""
        )

        # Format class id
        class_id = (
            str(detection.class_id)
            if detection.class_id is not None
            else ""
        )

        # Format confidence percentages (e.g. 62% or 47.5%)
        model_conf = (
            f"{detection.model_confidence * 100:.0f}%"
            if detection.model_confidence is not None
            else f"{detection.confidence * 100:.0f}%"
        )

        sys_score = (
            f"{detection.system_score * 100:.0f}%"
            if detection.system_score is not None
            else ""
        )

        # Format bounding box values
        bbox_x = detection.bbox.x if detection.bbox else ""
        bbox_y = detection.bbox.y if detection.bbox else ""
        bbox_width = detection.bbox.width if detection.bbox else ""
        bbox_height = detection.bbox.height if detection.bbox else ""

        writer.writerow(
            [
                detection.id,
                detection.class_name,
                class_id,
                model_conf,
                sys_score,
                detection.classification_type or "",
                detection.seafloor_assessment.artificial_pct,
                detection.seafloor_assessment.natural_pct,
                bbox_x,
                bbox_y,
                bbox_width,
                bbox_height,
                latitude,
                longitude,
                detection.location_status,
                detection.location_source or "",
                detection.priority or detection.severity or "",
                detection.input_type or "",
                detection.analysis_id or "",
                detection.timestamp or "",
            ]
        )

    return buffer.getvalue()


def build_json(
    detections: List[Detection],
) -> str:
    """
    Build a JSON anomaly report.
    Returns structured JSON with all dynamic properties of the detections list.
    """
    payload = {
        "report_type": "AquaScan AI Anomaly Report",
        "count": len(detections),
        "detections": [
            detection.model_dump(mode="json")
            for detection in detections
        ],
    }

    return json.dumps(
        payload,
        indent=2,
        ensure_ascii=False,
    )