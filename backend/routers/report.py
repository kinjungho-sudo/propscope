from fastapi import APIRouter, Response
from fastapi.responses import FileResponse
from ..models.filter import FilterCondition
from ..crawlers.naver import NaverCrawler
from ..crawlers.zigbang import ZigbangCrawler
from ..services.analyzer import PropertyAnalyzer
from ..services.pdf_generator import PDFGenerator
from datetime import datetime
import asyncio
import os
import tempfile

router = APIRouter(prefix="/api/report")

@router.post("/pdf")
async def generate_pdf_report(condition: FilterCondition):
    """검색 결과를 기반으로 PDF 리포트를 생성하고 다운로드합니다."""
    
    # 1. 데이터 수집 (Search와 동일)
    naver = NaverCrawler()
    zigbang = ZigbangCrawler()
    naver_items, zigbang_items = await asyncio.gather(naver.fetch(condition), zigbang.fetch(condition))
    
    total_items = naver_items + zigbang_items
    stats = PropertyAnalyzer.analyze(total_items)
    
    # 2. 데이터 정리
    data = {
        "region": condition.region_name,
        "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(total_items),
        "naver_count": len(naver_items),
        "zigbang_count": len(zigbang_items),
        "stats": stats
    }
    
    # 3. PDF 생성
    template_dir = os.path.join(os.path.dirname(__file__), "../../templates")
    generator = PDFGenerator(template_dir)
    
    filename = f"PropScope_{condition.region_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
    file_path = os.path.join(tempfile.gettempdir(), filename)
    
    output = generator.generate(data, file_path)
    
    # PDF 파일 반환
    return FileResponse(
        path=output,
        filename=filename,
        media_type="application/pdf" if output.endswith(".pdf") else "text/html"
    )
