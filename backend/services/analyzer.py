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
        # 평당가 계산 (만원/평)
        df['price_per_pyung'] = df.apply(lambda row: int(row['price_man'] / (row['area_val'] / 3.3)) if row['area_val'] > 0 else 0, axis=1)
        
        # 3. 전체 통계 (감정 평가용 핵심 지표)
        avg_price = int(df['price_man'].mean())
        median_price = int(df['price_man'].median())
        min_price = int(df['price_man'].min())
        max_price = int(df['price_man'].max())
        std_dev = int(df['price_man'].std()) if len(df) > 1 else 0 # 가격 변동성(표준편차)
        
        # 4. 평당가 통계
        avg_pyung_price = int(df['price_per_pyung'].mean())
        
        # 5. 사이트별 통계
        naver_df = df[df['source'] == 'naver']
        zigbang_df = df[df['source'] == 'zigbang']
        
        naver_avg = int(naver_df['price_man'].mean()) if not naver_df.empty else 0
        zigbang_avg = int(zigbang_df['price_man'].mean()) if not zigbang_df.empty else 0
        
        price_gap = abs(naver_avg - zigbang_avg) if naver_avg > 0 and zigbang_avg > 0 else 0
        gap_note = ""
        if naver_avg > 0 and zigbang_avg > 0:
            winner = "네이버" if naver_avg > zigbang_avg else "직방"
            gap_note = f"{winner}가 {format_price(price_gap)} 높음"

        # 6. 매물 유형별 심층 통계
        by_type = {}
        for prop_type in df['property_type'].unique():
            sub_df = df[df['property_type'] == prop_type]
            count = len(sub_df)
            t_avg = int(sub_df['price_man'].mean())
            t_median = int(sub_df['price_man'].median())
            t_avg_pyung = int(sub_df['price_per_pyung'].mean())
            t_std = int(sub_df['price_man'].std()) if len(sub_df) > 1 else 0
            
            by_type[prop_type] = {
                "count": count,
                "avg_price_str": format_price(t_avg),
                "median_price_str": format_price(t_median),
                "avg_pyung_price_str": format_price(t_avg_pyung),
                "std_dev_str": format_price(t_std)
            }

        # 7. 최저가/최고가 TOP 5
        top5_lowest = df.sort_values('price_man').head(5).to_dict('records')
        top5_highest = df.sort_values('price_man', ascending=False).head(5).to_dict('records')

        return {
            "summary": {
                "avg_price_str":    format_price(avg_price),
                "median_price_str": format_price(median_price),
                "min_price_str":    format_price(min_price),
                "max_price_str":    format_price(max_price),
                "std_dev_str":      format_price(std_dev),
                "avg_pyung_price_str": format_price(avg_pyung_price)
            },
            "comparison": {
                "naver_avg_str":    format_price(naver_avg),
                "zigbang_avg_str":  format_price(zigbang_avg),
                "price_gap_str":    format_price(price_gap),
                "gap_note":         gap_note
            },
            "by_type":          by_type,
            "top5_lowest":      top5_lowest,
            "top5_highest":     top5_highest,
            "total_count":      len(items)
        }
