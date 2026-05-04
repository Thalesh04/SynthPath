# ─────────────────────────────────────────────────────
# app.py — entry point, run this file with streamlit
# Sets up page config, sidebar navigation, and routing
# ─────────────────────────────────────────────────────

import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from frontend import home, saved_routes
from backend.database import create_tables
from backend.auth import (
    register_user,
    login_user,
    get_user_by_id,
    ensure_guest_user,
)

# Must be first Streamlit command in the file
st.set_page_config(
    page_title = "Traffic Route App",
    page_icon  = "🚦",
    layout     = "wide"   # uses full browser width
)

# Create database tables on startup
# IF NOT EXISTS means safe to call every time app starts
create_tables()
guest_user_id = ensure_guest_user()

# ─────────────────────────────────────
# SESSION STATE DEFAULTS
# Set default values if not already set
# These persist across page reruns
# ─────────────────────────────────────
if "search_done" not in st.session_state:
    st.session_state["search_done"] = False

if "user_id" not in st.session_state:
    st.session_state["user_id"] = guest_user_id   # default user, no login needed

if "auth_action" not in st.session_state:
    st.session_state["auth_action"] = None

if "auth_message" not in st.session_state:
    st.session_state["auth_message"] = ""

if "theme" not in st.session_state:
    st.session_state["theme"] = "Dark"

# ─────────────────────────────────────
# SIDEBAR
# st.sidebar.anything puts it in left panel
# ─────────────────────────────────────
st.sidebar.title("🚦 Traffic Route App")
user = get_user_by_id(st.session_state.get("user_id", guest_user_id))
if user and user["username"] != "guest":
    st.sidebar.success(f"Signed in as **{user['username']}**")
else:
    st.sidebar.info("Guest mode — search without signing in.")

st.sidebar.divider()

# Theme selector for light / dark mode
theme = st.sidebar.selectbox(
    "Theme",
    ["Light", "Dark"],
    index=0 if st.session_state["theme"] == "Light" else 1,
    key="theme"
)

# Radio buttons for navigation
# Returns the selected option as a string
page = st.sidebar.radio(
    "Navigate",
    ["🏠 Home", "⭐ Saved Routes"]
)

st.sidebar.divider()
st.sidebar.caption("Built with Streamlit + geopy")

# ─────────────────────────────────────
# AUTH UI
# Optional sign in / sign up controls
# ─────────────────────────────────────

def _render_auth_topbar():
    user = get_user_by_id(st.session_state.get("user_id", guest_user_id))
    _, action_col = st.columns([4, 1])

    with action_col:
        if user and user["username"] != "guest":
            if st.button("Log out", use_container_width=True, key="logout"):
                st.session_state["user_id"] = guest_user_id
                st.session_state["auth_action"] = None
                st.session_state["auth_message"] = "Logged out. You are using guest mode."
        else:
            if st.button("Sign in", use_container_width=True, key="sign_in"):
                st.session_state["auth_action"] = "signin"
                st.session_state["auth_message"] = ""
            if st.button("Sign up", use_container_width=True, key="sign_up"):
                st.session_state["auth_action"] = "signup"
                st.session_state["auth_message"] = ""

    if st.session_state.get("auth_message"):
        st.info(st.session_state["auth_message"])


def _render_auth_form():
    action = st.session_state.get("auth_action")
    if not action:
        return

    with st.expander("Authentication", expanded=True):
        if action == "signin":
            st.subheader("Sign in")
            username = st.text_input("Username", key="signin_username")
            password = st.text_input("Password", type="password", key="signin_password")

            if st.button("Login", key="login_button"):
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    user_id = login_user(username, password)
                    if user_id is not None:
                        st.session_state["user_id"] = user_id
                        st.session_state["auth_action"] = None
                        st.session_state["auth_message"] = f"Signed in as {username}."
                    else:
                        st.error("Invalid username or password.")

        elif action == "signup":
            st.subheader("Sign up")
            username = st.text_input("Choose a username", key="signup_username")
            password = st.text_input("Choose a password", type="password", key="signup_password")

            if st.button("Create account", key="create_account_button"):
                if not username or not password:
                    st.error("Please choose both username and password.")
                else:
                    registered = register_user(username, password)
                    if registered:
                        st.session_state["auth_action"] = "signin"
                        st.session_state["auth_message"] = "Account created. Please sign in."
                    else:
                        st.error("That username is already taken.")

        if st.button("Cancel", key="auth_cancel_button"):
            st.session_state["auth_action"] = None
            st.session_state["auth_message"] = ""


_render_auth_topbar()
_render_auth_form()

# ─────────────────────────────────────
# PAGE ROUTING
# Show page based on sidebar selection
# ─────────────────────────────────────
if page == "🏠 Home":
    home.show()
elif page == "⭐ Saved Routes":
    saved_routes.show()