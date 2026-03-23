/**
 * PropScope — Frontend App Logic
 * 은행 여신 시세 분석기
 */

let map;
let markers = [];
const API_BASE = CONFIG.API_BASE;

document.addEventListener("DOMContentLoaded", () => {
    initMap();
    initEvents();
    console.log("PropScope App Initialized 🚀");
});

function initMap() {
    const container = document.getElementById('map');

    // Kakao SDK 로드 확인
    if (typeof kakao === 'undefined' || !kakao.maps) {
        showMapFallback(container, "카카오맵 SDK 로드 실패", "Kakao Developers 콘솔에서 현재 도메인을 등록해 주세요.");
        map = null;
        return;
    }

    try {
        const options = {
            center: new kakao.maps.LatLng(37.5443, 126.9510),
            level: 5
        };
        map = new kakao.maps.Map(container, options);
    } catch (e) {
        console.error("Map Init Error:", e);
        showMapFallback(container, "지도 초기화 실패", e.message);
        map = null;
    }
}

function showMapFallback(container, title, desc) {
    if (!container) return;
    container.innerHTML = `
        <div style="height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; background:#0d1117; color:#e6edf3; text-align:center; padding:40px;">
            <i class="fas fa-map" style="font-size:48px; color:#7C4DFF; margin-bottom:20px; opacity:0.6;"></i>
            <h3 style="margin-bottom:8px; font-size:18px;">${title}</h3>
            <p style="font-size:13px; color:#8b949e; max-width:320px; line-height:1.7;">${desc}</p>
            <div style="margin-top:24px; padding:14px 20px; background:#161b22; border-radius:10px; font-size:12px; color:#8b949e; border:1px solid #30363d;">
                📌 좌측에서 조회 후 매물 목록을 확인할 수 있습니다.
            </div>
        </div>
    `;
}

// ⌨️ 이벤트 리스너
function initEvents() {
    document.getElementById('btnSearch').addEventListener('click', performSearch);

    document.querySelectorAll('.toggle').forEach(btn => {
        btn.addEventListener('click', () => btn.classList.toggle('active'));
    });

    document.getElementById('listHandle').addEventListener('click', () => {
        document.getElementById('listView').classList.add('active');
    });

    document.getElementById('listClose').addEventListener('click', () => {
        document.getElementById('listView').classList.remove('active');
    });

    document.getElementById('btnDownloadPdf').addEventListener('click', downloadPdf);
}

// 🔍 매물 검색
async function performSearch() {
    const regionName = document.getElementById('inputRegion').value.trim();
    if (!regionName) {
        alert("지역명을 입력해 주세요! (예: 마포구 공덕동)");
        return;
    }

    const btn = document.getElementById('btnSearch');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 데이터 수집 중...';
    btn.disabled = true;

    try {
        // 1. 지역 코드 조회
        const regionResp = await fetch(`${API_BASE}/region-code?region=${encodeURIComponent(regionName)}`);
        const regionData = await regionResp.json();

        // 2. 선택된 주거 형태
        const types = Array.from(document.querySelectorAll('.toggle.active')).map(b => b.dataset.type);
        if (types.length === 0) {
            alert("최소 1가지 이상 주거 형태를 선택해 주세요!");
            return;
        }

        // 3. 지도 중심 좌표
        let lat = regionData.lat || 37.5443;
        let lng = regionData.lng || 126.9510;
        if (map) {
            lat = map.getCenter().getLat();
            lng = map.getCenter().getLng();
        }

        const payload = {
            region_name: regionData.region || regionName,
            region_code: regionData.code || "1144010800",
            lat, lng,
            property_types: types,
            price_min: parseInt(document.getElementById('priceMin').value) || 0,
            price_max: parseInt(document.getElementById('priceMax').value) || 900000000,
            area_min: parseFloat(document.getElementById('areaMin').value) || 0,
            area_max: parseFloat(document.getElementById('areaMax').value) || 900000000,
            build_year_min: parseInt(document.getElementById('buildYear').value) || 2000,
            floor_min: 0,
            floor_max: 100,
            TRADE_TYPE: "매매"
        };

        const resp = await fetch(`${API_BASE}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || "서버 오류");
        }

        const result = await resp.json();
        updateUI(result);

    } catch (err) {
        console.error(err);
        alert(`오류가 발생했어요: ${err.message}`);
    } finally {
        btn.innerHTML = '<i class="fas fa-crosshairs"></i> 정밀 시세 조회';
        btn.disabled = false;
    }
}

// 📊 UI 업데이트
function updateUI(data) {
    const stats = data.stats || {};
    const summary = stats.summary || {};
    const comparison = stats.comparison || {};

    // 통계 패널 표시
    document.getElementById('statsPanel').style.display = 'block';
    document.getElementById('statAvgPrice').innerText   = summary.avg_price_str    || "데이터 없음";
    document.getElementById('statMedianPrice').innerText = summary.median_price_str || "데이터 없음";
    document.getElementById('statMinPrice').innerText   = summary.min_price_str    || "데이터 없음";
    document.getElementById('statMaxPrice').innerText   = summary.max_price_str    || "데이터 없음";
    document.getElementById('statGapNote').innerText    = comparison.gap_note      || "단일 플랫폼 데이터";

    // 매물 카운터
    const total = data.total_count || 0;
    document.getElementById('itemCount').innerText =
        `총 ${total}건 수집 (네이버 ${data.naver_count || 0}건 · 직방 ${data.zigbang_count || 0}건)`;

    // 매물 리스트
    const listBody = document.getElementById('propertyList');
    listBody.innerHTML = '';

    if (!data.items || data.items.length === 0) {
        listBody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:40px; color:#8b949e;">
            수집된 매물이 없습니다. 지역명을 확인하거나 필터 조건을 완화해 보세요.
        </td></tr>`;
    } else {
        data.items.forEach(item => {
            const row = document.createElement('tr');
            const safeUrl = item.url ? item.url : '#';
            row.innerHTML = `
                <td><span class="badge ${item.source}">${item.source === 'naver' ? '네이버' : '직방'}</span></td>
                <td>${item.property_type}</td>
                <td><strong>${item.name}</strong><br><small style="color:#8b949e">${item.address}</small></td>
                <td style="color:#7C4DFF; font-weight:700;">${item.price}</td>
                <td>${parseFloat(item.area).toFixed(1)}㎡</td>
                <td>${item.floor}</td>
                <td>${item.build_year || '-'}</td>
                <td>
                    <a href="${safeUrl}" target="_blank" class="btn-item-link">
                        <i class="fas fa-external-link-alt"></i>
                    </a>
                </td>
            `;
            listBody.appendChild(row);
        });
    }

    // 지도 마커
    if (map) {
        clearMarkers();
        data.items.forEach(item => addMarker(item));
    }

    // 목록 자동 오픈
    if (total > 0) {
        document.getElementById('listView').classList.add('active');
    }
}

// 📍 마커 추가
function addMarker(item) {
    if (!item.lat || !item.lng || item.lat === 0) return;

    const pos = new kakao.maps.LatLng(item.lat, item.lng);
    const colorClass = item.source === 'naver' ? 'marker-naver' : 'marker-zigbang';

    const content = `<div class="marker-bubble ${colorClass}">${item.price}</div>`;
    const overlay = new kakao.maps.CustomOverlay({ position: pos, content, yAnchor: 1.5 });
    overlay.setMap(map);
    markers.push(overlay);
}

function clearMarkers() {
    markers.forEach(m => m.setMap(null));
    markers = [];
}

// 📄 PDF 다운로드
async function downloadPdf() {
    const btn = document.getElementById('btnDownloadPdf');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 리포트 생성 중...';
    btn.disabled = true;

    const regionName = document.getElementById('inputRegion').value.trim();
    try {
        const regionResp = await fetch(`${API_BASE}/region-code?region=${encodeURIComponent(regionName)}`);
        const regionData = await regionResp.json();

        const types = Array.from(document.querySelectorAll('.toggle.active')).map(b => b.dataset.type);
        let lat = regionData.lat || 37.5443;
        let lng = regionData.lng || 126.9510;
        if (map) { lat = map.getCenter().getLat(); lng = map.getCenter().getLng(); }

        const payload = {
            region_name: regionData.region || regionName,
            region_code: regionData.code || "1144010800",
            lat, lng,
            property_types: types,
            price_min: parseInt(document.getElementById('priceMin').value) || 0,
            price_max: parseInt(document.getElementById('priceMax').value) || 900000000,
            area_min: parseFloat(document.getElementById('areaMin').value) || 0,
            area_max: parseFloat(document.getElementById('areaMax').value) || 900000000,
            build_year_min: parseInt(document.getElementById('buildYear').value) || 2000,
            floor_min: 0, floor_max: 100, TRADE_TYPE: "매매"
        };

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
        alert(`PDF 생성 중 오류: ${err.message}`);
    } finally {
        btn.innerHTML = '<i class="fas fa-file-pdf"></i> PDF 리포트 저장';
        btn.disabled = false;
    }
}
