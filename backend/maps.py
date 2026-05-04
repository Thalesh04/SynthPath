# ─────────────────────────────────────────────────────
# maps.py — finds coordinates and calculates route info
# geopy (Nominatim / OpenStreetMap) → coordinates
# OSRM (OpenStreetMap Routing Machine) → actual driving routes
# No API key required
# ─────────────────────────────────────────────────────

from typing import Tuple, Dict, Optional, List
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from geopy.extra.rate_limiter import RateLimiter

import sys, os as _os
sys.path.append(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from utils.helpers import parse_coordinates, clean_address

import requests
import time


class MapHandler:

    def __init__(self):
        # Nominatim requires a unique user-agent
        self.geolocator = Nominatim(user_agent="traffic-route-finder")
        # OSRM public demo server — free, no API key
        self.osrm_base = "http://router.project-osrm.org/route/v1/driving"

    # ─────────────────────────────────────
# COORDINATES
    # converts "Rajwada, Indore" → (22.71, 75.85)
    # ─────────────────────────────────────

    def get_coordinates(
        self,
        address: str,
        *,
        viewbox: Optional[Tuple[Tuple[float, float], Tuple[float, float]]] = None,
        country_codes: Optional[List[str]] = None
    ) -> Tuple[float, float]:
        """
        Converts address to coordinates using Nominatim (OpenStreetMap).
        Supports robust coordinate string parsing and country bias.
        Includes retry logic for handling temporary network issues.
        """

        # 1) Check if input is already coordinates using robust parser
        coords = parse_coordinates(address)
        if coords:
            return coords

        address = clean_address(address)
        if not address:
            raise ValueError("Address cannot be empty.")

        # Default country bias to India
        if country_codes is None:
            country_codes = ["in"]

        # Retry logic for handling temporary network issues
        max_retries = 3
        retry_delay = 2  # seconds between retries

        for attempt in range(max_retries):
            try:
                location = self.geolocator.geocode(
                    address,
                    language="en",
                    country_codes=country_codes,
                    viewbox=viewbox,
                    timeout=10  # Increased timeout
                )
                if location:
                    return (location.latitude, location.longitude)
                else:
                    raise ValueError(
                        f"Could not find '{address}'. "
                        f"Try adding city name e.g. '{address}, Indore'"
                    )
            except (GeocoderTimedOut, GeocoderServiceError) as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise ValueError(f"Geocoding failed after {max_retries} attempts: {e}")
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise ValueError(f"Geocoding failed: {e}")

    def reverse_geocode(
        self,
        lat: float,
        lon: float,
        language: str = "en"
    ) -> Dict:
        """
        Converts coordinates to a human-readable address using Nominatim.
        Returns dict with display_name, address components, and raw data.
        """
        try:
            location = self.geolocator.reverse(
                (lat, lon),
                language=language
            )
        except (GeocoderTimedOut, GeocoderServiceError):
            return {
                "display_name": f"{lat:.5f}, {lon:.5f}",
                "address": {},
                "raw": {}
            }

        if not location:
            return {
                "display_name": f"{lat:.5f}, {lon:.5f}",
                "address": {},
                "raw": {}
            }

        display_name = location.address or f"{lat:.5f}, {lon:.5f}"

        return {
            "display_name": display_name,
            "full_address": display_name,
            "address": location.raw.get("address", {}),
            "raw": location.raw
        }

    # ─────────────────────────────────────
    # OSRM ROUTING (actual vehicle routes)
    # ─────────────────────────────────────

    def _call_osrm(self, start: Tuple[float, float],
                         end: Tuple[float, float]) -> Optional[Dict]:
        """
        Query the OSRM public API for a real driving route.
        Returns a dict with:
            - coords: List[(lat, lon)] actual road-following path
            - distance_m: float route distance in meters
            - duration_s: float estimated duration in seconds
        Returns None on failure.
        """
        # OSRM expects coordinates as lon,lat
        url = (
            f"{self.osrm_base}/"
            f"{start[1]},{start[0]};{end[1]},{end[0]}"
            f"?overview=full&geometries=geojson"
        )
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return None

        if data.get("code") != "Ok" or not data.get("routes"):
            return None

        route = data["routes"][0]
        geometry = route.get("geometry", {})
        # GeoJSON coordinates are [lon, lat] — flip to (lat, lon)
        coords = [(c[1], c[0]) for c in geometry.get("coordinates", [])]

        return {
            "coords": coords,
            "distance_m": route.get("distance", 0),
            "duration_s": route.get("duration", 0)
        }

    def _call_osrm_alternatives(self, start: Tuple[float, float],
                                      end: Tuple[float, float]) -> Optional[List[Dict]]:
        """
        Query OSRM for multiple route alternatives.
        Returns a list of route dicts sorted by duration (fastest first),
        or None on failure.
        Each dict contains: coords, distance_m, duration_s.
        """
        url = (
            f"{self.osrm_base}/"
            f"{start[1]},{start[0]};{end[1]},{end[0]}"
            f"?alternatives=true&overview=full&geometries=geojson"
        )
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return None

        if data.get("code") != "Ok" or not data.get("routes"):
            return None

        routes = []
        for route in data["routes"]:
            geometry = route.get("geometry", {})
            coords = [(c[1], c[0]) for c in geometry.get("coordinates", [])]
            routes.append({
                "coords": coords,
                "distance_m": route.get("distance", 0),
                "duration_s": route.get("duration", 0)
            })

        # Sort by duration so fastest route is always first
        routes.sort(key=lambda r: r["duration_s"])
        return routes

    # ─────────────────────────────────────
    # ROUTE
    # builds an actual driving path via OSRM
    # falls back to straight line if OSRM is unavailable
    # ─────────────────────────────────────

    def get_route(self, start: Tuple[float, float],
                        end:   Tuple[float, float]) -> Dict:
        """
        Builds a real driving route between two points using OSRM.
        Falls back to a straight-line interpolation if OSRM fails.
        Returns a dictionary with start, end, and path coordinates.
        """
        osrm = self._call_osrm(start, end)
        if osrm and osrm["coords"]:
            return {
                "start": start,
                "end": end,
                "coords": osrm["coords"]
            }

        # ── Fallback: straight-line interpolation ──
        num_points = 20
        coords = [start]

        for i in range(1, num_points):
            fraction = i / num_points
            lat = start[0] + (end[0] - start[0]) * fraction
            lon = start[1] + (end[1] - start[1]) * fraction
            coords.append((lat, lon))

        coords.append(end)

        return {
            "start": start,
            "end": end,
            "coords": coords
        }

    def get_route_with_alternatives(self, start: Tuple[float, float],
                                          end:   Tuple[float, float]) -> Dict:
        """
        Builds one or more driving routes using OSRM with alternatives enabled.
        Falls back to a single straight-line route if OSRM fails.
        Returns a dictionary with start, end, and a list of route dicts.
        The first route in the list is always the fastest.
        """
        routes = self._call_osrm_alternatives(start, end)
        if routes:
            return {
                "start": start,
                "end": end,
                "routes": routes
            }

        # ── Fallback: single straight-line interpolation ──
        num_points = 20
        coords = [start]

        for i in range(1, num_points):
            fraction = i / num_points
            lat = start[0] + (end[0] - start[0]) * fraction
            lon = start[1] + (end[1] - start[1]) * fraction
            coords.append((lat, lon))

        coords.append(end)

        distance_m = geodesic(start, end).meters
        duration_s = (distance_m / 1000.0 / 40.0) * 3600  # 40 km/h estimate

        return {
            "start": start,
            "end": end,
            "routes": [{
                "coords": coords,
                "distance_m": distance_m,
                "duration_s": duration_s
            }]
        }

    # ─────────────────────────────────────
    # TRAFFIC DATA
    # uses OSRM real driving distance & duration
    # falls back to geodesic estimates
    # ─────────────────────────────────────

    def get_traffic_data(self, start: Tuple[float, float],
                               end:   Tuple[float, float],
                               osrm_route: Optional[Dict] = None) -> Dict:
        """
        Calculates distance and estimated travel time.
        Uses OSRM for real driving distance/duration when available.
        Falls back to geodesic distance + 40 km/h estimate if OSRM fails.
        Applies a modest traffic heuristic so normal and traffic times differ.
        Optionally accepts pre-fetched OSRM route data to avoid an extra API call.
        """
        if osrm_route is not None:
            osrm = osrm_route
        else:
            osrm = self._call_osrm(start, end)

        if osrm:
            distance_km = osrm["distance_m"] / 1000.0
            normal_mins = round(osrm["duration_s"] / 60.0)
            # Apply a realistic traffic multiplier (10–25 % depending on urban density)
            # Heuristic: shorter trips in dense areas suffer more from traffic
            if distance_km < 5:
                multiplier = 1.25
            elif distance_km < 15:
                multiplier = 1.15
            else:
                multiplier = 1.10
            traffic_mins = round(normal_mins * multiplier)
        else:
            # Fallback: straight-line geodesic + 40 km/h urban speed
            distance_km = geodesic(start, end).kilometers
            avg_speed_kmh = 40.0
            normal_mins = round((distance_km / avg_speed_kmh) * 60)
            traffic_mins = normal_mins

        def format_time(mins: int) -> str:
            if mins >= 60:
                hours = mins // 60
                m = mins % 60
                return f"{hours} hr {m} mins"
            return f"{mins} mins"

        if distance_km >= 1:
            distance_text = f"{distance_km:.1f} km"
        else:
            distance_text = f"{distance_km * 1000:.0f} m"

        return {
            "distance": distance_text,
            "normal_duration": format_time(normal_mins),
            "traffic_duration": format_time(traffic_mins)
        }

