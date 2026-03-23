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

# 구 단위 법정동코드 (5자리)
GU_CODE_MAP = {
    "종로구": "11110", "중구": "11140", "용산구": "11230", "성동구": "11215",
    "광진구": "11215", "동대문구": "11210", "중랑구": "11260", "성북구": "11290",
    "강북구": "11305", "도봉구": "11320", "노원구": "11350", "은평구": "11380",
    "서대문구": "11140", "마포구": "11440", "양천구": "11470", "강서구": "11500",
    "구로구": "11530", "금천구": "11545", "영등포구": "11560", "동작구": "11590",
    "관악구": "11620", "서초구": "11650", "강남구": "11680", "송파구": "11710",
    "강동구": "11740",
}

# 동 → 구 매핑
DONG_TO_GU = {
    "공덕동": "마포구", "서교동": "마포구", "합정동": "마포구", "망원동": "마포구",
    "연남동": "마포구", "성산동": "마포구", "상암동": "마포구", "아현동": "마포구",
    "동교동": "마포구", "대흥동": "마포구", "염리동": "마포구", "도화동": "마포구",
    "용강동": "마포구", "마포동": "마포구", "신수동": "마포구", "창전동": "마포구",
    "역삼동": "강남구", "삼성동": "강남구", "논현동": "강남구", "청담동": "강남구",
    "대치동": "강남구", "압구정동": "강남구", "개포동": "강남구", "도곡동": "강남구",
    "서초동": "서초구", "방배동": "서초구", "잠원동": "서초구", "반포동": "서초구",
    "양재동": "서초구",
    "잠실동": "송파구", "가락동": "송파구", "문정동": "송파구", "방이동": "송파구",
    "풍납동": "송파구", "거여동": "송파구",
    "이태원동": "용산구", "한남동": "용산구", "후암동": "용산구", "청파동": "용산구",
    "보광동": "용산구", "남영동": "용산구",
    "성수동": "성동구", "왕십리동": "성동구", "금호동": "성동구", "옥수동": "성동구",
    "행당동": "성동구",
    "흑석동": "동작구", "상도동": "동작구", "노량진동": "동작구", "대방동": "동작구",
    "신림동": "관악구", "봉천동": "관악구",
    "여의도동": "영등포구", "당산동": "영등포구", "문래동": "영등포구",
    "화곡동": "강서구", "마곡동": "강서구", "발산동": "강서구",
    "신촌동": "서대문구", "홍제동": "서대문구", "홍은동": "서대문구",
    "연희동": "서대문구", "남가좌동": "서대문구", "북가좌동": "서대문구",
    "상계동": "노원구", "중계동": "노원구", "하계동": "노원구", "공릉동": "노원구",
    "창동": "도봉구", "도봉동": "도봉구", "방학동": "도봉구",
    "수유동": "강북구", "미아동": "강북구", "번동": "강북구",
    "구로동": "구로구", "신도림동": "구로구", "개봉동": "구로구",
    "독산동": "금천구", "가산동": "금천구", "시흥동": "금천구",
    "목동": "양천구", "신정동": "양천구",
    "면목동": "중랑구", "상봉동": "중랑구",
    "전농동": "동대문구", "답십리동": "동대문구", "장안동": "동대문구",
    "신당동": "중구", "황학동": "중구",
    "성수동1가": "성동구", "성수동2가": "성동구",
}


def get_gu_code(region_name: str) -> str:
    """지역명에서 구 코드(5자리) 추출"""
    # 구 직접 매핑
    for gu, code in GU_CODE_MAP.items():
        if gu in region_name:
            return code
    # 동 → 구 → 코드
    for dong, gu in DONG_TO_GU.items():
        if dong in region_name:
            return GU_CODE_MAP.get(gu, "11440")
    return "11440"  # 기본값: 마포구


def calc_pyung_price(price_man: int, area_m2: float) -> str:
    if area_m2 <= 0 or price_man <= 0:
        return "-"
    per_pyung = int(price_man / (area_m2 / 3.3058))
    return f"{per_pyung:,}만원/평"


def get_sample_data(condition: FilterCondition) -> List[PropertyItem]:
    """API 미활성화 시 샘플 데이터 반환 (UI 확인용)"""
    samples = [
        {"name": "공덕 한신휴플러스", "dong": "공덕동", "price_man": 45000, "area_m2": 59.9, "floor": "4", "build_year": "2008", "is_new": False},
        {"name": "공덕 래미안", "dong": "공덕동", "price_man": 52000, "area_m2": 84.2, "floor": "7", "build_year": "2012", "is_new": False},
        {"name": "마포 신축빌라", "dong": "아현동", "price_man": 38000, "area_m2": 49.5, "floor": "2", "build_year": "2021", "is_new": True},
        {"name": "공덕 신영지웰", "dong": "공덕동", "price_man": 61000, "area_m2": 101.2, "floor": "9", "build_year": "2015", "is_new": False},
        {"name": "마포 아현역 1단지", "dong": "아현동", "price_man": 41500, "area_m2": 55.6, "floor": "3", "build_year": "2004", "is_new": False},
        {"name": "공덕 현대오피스텔", "dong": "공덕동", "price_man": 28000, "area_m2": 33.0, "floor": "6", "build_year": "2019", "is_new": True},
        {"name": "마포 성산시영", "dong": "성산동", "price_man": 55000, "area_m2": 76.8, "floor": "5", "build_year": "1993", "is_new": False},
        {"name": "공덕 신축다세대", "dong": "공덕동", "price_man": 33000, "area_m2": 42.1, "floor": "2", "build_year": "2022", "is_new": True},
    ]
    results = []
    for s in samples:
        price_man = s["price_man"]
        area_m2 = s["area_m2"]
        build_year = int(s["build_year"])
        results.append(PropertyItem(
            source="molit",
            property_type="빌라",
            name=s["name"],
            address=f"서울 마포구 {s['dong']}",
            price=format_price(price_man),
            price_man=price_man,
            price_per_pyung=calc_pyung_price(price_man, area_m2),
            area=str(area_m2),
            floor=s["floor"],
            build_year=s["build_year"],
            is_new=s["is_new"],
            description="[샘플] 실거래가 API 키 활성화 대기 중",
            url="https://rt.molit.go.kr",
            lat=37.5443 + (hash(s["name"]) % 100) * 0.0005,
            lng=126.9510 + (hash(s["dong"]) % 100) * 0.0005
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
        gu_code = get_gu_code(condition.region_name)
        dong_filter = condition.region_name  # 동 이름 필터링용

        today = date.today()
        # 최근 6개월 데이터
        months = []
        for i in range(6):
            m = today.month - i
            y = today.year
            if m <= 0:
                m += 12
                y -= 1
            months.append(f"{y}{m:02d}")

        for prop_type in condition.property_types:
            endpoint = self.ENDPOINTS.get(prop_type, "getRTMSDataSvcRHTrade")
            url = f"{self.BASE_URL}/{endpoint}"

            for deal_ymd in months:
                params = {
                    "serviceKey": self.api_key,
                    "LAWD_CD": gu_code,
                    "DEAL_YMD": deal_ymd,
                    "numOfRows": "100",
                    "pageNo": "1",
                    "_type": "json"
                }

                try:
                    resp = requests.get(url, params=params, timeout=15)
                    print(f"[MolitCrawler] {prop_type} {deal_ymd} gu={gu_code} status={resp.status_code}")

                    if resp.status_code != 200:
                        continue

                    body = resp.json().get("response", {}).get("body", {})
                    item_list = parse_molit_items(body.get("items", {}))
                    print(f"[MolitCrawler] {deal_ymd}: {len(item_list)}건")

                    for item in item_list:
                        # 동 필터 - 검색한 동이 있으면 해당 동만
                        dong_name = str(item.get("법정동", item.get("umdNm", ""))).strip()
                        # 동 단위 검색 시 해당 동만 포함
                        dong_keywords = [k for k in DONG_TO_GU.keys() if k in dong_filter]
                        if dong_keywords and dong_name not in dong_keywords:
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

                except Exception as e:
                    print(f"[MolitCrawler] Error {deal_ymd}: {e}")

                await asyncio.sleep(0.3)

        print(f"[MolitCrawler] Total: {len(results)}")
        return results
