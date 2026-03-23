from dataclasses import dataclass

@dataclass
class PropertyItem:
    """매매 매물 — 보증금·월세 필드 없음"""
    source:           str    # "naver" | "zigbang"
    property_type:    str    # "빌라" | "오피스텔"
    name:             str    # 건물명
    address:          str    # 주소
    price:            str    # 매매가 (문자열, 예: "3억 2,000만원")
    area:             str    # 전용면적 (㎡)
    floor:            str    # 층수
    build_year:       str    # 준공연도 (4자리)
    price_man:        int    = 0    # 매매가 (만원 단위 숫자, 평당가 계산용)
    price_per_pyung:  str    = "-"  # 평당가 (예: "1,200만원/평")
    is_new:           bool   = False  # 신축 여부 (준공 5년 이내)
    description:      str    = ""
    url:              str    = ""
    lat:              float  = 0.0
    lng:              float  = 0.0
