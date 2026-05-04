# ─────────────────────────────────────────────────────
# helpers.py — utility functions for coordinates & addresses
# ─────────────────────────────────────────────────────

import re
from typing import Tuple, Optional


def parse_coordinates(text: str) -> Optional[Tuple[float, float]]:
    """
    Robustly parse a coordinate string into (lat, lon).
    Handles formats:
      "22.7196, 75.8577"
      "22.7196,75.8577"
      "22.7196 75.8577"
      "  22.7196  ,  75.8577  "
    Returns None if parsing fails.
    """
    if not text or not isinstance(text, str):
        return None

    text = text.strip()
    if not text:
        return None

    # Try comma-separated first
    parts = [p.strip() for p in text.split(",") if p.strip() != ""]
    if len(parts) == 2:
        try:
            lat = float(parts[0])
            lon = float(parts[1])
            if validate_coordinates(lat, lon):
                return (lat, lon)
        except ValueError:
            pass

    # Try whitespace-separated (any whitespace including tabs)
    parts = [p.strip() for p in re.split(r"\s+", text) if p.strip() != ""]
    if len(parts) == 2:
        try:
            lat = float(parts[0])
            lon = float(parts[1])
            if validate_coordinates(lat, lon):
                return (lat, lon)
        except ValueError:
            pass

    return None


def validate_coordinates(lat: float, lon: float) -> bool:
    """
    Check if lat/lon values are within valid Earth ranges.
    Latitude:  -90  to  90
    Longitude: -180 to 180
    """
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0


def clean_address(address: str) -> str:
    """
    Normalize user-entered address before geocoding.
    - Strip extra whitespace
    - Remove multiple spaces
    - Remove special characters that break geocoding
    """
    if not address:
        return ""
    address = address.strip()
    # collapse multiple spaces/tabs into one space
    address = re.sub(r"\s+", " ", address)
    # remove characters that commonly cause geocoding failures
    address = re.sub(r"[\r\n\t]+", " ", address)
    return address.strip()


def format_coords(lat: float, lon: float, decimals: int = 4) -> str:
    """
    Format coordinates for display, e.g. '22.7196, 75.8577'.
    """
    return f"{lat:.{decimals}f}, {lon:.{decimals}f}"

