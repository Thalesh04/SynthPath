# TODO — Add Real Vehicle Routing via OSRM

## Steps
- [x] 1. Rewrite `backend/maps.py` — integrate OSRM API for actual driving routes
  - [x] 1a. Add `requests` import and OSRM helper method
  - [x] 1b. Rewrite `get_route()` to use OSRM geometry (with straight-line fallback)
  - [x] 1c. Rewrite `get_traffic_data()` to use OSRM distance/duration (with geodesic fallback)
- [x] 2. Run `python test_imports.py` to validate imports
- [x] 3. Test the Streamlit app with a real route to verify road-following paths
