import requests
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("MOLIT_API_KEY", "")

# 1. API 서버 접근 테스트
try:
    r0 = requests.get("https://apis.data.go.kr", timeout=10)
    print(f"API서버 접근: {r0.status_code}")
except Exception as e:
    print(f"API서버 접근 실패: {e}")

# 2. 정확한 에러 확인
url = (
    "https://apis.data.go.kr/1613000/RTMSOBJSvc/getRTMSDataSvcRHTrade"
    f"?serviceKey={key}"
    "&LAWD_CD=11440&DEAL_YMD=202502&numOfRows=3&pageNo=1"
)
r = requests.get(url, timeout=15)
print(f"Status: {r.status_code}")
print(f"Content-Type: {r.headers.get('Content-Type', '')}")
print(f"Body: {r.text[:600]}")
