from __future__ import annotations

def calculate_system_score(
    model_confidence: float,
    class_name: str,
    has_segmentation: bool = False,
    has_shadow: bool = False,
) -> float:
    """
    Deterministically calculate a secondary system score combining multiple evidence factors:
    - Base confidence (80% of model confidence)
    - Segmentation quality check (adds 10% if a segmentation mask is successfully generated)
    - Acoustic shadow evidence (adds 10% if shadow details are present; placeholder for future analysis)
    
    The score is bounded in [0.0, 1.0] and rounded to 3 decimal places.
    """
    score = model_confidence * 0.8
    if has_segmentation:
        score += 0.1
    if has_shadow:
        score += 0.1
    return round(min(max(score, 0.0), 1.0), 3)
