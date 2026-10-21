from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from ultralytics import YOLO


class YOLODetector:
    """
    Adapter for the trained YOLO11 model.

    Compatible with the existing AquaScan pipeline, which calls:

        predict(image, image_width, image_height)

    YOLO itself only needs the image, but the additional arguments
    are accepted for interface compatibility.
    """

    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = 0.25,
        image_size: int = 640,
    ) -> None:

        self.model_path = Path(model_path)

        if not self.model_path.is_file():
            raise FileNotFoundError(
                f"YOLO model file not found: {self.model_path}"
            )

        self.confidence_threshold = confidence_threshold
        self.image_size = image_size

        print(
            f"[AquaScan] Loading YOLO model: "
            f"{self.model_path}"
        )

        self.model = YOLO(
            str(self.model_path)
        )

        from verification.classifier import get_class_name, CLASS_NAMES
        self.class_names = CLASS_NAMES
        self.model_loaded = True

        # Validation of class mapping at startup
        if hasattr(self.model, "names") and self.model.names:
            model_names = self.model.names
            for cid, name in CLASS_NAMES.items():
                if cid not in model_names:
                    print(
                        f"[AquaScan] CONFIGURATION WARNING: Expected class ID {cid} is missing "
                        f"from model names: {model_names}"
                    )
                elif model_names[cid].lower() != name.lower():
                    print(
                        f"[AquaScan] CONFIGURATION WARNING: Model class {cid} is '{model_names[cid]}' "
                        f"instead of '{name}'"
                    )

        print(
            "[AquaScan] YOLO model loaded successfully."
        )

        print(
            f"[AquaScan] Classes: {self.class_names}"
        )

    def predict(
        self,
        image: Any,
        image_width: Optional[int] = None,
        image_height: Optional[int] = None,
    ) -> list[dict]:
        """
        Run inference.

        image_width and image_height are accepted because the
        existing AquaScan pipeline supplies them.

        Returns:
            [
                {
                    "class_id": 0,
                    "class_name": "class_0",
                    "confidence": 0.6175,
                    "bbox": {
                        "x1": ...,
                        "y1": ...,
                        "x2": ...,
                        "y2": ...
                    }
                }
            ]
        """

        results = self.model.predict(
            source=image,
            imgsz=self.image_size,
            conf=self.confidence_threshold,
            verbose=False,
        )

        detections: list[dict] = []

        for result in results:

            if result.boxes is None:
                continue

            for box in result.boxes:

                class_id = int(
                    box.cls[0].item()
                )

                confidence = float(
                    box.conf[0].item()
                )

                x1, y1, x2, y2 = (
                    float(value)
                    for value in box.xyxy[0].tolist()
                )

                from verification.classifier import get_class_name
                class_name = get_class_name(class_id)

                detections.append(
                    {
                        "class_id": class_id,
                        "class_name": class_name,
                        "confidence": confidence,
                        "bbox": {
                            "x1": x1,
                            "y1": y1,
                            "x2": x2,
                            "y2": y2,
                        },
                    }
                )

        return detections