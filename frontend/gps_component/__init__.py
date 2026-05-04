import os
import streamlit.components.v1 as components

# Absolute path to this component's directory (where index.html lives)
_COMPONENT_PATH = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")

# Declare the bi-directional Streamlit component
_gps_component = components.declare_component("gps_locator", path=_COMPONENT_PATH)


def get_gps_location(key=None):
    """
    Renders the GPS button and returns the user's coordinates when clicked.
    Returns None initially; returns {"lat", "lon", "acc"} dict after click.
    If an error occurs, returns {"error": "message"}.
    """
    return _gps_component(default=None, key=key, height=50)

