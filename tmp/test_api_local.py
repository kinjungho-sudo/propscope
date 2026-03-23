import requests, json

payload = {
    "region_name": "마포구 공덕동",
    "region_code": "1144010200",
    "lat": 37.5443, "lng": 126.951,
    "property_types": ["빌라"],
    "price_min": 5000, "price_max": 200000,
    "area_min": 15, "area_max": 200,
    "build_year_min": 2000,
    "floor_min": 0, "floor_max": 100,
    "TRADE_TYPE": "매매"
}

r = requests.post("http://localhost:8765/api/search", json=payload, timeout=35)
d = r.json()
print("Status:", r.status_code)
print("Total:", d.get("total_count"), "Naver:", d.get("naver_count"), "Zigbang:", d.get("zigbang_count"))
print("= Stats =")
print(json.dumps(d.get("stats", {}).get("summary", {}), ensure_ascii=False, indent=2))
if d.get("items"):
    print("= First Item =")
    print(json.dumps(d["items"][0], ensure_ascii=False, indent=2))
