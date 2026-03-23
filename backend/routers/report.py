from fastapi import APIRouter, Response
from fastapi.responses import FileResponse
from ..models.filter import FilterCondition
from ..crawlers.molit import MolitCrawler
from ..services.analyzer import PropertyAnalyzer
from ..services.pdf_generator import PDFGenerator
from datetime import datetime
import asyncio
import os
import tempfile

router = APIRouter(prefix="/api/report")

@router.post("/pdf")
async def generate_pdf_report(condition: FilterCondition):
    """국토교통부 실거래가 데이터를 기반으로 PDF 리포트를 생성합니다."""
    
    # 1. 국토부 데이터 수집
    molit = MolitCrawler()
    items = await molit.fetch(condition)
    
    stats = PropertyAnalyzer.analyze(items)
    
    # 2. 데이터 정리
    data = {
        "region": condition.region_name,
        "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(items),
        "source": "국토교통부 실거래가",
        "stats": stats,
        "items": items[:50] # 리포트에는 상위 50개만 포함
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
