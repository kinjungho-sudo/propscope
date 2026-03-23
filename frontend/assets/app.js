/**
 * PropScope v2 — 동 단위 실거래가 분석기
 */

let map;
let markers = [];
let allItems = [];         // 전체 매물 캐시 (정렬용)
let sortKey   = null;     // 현재 정렬 컬럼
let sortAsc   = true;     // 오름차순 여부
const API_BASE = CONFIG.API_BASE;

document.addEventListener("DOMContentLoaded", () => {
    initMap();
    initEvents();
});

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 🗺️ 지도 초기화
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function initMap() {
    const container = document.getElementById('map');
    if (typeof kakao === 'undefined' || !kakao.maps) {
        showMapFallback(container);
        map = null;
        return;
    }
    try {
        map = new kakao.maps.Map(container, {
            center: new kakao.maps.LatLng(37.5443, 126.9510),
            level: 5
        });
    } catch (e) {
        showMapFallback(container);
        map = null;
    }
}

function showMapFallback(container) {
    if (!container) return;
    container.innerHTML = `
        <div style="height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;
                    background:#0d1117;color:#e6edf3;text-align:center;padding:40px;">
            <i class="fas fa-map" style="font-size:56px;color:#7C4DFF;margin-bottom:20px;opacity:0.5;"></i>
            <h3 style="margin-bottom:8px;font-size:18px;">카카오맵 로드 대기 중</h3>
            <p style="font-size:13px;color:#8b949e;max-width:340px;line-height:1.8;">
                Kakao Developers 콘솔 → <b style="color:#e6edf3">플랫폼 → Web</b> 에서<br>
                <code style="background:#161b22;padding:2px 8px;border-radius:4px;color:#7C4DFF;">
                    https://propscope-c861.onrender.com
                </code><br>도메인을 등록하면 지도가 표시됩니다.
            </p>
            <p style="margin-top:20px;font-size:12px;color:#555;">
                📋 지도 없이도 조회 결과 목록은 정상 사용 가능합니다.
            </p>
        </div>`;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// ⌨️ 이벤트 바인딩
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function initEvents() {
    document.getElementById('btnSearch').addEventListener('click', performSearch);
    document.getElementById('btnDownloadPdf').addEventListener('click', downloadPdf);

    document.querySelectorAll('.toggle').forEach(btn =>
        btn.addEventListener('click', () => btn.classList.toggle('active'))
    );

    document.getElementById('listHandle').addEventListener('click', () =>
        document.getElementById('listView').classList.add('active')
    );
    document.getElementById('listClose').addEventListener('click', () =>
        document.getElementById('listView').classList.remove('active')
    );

    // Enter 키 검색
    document.getElementById('inputRegion').addEventListener('keydown', e => {
        if (e.key === 'Enter') performSearch();
    });
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 🔍 매물 검색 (온디맨드)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async function performSearch() {
    const regionName = document.getElementById('inputRegion').value.trim();
    if (!regionName) { alert("동 이름을 입력해 주세요."); return; }

    const btn = document.getElementById('btnSearch');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 실거래가 수집 중...';
    btn.disabled = true;

    try {
        // 1. 동 코드 + 위경도 조회
        const regionResp = await fetch(`${API_BASE}/region-code?region=${encodeURIComponent(regionName)}`);
        if (!regionResp.ok) throw new Error("지역 코드 조회 실패");
        const rd = await regionResp.json();

        // 지도 중심 이동
        if (map && rd.lat && rd.lng) {
            map.setCenter(new kakao.maps.LatLng(rd.lat, rd.lng));
            map.setLevel(5);
        }

        // 2. 선택된 유형
        const types = Array.from(document.querySelectorAll('.toggle.active')).map(b => b.dataset.type);
        if (types.length === 0) { alert("주거 형태를 하나 이상 선택해 주세요."); return; }

        const payload = {
            region_name: rd.region || regionName,
            region_code: rd.code  || "1144010200",
            lat: rd.lat || 37.5443,
            lng: rd.lng || 126.9510,
            property_types: types,
            price_min: parseInt(document.getElementById('priceMin').value) || 0,
            price_max: parseInt(document.getElementById('priceMax').value) || 900000000,
            area_min:  parseFloat(document.getElementById('areaMin').value) || 0,
            area_max:  parseFloat(document.getElementById('areaMax').value) || 900000000,
            build_year_min: parseInt(document.getElementById('buildYear').value) || 2000,
            floor_min: 0, floor_max: 100,
            TRADE_TYPE: "매매"
        };

        const resp = await fetch(`${API_BASE}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ detail: resp.statusText }));
            throw new Error(err.detail || "서버 오류");
        }

        const result = await resp.json();
        updateUI(result);

    } catch (err) {
        console.error(err);
        alert(`오류: ${err.message}`);
    } finally {
        btn.innerHTML = '<i class="fas fa-crosshairs"></i> 지금 시세 조회';
        btn.disabled = false;
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 📊 UI 업데이트
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function updateUI(data) {
    const stats      = data.stats || {};
    const summary    = stats.summary    || {};
    const comparison = stats.comparison || {};
    const total      = data.total_count || 0;

    // ── 통계 패널 ──
    document.getElementById('statsPanel').style.display = 'block';
    setText('statAvgPrice',    summary.avg_price_str      || "데이터 없음");
    setText('statMedianPrice', summary.median_price_str   || "데이터 없음");
    setText('statMinPrice',    summary.min_price_str      || "데이터 없음");
    setText('statMaxPrice',    summary.max_price_str      || "데이터 없음");
    setText('statPyungPrice',  summary.avg_pyung_price_str|| "데이터 없음");
    setText('statStdDev',      summary.std_dev_str        || "데이터 없음");
    setText('statGapNote',     comparison.gap_note        || "단일 소스 데이터");

    // ── 카운터 ──
    setText('itemCount', `총 ${total}건 (국토교통부 실거래가 기준)`);

    // ── 신축 분양율 섹션 ──
    const newItems = (data.items || []).filter(it => it.is_new);
    const newSection = document.getElementById('newBuildSection');
    if (newItems.length > 0) {
        newSection.style.display = 'block';
        setText('newBuildCount', `${newItems.length}건`);

        const newPrices = newItems.filter(it => it.price_man > 0).map(it => it.price_man);
        if (newPrices.length > 0) {
            const avg = Math.round(newPrices.reduce((a,b)=>a+b,0) / newPrices.length);
            setText('newBuildAvg', formatWan(avg));
        }

        const pyungPrices = newItems
            .filter(it => it.price_per_pyung && it.price_per_pyung !== '-')
            .map(it => parseInt(it.price_per_pyung.replace(/[^0-9]/g,'')))
            .filter(v => v > 0);
        if (pyungPrices.length > 0) {
            const avgPyung = Math.round(pyungPrices.reduce((a,b)=>a+b,0) / pyungPrices.length);
            setText('newBuildPyung', `평균 ${avgPyung.toLocaleString()}만원/평`);
        }

        const region = document.getElementById('inputRegion').value;
        document.getElementById('newBuildNaverLink').href =
            `https://new.land.naver.com/complexes?ms=37.5,127.0,14&a=APT:OPST:VL&e=RETAIL&q=${encodeURIComponent(region)}`;
    } else {
        newSection.style.display = 'none';
    }

    // ── 매물 목록 (정렬 지원) ──
    allItems = data.items || [];  // 캐시 저장
    sortKey = null;               // 정렬 초기화
    sortAsc = true;
    renderTable(allItems);
    updateSortHeaders();

    // ── 지도 마커 ──
    if (map) {
        clearMarkers();
        (data.items || []).forEach(addMarker);
    }

    if (total > 0) {
        document.getElementById('listView').classList.add('active');
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 📋 테이블 렌더 (정렬 지원)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function renderTable(items) {
    const listBody = document.getElementById('propertyList');
    listBody.innerHTML = '';

    if (!items || items.length === 0) {
        listBody.innerHTML = `
            <tr><td colspan="9" style="text-align:center;padding:48px;color:#8b949e;">
                <i class="fas fa-search" style="font-size:32px;margin-bottom:12px;display:block;opacity:0.3;"></i>
                수집된 매물이 없습니다.<br>
                <small>지역명 확인 또는 필터 조건을 완화해 보세요.</small>
            </td></tr>`;
        return;
    }

    items.forEach(item => {
        const isNew   = item.is_new;
        const areaM2  = parseFloat(item.area || 0);
        const areaPy  = areaM2 > 0 ? (areaM2 / 3.3058).toFixed(1) : '-';
        const areaStr = areaM2 > 0 ? `${areaM2.toFixed(1)}㎡<br><small style="color:#8b949e;">(${areaPy}평)</small>` : '-';
        const yearNum = parseInt(item.build_year) || 0;
        const age     = yearNum > 0 ? `${item.build_year}<br><small style="color:#8b949e;">築${new Date().getFullYear()-yearNum}년</small>` : (item.build_year || '-');

        const row = document.createElement('tr');
        if (isNew) row.classList.add('row-new');
        row.innerHTML = `
            <td><span class="badge ${item.source}">${item.source === 'molit' ? '국토부' : item.source === 'naver' ? '네이버' : '직방'}</span></td>
            <td>${item.property_type}</td>
            <td>
                ${isNew ? '<span class="badge-new">🏗️ 신축</span> ' : ''}
                <strong>${item.name}</strong>
                <br><small style="color:#8b949e;">${item.address}</small>
            </td>
            <td style="color:#7C4DFF;font-weight:700;">${item.price}</td>
            <td style="color:#FFD700;font-weight:600;">${item.price_per_pyung || '-'}</td>
            <td>${areaStr}</td>
            <td>${item.floor || '-'}</td>
            <td>${age}</td>
            <td>
                <a href="${item.url || '#'}" target="_blank" class="btn-item-link">
                    <i class="fas fa-external-link-alt"></i>
                </a>
            </td>`;
        listBody.appendChild(row);
    });
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 🔃 테이블 정렬
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function sortTable(key) {
    if (sortKey === key) {
        sortAsc = !sortAsc;
    } else {
        sortKey = key;
        sortAsc = true;
    }

    const sorted = [...allItems].sort((a, b) => {
        let va, vb;
        if (key === 'price') {
            va = a.price_man || 0;
            vb = b.price_man || 0;
        } else if (key === 'pyung') {
            va = parseInt((a.price_per_pyung || '0').replace(/[^0-9]/g, '')) || 0;
            vb = parseInt((b.price_per_pyung || '0').replace(/[^0-9]/g, '')) || 0;
        } else if (key === 'area') {
            va = parseFloat(a.area || 0);
            vb = parseFloat(b.area || 0);
        } else if (key === 'year') {
            va = parseInt(a.build_year) || 0;
            vb = parseInt(b.build_year) || 0;
        } else {
            return 0;
        }
        return sortAsc ? va - vb : vb - va;
    });

    renderTable(sorted);
    updateSortHeaders();
}

function updateSortHeaders() {
    const cols = [
        { id: 'thPrice', key: 'price' },
        { id: 'thPyung', key: 'pyung' },
        { id: 'thArea',  key: 'area'  },
        { id: 'thYear',  key: 'year'  }
    ];
    cols.forEach(({ id, key }) => {
        const el = document.getElementById(id);
        if (!el) return;
        const base = el.dataset.label || el.innerText.replace(/ [▲▼↕]/g,'').trim();
        el.dataset.label = base;
        if (sortKey === key) {
            el.innerText = base + (sortAsc ? ' ▲' : ' ▼');
        } else {
            el.innerText = base + ' ↕';
        }
    });
}

// ── 헬퍼 ──
function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.innerText = val;
}

function formatWan(man) {
    if (!man || man <= 0) return "-";
    const bill = Math.floor(man / 10000);
    const rem  = man % 10000;
    const parts = [];
    if (bill > 0) parts.push(`${bill}억`);
    if (rem  > 0) parts.push(`${rem.toLocaleString()}만원`);
    return parts.join(' ') || '0만원';
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 📍 카카오맵 마커 (건물명 + 실거래가)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
let activeOverlay = null;

function addMarker(item) {
    if (!item.lat || !item.lng || item.lat === 0) return;
    const pos = new kakao.maps.LatLng(item.lat, item.lng);

    // 마커 콘텐츠 (건물명 일부 + 가격)
    const shortName = item.name.length > 6 ? item.name.slice(0, 5) + '..' : item.name;
    const content = `
        <div class="marker-wrapper" onclick="showItemDetail('${item.name}')">
            <div class="marker-bubble molit">
                <span class="m-name">${shortName}</span>
                <span class="m-price">${item.price}</span>
            </div>
            <div class="marker-pin"></div>
        </div>`;

    const overlay = new kakao.maps.CustomOverlay({
        position: pos,
        content: content,
        yAnchor: 1.1
    });

    overlay.setMap(map);
    markers.push(overlay);
}

// 지도 위 항목 클릭 시 상세 표시
function showItemDetail(name) {
    const item = allItems.find(it => it.name === name);
    if (!item) return;

    if (activeOverlay) activeOverlay.setMap(null);

    const content = `
        <div class="map-detail-card">
            <div class="card-header">
                <span class="badge molit">국토부 실거래</span>
                <button onclick="closeDetail()" class="btn-close-mini">×</button>
            </div>
            <div class="card-body">
                <h3>${item.name}</h3>
                <p class="addr">${item.address}</p>
                <div class="specs">
                    <div class="spec"><span>전용</span><strong>${item.area}㎡</strong></div>
                    <div class="spec"><span>층수</span><strong>${item.floor}층</strong></div>
                    <div class="spec"><span>준공</span><strong>${item.build_year}년</strong></div>
                </div>
                <div class="price-row">
                    <span class="label">실거래가</span>
                    <span class="val">${item.price}</span>
                </div>
                <p class="desc">${item.description}</p>
            </div>
            <div class="card-footer">
                <a href="${item.url}" target="_blank">자세히 보기 <i class="fas fa-chevron-right"></i></a>
            </div>
        </div>`;

    activeOverlay = new kakao.maps.CustomOverlay({
        position: new kakao.maps.LatLng(item.lat, item.lng),
        content: content,
        yAnchor: 1.05
    });

    activeOverlay.setMap(map);
    map.panTo(new kakao.maps.LatLng(item.lat, item.lng));
}

window.closeDetail = () => {
    if (activeOverlay) activeOverlay.setMap(null);
};

function clearMarkers() {
    markers.forEach(m => m.setMap(null));
    markers = [];
    if (activeOverlay) activeOverlay.setMap(null);
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 📄 PDF 리포트 다운로드
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async function downloadPdf() {
    const btn = document.getElementById('btnDownloadPdf');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 리포트 생성 중...';
    btn.disabled = true;

    const regionName = document.getElementById('inputRegion').value.trim();
    try {
        const rd = await fetch(`${API_BASE}/region-code?region=${encodeURIComponent(regionName)}`).then(r => r.json());
        const types = Array.from(document.querySelectorAll('.toggle.active')).map(b => b.dataset.type);

        const payload = {
            region_name: rd.region || regionName,
            region_code: rd.code   || "1144010200",
            lat: rd.lat || 37.5443,
            lng: rd.lng || 126.9510,
            property_types: types,
            price_min: parseInt(document.getElementById('priceMin').value) || 0,
            price_max: parseInt(document.getElementById('priceMax').value) || 900000000,
            area_min:  parseFloat(document.getElementById('areaMin').value) || 0,
            area_max:  parseFloat(document.getElementById('areaMax').value) || 900000000,
            build_year_min: parseInt(document.getElementById('buildYear').value) || 2000,
            floor_min: 0, floor_max: 100, TRADE_TYPE: "매매"
        };

        const resp = await fetch(`${API_BASE}/report/pdf`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const blob = await resp.blob();
        const url  = window.URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = `PropScope_${regionName}_${new Date().toISOString().slice(0,10)}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);

    } catch (err) {
        alert(`PDF 오류: ${err.message}`);
    } finally {
        btn.innerHTML = '<i class="fas fa-file-pdf"></i> 감정 리포트 PDF 저장';
        btn.disabled = false;
    }
}
