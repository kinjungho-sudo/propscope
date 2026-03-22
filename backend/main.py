from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import search, report
import time

app = FastAPI(title="PropScope API", version="1.0")

# CORS 설정 (프론트엔드 연동)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(search.router)
app.include_router(report.router)

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": time.time()}

@app.get("/api/region-code")
def get_region_code(region: str):
    """
    대표님, 마포구 공덕동 검색용 정적 매핑 예시예요!
    실제 서비스 시에는 네이버 API나 DB 연동이 필요할 수 있어요.
    """
    mapping = {
        "공덕동": "1144010200",
        "서교동": "1144012000",
        "아현동": "1144010100",
        "논현동": "1168010800",
        "역삼동": "1168010100",
        "서초동": "1165010100",
        "구로동": "1153010200"
    }
    # 간단한 키값 매칭
    for key, value in mapping.items():
        if key in region:
            return {"region": region, "code": value}
            
    # 매칭되는 게 없으면 입력된 지역명을 그대로 쓰고 코드는 공덕동(기본)으로 반환하되 로그 남김
    print(f"[Region Mapping] No match for '{region}'. Using default.")
    return {"region": region, "code": "1144010200"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
