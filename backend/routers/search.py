from fastapi import APIRouter, HTTPException
from ..models.filter import FilterCondition
from ..crawlers.naver import NaverCrawler
from ..crawlers.zigbang import ZigbangCrawler
from ..services.analyzer import PropertyAnalyzer
from datetime import datetime
import asyncio
import requests
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


@router.get("/debug/test")
async def debug_crawlers():
    """크롤러 상태 진단 - 네이버/직방 API 응답 확인용"""
    result = {}

    # ── 1. 네이버 API 테스트 ──
    try:
        naver_url = "https://new.land.naver.com/api/articles/dong/1144010200"
        naver_params = {
            "realEstateType": "VL:DDDGG:OR",
            "tradeType": "A1",
            "tag": ":::::::::",
            "rentPriceMin": 0, "rentPriceMax": 900000000,
            "priceMin": 0, "priceMax": 900000000,
            "areaMin": 0, "areaMax": 900000000,
            "oldBuildYears": "", "recentlyBuildYears": "",
            "page": 1, "articleListVO": "articleList"
        }
        naver_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://new.land.naver.com/",
            "Accept-Language": "ko-KR,ko;q=0.9",
            "X-Requested-With": "XMLHttpRequest"
        }
        sess = requests.Session()
        sess.headers.update(naver_headers)
        sess.get("https://new.land.naver.com/main", timeout=8)
        resp = sess.get(naver_url, params=naver_params, timeout=15)
        data = resp.json() if resp.status_code == 200 else {}
        articles = data.get("articleList", [])
        result["naver"] = {
            "status": resp.status_code,
            "article_count": len(articles),
            "sample_fields": list(articles[0].keys()) if articles else [],
            "sample": {k: articles[0].get(k) for k in ["articleNo","articleName","dealOrWarrantPrice","area2","buildYear","approveYear","useApprovYmd","buildingName","floorInfo","lat","lng"] if k in (articles[0] if articles else {})} if articles else None
        }
    except Exception as e:
        result["naver"] = {"status": "error", "detail": str(e)}

    # ── 2. 직방 API 테스트 ──
    try:
        from ..utils.geohash import encode_geohash
        ghash = encode_geohash(37.5443, 126.9510, precision=5)
        zb_url = "https://apis.zigbang.com/house/property/v1/items/villas"
        zb_params = {
            "geohash": ghash,
            "salesType": "매매",
            "salesPriceMin": 0,
            "salesPriceMax": 0,
            "depositMin": 0,
            "rentMin": 0
        }
        zb_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Origin": "https://www.zigbang.com",
            "Referer": "https://www.zigbang.com/home/villa/map",
            "x-zigbang-platform": "www",
            "Accept": "application/json"
        }
        zb_resp = requests.get(zb_url, params=zb_params, headers=zb_headers, timeout=10)
        zb_data = zb_resp.json() if zb_resp.status_code == 200 else {}
        item_ids = zb_data.get("item_ids", [])
        result["zigbang"] = {
            "status": zb_resp.status_code,
            "geohash": ghash,
            "item_ids_count": len(item_ids),
            "sample_ids": item_ids[:5],
            "raw_response_keys": list(zb_data.keys()) if zb_data else []
        }
    except Exception as e:
        result["zigbang"] = {"status": "error", "detail": str(e)}

    return JSONResponse(result)
