# PropScope — 부동산 매매 시세 비교 시스템

네이버 부동산 + 직방의 매매 매물 데이터를 수집·비교하여 PDF 리포트를 생성하는 부동산 분석 도구입니다.

---

## 📌 주요 기능
- **통합 매물 검색**: 네이버부동산과 직방의 빌라/오피스텔 매매 데이터를 동시 수집
- **지도 기반 시각화**: 카카오맵 위에 출처별 마커 표시 및 통계 분석
- **AI PDF 리포트**: 수집된 데이터를 바탕으로 A4 규격의 전문적인 매매 리포트 자동 생성

## 🚀 시작하기
1. **의존성 설치**: `pip install -r requirements.txt`
2. **브라우저 설치**: `playwright install chromium`
3. **서버 실행**: `uvicorn backend.main:app --reload`
4. **프론트엔드**: `frontend/index.html`을 브라우저에서 실행

Created by PropScope v1.0 | 2026.03
