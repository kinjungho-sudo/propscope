# PropScope 디자인 가이드 (Design System)

부동산 시세 비교의 정확성과 데이터를 가장 아름답게 보여주기 위한 디자인 가이드라인입니다.

---

## 🎨 컬러 팔레트 (Color Palette)

매매 시세 데이터의 가독성을 높이고, "프리미엄 부동산 자산" 느낌을 주기 위해 깊이 있는 다크 모드를 지향합니다.

### 🏢 시안 색상 (Core Colors)
- **Background**: `#121212` (깊은 블랙)
- **Surface**: `#1E1E1E` (카드, 서피스)
- **Primary (Accent)**: `#7C4DFF` (신뢰를 주는 프리미엄 바이올렛)
- **Secondary (Info)**: `#03DAC6` (밝고 산뜻한 민트티)

### 📍 서비스별 마커 색상 (Brand Markers)
- **네이버 (Naver)**: `#03c75a` (네이버 고유 브랜드 그린)
- **직방 (Zigbang)**: `#ff6e30` (직방 고유 브랜드 오렌지)
- **Overlay Text**: `#FFFFFF` (깔끔한 화이트 텍스트 버블)

### 📊 상태 색상 (Status Colors)
- **Positive / Buy**: `#FF4B4B` (급등, 고가)
- **Negative / Sell**: `#4B7BFF` (급락, 저가)
- **Text (Emphasis)**: `#FFFFFF`
- **Text (Normal)**: `#E0E0E0`

---

## 🖋️ 타이포그래피 (Typography)

신뢰감을 주는 **Inter**와 **Noto Sans KR**을 사용하여 데이터를 명확하게 전달합니다.

- **Main Heading**: H1 - H2 (32px - 24px) | Bold
- **Body Text**: 14px - 16px | Regular / Medium
- **Data UI**: 12px Mono | Medium (숫자 및 시세 가독성 향상)

---

## ✨ UI/UX 인터렉션 (Interactions)

- **유리 질감 (Glassmorphism)**: 상단 헤더와 필터 패널에 적용 (`backdrop-filter: blur(10px)`)
- **부드러운 마커**: 지도 마커 호버 시 매물 요약 정보가 부드럽게(Fade-in) 노출
- **슬라이드 업 목록**: 하단 매물 목록은 마포구 지역을 분석했다가 슬라이드 업으로 요약표가 올라오는 모션

---

## 📸 이미지 리소스 (Assets)
- 로고: `assets/logo.png`
- 마커 아이콘: `assets/marker_naver.png`, `assets/marker_zigbang.png`

Designed by **AI 디자인실장 영자** 💖
