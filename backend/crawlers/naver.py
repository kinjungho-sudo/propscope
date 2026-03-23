import requests
import asyncio
from typing import List
from .base import BaseCrawler
from ..models.filter import FilterCondition
from ..models.property import PropertyItem

class NaverCrawler(BaseCrawler):
    """네이버 부동산 매물 수집기 (Playwright 활용 버전)"""
    
    BASE_URL = "https://new.land.naver.com/api/articles"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://new.land.naver.com/main"
    }

    async def fetch(self, condition: FilterCondition) -> List[PropertyItem]:
        # Playwright를 사용하여 실제 브라우저 환경에서 데이터 수집
        # 이는 429 에러를 방지하고 토큰 문제를 해결하기 위함입니다.
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("[NaverCrawler] Playwright not installed. Falling back to simple requests (likely to fail).")
            return await self._fetch_via_requests(condition)

        results = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # 네이버 부동산 메인 접속하여 세션 생성
            await page.goto("https://new.land.naver.com/main", wait_until="networkidle")
            
            # 검색 API URL 생성
            # 매매(A1), 빌라(VL), 오피스텔(OR)
            real_estate_types = []
            if "빌라" in condition.property_types: real_estate_types.append("VL")
            if "오피스텔" in condition.property_types: real_estate_types.append("OR")
            
            types_str = "%3A".join(real_estate_types)
            
            # API 직접 호출 (Playwright 내부 fetch 권장)
            for page_num in range(1, 4): # 너무 많이 가져오면 느리므로 3페이지 상한
                api_url = f"{self.BASE_URL}/dong/{condition.region_code}?realEstateType={types_str}&tradeType=A1&tag=%3A%3A%3A%3A%3A%3A%3A%3A&rentPriceMin=0&rentPriceMax=900000000&priceMin=0&priceMax=900000000&areaMin=0&areaMax=900000000&oldBuildYears&recentlyBuildYears&minHouseHoldCount&maxHouseHoldCount&showArticle=false&sameAddressGroup=false&minMaintenanceCost&maxMaintenanceCost&directions=&page={page_num}&articleListVO=articleList"
                
                try:
                    # evaluate를 사용하여 브라우저 컨텍스트 내에서 fetch 호출 (토큰 자동 포함)
                    response_json = await page.evaluate(f"""
                        async () => {{
                            const resp = await fetch('{api_url}');
                            return await resp.json();
                        }}
                    """)
                    
                    articles = response_json.get("articleList", [])
                    print(f"[NaverCrawler] Page {page_num} Collected: {len(articles)}")
                    
                    for art in articles:
                        price = art.get("dealPrice", "0")
                        # 억 단위 포맷팅
                        price_int = int(price.replace(",", "")) if isinstance(price, str) else price
                        price_str = f"{price_int // 10000}억 {price_int % 10000:,}만원" if price_int >= 10000 else f"{price_int:,}만원"
                        
                        prop = PropertyItem(
                            source="naver",
                            property_type="빌라" if art.get("realEstateTypeName") == "빌라" else "오피스텔",
                            name=art.get("articleName", "건물명 없음"),
                            address=art.get("areaName", ""), # 상세 주소는 기밀인 경우가 많음
                            price=price_str,
                            area=str(art.get("area2", "0")), # 전용면적
                            floor=f"{art.get('floorInfo', '')}",
                            build_year=art.get("isRepart", "-"), # 준공연도 정보가 없는 경우 대체
                            description=f"{art.get('articleFeatureDescription', '')}",
                            url=f"https://finland.naver.com/articles/{art.get('articleNo')}",
                            lat=float(art.get("lat", 0.0)),
                            lng=float(art.get("lng", 0.0))
                        )
                        results.append(prop)
                        
                    if not articles: break
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"[NaverCrawler] Page {page_num} Error: {e}")
                    break
                    
            await browser.close()
        return results

    async def _fetch_via_requests(self, condition: FilterCondition) -> List[PropertyItem]:
        # 기존 Requests 방식 (Fallback)
        # 429 에러 발생 가능성 높음
        return []
