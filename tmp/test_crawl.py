import requests
import json
import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.crawlers.naver import NaverCrawler
from backend.models.filter import FilterCondition

async def main():
    crawler = NaverCrawler()
    condition = FilterCondition(
        region_name="공덕동",
        region_code="1144010200",
        lat=37.5443,
        lng=126.9510,
        property_types=["빌라"],
        price_min=1000,
        price_max=100000,
        area_min=10,
        area_max=200,
        floor_min=1,
        floor_max=50,
        build_year_min=1990
    )
    
    print("Testing Naver Crawler...")
    items = await crawler.fetch(condition)
    print(f"Collected {len(items)} items from Naver.")
    for item in items[:3]:
        print(f"- {item.name} | {item.price} | {item.url}")

if __name__ == "__main__":
    asyncio.run(main())
