# ─────────────────────────────────────────────────────
# home.py — main search page
# User enters origin and destination
# App finds coordinates, calculates route, shows map
# ─────────────────────────────────────────────────────

import streamlit as st
import pandas as pd
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.maps import MapHandler
from backend.database import save_route, get_route_history
from frontend.map_view import render_map


def show():
    st.markdown("### Why it works")
    col_a, col_b, col_c = st.columns(3)
    col_a.markdown("**🚦 Live traffic**\n\nSee route times with real congestion estimates.")
    col_b.markdown("**🧭 Smart routing**\n\nCompare alternatives so you can choose the fastest path.")
    col_c.markdown("**📚 History saved**\n\nReview recent searches without logging in.")

    handler = MapHandler()

    # ─────────────────────────────────────
    # INPUT SECTION
    # modern search form design
    # ─────────────────────────────────────
    with st.container():
        with st.form("route_search_form"):
            st.markdown("#### Search your route")
            col1, col2 = st.columns(2)
            with col1:
                origin = st.text_input(
                    "📍 Starting Point",
                    value       = "",
                    placeholder = "e.g. Rajwada, Indore"
                )
            with col2:
                destination = st.text_input(
                    "🏁 Destination",
                    placeholder = "e.g. Indore Railway Station"
                )

            search_clicked = st.form_submit_button(
                "🔍 Find best route",
                type                = "primary",
                use_container_width = True
            )

    # ─────────────────────────────────────
    # SEARCH LOGIC
    # Only runs when button is clicked
    # ─────────────────────────────────────
    if search_clicked:

        # Validate — check inputs are not empty
        if not origin or not destination:
            st.error("❌ Please enter both locations.")
            return   # return stops the function here

        # Check origin and destination are not the same
        if origin.strip() == destination.strip():
            st.error("❌ Start and destination cannot be the same.")
            return

        # st.spinner shows a loading animation while code inside runs
        with st.spinner("Finding route..."):
            try:
                # Step 1 — convert addresses to coordinates
                start_coords = handler.get_coordinates(origin)
                end_coords   = handler.get_coordinates(destination)

                # Step 2 — get route with alternatives
                route_result = handler.get_route_with_alternatives(start_coords, end_coords)

                # Step 3 — get traffic estimate for the fastest route
                # Pass the fastest route data to avoid an extra API call
                fastest_route = route_result["routes"][0] if route_result.get("routes") else None
                traffic_data = handler.get_traffic_data(
                    start_coords, end_coords, osrm_route=fastest_route
                )

                # Step 4 — save to database
                user_id = st.session_state.get("user_id", 1)
                save_route(
                    user_id     = user_id,
                    origin      = origin,
                    destination = destination,
                    distance    = traffic_data["distance"],
                    duration    = traffic_data["traffic_duration"]
                )

                # Step 5 — store results in session_state
                # session_state persists data between Streamlit reruns
                st.session_state["route_result"] = route_result
                st.session_state["traffic_data"] = traffic_data
                st.session_state["search_done"]  = True

            except ValueError as e:
                # ValueError is raised by get_coordinates when address not found
                st.error(f"❌ {e}")
                return

            except Exception as e:
                # Catch any other unexpected errors
                st.error(f"❌ Error: {e}")
                return

    # ─────────────────────────────────────
    # RESULTS SECTION
    # Only shows if a search was done
    # ─────────────────────────────────────
    if st.session_state.get("search_done"):
        traffic_data = st.session_state["traffic_data"]
        route_result = st.session_state["route_result"]

        st.divider()
        st.markdown("## Results")

        # Show metrics — distance and time
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📏 Distance", traffic_data["distance"])
        with col2:
            st.metric("🕐 No traffic", traffic_data["normal_duration"])
        with col3:
            st.metric("🚦 With traffic", traffic_data["traffic_duration"])

        if traffic_data["normal_duration"] == traffic_data["traffic_duration"]:
            st.success("🟢 Traffic is clear! This route is smooth.")
        else:
            st.warning("🔴 Expect delays on this route. Plan accordingly.")

        st.caption("⏱️ Estimates use live traffic data for better route planning.")

        routes = route_result.get("routes", [])
        if len(routes) > 1:
            st.divider()
            st.markdown("### 🛣️ Route options")
            for idx, route in enumerate(routes):
                dist_km = route.get("distance_m", 0) / 1000.0
                dur_min = round(route.get("duration_s", 0) / 60.0)
                is_fastest = (idx == 0)
                if is_fastest:
                    st.success(f"**Best route** — {dist_km:.1f} km, ~{dur_min} mins")
                else:
                    st.info(f"Route {idx + 1} — {dist_km:.1f} km, ~{dur_min} mins")

        st.divider()
        st.markdown("### 🗺️ Route map")
        render_map(route_result)

        st.divider()
        st.markdown("### 📋 Recent searches")
        user_id = st.session_state.get("user_id", 1)
        history = get_route_history(user_id)

        if history:
            st.dataframe(pd.DataFrame(history), use_container_width=True)
        else:
            st.info("No routes searched yet. Start one above to see it here.")