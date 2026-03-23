import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.crawlers.naver import NaverCrawler
from backend.crawlers.zigbang import ZigbangCrawler
from backend.models.filter import FilterCondition
from backend.services.analyzer import PropertyAnalyzer

async def main():
    condition = FilterCondition(
        region_name="공덕동",
        region_code="1144010200",
        lat=37.5443,
        lng=126.9510,
        property_types=["빌라", "오피스텔"],
        price_min=1000,
        price_max=1000000,
        area_min=10,
        area_max=200,
        floor_min=1,
        floor_max=50,
        build_year_min=1990
    )
    
    naver = NaverCrawler()
    zigbang = ZigbangCrawler()
    
    print("Testing Total Search...")
    n_items = await naver.fetch(condition)
    z_items = await zigbang.fetch(condition)
    
    total = n_items + z_items
    print(f"Total items collected: {len(total)} (Naver: {len(n_items)}, Zigbang: {len(z_items)})")
    
    if total:
        stats = PropertyAnalyzer.analyze(total)
        print("\n--- Statistics ---")
        print(f"Average Price: {stats['avg_price_str']}")
        if "빌라" in stats['by_type']:
            print(f"Villa Avg Price: {stats['by_type']['빌라']['avg_price_str']} (Pyung: {stats['by_type']['빌라']['pyung_price_str']})")
        if "오피스텔" in stats['by_type']:
            print(f"Officetel Avg Price: {stats['by_type']['오피스텔']['avg_price_str']} (Pyung: {stats['by_type']['오피스텔']['pyung_price_str']})")

if __name__ == "__main__":
    asyncio.run(main())
