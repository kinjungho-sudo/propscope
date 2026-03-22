from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class PropertyItemSchema(BaseModel):
    source: str
    property_type: str
    name: str
    address: str
    price: str
    area: str
    floor: str
    build_year: str
    description: str = ""
    url: str = ""
    lat: float = 0.0
    lng: float = 0.0

class TypeStats(BaseModel):
    count: int
    avg_price_str: str
    pyung_price_str: str

class SearchResponse(BaseModel):
    region: str
    collected_at: str
    total: int
    naver_count: int
    zigbang_count: int
    items: List[PropertyItemSchema]
    stats: Dict[str, Any]
