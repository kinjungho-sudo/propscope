# PropScope 디자인 가이드 (Design System) — Obsidian Prime 💎

네이버 부동산의 직관적인 레이아웃과 **PropScope**만의 독보적인 프리미엄 다크 데이터를 결합한 디자인 시스템입니다.

---

## 🎨 컬러 시스템 (Atmospheric Palette)
"Architectural Model at Night" 컨셉을 지향하며, 1px 선을 배제하고 톤의 차이(Tonal Depth)로 레이어를 구분합니다.

### 🏢 핵심 색상 (Core UI)
- **Base Background**: `#121212` (깊은 블랙, 전체 캔버스)
- **Sidebar Surface**: `#1C1B1B` (사이드바 메뉴 영역)
- **Interactive Surface**: `#353534` (카드, 버튼 등 상호작용 요소)
- **Primary Accent**: `#7C4DFF` (신뢰와 혁신의 프리미엄 바이올렛)
- **Glass Panel**: `rgba(25, 25, 25, 0.6)` + `backdrop-filter: blur(20px)`

### 📍 데이터 마커 (Map Markers)
- **Naver (네이버)**: `#03C75A` (네이버 고유 브랜드 그린)
- **Zigbang (직방)**: `#FF6E30` (직방 고유 브랜드 오렌지)
- **Marker Text**: `#FFFFFF` (선명한 화이트 데이터)

---

## 🖋️ 타이포그래피 (Editorial Authority)
데이터의 밀도를 조절하면서도 가독성을 잃지 않는 서체를 선정합니다.

- **Headlines**: **Manrope** (Bold, 32px / 24px) - 현대적인 권위를 전달
- **Main UI & Data**: **Inter** (Medium, 14px~16px) - 정밀한 데이터 가독성
- **Label Unit**: 12px Mono | Uppercase - 고전적인 시스템 감성

---

## ✨ UI/UX 인터렉션 (Naver Benchmarking)

- **The "No-Line" Rule**: 경계를 나눌 때 실선을 쓰지 않고 배경색의 명도 차이로만 구분하여 세련된 분위기를 유지합니다.
- **Glassmorphism Detail**: 지도의 시야를 방해하지 않도록 통계 패널 등은 유리에 비친 듯한 블러 효과를 적용합니다.
- **Micro-interactions**: 마커 호버 시 매물 가격이 살짝 커지며 부채꼴 형태로 발광 효과(Glow)를 주어 선택감을 높입니다.

---

## 📸 이미지 리소스 (Assets)
- 로고: `assets/logo.png`
- 마커 아이콘: `assets/marker_naver.png`, `assets/marker_zigbang.png` (둥근 버블 형태)

---

Designed by **AI 디자인실장 영자** 💖
*(Benchmarked from Naver Real Estate with Premium Dark Mode Extension)*
