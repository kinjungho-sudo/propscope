import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

region_query = "공덕동"
search_url = f"https://apis.zigbang.com/v2/search?q={region_query}&serviceType=빌라"
resp = requests.get(search_url, headers=headers)
if resp.status_code == 200:
    items = resp.json().get("items", [])
    if items:
        for item in items:
            print(f"ID: {item.get('id')}, Description: {item.get('description')}, Lat: {item.get('lat')}, Lng: {item.get('lng')}")
            # Try to see if it provides a geohash
    else:
        print("No items found in search.")
else:
    print(f"Search failed: {resp.status_code}")
