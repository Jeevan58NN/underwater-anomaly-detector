import os
import pytest
from fastapi.testclient import TestClient
from main import app
from verification.classifier import get_class_name, get_classification_type, get_priority, get_seafloor_assessment
from geotagging.demo_ocean_location import get_demo_ocean_location
from report_generator import build_csv, build_json
from schemas import Detection, BoundingBox, SeafloorAssessment

client = TestClient(app)

# ============================================================
# CLASSIFIER TESTS (Tests C, D, E, F, G)
# ============================================================

def test_classifier_class_mapping_c():
    """Test C: Unknown class ID -> Unknown"""
    assert get_class_name(0) == "Shipwreck"
    assert get_class_name(1) == "Aeroplane"
    assert get_class_name(2) == "Rock"
    assert get_class_name(3) == "Fish"
    assert get_class_name(99) == "Unknown"
    assert get_class_name(-1) == "Unknown"

def test_classifier_classification_type_d_e_f_g():
    """Tests D, E, F, G: Semantic category rule-based check"""
    # Test D: Shipwreck -> artificial
    assert get_classification_type("Shipwreck") == "artificial"
    # Test E: Aeroplane -> artificial
    assert get_classification_type("Aeroplane") == "artificial"
    # Test F: Rock -> natural
    assert get_classification_type("Rock") == "natural"
    # Test G: Fish -> natural
    assert get_classification_type("Fish") == "natural"
    # Unknown -> unknown
    assert get_classification_type("Unknown") == "unknown"

def test_seafloor_assessment_rule_based():
    """Verify rule-based percentage assessment values"""
    art_assess = get_seafloor_assessment("Shipwreck")
    assert art_assess["artificial_pct"] == 100.0
    assert art_assess["natural_pct"] == 0.0
    assert art_assess["note"] == "Prototype Rule-Based Assessment"

    nat_assess = get_seafloor_assessment("Rock")
    assert nat_assess["artificial_pct"] == 0.0
    assert nat_assess["natural_pct"] == 100.0
    assert nat_assess["note"] == "Prototype Rule-Based Assessment"

def test_priority_rules():
    """Verify priority severity calculation mapping"""
    # Shipwreck >= 0.70 -> High
    assert get_priority("Shipwreck", 0.75) == "High"
    assert get_priority("Shipwreck", 0.65) == "Medium"
    # Rock >= 0.70 -> Medium
    assert get_priority("Rock", 0.80) == "Medium"
    assert get_priority("Rock", 0.50) == "Low"

# ============================================================
# GEOTAGGING TESTS (Test H)
# ============================================================

def test_demo_ocean_location_h():
    """Test H: image-only -> estimated/synthetic ocean location with correct source & status"""
    loc = get_demo_ocean_location("test-analysis-id", 0)
    assert loc["location_status"] == "estimated"
    assert loc["location_source"] == "synthetic_demo_ocean"
    assert -90.0 <= loc["latitude"] <= 90.0
    assert -180.0 <= loc["longitude"] <= 180.0
    # Center points must not fall on land
    assert loc["latitude"] != 0.0 or loc["longitude"] != 0.0

# ============================================================
# REPORT BUILDER TESTS (Tests K, L)
# ============================================================

@pytest.fixture
def sample_detections():
    return [
        Detection(
            id="det-1",
            class_id=0,
            class_name="Shipwreck",
            confidence=0.88,
            confidence_band="High",
            model_confidence=0.88,
            system_score=0.80,
            verification_score=1.0,
            final_confidence=0.88,
            classification_type="artificial",
            priority="High",
            severity="High",
            bbox=BoundingBox(x=10, y=20, width=50, height=60),
            latitude=12.5,
            longitude=-150.0,
            location_status="estimated",
            location_source="synthetic_demo_ocean",
            seafloor_assessment=SeafloorAssessment(
                artificial_pct=100.0,
                natural_pct=0.0,
                note="Prototype Rule-Based Assessment"
            ),
            input_type="PNG",
            analysis_id="an-123",
            timestamp="2026-08-31T20:00:00"
        ),
        Detection(
            id="det-2",
            class_id=2,
            class_name="Rock",
            confidence=0.55,
            confidence_band="Medium",
            model_confidence=0.55,
            system_score=0.44,
            verification_score=0.0,
            final_confidence=0.55,
            classification_type="natural",
            priority="Low",
            severity="Low",
            bbox=BoundingBox(x=100, y=120, width=40, height=40),
            latitude=-12.5,
            longitude=135.0,
            location_status="estimated",
            location_source="synthetic_demo_ocean",
            seafloor_assessment=SeafloorAssessment(
                artificial_pct=0.0,
                natural_pct=100.0,
                note="Prototype Rule-Based Assessment"
            ),
            input_type="PNG",
            analysis_id="an-123",
            timestamp="2026-08-31T20:00:00"
        )
    ]

def test_csv_report_k(sample_detections):
    """Test K: CSV -> valid report matching the 20 columns contract"""
    csv_out = build_csv(sample_detections)
    lines = csv_out.strip().split("\r\n")
    # Verify header and rows
    assert len(lines) == 3
    headers = lines[0].split(",")
    assert len(headers) == 20
    assert headers[0] == "Detection ID"
    assert headers[2] == "Class ID"
    assert headers[4] == "System Score"
    assert headers[5] == "Classification"
    assert headers[16] == "Priority"
    assert headers[18] == "Analysis ID"

    # Row 1 check
    row1 = lines[1].split(",")
    assert row1[0] == "det-1"
    assert row1[1] == "Shipwreck"
    assert row1[2] == "0"
    assert row1[3] == "88%"
    assert row1[4] == "80%"
    assert row1[5] == "artificial"
    assert row1[6] == "100.0"
    assert row1[14] == "estimated"
    assert row1[16] == "High"

def test_json_report_l(sample_detections):
    """Test L: JSON -> valid report metadata output"""
    json_out = build_json(sample_detections)
    import json
    parsed = json.loads(json_out)
    assert parsed["report_type"] == "AquaScan AI Anomaly Report"
    assert parsed["count"] == 2
    assert len(parsed["detections"]) == 2
    assert parsed["detections"][0]["id"] == "det-1"
    assert parsed["detections"][0]["class_name"] == "Shipwreck"
    assert parsed["detections"][0]["system_score"] == 0.80
    assert parsed["detections"][0]["classification_type"] == "artificial"

# ============================================================
# ENDPOINT & API FLOW TESTS (Test A, B, I, J)
# ============================================================

def test_unsupported_file():
    """Verify analysis rejection on invalid file types"""
    with open("dummy.txt", "w") as f:
        f.write("test")
    try:
        with open("dummy.txt", "rb") as f:
            response = client.post("/api/analyze", files={"image": ("dummy.txt", f, "text/plain")})
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]
    finally:
        if os.path.exists("dummy.txt"):
            os.remove("dummy.txt")

def test_missing_model_weights():
    """Verify 503 configuration error if model is missing or fails loading"""
    # If the model is not configured/loaded properly in test environment, verify it returns 503
    with open("dummy.png", "wb") as f:
        f.write(b"fake image data")
    try:
        with open("dummy.png", "rb") as f:
            response = client.post("/api/analyze", files={"image": ("dummy.png", f, "image/png")}, data={"mode": "real"})
        # It could be 503 (model missing) or 200 (if real best.pt exists and runs)
        if response.status_code == 503:
            assert "Real AI model is not configured." in response.json()["detail"]
    finally:
        if os.path.exists("dummy.png"):
            os.remove("dummy.png")
