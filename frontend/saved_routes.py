# ─────────────────────────────────────────────────────
# saved_routes.py — shows saved and frequent routes
# Two tabs: frequent routes and full search history
# ─────────────────────────────────────────────────────

import streamlit as st
import pandas as pd
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_route_history, get_frequent_routes


def show():
    st.markdown(
        """
        <div style="border-radius: 18px; background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%); padding: 24px; margin-bottom: 24px;">
            <div style="display:flex; flex-wrap:wrap; justify-content:space-between; gap:16px;">
                <div style="max-width: 760px;">
                    <h1 style="margin:0 0 8px;">⭐ Saved & Frequent Routes</h1>
                    <p style="margin:0; color:#475569; font-size:1rem; line-height:1.6;">
                        Track your route history, spot repeated trips, and keep your navigation habits visible in one clean dashboard.
                    </p>
                </div>
                <div style="min-width:180px; text-align:right;">
                    <span style="display:inline-block; background:#10b981; color:#ffffff; padding:10px 18px; border-radius:999px; font-weight:600;">History dashboard</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    user_id = st.session_state.get("user_id", 1)

    tab1, tab2 = st.tabs(["⭐ Frequent Routes", "📋 Route History"])

    # ─────────────────────────────────────
    # TAB 1 — FREQUENT ROUTES
    # ─────────────────────────────────────
    with tab1:
        st.markdown("### Your most used routes")
        frequent = get_frequent_routes(user_id)

        if not frequent:
            st.info("No frequent routes yet. Search routes to start building your dashboard.")
        else:
            df = pd.DataFrame(frequent)
            df.columns = ["Origin", "Destination", "Times Used"]
            df.index   = df.index + 1
            st.dataframe(df, use_container_width=True)

            top = frequent[0]
            st.success(
                f"🏆 Top route: **{top['origin']}** → **{top['destination']}** — {top['trip_count']}x"
            )

    # ─────────────────────────────────────
    # TAB 2 — FULL HISTORY
    # ─────────────────────────────────────
    with tab2:
        st.markdown("### Your search history")
        history = get_route_history(user_id)

        if not history:
            st.info("No history yet. Search a route to populate this panel.")
        else:
            df = pd.DataFrame(history)
            search = st.text_input("🔎 Filter history", placeholder="Search origin or destination")
            if search:
                mask = (
                    df["origin"].str.contains(search, case=False, na=False) |
                    df["destination"].str.contains(search, case=False, na=False)
                )
                df = df[mask]

            st.dataframe(df, use_container_width=True)

            st.divider()
            col1, col2, col3 = st.columns(3)
            all_history = get_route_history(user_id)
            all_frequent = get_frequent_routes(user_id)

            with col1:
                st.metric("Total Searches", len(all_history))
            with col2:
                st.metric("Unique Routes",  len(all_frequent))
            with col3:
                top_count = all_frequent[0]["trip_count"] if all_frequent else 0
                st.metric("Most Used Route", f"{top_count}x")
