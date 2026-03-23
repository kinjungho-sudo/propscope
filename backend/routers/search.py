from fastapi import APIRouter, HTTPException
from ..models.filter import FilterCondition
from ..crawlers.molit import MolitCrawler
from ..services.analyzer import PropertyAnalyzer
from datetime import datetime
import asyncio
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api")


@router.post("/search")
async def search_properties(condition: FilterCondition):
    """국토교통부 실거래가 API에서 매물을 검색하고 분석합니다."""
    crawler = MolitCrawler()
    try:
        items = await crawler.fetch(condition)
        stats = PropertyAnalyzer.analyze(items)

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

        items_data = [vars(item) for item in items]

        return JSONResponse({
            "region": condition.region_name,
            "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_count": len(items),
            "naver_count": 0,
            "zigbang_count": 0,
            "molit_count": len(items),
            "items": items_data,
            "stats": stats
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/test")
async def debug_molit():
    """MOLIT API 연결 테스트"""
    import os
    import requests
    key = os.getenv("MOLIT_API_KEY", "")
    if not key:
        return JSONResponse({"status": "error", "message": "MOLIT_API_KEY 환경변수 없음"})

    try:
        url = "https://apis.data.go.kr/1613000/RTMSOBJSvc/getRTMSDataSvcRHTrade"
        params = {
            "serviceKey": key,
            "LAWD_CD": "11440",  # 마포구
            "DEAL_YMD": datetime.now().strftime("%Y%m"),
            "numOfRows": "5",
            "pageNo": "1",
            "_type": "json"
        }
        r = requests.get(url, params=params, timeout=15)
        data = r.json() if r.status_code == 200 else {}
        body = data.get("response", {}).get("body", {})
        items = body.get("items", {})
        item_list = items.get("item", []) if isinstance(items, dict) else []
        if isinstance(item_list, dict):
            item_list = [item_list]

        return JSONResponse({
            "status": r.status_code,
            "total_count": body.get("totalCount", 0),
            "sample_count": len(item_list),
            "sample": item_list[:2] if item_list else []
        })
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)})
