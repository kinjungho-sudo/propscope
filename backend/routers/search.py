from fastapi import APIRouter, HTTPException
from ..models.filter import FilterCondition
from ..crawlers.naver import NaverCrawler
from ..crawlers.zigbang import ZigbangCrawler
from ..services.analyzer import PropertyAnalyzer
from datetime import datetime
import asyncio
from typing import Any, Dict, List
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api")

@router.post("/search")
async def search_properties(condition: FilterCondition):
    """네이버부동산과 직방에서 매물을 검색하고 분석합니다."""
    
    naver = NaverCrawler()
    zigbang = ZigbangCrawler()
    
    try:
        naver_task = naver.fetch(condition)
        zigbang_task = zigbang.fetch(condition)
        
        naver_items, zigbang_items = await asyncio.gather(naver_task, zigbang_task)
        
        total_items = naver_items + zigbang_items
        
        # 분석 수행
        stats = PropertyAnalyzer.analyze(total_items)
        
        # stats가 비어 있으면 기본값 채워서 반환 (undefined 방지)
        if not stats:
            stats = {
                "summary": {
                    "avg_price_str": "데이터 없음",
                    "median_price_str": "데이터 없음",
                    "min_price_str": "데이터 없음",
                    "max_price_str": "데이터 없음",
                    "std_dev_str": "데이터 없음",
                    "avg_pyung_price_str": "데이터 없음"
                },
                "comparison": {
                    "naver_avg_str": "데이터 없음",
                    "zigbang_avg_str": "데이터 없음",
                    "price_gap_str": "데이터 없음",
                    "gap_note": "매물이 수집되지 않아 비교할 수 없습니다."
                },
                "by_type": {},
                "top5_lowest": [],
                "top5_highest": [],
                "total_count": 0
            }
        
        # items를 직렬화 가능한 dict 형태로 변환
        items_data = [vars(item) for item in total_items]
        
        return JSONResponse({
            "region": condition.region_name,
            "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_count": len(total_items),
            "naver_count": len(naver_items),
            "zigbang_count": len(zigbang_items),
            "items": items_data,
            "stats": stats
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
