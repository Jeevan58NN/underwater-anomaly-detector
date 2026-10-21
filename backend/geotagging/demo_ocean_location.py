from __future__ import annotations
import hashlib
from typing import Dict, Any

def get_demo_ocean_location(analysis_id: str, detection_index: int) -> Dict[str, Any]:
    """
    Generate deterministic, valid coordinates inside safe oceanic regions (away from land).
    Uses a seed derived from analysis_id and detection_index.
    """
    seed_str = f"{analysis_id}-{detection_index}"
    h = hashlib.md5(seed_str.encode("utf-8")).hexdigest()
    seed = int(h[:8], 16)
    
    # Predefined safe ocean bounding regions (WGS84) where there's only ocean water
    # [lat_min, lat_max, lon_min, lon_max, region_name]
    regions = [
        (5.0, 15.0, -165.0, -145.0, "Pacific Ocean (North)"),
        (-15.0, -5.0, -140.0, -120.0, "Pacific Ocean (South)"),
        (20.0, 30.0, -45.0, -35.0, "Atlantic Ocean (North)"),
        (-30.0, -20.0, -20.0, -10.0, "Atlantic Ocean (South)"),
    ]
    
    # Pick a region based on the seed
    region_idx = seed % len(regions)
    lat_min, lat_max, lon_min, lon_max, region_name = regions[region_idx]
    
    # Deterministic values within the selected region
    lat_seed = int(h[8:16], 16)
    lon_seed = int(h[16:24], 16)
    
    lat_frac = (lat_seed % 1000000) / 1000000.0
    lon_frac = (lon_seed % 1000000) / 1000000.0
    
    latitude = lat_min + lat_frac * (lat_max - lat_min)
    longitude = lon_min + lon_frac * (lon_max - lon_min)
    
    return {
        "latitude": round(latitude, 6),
        "longitude": round(longitude, 6),
        "location_status": "estimated",
        "location_source": "synthetic_demo_ocean",
        "reason": f"Estimated location in {region_name} assigned for prototype demonstration."
    }
