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

    def _get_session(self) -> requests.Session:
        """직방 메인 접속으로 쿠키 자동 획득"""
        sess = requests.Session()
        sess.headers.update(self.HEADERS)
        try:
            sess.get("https://www.zigbang.com", timeout=8)
            print("[ZigbangCrawler] Session cookies acquired")
        except Exception as e:
            print(f"[ZigbangCrawler] Session init failed: {e}")
        return sess

    async def fetch(self, condition: FilterCondition) -> List[PropertyItem]:
        results: List[PropertyItem] = []

        lat = condition.lat if condition.lat and condition.lat != 0 else 37.5443
        lng = condition.lng if condition.lng and condition.lng != 0 else 126.9510
        session = self._get_session()

        # precision 4 → 3 으로 확장 시도 (5는 셀이 너무 좁아 매물 없을 수 있음)
        for precision in [4, 3]:
            ghash = encode_geohash(lat, lng, precision=precision)

            for target_type in condition.property_types:
                service_path = "villas" if target_type == "빌라" else "officetels"
                list_url = f"{self.BASE_URL}/house/property/v1/items/{service_path}"
                params = {
                    "geohash": ghash,
                    "salesType": "매매",
                    "salesPriceMin": condition.price_min or 0,
                    "salesPriceMax": condition.price_max or 0,
                    "depositMin": 0,
                    "rentMin": 0
                }

                try:
                    resp = session.get(list_url, params=params, timeout=10)
                    print(f"[ZigbangCrawler] {target_type} | precision={precision} geohash={ghash} | status={resp.status_code}")

                    if resp.status_code != 200:
                        continue

                    resp_data = resp.json()

                    # ✅ 신 API: items=[{id, lat, lng}, ...]
                    # ✅ 구 API: item_ids=[...] (fallback)
                    raw_items = resp_data.get("items", [])
                    if raw_items:
                        # 반경 필터: 목표 좌표에서 ±0.05도 (약 5km) 이내만 사용
                        def in_range(it):
                            return (abs(it.get("lat", 0) - lat) < 0.05 and
                                    abs(it.get("lng", 0) - lng) < 0.05)
                        item_ids = [it["id"] for it in raw_items if in_range(it)]
                    else:
                        item_ids = resp_data.get("item_ids", [])

                    print(f"[ZigbangCrawler] IDs (after geo-filter): {len(item_ids)}")

                    if not item_ids:
                        continue

                    # 상세 조회 (50개 배치, 최대 150개)
                    detail_url = f"{self.BASE_URL}/house/property/v1/items/list"
                    for i in range(0, min(len(item_ids), 150), 50):
                        batch = item_ids[i:i + 50]
                        detail_resp = session.post(
                            detail_url, json={"item_ids": batch}, timeout=10
                        )
                        if detail_resp.status_code != 200:
                            print(f"[ZigbangCrawler] detail status={detail_resp.status_code}")
                            continue

                        for item in detail_resp.json().get("items", []):
                            if item.get("sales_type") != "매매":
                                continue

                            price_man = item.get("sales_price", 0)
                            area_m2 = float(item.get("m2", 0))

                            # 가격/면적 필터
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

                            item_id = item.get("item_id") or item.get("id", "")
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
                                url=f"https://www.zigbang.com/home/share/item/{item_id}",
                                lat=float(item.get("lat", 0.0)),
                                lng=float(item.get("lng", 0.0))
                            )
                            results.append(prop)

                        await asyncio.sleep(0.3)

                except Exception as e:
                    print(f"[ZigbangCrawler] Error: {e}")

            if results:
                break

        print(f"[ZigbangCrawler] Total: {len(results)}")
        return results
