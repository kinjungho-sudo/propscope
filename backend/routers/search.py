from fastapi import APIRouter, HTTPException
from ..models.filter import FilterCondition
from ..models.response import SearchResponse
from ..crawlers.naver import NaverCrawler
from ..crawlers.zigbang import ZigbangCrawler
from ..services.analyzer import PropertyAnalyzer
from datetime import datetime
import asyncio

router = APIRouter(prefix="/api")

@router.post("/search", response_model=SearchResponse)
async def search_properties(condition: FilterCondition):
    """네이버부동산과 직방에서 매물을 검색하고 분석합니다."""
    
    # 두 크롤러 인스턴스 생성
    naver = NaverCrawler()
    zigbang = ZigbangCrawler()
    
    # 병렬로 데이터 수집
    try:
        naver_task = naver.fetch(condition)
        zigbang_task = zigbang.fetch(condition)
        
        naver_items, zigbang_items = await asyncio.gather(naver_task, zigbang_task)
        
        total_items = naver_items + zigbang_items
        
        # 분석 수행
        stats = PropertyAnalyzer.analyze(total_items)
        
        return SearchResponse(
            region=condition.region_name,
            collected_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total=len(total_items),
            naver_count=len(naver_items),
            zigbang_count=len(zigbang_items),
            items=total_items,
            stats=stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
