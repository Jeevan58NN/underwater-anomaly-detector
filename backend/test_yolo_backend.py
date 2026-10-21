from detectors.yolo_detector import YOLODetector


detector = YOLODetector(
    model_path="weights/best.pt",
    confidence_threshold=0.25,
    image_size=640,
)

detections = detector.predict(
    "uploads/SCAN-1F95C2F0.jpg"
)

print("\n===== MODEL RESULT =====")

for detection in detections:
    print(detection)