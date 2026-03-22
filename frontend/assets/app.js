/**
 * PropScope — Frontend App Logic
 * Designed by AI 디자인실장 영자 💖
 */

let map;
let markers = [];
const API_BASE = CONFIG.API_BASE;

document.addEventListener("DOMContentLoaded", () => {
    initMap();
    initEvents();
});

// 🗺️ 카카오 맵 초기화
function initMap() {
    try {
        if (typeof kakao === 'undefined' || !kakao.maps) {
            console.error("Kakao Maps SDK not loaded.");
            const mapContainer = document.getElementById('map');
            if (mapContainer) {
                mapContainer.innerHTML = `
                    <div style="height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; background:#f8fafc; color:#64748b; text-align:center; padding:20px;">
                        <i class="fas fa-map-marked-alt" style="font-size:48px; margin-bottom:16px; color:#cbd5e1;"></i>
                        <h3 style="margin-bottom:8px;">지도를 불러올 수 없습니다</h3>
                        <p style="font-size:14px; line-height:1.6;">카카오 개발자 콘솔에서 도메인(propscope-52a.pages.dev)을<br>플랫폼에 등록하셨는지 확인해주세요! 😍</p>
                    </div>
                `;
            }
            return;
        }
        const container = document.getElementById('map');
        const options = {
            center: new kakao.maps.LatLng(37.5443, 126.9510), // 기본: 공덕동
            level: 5
        };
        map = new kakao.maps.Map(container, options);
    } catch (e) {
        console.error("Map Init Error:", e);
    }
}

// ⌨️ 이벤트 리스너 설정
function initEvents() {
    // 조회 버튼 클릭
    document.getElementById('btnSearch').addEventListener('click', () => {
        performSearch();
    });

    // 필터 토글 클릭
    document.querySelectorAll('.toggle').forEach(btn => {
        btn.addEventListener('click', () => {
            btn.classList.toggle('active');
        });
    });

    // 리스트 핸들 클릭 (슬라이드업)
    document.getElementById('listHandle').addEventListener('click', () => {
        document.getElementById('listView').classList.add('active');
    });

    // 닫기 버튼
    document.getElementById('listClose').addEventListener('click', () => {
        document.getElementById('listView').classList.remove('active');
    });

    // PDF 리포트 다운로드
    document.getElementById('btnDownloadPdf').addEventListener('click', () => {
        downloadPdf();
    });
}

// 🔍 매물 검색 API 호출
async function performSearch() {
    const regionName = document.getElementById('inputRegion').value;
    
    // 1. 지역 코드를 먼저 가져옵니다 (간단 예시)
    const regionResp = await fetch(`${API_BASE}/region-code?region=${encodeURIComponent(regionName)}`);
    const regionData = await regionResp.json();
    
    const types = Array.from(document.querySelectorAll('.toggle.active')).map(b => b.dataset.type);
    
    const payload = {
        region_name: regionData.region,
        region_code: regionData.code,
        lat: map.getCenter().getLat(),
        lng: map.getCenter().getLng(),
        property_types: types,
        price_min: parseInt(document.getElementById('priceMin').value),
        price_max: parseInt(document.getElementById('priceMax').value),
        area_min: parseFloat(document.getElementById('areaMin').value),
        area_max: parseFloat(document.getElementById('areaMax').value),
        build_year_min: parseInt(document.getElementById('buildYear').value)
    };

    // 로딩 처리
    document.getElementById('btnSearch').innerText = "데이터 수집 중... 🕸️";
    
    try {
        const resp = await fetch(`${API_BASE}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const result = await resp.json();
        updateUI(result);
    } catch (err) {
        alert("데이터를 가져오는 데 실패했어요. 서버가 켜져 있는지 확인해 주세요! 😭");
    } finally {
        document.getElementById('btnSearch').innerText = "조회하기 🔍";
    }
}

// 📊 UI 및 지도 업데이트
function updateUI(data) {
    // 1. 통계 패널 업데이트
    document.getElementById('statsPanel').style.display = 'block';
    document.getElementById('statAvgPrice').innerText = data.stats.avg_price_str;
    document.getElementById('statMinMax').innerText = `${data.stats.min_price_str} / ${data.stats.max_price_str}`;
    document.getElementById('statGap').innerText = data.stats.price_gap_str;
    document.getElementById('statGapNote').innerText = data.stats.gap_note || "비교 데이터가 충분하지 않아요.";

    // 2. 리스트 하단 업데이트
    document.getElementById('itemCount').innerText = `전체 매물 ${data.total}건 (네이버 ${data.naver_count}, 직방 ${data.zigbang_count})`;
    const listBody = document.getElementById('propertyList');
    listBody.innerHTML = '';

    data.items.forEach(item => {
        const row = document.createElement('tr');
        const mapUrl = `https://map.kakao.com/link/search/${encodeURIComponent(item.name)}`;
        row.innerHTML = `
            <td><span class="badge ${item.source}">${item.source.toUpperCase()}</span></td>
            <td>${item.property_type}</td>
            <td><strong>${item.name}</strong></td>
            <td style="color: #2563EB; font-weight:700;">${item.price}</td>
            <td>${item.area}㎡</td>
            <td>${item.floor}</td>
            <td>
                <a href="${mapUrl}" target="_blank" style="text-decoration:none; color:var(--primary); font-size:12px; display:flex; align-items:center; gap:4px; font-weight:700;">
                    <i class="fas fa-map-location-dot"></i> 열기
                </a>
            </td>
        `;
        listBody.appendChild(row);
    });

    // 3. 지도 마커 표시
    clearMarkers();
    data.items.forEach(item => {
        addMarker(item);
    });
    
    // 리스트 뷰 살짝 올리기
    document.getElementById('listView').classList.add('active');
}

// 📍 마커 추가
function addMarker(item) {
    if (!item.lat || !item.lng) return;
    
    const pos = new kakao.maps.LatLng(item.lat, item.lng);
    const brandClass = item.source === 'naver' ? 'marker-naver' : 'marker-zigbang';
    
    const content = `
        <div class="marker-bubble ${brandClass}">
            ${item.price}
        </div>
    `;

    const overlay = new kakao.maps.CustomOverlay({
        position: pos,
        content: content,
        yAnchor: 1.5
    });

    overlay.setMap(map);
    markers.push(overlay);
}

function clearMarkers() {
    markers.forEach(m => m.setMap(null));
    markers = [];
}

// 📄 PDF 다운로드 호출
async function downloadPdf() {
    const btn = document.getElementById('btnDownloadPdf');
    btn.innerText = "리포트 생성 중... 📄";
    
    const regionName = document.getElementById('inputRegion').value;
    const regionResp = await fetch(`${API_BASE}/region-code?region=${encodeURIComponent(regionName)}`);
    const regionData = await regionResp.json();
    
    const types = Array.from(document.querySelectorAll('.toggle.active')).map(b => b.dataset.type);
    
    const payload = {
        region_name: regionData.region,
        region_code: regionData.code,
        lat: map.getCenter().getLat(),
        lng: map.getCenter().getLng(),
        property_types: types,
        price_min: parseInt(document.getElementById('priceMin').value),
        price_max: parseInt(document.getElementById('priceMax').value),
        area_min: parseFloat(document.getElementById('areaMin').value),
        area_max: parseFloat(document.getElementById('areaMax').value),
        build_year_min: parseInt(document.getElementById('buildYear').value)
    };

    try {
        const resp = await fetch(`${API_BASE}/report/pdf`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const blob = await resp.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `PropScope_${regionName}_${new Date().toISOString().slice(0,10)}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    } catch (err) {
        alert("PDF 생성에 실패했습니다. WeasyPrint 라이브러리 설치를 확인해 주세요!");
    } finally {
        btn.innerText = "PDF 리포트 다운로드 📄";
    }
}
