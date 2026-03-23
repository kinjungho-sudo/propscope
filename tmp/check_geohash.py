import sys
import os

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.utils.geohash import encode_geohash

lat = 37.5443
lng = 126.9510
print(f"Geohash (Prec 5): {encode_geohash(lat, lng, 5)}")
print(f"Geohash (Prec 6): {encode_geohash(lat, lng, 6)}")
