import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
from ..models.property import PropertyItem
from ..utils.price_parser import parse_price, format_price

class PropertyAnalyzer:
    """수집된 매물 데이터를 분석하고 통계를 생성합니다."""

    @staticmethod
    def analyze(items: List[PropertyItem]) -> Dict[str, Any]:
        if not items:
            return {}

        # 1. 데이터프레임 변환
        df = pd.DataFrame([vars(item) for item in items])
        
        # 2. 가격 파싱 (만원 단위 수치화)
        df['price_man'] = df['price'].apply(parse_price)
        df['area_val'] = df['area'].astype(float)
        
        # 3. 전체 통계
        avg_price = int(df['price_man'].mean())
        min_price = int(df['price_man'].min())
        max_price = int(df['price_man'].max())

        # 4. 사이트별 통계
        naver_avg = int(df[df['source'] == 'naver']['price_man'].mean()) if not df[df['source'] == 'naver'].empty else 0
        zigbang_avg = int(df[df['source'] == 'zigbang']['price_man'].mean()) if not df[df['source'] == 'zigbang'].empty else 0
        
        price_gap = abs(naver_avg - zigbang_avg) if naver_avg > 0 and zigbang_avg > 0 else 0
        gap_note = ""
        if naver_avg > 0 and zigbang_avg > 0:
            winner = "네이버" if naver_avg > zigbang_avg else "직방"
            gap_note = f"{winner}가 높음 ({format_price(price_gap)} 차이)"

        # 5. 매물 유형별 통계
        by_type = {}
        for prop_type in df['property_type'].unique():
            sub_df = df[df['property_type'] == prop_type]
            count = len(sub_df)
            t_avg = int(sub_df['price_man'].mean())
            # 평당가 (전용면적당 가격)
            avg_area = sub_df['area_val'].mean()
            pyung_price = int(t_avg / (avg_area / 3.3)) if avg_area > 0 else 0
            
            by_type[prop_type] = {
                "count": count,
                "avg_price_str": format_price(t_avg),
                "pyung_price_str": format_price(pyung_price)
            }

        # 6. 최저가/최고가 TOP 5
        top5_lowest = df.sort_values('price_man').head(5).to_dict('records')
        top5_highest = df.sort_values('price_man', ascending=False).head(5).to_dict('records')

        return {
            "avg_price_str":    format_price(avg_price),
            "min_price_str":    format_price(min_price),
            "max_price_str":    format_price(max_price),
            "naver_avg_str":    format_price(naver_avg),
            "zigbang_avg_str":  format_price(zigbang_avg),
            "price_gap_str":    format_price(price_gap),
            "gap_note":         gap_note,
            "by_type":          by_type,
            "top5_lowest":      top5_lowest,
            "top5_highest":     top5_highest
        }
