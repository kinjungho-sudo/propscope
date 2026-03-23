import requests
import asyncio
from typing import List
from .base import BaseCrawler
from ..models.filter import FilterCondition
from ..models.property import PropertyItem
from ..utils.price_parser import format_price

class NaverCrawler(BaseCrawler):
    """네이버 부동산 실거래가 수집기 (국토교통부 실거래가 공공 API 활용)"""

    # 국토교통부 실거래가 공개시스템 (인증 불필요, 공공 데이터)
    # 빌라/다세대: 연립다세대 실거래가
    # Zigbang에서 현재 데이터를 더 잘 가져오므로 Naver는 공개 API 사용
    RTK_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcRHRent/getRTMSDataSvcRHRent"
    VILLA_DEAL_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcSLRhTrade/getRTMSDataSvcSLRhTrade"
    
    # 네이버 부동산 직접 API
    NAVER_BASE = "https://new.land.naver.com/api/articles"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://new.land.naver.com/",
        "Accept-Language": "ko-KR,ko;q=0.9"
    }

    async def fetch(self, condition: FilterCondition) -> List[PropertyItem]:
        """네이버 부동산 API를 통해 매물 수집 (requests 기반, 세션 우회)"""
        results = []
        
        real_estate_types = []
        if "빌라" in condition.property_types:
            real_estate_types.extend(["VL", "DDDGG"])
        if "오피스텔" in condition.property_types:
            real_estate_types.append("OR")
        
        if not real_estate_types:
            real_estate_types = ["VL", "DDDGG", "OR"]
        
        types_str = ":".join(real_estate_types)
        region_code = condition.region_code or "1168010800"  # 기본: 공덕동
        
        # 세션 획득 후 API 호출
        session = requests.Session()
        session.headers.update(self.HEADERS)
        
        try:
            # 먼저 메인 페이지 방문 (쿠키/세션 획득)
            session.get("https://new.land.naver.com/main", timeout=10)
            await asyncio.sleep(0.5)
        except:
            pass

        for page_num in range(1, 4):
            api_url = (
                f"{self.NAVER_BASE}/dong/{region_code}"
                f"?realEstateType={types_str}"
                f"&tradeType=A1"  # A1 = 매매
                f"&tag=:::::::: "
                f"&rentPriceMin=0&rentPriceMax=900000000"
                f"&priceMin={condition.price_min or 0}"
                f"&priceMax={condition.price_max or 900000000}"
                f"&areaMin={int(condition.area_min or 0)}"
                f"&areaMax={int(condition.area_max or 900000000)}"
                f"&oldBuildYears&recentlyBuildYears"
                f"&minHouseHoldCount&maxHouseHoldCount"
                f"&showArticle=false&sameAddressGroup=false"
                f"&minMaintenanceCost&maxMaintenanceCost"
                f"&directions=&page={page_num}&articleListVO=articleList"
            )
            
            try:
                resp = session.get(api_url, timeout=15)
                print(f"[NaverCrawler] Page {page_num} Status: {resp.status_code}")
                
                if resp.status_code == 200:
                    data = resp.json()
                    articles = data.get("articleList", [])
                    print(f"[NaverCrawler] Page {page_num}: {len(articles)}건 수집")
                    
                    for art in articles:
                        price = art.get("dealOrWarrantPrice", art.get("dealPrice", "0"))
                        price_str = price.replace(",", "").strip() if isinstance(price, str) else str(price)
                        try:
                            price_val = int(price_str)
                        except:
                            price_val = 0
                        
                        prop_type_name = art.get("realEstateTypeName", "")
                        if "오피스텔" in prop_type_name:
                            prop_type = "오피스텔"
                        else:
                            prop_type = "빌라"
                        
                        prop = PropertyItem(
                            source="naver",
                            property_type=prop_type,
                            name=art.get("articleName", "건물명 없음"),
                            address=art.get("areaName", ""),
                            price=format_price(price_val),
                            area=str(art.get("area2", "0")),
                            floor=str(art.get("floorInfo", "-")),
                            build_year=str(art.get("buildingName", "-")),
                            description=art.get("articleFeatureDescription", ""),
                            url=f"https://new.land.naver.com/articles/{art.get('articleNo')}",
                            lat=float(art.get("lat", 0.0)),
                            lng=float(art.get("lng", 0.0))
                        )
                        results.append(prop)
                    
                    if not articles:
                        break
                        
                elif resp.status_code == 429:
                    print(f"[NaverCrawler] Rate limited (429). Stopping.")
                    break
                    
            except Exception as e:
                print(f"[NaverCrawler] Page {page_num} Error: {e}")
                break
            
            await asyncio.sleep(1.5)
        
        print(f"[NaverCrawler] Total collected: {len(results)}")
        return results
