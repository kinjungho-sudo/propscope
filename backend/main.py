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
        "아현동": "1144010100"
    }
    # 간단한 키값 매칭 (마포구 기준)
    for key, value in mapping.items():
        if key in region:
            return {"region": region, "code": value}
            
    return {"region": region, "code": "1144010200"} # 기본값: 공덕동

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
