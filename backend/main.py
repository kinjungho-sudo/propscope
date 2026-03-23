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
    네이버 부동산 지역 검색 API → 정적 매핑 순으로 fallback.
    """
    import re

    # 입력 전처리: 앞뒤 공백 제거, "서울 마포구 공덕동" → "공덕동" 등 동명 추출
    region_clean = region.strip()

    # ── 1차: 네이버 부동산 지역 자동완성 API ──
    try:
        url = "https://new.land.naver.com/api/regions/list"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://new.land.naver.com/",
            "Accept": "application/json",
            "Accept-Language": "ko-KR,ko;q=0.9"
        }

        # 전체 입력으로 먼저 시도
        for query in [region_clean, re.sub(r'^.*(시|도)\s*', '', region_clean).strip()]:
            params = {"cortarName": query}
            resp = requests.get(url, params=params, headers=headers, timeout=8)
            print(f"[RegionCode] Naver API query='{query}' → status={resp.status_code}")

            if resp.status_code == 200:
                data = resp.json()
                regions_list = data.get("regionList", [])

                if regions_list:
                    # 동(읍·면·동) 레벨 우선, 그 다음 구 레벨
                    dong_results = [r for r in regions_list if r.get("cortarType") == "3"]
                    best = dong_results[0] if dong_results else regions_list[0]

                    print(f"[RegionCode] Naver hit: {best.get('fullCortarName')} / {best.get('cortarNo')}")
                    return JSONResponse({
                        "region": best.get("cortarName", region),
                        "code": best.get("cortarNo", "1144010200"),
                        "lat": float(best.get("centerLat", 37.5443)),
                        "lng": float(best.get("centerLon", 126.9510)),
                        "full_address": best.get("fullCortarName", region)
                    })

    except Exception as e:
        print(f"[RegionCode] Naver API Error: {e}")

    # ── 2차: 정적 매핑 (서울 주요 동 전수 확장) ──
    STATIC_MAP = {
        # ── 마포구 ──
        "공덕동":    {"code": "1144010200", "lat": 37.5443, "lng": 126.9510},
        "서교동":    {"code": "1144012000", "lat": 37.5534, "lng": 126.9221},
        "아현동":    {"code": "1144010100", "lat": 37.5530, "lng": 126.9609},
        "합정동":    {"code": "1144013100", "lat": 37.5493, "lng": 126.9139},
        "망원동":    {"code": "1144013200", "lat": 37.5559, "lng": 126.9031},
        "마포동":    {"code": "1144010300", "lat": 37.5502, "lng": 126.9492},
        "성산동":    {"code": "1144014100", "lat": 37.5660, "lng": 126.9033},
        "상암동":    {"code": "1144016800", "lat": 37.5794, "lng": 126.8894},
        "신수동":    {"code": "1144010600", "lat": 37.5468, "lng": 126.9407},
        "대흥동":    {"code": "1144010700", "lat": 37.5499, "lng": 126.9464},
        "염리동":    {"code": "1144010900", "lat": 37.5476, "lng": 126.9533},
        "도화동":    {"code": "1144011000", "lat": 37.5413, "lng": 126.9564},
        "용강동":    {"code": "1144011100", "lat": 37.5358, "lng": 126.9527},
        "토정동":    {"code": "1144011200", "lat": 37.5348, "lng": 126.9549},
        "창전동":    {"code": "1144011600", "lat": 37.5473, "lng": 126.9333},
        "노고산동":  {"code": "1144011700", "lat": 37.5487, "lng": 126.9400},
        "신정동":    {"code": "1144011800", "lat": 37.5456, "lng": 126.9337},
        "현석동":    {"code": "1144015400", "lat": 37.5421, "lng": 126.9313},
        "구수동":    {"code": "1144015500", "lat": 37.5457, "lng": 126.9358},
        "동교동":    {"code": "1144012100", "lat": 37.5568, "lng": 126.9248},
        "연남동":    {"code": "1144012200", "lat": 37.5604, "lng": 126.9233},
        # ── 강남구 ──
        "역삼동":    {"code": "1168010100", "lat": 37.5012, "lng": 127.0363},
        "논현동":    {"code": "1168010800", "lat": 37.5174, "lng": 127.0286},
        "삼성동":    {"code": "1168010500", "lat": 37.5140, "lng": 127.0572},
        "대치동":    {"code": "1168010600", "lat": 37.4943, "lng": 127.0656},
        "개포동":    {"code": "1168011100", "lat": 37.4831, "lng": 127.0471},
        "일원동":    {"code": "1168011200", "lat": 37.4833, "lng": 127.0803},
        "수서동":    {"code": "1168011300", "lat": 37.4908, "lng": 127.1030},
        "압구정동":  {"code": "1168010200", "lat": 37.5274, "lng": 127.0308},
        "청담동":    {"code": "1168010400", "lat": 37.5229, "lng": 127.0518},
        "도곡동":    {"code": "1168010700", "lat": 37.4958, "lng": 127.0442},
        # ── 서초구 ──
        "서초동":    {"code": "1165010100", "lat": 37.4833, "lng": 127.0322},
        "방배동":    {"code": "1165010900", "lat": 37.4816, "lng": 126.9966},
        "잠원동":    {"code": "1165010200", "lat": 37.5146, "lng": 127.0024},
        "반포동":    {"code": "1165010300", "lat": 37.5044, "lng": 127.0040},
        "양재동":    {"code": "1165010800", "lat": 37.4683, "lng": 127.0356},
        "우면동":    {"code": "1165011100", "lat": 37.4643, "lng": 127.0209},
        # ── 송파구 ──
        "잠실동":    {"code": "1171010100", "lat": 37.5119, "lng": 127.0990},
        "가락동":    {"code": "1171013100", "lat": 37.4935, "lng": 127.1180},
        "문정동":    {"code": "1171013400", "lat": 37.4822, "lng": 127.1233},
        "거여동":    {"code": "1171014000", "lat": 37.4946, "lng": 127.1489},
        "방이동":    {"code": "1171010400", "lat": 37.5079, "lng": 127.1145},
        "풍납동":    {"code": "1171010600", "lat": 37.5341, "lng": 127.1148},
        # ── 용산구 ──
        "이태원동":  {"code": "1123010900", "lat": 37.5345, "lng": 126.9946},
        "용산동":    {"code": "1123010100", "lat": 37.5384, "lng": 126.9805},
        "한남동":    {"code": "1123011000", "lat": 37.5362, "lng": 127.0026},
        "후암동":    {"code": "1123010200", "lat": 37.5446, "lng": 126.9801},
        "남영동":    {"code": "1123010300", "lat": 37.5411, "lng": 126.9738},
        "원효로1가": {"code": "1123010400", "lat": 37.5416, "lng": 126.9699},
        "청파동":    {"code": "1123010700", "lat": 37.5454, "lng": 126.9675},
        "보광동":    {"code": "1123011200", "lat": 37.5312, "lng": 126.9979},
        # ── 성동구 ──
        "성수동":    {"code": "1121511300", "lat": 37.5445, "lng": 127.0559},
        "왕십리동":  {"code": "1121510100", "lat": 37.5615, "lng": 127.0380},
        "금호동":    {"code": "1121510900", "lat": 37.5548, "lng": 127.0188},
        "옥수동":    {"code": "1121511000", "lat": 37.5496, "lng": 127.0128},
        "행당동":    {"code": "1121510700", "lat": 37.5582, "lng": 127.0461},
        "사근동":    {"code": "1121510800", "lat": 37.5622, "lng": 127.0468},
        # ── 은평구 ──
        "신사동":    {"code": "1138010400", "lat": 37.6206, "lng": 126.9256},
        "역촌동":    {"code": "1138010200", "lat": 37.6224, "lng": 126.9197},
        "응암동":    {"code": "1138010300", "lat": 37.6139, "lng": 126.9181},
        "불광동":    {"code": "1138010700", "lat": 37.6084, "lng": 126.9266},
        # ── 서대문구 ──
        "신촌동":    {"code": "1114015300", "lat": 37.5555, "lng": 126.9366},
        "연희동":    {"code": "1114015400", "lat": 37.5689, "lng": 126.9315},
        "홍제동":    {"code": "1114010100", "lat": 37.5956, "lng": 126.9386},
        "홍은동":    {"code": "1114010200", "lat": 37.5979, "lng": 126.9301},
        "남가좌동":  {"code": "1114016800", "lat": 37.5759, "lng": 126.9064},
        "북가좌동":  {"code": "1114016900", "lat": 37.5802, "lng": 126.9093},
        # ── 동작구 ──
        "흑석동":    {"code": "1159010700", "lat": 37.5100, "lng": 126.9632},
        "상도동":    {"code": "1159010400", "lat": 37.4979, "lng": 126.9526},
        "노량진동":  {"code": "1159010100", "lat": 37.5135, "lng": 126.9416},
        "대방동":    {"code": "1159010900", "lat": 37.5100, "lng": 126.9198},
        # ── 관악구 ──
        "봉천동":    {"code": "1162010100", "lat": 37.4813, "lng": 126.9527},
        "신림동":    {"code": "1162010200", "lat": 37.4839, "lng": 126.9286},
        "남현동":    {"code": "1162010300", "lat": 37.4743, "lng": 126.9597},
        # ── 구로구 ──
        "구로동":    {"code": "1153010200", "lat": 37.4957, "lng": 126.8879},
        "개봉동":    {"code": "1153010400", "lat": 37.4987, "lng": 126.8629},
        "오류동":    {"code": "1153010500", "lat": 37.4926, "lng": 126.8499},
        "고척동":    {"code": "1153010600", "lat": 37.5006, "lng": 126.8604},
        "신도림동":  {"code": "1153010800", "lat": 37.5092, "lng": 126.8917},
        # ── 금천구 ──
        "독산동":    {"code": "1154510300", "lat": 37.4750, "lng": 126.8935},
        "시흥동":    {"code": "1154510400", "lat": 37.4603, "lng": 126.8975},
        "가산동":    {"code": "1154510200", "lat": 37.4810, "lng": 126.8825},
        # ── 양천구 ──
        "목동":      {"code": "1147010600", "lat": 37.5265, "lng": 126.8745},
        "신정동":    {"code": "1147010800", "lat": 37.5190, "lng": 126.8620},
        # ── 영등포구 ──
        "여의도동":  {"code": "1156010100", "lat": 37.5219, "lng": 126.9245},
        "당산동":    {"code": "1156010800", "lat": 37.5362, "lng": 126.8999},
        "문래동":    {"code": "1156011100", "lat": 37.5189, "lng": 126.8995},
        "대림동":    {"code": "1156012400", "lat": 37.4902, "lng": 126.8960},
        # ── 강서구 ──
        "화곡동":    {"code": "1150010100", "lat": 37.5484, "lng": 126.8493},
        "방화동":    {"code": "1150010900", "lat": 37.5713, "lng": 126.8043},
        "마곡동":    {"code": "1150011000", "lat": 37.5579, "lng": 126.8319},
        "발산동":    {"code": "1150010800", "lat": 37.5583, "lng": 126.8426},
        # ── 강북구 ──
        "수유동":    {"code": "1130510100", "lat": 37.6400, "lng": 127.0253},
        "미아동":    {"code": "1130510200", "lat": 37.6364, "lng": 127.0265},
        "번동":      {"code": "1130510400", "lat": 37.6357, "lng": 127.0398},
        # ── 도봉구 ──
        "창동":      {"code": "1132010100", "lat": 37.6553, "lng": 127.0466},
        "도봉동":    {"code": "1132010200", "lat": 37.6747, "lng": 127.0461},
        "방학동":    {"code": "1132010300", "lat": 37.6641, "lng": 127.0397},
        # ── 노원구 ──
        "상계동":    {"code": "1135010800", "lat": 37.6540, "lng": 127.0645},
        "중계동":    {"code": "1135010700", "lat": 37.6390, "lng": 127.0697},
        "하계동":    {"code": "1135010600", "lat": 37.6294, "lng": 127.0709},
        "공릉동":    {"code": "1135010500", "lat": 37.6201, "lng": 127.0744},
        # ── 중랑구 ──
        "면목동":    {"code": "1126010100", "lat": 37.5826, "lng": 127.0869},
        "상봉동":    {"code": "1126010400", "lat": 37.5951, "lng": 127.0934},
        "묵동":      {"code": "1126010600", "lat": 37.6126, "lng": 127.0929},
        # ── 동대문구 ──
        "전농동":    {"code": "1121010100", "lat": 37.5766, "lng": 127.0535},
        "답십리동":  {"code": "1121010200", "lat": 37.5698, "lng": 127.0598},
        "장안동":    {"code": "1121010300", "lat": 37.5743, "lng": 127.0695},
        "용신동":    {"code": "1121010400", "lat": 37.5739, "lng": 127.0350},
        # ── 중구 ──
        "황학동":    {"code": "1114410200", "lat": 37.5696, "lng": 127.0138},
        "신당동":    {"code": "1114410100", "lat": 37.5613, "lng": 127.0200},
        "청구동":    {"code": "1114410300", "lat": 37.5594, "lng": 127.0109},
        # ── 종로구 ──
        "창신동":    {"code": "1111016700", "lat": 37.5764, "lng": 127.0113},
        "숭인동":    {"code": "1111016800", "lat": 37.5783, "lng": 127.0159},
        # ── 광진구 ──
        "광장동":    {"code": "1121510400", "lat": 37.5448, "lng": 127.1116},
        "구의동":    {"code": "1121510300", "lat": 37.5474, "lng": 127.0837},
        "건대입구":  {"code": "1121510200", "lat": 37.5402, "lng": 127.0695},
        "자양동":    {"code": "1121510600", "lat": 37.5356, "lng": 127.0855},
    }

    # 정확히 일치하는 동명 우선, 그 다음 부분 일치
    for key, val in STATIC_MAP.items():
        if key == region_clean or region_clean.endswith(key):
            print(f"[RegionCode] Static exact match: {key}")
            return JSONResponse({
                "region": key,
                "code": val["code"],
                "lat": val["lat"],
                "lng": val["lng"],
                "full_address": region_clean
            })

    for key, val in STATIC_MAP.items():
        if key in region_clean:
            print(f"[RegionCode] Static partial match: {key}")
            return JSONResponse({
                "region": key,
                "code": val["code"],
                "lat": val["lat"],
                "lng": val["lng"],
                "full_address": region_clean
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
