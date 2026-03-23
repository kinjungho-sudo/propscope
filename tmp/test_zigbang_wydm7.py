import requests
import json
import asyncio
import sys
import os

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

async def test_zigbang_wydm7():
    ghash = "wydm7"
    print(f"Geohash: {ghash}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Origin": "https://www.zigbang.com",
        "Referer": "https://www.zigbang.com/"
    }
    
    url = f"https://apis.zigbang.com/house/property/v1/items/villas?geohash={ghash}&salesPriceMin=0&depositMin=0&rentMin=0"
    resp = requests.get(url, headers=headers)
    print(f"List Request Status: {resp.status_code}")
    if resp.status_code == 200:
        item_ids = resp.json().get("item_ids", [])
        print(f"Found {len(item_ids)} items for {ghash}")
        
if __name__ == "__main__":
    asyncio.run(test_zigbang_wydm7())
