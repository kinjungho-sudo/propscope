import requests
import asyncio
from typing import List
from datetime import datetime
from .base import BaseCrawler
from ..models.filter import FilterCondition
from ..models.property import PropertyItem
from ..utils.geohash import encode_geohash
from ..utils.price_parser import format_price

CURRENT_YEAR = datetime.now().year
NEW_BUILD_THRESHOLD = 5


def calc_pyung_price(price_man: int, area_m2: float) -> str:
    if area_m2 <= 0 or price_man <= 0:
        return "-"
    pyung = area_m2 / 3.3058
    per_pyung = int(price_man / pyung)
    return f"{per_pyung:,}만원/평"


class ZigbangCrawler(BaseCrawler):
    """직방 매매 매물 수집기 (house/property v1 API)"""

    BASE_URL = "https://apis.zigbang.com"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Origin": "https://www.zigbang.com",
        "Referer": "https://www.zigbang.com/home/villa/map",
        "x-zigbang-platform": "www",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ko-KR,ko;q=0.9"
    }
    COOKIES = {
        "_zid": "88efeaa0-265b-11f1-97d9-67dc6ccdc3e2",
        "afUserId": "329c63a9-2c6b-4ebd-beba-f8a4c83c9bf3-p"
    }

    async def fetch(self, condition: FilterCondition) -> List[PropertyItem]:
        results: List[PropertyItem] = []

        lat = condition.lat if condition.lat and condition.lat != 0 else 37.5443
        lng = condition.lng if condition.lng and condition.lng != 0 else 126.9510

        # precision=5 → 약 4.9km²; 결과 없으면 4(약 39km²)로 확장
        for precision in [5, 4]:
            ghash = encode_geohash(lat, lng, precision=precision)

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
                    resp = requests.get(
                        list_url, params=params,
                        headers=self.HEADERS, cookies=self.COOKIES, timeout=10
                    )
                    print(f"[ZigbangCrawler] {target_type} | geohash={ghash} | status={resp.status_code}")

                    if resp.status_code != 200:
                        continue

                    item_ids = resp.json().get("item_ids", [])
                    print(f"[ZigbangCrawler] Found {len(item_ids)} IDs")

                    if not item_ids:
                        continue

                    # 상세 조회 (50개 배치)
                    detail_url = f"{self.BASE_URL}/house/property/v1/items/list"
                    for i in range(0, min(len(item_ids), 100), 50):
                        batch = item_ids[i:i + 50]
                        detail_resp = requests.post(
                            detail_url, json={"item_ids": batch},
                            headers=self.HEADERS, cookies=self.COOKIES, timeout=10
                        )
                        if detail_resp.status_code != 200:
                            continue

                        for item in detail_resp.json().get("items", []):
                            if item.get("sales_type") != "매매":
                                continue

                            price_man = item.get("sales_price", 0)
                            area_m2 = float(item.get("m2", 0))

                            # 필터 적용
                            if condition.price_min and price_man < condition.price_min:
                                continue
                            if condition.price_max and price_man > condition.price_max:
                                continue
                            if condition.area_min and area_m2 < condition.area_min:
                                continue

                            # 준공연도 / 신축 판단
                            build_year_raw = item.get("build_year", "-")
                            try:
                                build_year_int = int(str(build_year_raw))
                                is_new = (CURRENT_YEAR - build_year_int) <= NEW_BUILD_THRESHOLD
                            except Exception:
                                build_year_int = 0
                                is_new = False

                            prop = PropertyItem(
                                source="zigbang",
                                property_type=target_type,
                                name=item.get("title", "건물명 없음"),
                                address=item.get("address1", ""),
                                price=format_price(price_man),
                                price_man=price_man,
                                price_per_pyung=calc_pyung_price(price_man, area_m2),
                                area=str(area_m2),
                                floor=str(item.get("floor", "-")),
                                build_year=str(build_year_raw),
                                is_new=is_new,
                                description=item.get("description", ""),
                                url=f"https://www.zigbang.com/home/share/item/{item.get('item_id')}",
                                lat=float(item.get("lat", 0.0)),
                                lng=float(item.get("lng", 0.0))
                            )
                            results.append(prop)

                        await asyncio.sleep(0.5)

                except Exception as e:
                    print(f"[ZigbangCrawler] Error: {e}")

            # 매물이 생기면 정밀도 낮춰서 재시도 안 해도 됨
            if results:
                break

        print(f"[ZigbangCrawler] Total: {len(results)}")
        return results
