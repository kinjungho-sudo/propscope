import requests
import json
import time
from typing import List
from .base import BaseCrawler
from ..models.filter import FilterCondition
from ..models.property import PropertyItem

class ZigbangCrawler(BaseCrawler):
    """직방 매매 매물 수집기"""
    
    BASE_URL = "https://apis.zigbang.com"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    async def fetch(self, condition: FilterCondition) -> List[PropertyItem]:
        results: List[PropertyItem] = []
        
        # 빌라, 오피스텔 각각 요청
        for target_type in condition.property_types:
            service_type = "villa" if target_type == "빌라" else "officetel"
            
            # 위도/경도가 없으면 기본값(공덕동) 사용
            lat = condition.lat if condition.lat and condition.lat != 0 else 37.5443
            lng = condition.lng if condition.lng and condition.lng != 0 else 126.9510
            
            # Step 1: 위도/경도 기반 매물 ID 목록 수집
            url_list = f"{self.BASE_URL}/v2/items/geo-items"
            params = {
                "serviceType": service_type,
                "transactionType": "buy",
                "lat": lat,
                "lng": lng,
                "radius": 1000,
                "zoom": 15
            }
            
            try:
                resp = requests.get(url_list, params=params, headers=self.HEADERS)
                print(f"[ZigbangCrawler] Geo-items URL: {url_list} | Status: {resp.status_code}")
                if resp.status_code != 200:
                    continue
                
                item_ids = resp.json().get("itemIds", [])
                if not item_ids:
                    continue
                    
                # Step 2: 100건씩 상세 정보 조회
                batch_size = 100
                for i in range(0, len(item_ids), batch_size):
                    batch_ids = item_ids[i:i+batch_size]
                    url_detail = f"{self.BASE_URL}/v2/items"
                    detail_params = {
                        "serviceType": service_type,
                        "itemIds": ",".join(map(str, batch_ids))
                    }
                    
                    detail_resp = requests.get(url_detail, params=detail_params, headers=self.HEADERS)
                    if detail_resp.status_code != 200:
                        continue
                        
                    items = detail_resp.json().get("items", [])
                    for item in items:
                        # 필터링 적용 (가격, 면적 등)
                        price = item.get("price", 0)
                        area = item.get("m2", 0)
                        
                        if condition.price_min and price < condition.price_min: continue
                        if condition.price_max and price > condition.price_max: continue
                        if condition.area_min and area < condition.area_min: continue
                        if condition.area_max and area > condition.area_max: continue
                        
                        # PropertyItem 변환
                        prop = PropertyItem(
                            source="zigbang",
                            property_type=target_type,
                            name=item.get("title", "건물명 없음"),
                            address=item.get("address1", ""),
                            price=f"{price // 10000}억 {price % 10000:,}만원" if price >= 10000 else f"{price:,}만원",
                            area=f"{area}",
                            floor=str(item.get("floor", "저/고")),
                            build_year=str(item.get("build_year", "-")),
                            description=item.get("description", ""),
                            url=f"https://www.zigbang.com/home/share/item/{item.get('itemId')}",
                            lat=item.get("lat", 0.0),
                            lng=item.get("lng", 0.0)
                        )
                        results.append(prop)
                        
                    time.sleep(0.5) # CAPTCHA 방지
                    
            except Exception as e:
                print(f"[ZigbangCrawler] Error: {e}")
                
        return results
