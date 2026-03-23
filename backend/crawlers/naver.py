import requests
import asyncio
from typing import List
from datetime import datetime
from .base import BaseCrawler
from ..models.filter import FilterCondition
from ..models.property import PropertyItem
from ..utils.price_parser import parse_price, format_price

CURRENT_YEAR = datetime.now().year
NEW_BUILD_THRESHOLD = 5  # 준공 5년 이내 = 신축

def calc_pyung_price(price_man: int, area_m2: float) -> str:
    """㎡ 기준 면적으로 평당가 계산"""
    if area_m2 <= 0 or price_man <= 0:
        return "-"
    pyung = area_m2 / 3.3058
    per_pyung = int(price_man / pyung)
    return f"{per_pyung:,}만원/평"


class NaverCrawler(BaseCrawler):
    """네이버 부동산 매물 수집기 (requests 세션 방식)"""

    NAVER_BASE = "https://new.land.naver.com/api/articles"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://new.land.naver.com/",
        "Accept-Language": "ko-KR,ko;q=0.9"
    }

    async def fetch(self, condition: FilterCondition) -> List[PropertyItem]:
        results = []

        real_estate_types = []
        if "빌라" in condition.property_types:
            real_estate_types.extend(["VL", "DDDGG"])  # 빌라, 다세대
        if "오피스텔" in condition.property_types:
            real_estate_types.append("OR")             # 주거용 오피스텔

        if not real_estate_types:
            real_estate_types = ["VL", "DDDGG", "OR"]

        types_str = ":".join(real_estate_types)
        region_code = condition.region_code or "1144010200"

        session = requests.Session()
        session.headers.update(self.HEADERS)

        try:
            session.get("https://new.land.naver.com/main", timeout=10)
            await asyncio.sleep(0.5)
        except Exception:
            pass

        for page_num in range(1, 4):
            api_url = (
                f"{self.NAVER_BASE}/dong/{region_code}"
                f"?realEstateType={types_str}"
                f"&tradeType=A1"
                f"&tag=::::::::"
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
                resp = None
                for attempt in range(3):  # 최대 3회 재시도
                    resp = session.get(api_url, timeout=15)
                    print(f"[NaverCrawler] Page {page_num} attempt={attempt+1} Status: {resp.status_code}")
                    if resp.status_code == 429:
                        wait = (attempt + 1) * 3
                        print(f"[NaverCrawler] 429 Rate limit - waiting {wait}s...")
                        await asyncio.sleep(wait)
                        continue
                    break

                if resp.status_code == 200:
                    data = resp.json()
                    articles = data.get("articleList", [])
                    print(f"[NaverCrawler] Page {page_num}: {len(articles)}건")

                    for art in articles:
                        price_raw = art.get("dealOrWarrantPrice", art.get("dealPrice", "0"))
                        price_str_clean = price_raw.replace(",", "").strip() if isinstance(price_raw, str) else str(price_raw)
                        try:
                            price_man = int(price_str_clean)
                        except Exception:
                            price_man = 0

                        area_str = str(art.get("area2", "0"))
                        try:
                            area_m2 = float(area_str)
                        except Exception:
                            area_m2 = 0.0

                        # 준공연도 파싱 (여러 필드 순서대로 시도)
                        build_year = 0
                        build_year_str = "-"
                        for field in ["buildYear", "approveYear", "useApprovYmd"]:
                            raw = art.get(field, "")
                            if raw:
                                raw_str = str(raw)
                                try:
                                    yr = int(raw_str[:4])
                                    if 1950 <= yr <= 2030:
                                        build_year = yr
                                        build_year_str = str(yr)
                                        break
                                except Exception:
                                    pass


                        is_new = (build_year > 0 and (CURRENT_YEAR - build_year) <= NEW_BUILD_THRESHOLD)

                        prop_type_name = art.get("realEstateTypeName", "")
                        prop_type = "오피스텔" if "오피스텔" in prop_type_name else "빌라"

                        prop = PropertyItem(
                            source="naver",
                            property_type=prop_type,
                            name=art.get("articleName", "건물명 없음"),
                            address=art.get("areaName", ""),
                            price=format_price(price_man),
                            price_man=price_man,
                            price_per_pyung=calc_pyung_price(price_man, area_m2),
                            area=area_str,
                            floor=str(art.get("floorInfo", "-")),
                            build_year=build_year_str,
                            is_new=is_new,
                            description=art.get("articleFeatureDescription", ""),
                            url=f"https://new.land.naver.com/articles/{art.get('articleNo')}",
                            lat=float(art.get("lat", 0.0)),
                            lng=float(art.get("lng", 0.0))
                        )
                        results.append(prop)

                    if not articles:
                        break

                elif resp.status_code == 429:
                    print("[NaverCrawler] Rate limited (429). Stopping.")
                    break

            except Exception as e:
                print(f"[NaverCrawler] Page {page_num} Error: {e}")
                break

            await asyncio.sleep(1.5)

        print(f"[NaverCrawler] Total: {len(results)}")
        return results
