import hashlib
from typing import List
from .base import Detector, RawDetection

PROTOTYPE_CLASSES = ["Ghost Net", "Pipe", "Cylinder", "Shipwreck", "Unknown Anomaly"]

class MockDetector(Detector):
    @property
    def name(self) -> str:
        return "MockDetector"

    def predict(self, image_path: str, image_width: int, image_height: int) -> List[RawDetection]:
        seed = self._seed_from_file(image_path)
        rng_state = seed

        def next_val(lo: float, hi: float) -> float:
            nonlocal rng_state
            rng_state = (1103515245 * rng_state + 12345) & 0x7FFFFFFF
            frac = rng_state / 0x7FFFFFFF
            return lo + frac * (hi - lo)

        num_detections = 2 if (seed % 3 != 0) else 3
        detections: List[RawDetection] = []

        for i in range(num_detections):
            cls = PROTOTYPE_CLASSES[(seed + i * 7) % len(PROTOTYPE_CLASSES)]
            confidence = round(next_val(0.62, 0.97), 2)

            box_w = int(next_val(90, 240))
            box_h = int(next_val(60, 160))
            x = int(next_val(40, max(41, image_width - box_w - 40)))
            y = int(next_val(40, max(41, image_height - box_h - 40)))

            relative_angle = next_val(0, 360)
            sonar_range = next_val(15, 80)

            detections.append(
                RawDetection(
                    class_name=cls,
                    confidence=confidence,
                    bbox={"x": x, "y": y, "width": box_w, "height": box_h},
                    relative_angle=relative_angle,
                    sonar_range=sonar_range,
                )
            )

        return detections

    @staticmethod
    def _seed_from_file(image_path: str) -> int:
        h = hashlib.md5(image_path.encode("utf-8")).hexdigest()
        return int(h[:8], 16)
