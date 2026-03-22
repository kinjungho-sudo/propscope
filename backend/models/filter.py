from dataclasses import dataclass
from typing import Optional, List

@dataclass
class FilterCondition:
    """매매 전용 필터 조건 — 전세·월세 필드 없음"""
    region_name:    str              # 지역명 (예: 서울 마포구 공덕동)
    region_code:    str              # 네이버용 법정동 코드
    lat:            float            # 직방용 위도
    lng:            float            # 직방용 경도
    property_types: List[str]        # ["빌라", "오피스텔"]
    price_min:      Optional[int]    # 최소 매매가 (만원)
    price_max:      Optional[int]    # 최대 매매가 (만원)
    area_min:       Optional[float]  # 최소 전용면적 (㎡)
    area_max:       Optional[float]  # 최대 전용면적 (㎡)
    floor_min:      Optional[int]    # 최소 층수
    floor_max:      Optional[int]    # 최대 층수
    build_year_min: Optional[int]    # 최소 준공연도

    TRADE_TYPE: str = "매매"         # 고정값 — 변경 불가
