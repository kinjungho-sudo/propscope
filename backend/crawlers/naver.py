import requests
import json
import time
import asyncio
from typing import List
from .base import BaseCrawler
from ..models.filter import FilterCondition
from ..models.property import PropertyItem

class NaverCrawler(BaseCrawler):
    """네이버 부동산 매매 매물 수집기 (Requests 기반)"""
    
    BASE_URL = "https://new.land.naver.com/api/articles/complex"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://new.land.naver.com/"
    }

    async def fetch(self, condition: FilterCondition) -> List[PropertyItem]:
        results: List[PropertyItem] = []
        
        # Requests를 비동기 루프에서 실행하기 위해 run_in_executor 사용 가능하지만, 
        # 여기서는 간단하게 동기 요청 후 sleep으로 처리합니다. (기존 로직 유지)
        
        for target_type in condition.property_types:
            # 네이버 코드: VL(빌라), OR(오피스텔)
            estate_type = "VL" if target_type == "빌라" else "OR"
            
            # 최대 5페이지 (100건) 수집
            for p_num in range(1, 6):
                url = f"{self.BASE_URL}/{condition.region_code}?realEstateType={estate_type}&tradeType=A1&page={p_num}&pageSize=20"
                
                try:
                    resp = requests.get(url, headers=self.HEADERS, timeout=10)
                    print(f"[NaverCrawler] Request URL: {url} | Status: {resp.status_code}")
                    if resp.status_code != 200:
                        break
                        
                    data = resp.json()
                    articles = data.get("articleList", [])
                    if not articles:
                        break
                        
                    for art in articles:
                        # 가격 필터 (dealOrWarrantPrc 가 매매가)
                        price_man_str = art.get("dealOrWarrantPrc", "0").replace(",", "")
                        price_man = int(price_man_str) if price_man_str.isdigit() else 0
                        area = float(art.get("area1", "0"))
                        
                        # 필터링
                        if condition.price_min and price_man < condition.price_min: continue
                        if condition.price_max and price_man > condition.price_max: continue
                        if condition.area_min and area < condition.area_min: continue
                        if condition.area_max and area > condition.area_max: continue
                        
                        prop = PropertyItem(
                            source="naver",
                            property_type=target_type,
                            name=art.get("articleName", "건물명 없음"),
                            address=art.get("articleAddress", ""),
                            price=art.get("dealOrWarrantPrc", "0원"),
                            area=str(area),
                            floor=art.get("floorInfo", "-"),
                            build_year=art.get("useApproveYmd", "-")[:4],
                            description=art.get("articleFeatureDescription", ""),
                            url=f"https://new.land.naver.com/articles/{art.get('articleNo')}",
                            lat=float(art.get("lat", 0.0)),
                            lng=float(art.get("lng", 0.0))
                        )
                        results.append(prop)
                        
                    time.sleep(1.0) # CAPTCHA 방지
                    
                except Exception as e:
                    print(f"[NaverCrawler] Error: {e}")
                    break
                        
        return results
