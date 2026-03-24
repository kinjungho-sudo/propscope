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
        results = []
        # 시군구 코드 (10자리 법정동코드의 앞 5자리)
        gu_code = condition.region_code[:5] if condition.region_code else "11440"
        
        # 최근 36개월 (3년) 데이터 수집
        months = []
        for i in range(1, 37):
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            months.append(f"{y}{m:02d}")

        print(f"[MolitCrawler] Parallel fetching for {months[0]}~{months[-1]} (3 Years)")

        import concurrent.futures
        import random

        def fetch_month_data(deal_ymd: str, prop_type: str):
            endpoint = self.ENDPOINTS.get(prop_type, "getRTMSDataSvcRHTrade")
            url = f"{self.BASE_URL}/{endpoint}"
            m_results = []
            page_no = 1
            while True:
                params = {
                    "serviceKey": self.api_key,
                    "LAWD_CD": gu_code,
                    "DEAL_YMD": deal_ymd,
                    "numOfRows": "200",
                    "pageNo": str(page_no),
                    "_type": "json"
                }
                try:
                    r = requests.get(url, params=params, timeout=12)
                    if r.status_code != 200: break
                    data = r.json()
                    body = data.get("response", {}).get("body", {})
                    items = parse_molit_items(body.get("items", {}))
                    if not items: break
                    
                    dong_filter = condition.region_name
                    for it in items:
                        dong_name = str(it.get("법정동", it.get("umdNm", ""))).strip()
                        if dong_filter and (dong_name not in dong_filter and dong_filter not in dong_name):
                            continue
                        
                        try:
                            # 가격/면적
                            price_raw = str(it.get("거래금액", it.get("dealAmount", "0"))).replace(",", "").strip()
                            price_man = int(price_raw)
                            if price_man <= 0: continue
                            if condition.price_min and price_man < condition.price_min: continue
                            if condition.price_max and price_man > condition.price_max: continue
                            
                            area_m2 = float(str(it.get("전용면적", it.get("excluUseAr", "0"))).strip())
                            build_year = int(str(it.get("건축년도", it.get("buildYear", "0"))).strip())
                            
                            bld_name = (it.get("연립다세대") or it.get("아파트") or it.get("단지명") or it.get("offiNm") or f"{dong_name} 매물")
                            deal_y = str(it.get("년", it.get("dealYear", ""))).strip()
                            deal_m = str(it.get("월", it.get("dealMonth", ""))).strip().zfill(2)
                            deal_d = str(it.get("일", it.get("dealDay", ""))).strip().zfill(2)

                            m_results.append(PropertyItem(
                                source="molit",
                                property_type=prop_type,
                                name=str(bld_name).strip(),
                                address=f"{dong_filter} {dong_name}".strip(),
                                price=format_price(price_man),
                                price_man=price_man,
                                price_per_pyung=calc_pyung_price(price_man, area_m2),
                                area=str(area_m2),
                                floor=str(it.get("층", "-")).strip(),
                                build_year=str(build_year) if build_year > 0 else "-",
                                is_new=(CURRENT_YEAR - build_year) <= NEW_BUILD_THRESHOLD if build_year > 0 else False,
                                description=f"실거래 {deal_y}.{deal_m}.{deal_d}",
                                url="https://rt.molit.go.kr",
                                lat=condition.lat + (random.random() - 0.5) * 0.008,
                                lng=condition.lng + (random.random() - 0.5) * 0.008
                            ))
                        except: continue

                    if page_no * 200 >= body.get("totalCount", 0) or page_no >= 5: break
                    page_no += 1
                except: break
            return m_results

        # 병렬 실행 (최대 15개 스레드)
        loop = asyncio.get_event_loop()
        tasks = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            for ymd in months:
                for pt in condition.property_types:
                    tasks.append(loop.run_in_executor(executor, fetch_month_data, ymd, pt))
            
            # 수집 결과 통합
            all_lists = await asyncio.gather(*tasks)
            for sublist in all_lists:
                results.extend(sublist)

        print(f"[MolitCrawler] 5Years Collection Finished: Total {len(results)} items.")
        return results
