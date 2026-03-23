"""
국토교통부 실거래가 API 크롤러
- 연립다세대 매매: getRTMSDataSvcRHTrade
- 오피스텔 매매:  getRTMSDataSvcOffiTrade
API 키: https://www.data.go.kr 에서 무료 즉시 발급
"""
import requests
import asyncio
from typing import List, Union
from datetime import datetime, date
import os

from .base import BaseCrawler
from ..models.filter import FilterCondition
from ..models.property import PropertyItem
from ..utils.price_parser import format_price

CURRENT_YEAR = datetime.now().year
NEW_BUILD_THRESHOLD = 5

# ── 기존 정적 매핑 제거 (법정동코드 직접 활용) ──


def calc_pyung_price(price_man: int, area_m2: float) -> str:
    if area_m2 <= 0 or price_man <= 0:
        return "-"
    per_pyung = int(price_man / (area_m2 / 3.3058))
    return f"{per_pyung:,}만원/평"


def get_sample_data(condition: FilterCondition) -> List[PropertyItem]:
    """API 미활성화 시 현재 검색 지역에 맞는 샘플 데이터 생성"""
    region = condition.region_name
    samples = [
        {"name": f"{region} 래미안", "price_man": 125000, "area_m2": 84.9, "floor": "12", "build_year": "2015"},
        {"name": f"{region} 자이", "price_man": 138000, "area_m2": 84.8, "floor": "8", "build_year": "2018"},
        {"name": f"{region} 힐스테이트", "price_man": 112000, "area_m2": 59.9, "floor": "5", "build_year": "2012"},
        {"name": f"{region} 푸르지오", "price_man": 98000, "area_m2": 59.7, "floor": "15", "build_year": "2010"},
        {"name": f"{region} 신축빌라", "price_man": 45000, "area_m2": 42.5, "floor": "3", "build_year": "2023"},
        {"name": f"{region} 오피스텔", "price_man": 28000, "area_m2": 33.2, "floor": "10", "build_year": "2021"},
    ]
    results = []
    import random
    for i, s in enumerate(samples):
        price_man = s["price_man"]
        area_m2 = s["area_m2"]
        results.append(PropertyItem(
            source="molit",
            property_type="빌라" if "빌라" in s["name"] else "오피스텔" if "오피스텔" in s["name"] else "빌라",
            name=s["name"],
            address=f"서울 {region} {i+1}번지",
            price=format_price(price_man),
            price_man=price_man,
            price_per_pyung=calc_pyung_price(price_man, area_m2),
            area=str(area_m2),
            floor=s["floor"],
            build_year=s["build_year"],
            is_new=int(s["build_year"]) >= (CURRENT_YEAR - NEW_BUILD_THRESHOLD),
            description="[샘플 데이터] 실제 데이터 수집 중 문제가 발생하여 표시되는 데이터입니다.",
            url="https://rt.molit.go.kr",
            lat=condition.lat + (random.random() - 0.5) * 0.01,
            lng=condition.lng + (random.random() - 0.5) * 0.01
        ))
    return results


def parse_molit_items(raw: Union[dict, list]) -> list:
    """MOLIT API items 필드를 안전하게 리스트로 변환"""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        item = raw.get("item", [])
        if isinstance(item, dict):
            return [item]
        return item if isinstance(item, list) else []
    return []


class MolitCrawler(BaseCrawler):
    """국토교통부 실거래가 API 크롤러"""

    BASE_URL = "https://apis.data.go.kr/1613000/RTMSOBJSvc"
    ENDPOINTS = {
        "빌라": "getRTMSDataSvcRHTrade",
        "오피스텔": "getRTMSDataSvcOffiTrade",
    }

    def __init__(self):
        self.api_key = os.getenv("MOLIT_API_KEY", "")

    async def fetch(self, condition: FilterCondition) -> List[PropertyItem]:
        if not self.api_key:
            print("[MolitCrawler] MOLIT_API_KEY 없음 → 샘플 데이터 반환")
            return get_sample_data(condition)

        # API 활성화 확인 (첫 요청으로 테스트)
        test_url = (
            f"{self.BASE_URL}/getRTMSDataSvcRHTrade"
            f"?serviceKey={self.api_key}&LAWD_CD=11440&DEAL_YMD=202502&numOfRows=1&pageNo=1&_type=json"
        )
        try:
            test_resp = requests.get(test_url, timeout=10)
            if test_resp.status_code != 200:
                print(f"[MolitCrawler] API 미활성화 (status={test_resp.status_code}) → 샘플 데이터 반환")
                return get_sample_data(condition)
        except Exception as e:
            print(f"[MolitCrawler] API 연결 실패: {e} → 샘플 데이터")
            return get_sample_data(condition)

        results = []
        # 시군구 코드 (10자리 법정동코드의 앞 5자리)
        gu_code = condition.region_code[:5] if condition.region_code else "11440"
        
        # 최근 12개월 데이터 (현재 달은 데이터가 없으므로 전달부터 수집)
        months = []
        for i in range(1, 13):
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            months.append(f"{y}{m:02d}")

        for prop_type in condition.property_types:
            endpoint = self.ENDPOINTS.get(prop_type, "getRTMSDataSvcRHTrade")
            url = f"{self.BASE_URL}/{endpoint}"

            for deal_ymd in months:
                page_no = 1
                while True:
                    params = {
                        "serviceKey": self.api_key,
                        "LAWD_CD": gu_code,
                        "DEAL_YMD": deal_ymd,
                        "numOfRows": "100",
                        "pageNo": str(page_no),
                        "_type": "json"
                    }

                    try:
                        resp = requests.get(url, params=params, timeout=15)
                        if resp.status_code != 200:
                            break

                        res_json = resp.json()
                        body = res_json.get("response", {}).get("body", {})
                        total_count = body.get("totalCount", 0)
                        item_list = parse_molit_items(body.get("items", {}))
                        
                        if not item_list:
                            break

                        print(f"[MolitCrawler] {prop_type} {deal_ymd} p{page_no}: {len(item_list)}건 / 총 {total_count}건")

                        dong_filter = condition.region_name
                        for item in item_list:
                            # 동 필터 - 검색한 동이 있으면 해당 동만
                            dong_name = str(item.get("법정동", item.get("umdNm", ""))).strip()
                            
                            # 검색어가 동 이름에 포함되거나, 동 이름이 검색어에 포함되는지 확인 (예: "역삼동" vs "역삼동")
                            if dong_filter and (dong_name not in dong_filter and dong_filter not in dong_name):
                                continue

                            # 가격
                            price_raw = str(item.get("거래금액", item.get("dealAmount", "0"))).replace(",", "").strip()
                            try:
                                price_man = int(price_raw)
                            except Exception:
                                price_man = 0

                            if price_man <= 0:
                                continue

                            # 면적
                            area_raw = str(item.get("전용면적", item.get("excluUseAr", "0"))).strip()
                            try:
                                area_m2 = float(area_raw)
                            except Exception:
                                area_m2 = 0.0

                            # 가격/면적 필터
                            if condition.price_min and price_man < condition.price_min:
                                continue
                            if condition.price_max and price_man > condition.price_max:
                                continue
                            if condition.area_min and area_m2 < condition.area_min:
                                continue

                            # 건축연도
                            build_year_raw = str(item.get("건축년도", item.get("buildYear", "0"))).strip()
                            try:
                                build_year = int(build_year_raw)
                                is_new = 0 < build_year and (CURRENT_YEAR - build_year) <= NEW_BUILD_THRESHOLD
                            except Exception:
                                build_year = 0
                                is_new = False

                            # 준공연도 필터
                            if condition.build_year_min and build_year > 0 and build_year < condition.build_year_min:
                                continue

                            # 거래날짜 및 주소
                            deal_y = str(item.get("년", item.get("dealYear", ""))).strip()
                            deal_m = str(item.get("월", item.get("dealMonth", ""))).strip().zfill(2)
                            deal_d = str(item.get("일", item.get("dealDay", ""))).strip().zfill(2)
                            road_nm = str(item.get("도로명", item.get("roadNm", ""))).strip()
                            floor_raw = str(item.get("층", item.get("floor", "-"))).strip()

                            # 건물명 (연립다세대 vs 오피스텔)
                            bld_name = (
                                item.get("연립다세대") or
                                item.get("아파트") or
                                item.get("단지명") or
                                item.get("offiNm") or
                                dong_name + " 매물"
                            )

                            address = f"서울 {dong_filter} {dong_name}"
                            if road_nm:
                                address += f" {road_nm}"

                            prop = PropertyItem(
                                source="molit",
                                property_type=prop_type,
                                name=str(bld_name).strip(),
                                address=address.strip(),
                                price=format_price(price_man),
                                price_man=price_man,
                                price_per_pyung=calc_pyung_price(price_man, area_m2),
                                area=str(area_m2),
                                floor=floor_raw,
                                build_year=build_year_raw if build_year > 0 else "-",
                                is_new=is_new,
                                description=f"실거래 {deal_y}.{deal_m}.{deal_d}",
                                url="https://rt.molit.go.kr",
                                lat=0.0,
                                lng=0.0
                            )
                            results.append(prop)

                        # 다음 페이지 확인
                        if page_no * 100 >= total_count or page_no >= 10:
                            break
                        page_no += 1

                    except Exception as e:
                        print(f"[MolitCrawler] Error {deal_ymd} p{page_no}: {e}")
                        break

                    await asyncio.sleep(0.3)

        print(f"[MolitCrawler] Total: {len(results)}")
        return results
