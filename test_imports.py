import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test helpers
from utils.helpers import parse_coordinates, validate_coordinates, clean_address, format_coords
assert parse_coordinates("22.71, 75.85") == (22.71, 75.85)
assert parse_coordinates("22.71 75.85") == (22.71, 75.85)
assert parse_coordinates("  22.71  ,  75.85  ") == (22.71, 75.85)
assert validate_coordinates(22.71, 75.85)
assert not validate_coordinates(100, 75.85)
assert clean_address("  Rajwada,   Indore  ") == "Rajwada, Indore"
print("✅ utils/helpers.py OK")

# Test maps (no API key needed — uses geopy / Nominatim)
from backend.maps import MapHandler
assert hasattr(MapHandler, 'get_coordinates')
assert hasattr(MapHandler, 'reverse_geocode')
assert hasattr(MapHandler, 'get_route')
assert hasattr(MapHandler, 'get_traffic_data')

h = MapHandler()
print("✅ backend/maps.py OK (MapHandler instantiated)")

# Test gps_component (just import)
from frontend.gps_component import get_gps_location
print("✅ frontend/gps_component OK")

print("\n🎉 All backend imports and basic tests passed!")
print("   Frontend files were updated but require Streamlit runtime to test.")

