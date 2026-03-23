import requests, sys, json, time
sys.path.insert(0, '.')
from backend.utils.geohash import encode_geohash

lat, lng = 37.5443, 126.9510

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Origin': 'https://www.zigbang.com',
    'Referer': 'https://www.zigbang.com/home/villa/map',
    'x-zigbang-platform': 'www',
    'Accept': 'application/json'
})
s.get('https://www.zigbang.com', timeout=8)

ghash4 = encode_geohash(lat, lng, precision=4)
ghash3 = encode_geohash(lat, lng, precision=3)

# 직방 매매 전용 엔드포인트 후보들 탐색
print('=== 직방 매매 엔드포인트 탐색 ===')
endpoints = [
    ('GET', f'https://apis.zigbang.com/house/property/v1/items/villas', {'geohash': ghash4, 'salesPriceMin': 5000, 'salesPriceMax': 900000, 'depositMin': 0, 'rentMin': 0}),
    ('GET', f'https://apis.zigbang.com/v2/items', {'geohash': ghash4, 'itemDealType': 'S', 'serviceType': 'villa'}),
    ('GET', f'https://apis.zigbang.com/house/sells/v1/items/villas', {'geohash': ghash4}),
    ('GET', f'https://apis.zigbang.com/house/property/v2/items/villas', {'geohash': ghash4, 'salesType': '매매'}),
    ('GET', f'https://apis.zigbang.com/property/v2/items', {'geohash': ghash4, 'sales_type': '매매'}),
    ('GET', f'https://apis.zigbang.com/house/price/v1/items/villas', {'geohash': ghash4}),
]

for method, url, params in endpoints:
    try:
        r = s.get(url, params=params, timeout=8)
        data = r.json() if r.status_code in [200, 400] else {}
        keys = list(data.keys()) if data else []
        cnt = len(data.get('items', data.get('item_ids', data.get('data', []))))
        print(f'{r.status_code} | {url.split("apis.zigbang.com")[1][:50]} | keys={keys[:4]} | count={cnt}')
    except Exception as e:
        print(f'ERR | {url.split("apis.zigbang.com")[1][:50]} | {str(e)[:50]}')
    time.sleep(0.5)

# 네이버 재시도 (충분한 대기)
print('\n=== 네이버 API 재시도 (5초 대기 후) ===')
time.sleep(5)
ns = requests.Session()
ns.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Referer': 'https://new.land.naver.com/',
    'Accept-Language': 'ko-KR,ko;q=0.9',
    'X-Requested-With': 'XMLHttpRequest'
})
ns.get('https://new.land.naver.com/main', timeout=8)
time.sleep(2)

r = ns.get('https://new.land.naver.com/api/articles/dong/1144010200',
    params={
        'realEstateType': 'VL:DDDGG',
        'tradeType': 'A1',
        'tag': '::::::::',
        'rentPriceMin': 0, 'rentPriceMax': 900000000,
        'priceMin': 0, 'priceMax': 900000000,
        'areaMin': 0, 'areaMax': 900000000,
        'oldBuildYears': '', 'recentlyBuildYears': '',
        'page': 1, 'articleListVO': 'articleList'
    }, timeout=15)
data = r.json() if r.status_code == 200 else {}
arts = data.get('articleList', [])
print(f'Naver status={r.status_code} | articles={len(arts)}')
if arts:
    a = arts[0]
    print(f'샘플 keys: {list(a.keys())}')
    print(f'샘플: {json.dumps({k: a.get(k) for k in ["articleName","dealOrWarrantPrice","area2","buildYear","approveYear","useApprovYmd","floorInfo","lat","lng"]}, ensure_ascii=False)}')
