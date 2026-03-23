from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .routers import search, report
import requests
import time

app = FastAPI(title="PropScope API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(report.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": time.time()}


@app.get("/api/region-code")
def get_region_code(region: str):
    """
    동 단위 실시간 지역 코드 조회.
    네이버 부동산 지역 검색 API를 사용하여 법정동 코드 + 위경도 반환.
    """
    try:
        # 네이버 부동산 지역 자동완성 API (공개 엔드포인트)
        url = "https://new.land.naver.com/api/regions/list"
        params = {"cortarName": region}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://new.land.naver.com/",
            "Accept": "application/json"
        }
        resp = requests.get(url, params=params, headers=headers, timeout=8)

        if resp.status_code == 200:
            data = resp.json()
            regions = data.get("regionList", [])

            if regions:
                # 첫 번째 결과 사용 (가장 정확한 결과)
                best = regions[0]
                return JSONResponse({
                    "region": best.get("cortarName", region),
                    "code": best.get("cortarNo", "1144010200"),
                    "lat": float(best.get("centerLat", 37.5443)),
                    "lng": float(best.get("centerLon", 126.9510)),
                    "full_address": best.get("fullCortarName", region)
                })

    except Exception as e:
        print(f"[RegionCode] API Error: {e}")

    # Fallback: 정적 매핑 (동 이름으로 매핑)
    STATIC_MAP = {
        "공덕동":   {"code": "1144010200", "lat": 37.5443, "lng": 126.9510},
        "서교동":   {"code": "1144012000", "lat": 37.5534, "lng": 126.9221},
        "아현동":   {"code": "1144010100", "lat": 37.5530, "lng": 126.9609},
        "합정동":   {"code": "1144013100", "lat": 37.5493, "lng": 126.9139},
        "망원동":   {"code": "1144013200", "lat": 37.5559, "lng": 126.9031},
        "성수동":   {"code": "1121511300", "lat": 37.5445, "lng": 127.0559},
        "이태원동": {"code": "1123010900", "lat": 37.5345, "lng": 126.9946},
        "논현동":   {"code": "1168010800", "lat": 37.5174, "lng": 127.0286},
        "역삼동":   {"code": "1168010100", "lat": 37.5012, "lng": 127.0363},
        "서초동":   {"code": "1165010100", "lat": 37.4833, "lng": 127.0322},
        "방배동":   {"code": "1165010900", "lat": 37.4816, "lng": 126.9966},
        "구로동":   {"code": "1153010200", "lat": 37.4957, "lng": 126.8879},
        "독산동":   {"code": "1154510300", "lat": 37.4750, "lng": 126.8935},
        "마포동":   {"code": "1144010300", "lat": 37.5502, "lng": 126.9492},
        "용산동":   {"code": "1123010100", "lat": 37.5384, "lng": 126.9805},
        "신촌동":   {"code": "1114015300", "lat": 37.5555, "lng": 126.9366},
    }

    for key, val in STATIC_MAP.items():
        if key in region:
            return JSONResponse({
                "region": region,
                "code": val["code"],
                "lat": val["lat"],
                "lng": val["lng"],
                "full_address": region
            })

    print(f"[RegionCode] No match for '{region}'. Using default (공덕동).")
    return JSONResponse({
        "region": region,
        "code": "1144010200",
        "lat": 37.5443,
        "lng": 126.9510,
        "full_address": region
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
