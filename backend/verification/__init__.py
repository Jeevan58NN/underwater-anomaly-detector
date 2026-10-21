from __future__ import annotations
from .classifier import get_seafloor_assessment

def verify_detection(
    class_name: str,
    bbox: dict,
    processing_mode: str,
    seed_val: int = 0,
) -> dict:
    """
    Verification layer wrapping the central rule-based classifier.
    """
    return get_seafloor_assessment(class_name)
