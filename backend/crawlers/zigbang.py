import requests
import json
import asyncio
from typing import List
from .base import BaseCrawler
from ..models.filter import FilterCondition
from ..models.property import PropertyItem
from ..utils.geohash import encode_geohash
from ..utils.price_parser import format_price

class ZigbangCrawler(BaseCrawler):
    """직방 매매 매물 수집기 (v1/house/property API 대응)"""
    
    BASE_URL = "https://apis.zigbang.com"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Origin": "https://www.zigbang.com",
        "Referer": "https://www.zigbang.com/home/villa/map",
        "x-zigbang-platform": "www",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    # 브라우저에서 획득한 세션 쿠키 (세션이 만료될 경우 갱신 필요)
    COOKIES = {
        "_zid": "88efeaa0-265b-11f1-97d9-67dc6ccdc3e2",
        "x-path": "/home/villa/map",
        "afUserId": "329c63a9-2c6b-4ebd-beba-f8a4c83c9bf3-p"
    }

    async def fetch(self, condition: FilterCondition) -> List[PropertyItem]:
        results: List[PropertyItem] = []
        
        # 위도/경도가 없으면 기본값(공덕동) 사용
        lat = condition.lat if condition.lat and condition.lat != 0 else 37.5443
        lng = condition.lng if condition.lng and condition.lng != 0 else 126.9510
        
        # Geohash 생성 (wydm8 등)
        ghash = encode_geohash(lat, lng, precision=5)
        
        for target_type in condition.property_types:
            service_path = "villas" if target_type == "빌라" else "officetels"
            list_url = f"{self.BASE_URL}/house/property/v1/items/{service_path}"
            params = {
                "geohash": ghash,
                "salesPriceMin": 0,
                "depositMin": 0,
                "rentMin": 0
            }
            
            try:
                # 쿠키와 헤더를 포함하여 요청
                resp = requests.get(list_url, params=params, headers=self.HEADERS, cookies=self.COOKIES, timeout=10)
                print(f"[ZigbangCrawler] List Request: {ghash} | Status: {resp.status_code}")
                
                if resp.status_code != 200: continue
                
                item_ids = resp.json().get("item_ids", [])
                if not item_ids:
                    # 지오해시 정밀도를 낮춰서 재시도 (wydm)
                    alt_ghash = ghash[:4]
                    params["geohash"] = alt_ghash
                    resp = requests.get(list_url, params=params, headers=self.HEADERS, cookies=self.COOKIES, timeout=10)
                    item_ids = resp.json().get("item_ids", [])
                    print(f"[ZigbangCrawler] Retry with {alt_ghash}: {len(item_ids)} found")

                if not item_ids: continue
                
                detail_url = f"{self.BASE_URL}/house/property/v1/items/list"
                batch_size = 50
                # 은행 여신 심사이므로 상위 100개 매물에 집중
                for i in range(0, min(len(item_ids), 100), batch_size): 
                    batch = item_ids[i:i+batch_size]
                    payload = {"item_ids": batch}
                    
                    detail_resp = requests.post(detail_url, json=payload, headers=self.HEADERS, cookies=self.COOKIES, timeout=10)
                    if detail_resp.status_code != 200: continue
                    
                    items = detail_resp.json().get("items", [])
                    for item in items:
                        # 매매(buy) 인지 확인
                        if item.get("sales_type") != "매매": continue
                        
                        price_min = item.get("sales_price", 0)
                        area = float(item.get("m2", 0))
                        
                        # 필터링
                        if condition.price_min and price_min < condition.price_min: continue
                        if condition.price_max and price_min > condition.price_max: continue
                        if condition.area_min and area < condition.area_min: continue
                        
                        prop = PropertyItem(
                            source="zigbang",
                            property_type=target_type,
                            name=item.get("title", "건물명 없음"),
                            address=item.get("address1", ""),
                            price=format_price(price_min), # 통일된 포맷터 사용
                            area=f"{area}",
                            floor=str(item.get("floor", "-")),
                            build_year=str(item.get("build_year", "-")),
                            description=item.get("description", ""),
                            url=f"https://www.zigbang.com/home/share/item/{item.get('item_id')}",
                            lat=float(item.get("lat", 0.0)),
                            lng=float(item.get("lng", 0.0))
                        )
                        results.append(prop)
                        
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                print(f"[ZigbangCrawler] Error: {e}")
                
        return results
