from __future__ import annotations
from typing import Any, Dict

def geotag_xtf_detection(
    survey: Any,
    bbox: dict,
) -> Dict[str, Any]:
    """
    Placeholder/stub for XTF navigation / sonar geometry parsing.
    Returns location unavailable until the raw XTF ping mapping layer is finalized.
    """
    return {
        "latitude": None,
        "longitude": None,
        "location_status": "unavailable",
        "location_source": None,
        "reason": "XTF navigation/sonar geometry geotagging is not implemented yet.",
    }
