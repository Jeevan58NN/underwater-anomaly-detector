from __future__ import annotations
from typing import Dict, Literal

# Centralized class mapping for YOLO11
CLASS_NAMES: Dict[int, str] = {
    0: "Shipwreck",
    1: "Aeroplane",
    2: "Rock",
    3: "Fish",
}

def get_class_name(class_id: int) -> str:
    """
    Map class ID to name, handling unknown or unrecognized classes safely.
    """
    return CLASS_NAMES.get(class_id, "Unknown")

def get_classification_type(class_name: str) -> Literal["artificial", "natural", "unknown"]:
    """
    Semantic category mapping layer:
      Artificial -> Shipwreck, Aeroplane
      Natural -> Rock, Fish
    """
    name_lower = class_name.strip().lower()
    if name_lower in {"shipwreck", "aeroplane"}:
        return "artificial"
    elif name_lower in {"rock", "fish"}:
        return "natural"
    return "unknown"

def get_seafloor_assessment(class_name: str) -> dict:
    """
    Prototype rule-based seafloor assessment percentages.
      Artificial -> 100% Artificial, 0% Natural
      Natural -> 0% Artificial, 100% Natural
      Unknown/Other -> 0% Artificial, 0% Natural
    """
    category = get_classification_type(class_name)
    if category == "artificial":
        return {
            "artificial_pct": 100.0,
            "natural_pct": 0.0,
            "note": "Prototype Rule-Based Assessment"
        }
    elif category == "natural":
        return {
            "artificial_pct": 0.0,
            "natural_pct": 100.0,
            "note": "Prototype Rule-Based Assessment"
        }
    return {
        "artificial_pct": 0.0,
        "natural_pct": 0.0,
        "note": "Prototype Rule-Based Assessment (Unknown Anomaly)"
    }

def get_priority(class_name: str, confidence: float) -> str:
    """
    Data-driven priority severity mapping.
    - Shipwreck / Aeroplane: High priority when confidence is >= 0.70, else Medium.
    - Rock / Fish: Medium priority when confidence is >= 0.70, else Low.
    - Unknown: Medium or Low depending on confidence.
    """
    category = get_classification_type(class_name)
    if category == "artificial":
        if confidence >= 0.70:
            return "High"
        return "Medium"
    elif category == "natural":
        if confidence >= 0.70:
            return "Medium"
        return "Low"
    else:
        if confidence >= 0.70:
            return "Medium"
        return "Low"
