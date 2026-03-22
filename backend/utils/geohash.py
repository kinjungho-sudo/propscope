# Zigbang API에서 사용하는 Geohash 인코딩 유틸리티
# 기본적으로 위도/경도를 Geohash 문자열로 변환합니다.

def encode_geohash(latitude, longitude, precision=5):
    """
    Geohash 인코딩 (Zigbang API 대응용 초간단 버전)
    실제 Zigbang API는 내부적으로 Geohash를 사용하여 클러스터링된 데이터를 처리합니다.
    """
    __base32 = '0123456789bcdefghjkmnpqrstuvwxyz'
    
    lat_interval = (-90.0, 90.0)
    lon_interval = (-180.0, 180.0)
    
    geohash = []
    bits = [16, 8, 4, 2, 1]
    bit = 0
    ch = 0
    even = True
    
    while len(geohash) < precision:
        if even:
            mid = (lon_interval[0] + lon_interval[1]) / 2
            if longitude > mid:
                ch |= bits[bit]
                lon_interval = (mid, lon_interval[1])
            else:
                lon_interval = (lon_interval[0], mid)
        else:
            mid = (lat_interval[0] + lat_interval[1]) / 2
            if latitude > mid:
                ch |= bits[bit]
                lat_interval = (mid, lat_interval[1])
            else:
                lat_interval = (lat_interval[0], mid)
        
        even = not even
        if bit < 4:
            bit += 1
        else:
            geohash.append(__base32[ch])
            bit = 0
            ch = 0
            
    return ''.join(geohash)
