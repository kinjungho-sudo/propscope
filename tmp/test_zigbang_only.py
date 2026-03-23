import requests
import json
import asyncio
import sys
import os

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.utils.geohash import encode_geohash

async def test_zigbang():
    lat = 37.5443
    lng = 126.9510
    ghash = encode_geohash(lat, lng, 5)
    print(f"Geohash: {ghash}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Origin": "https://www.zigbang.com",
        "Referer": "https://www.zigbang.com/"
    }
    
    # Step 1: List IDs
    url = f"https://apis.zigbang.com/house/property/v1/items/villas?geohash={ghash}&salesPriceMin=0&depositMin=0&rentMin=0"
    resp = requests.get(url, headers=headers)
    print(f"List Request Status: {resp.status_code}")
    if resp.status_code == 200:
        item_ids = resp.json().get("item_ids", [])
        print(f"Found {len(item_ids)} items.")
        
        if item_ids:
            # Step 2: Detail
            detail_url = "https://apis.zigbang.com/house/property/v1/items/list"
            payload = {"item_ids": item_ids[:10]} # Test with 10 items
            detail_resp = requests.post(detail_url, json=payload, headers=headers)
            print(f"Detail Request Status: {detail_resp.status_code}")
            if detail_resp.status_code == 200:
                items = detail_resp.json().get("items", [])
                for it in items:
                    print(f"Name: {it.get('title')}, Sales Type: {it.get('sales_type')}, Price: {it.get('sales_price')}")

if __name__ == "__main__":
    asyncio.run(test_zigbang())
