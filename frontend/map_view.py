# ─────────────────────────────────────────────────────
# map_view.py — draws the route on an interactive map
# Uses Folium to create the map
# Uses streamlit-folium to show it inside Streamlit
# ─────────────────────────────────────────────────────

import folium                        # creates interactive maps
from streamlit_folium import st_folium   # embeds folium maps in Streamlit


# Color constants for route styling
_FASTEST_COLOR = "#2E5BFF"   # deep blue
_ALTERNATE_COLOR = "#ff7f0e"  # orange


def _find_fastest_idx(routes: list) -> int:
    """Return index of route with the smallest duration."""
    if len(routes) <= 1:
        return 0
    return min(range(len(routes)), key=lambda i: routes[i].get("duration_s", float("inf")))


def render_map(route_result: dict):
    """
    Takes the route dictionary from maps.py and draws it on a Folium map.
    Supports both single-route (legacy) and multi-route (alternatives) formats.
    Fastest route is drawn as a solid blue line; alternate routes are thinner dashed orange lines.
    """
    # Extract start and end from route result
    start = route_result["start"]    # (lat, lon) tuple
    end   = route_result["end"]      # (lat, lon) tuple

    # Handle legacy format (single coords list) and new format (routes list)
    routes = route_result.get("routes")
    if routes is None:
        # Legacy format — wrap single coords into a route list
        coords = route_result.get("coords", [])
        routes = [{"coords": coords, "distance_m": 0, "duration_s": 0}]

    fastest_idx = _find_fastest_idx(routes)

    # Create a Folium map centered at the start location
    # zoom_start is just a fallback — fit_bounds will override it
    map_ = folium.Map(location=start, zoom_start=13)

    for idx, route in enumerate(routes):
        coords = route.get("coords", [])
        if not coords:
            continue

        if idx == fastest_idx:
            color = _FASTEST_COLOR
            weight = 5
            tooltip = f"Route {idx + 1} — ★ Fastest"
        else:
            color = _ALTERNATE_COLOR
            weight = 3
            tooltip = f"Route {idx + 1}"

        folium.PolyLine(
            locations=coords,
            color=color,
            weight=weight,
            opacity=0.85,
            tooltip=tooltip,
            dash_array="8" if idx != fastest_idx else None
        ).add_to(map_)

    # Green marker at start point with popup showing coordinates
    folium.Marker(
        location=start,
        tooltip="Start",
        popup=f"Start<br>{start[0]:.5f}, {start[1]:.5f}",
        icon=folium.Icon(color="green", icon="play")
    ).add_to(map_)

    # Red marker at destination with popup
    folium.Marker(
        location=end,
        tooltip="Destination",
        popup=f"Destination<br>{end[0]:.5f}, {end[1]:.5f}",
        icon=folium.Icon(color="red", icon="stop")
    ).add_to(map_)

    # Fit bounds to show all routes entirely
    all_coords = []
    for route in routes:
        all_coords.extend(route.get("coords", []))

    if all_coords:
        sw = [min(p[0] for p in all_coords), min(p[1] for p in all_coords)]
        ne = [max(p[0] for p in all_coords), max(p[1] for p in all_coords)]
        map_.fit_bounds([sw, ne], padding=(40, 40))
    else:
        map_.fit_bounds([start, end], padding=(30, 30))

    # Render the map inside Streamlit
    st_folium(map_, width=800, height=450)

