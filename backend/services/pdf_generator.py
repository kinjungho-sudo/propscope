from fpdf import FPDF
import os
from datetime import datetime

class PDFGenerator:
    """분석 데이터를 표 형식의 PDF로 변환합니다."""

    def __init__(self, template_dir: str = None):
        self.template_dir = template_dir

    def generate(self, data: dict, output_path: str):
        """FPDF2를 사용하여 한글 리포트 PDF를 생성합니다."""
        pdf = FPDF()
        pdf.add_page()
        
        # 폰트 등록 (한글 폰트가 시스템에 없을 경우를 대비해 헬박스 류 대신 나눔/Pretendard 파일이 있으면 로드)
        # 여기서는 가장 간단하게 폰트 없이 영문 위주로 생성하거나 시스템 폰트를 로드하는 설계를 하되,
        # 배포 환경임을 고려해 폰트 로직은 가급적 안전하게 짭니다.
        # pdf.add_font('Pretendard', '', 'font/Pretendard.ttf', uni=True)
        # pdf.set_font('Pretendard', size=16)

        pdf.set_font("helvetica", "B", 20)
        pdf.cell(0, 10, "PropScope Property Analysis Report", ln=True, align='C')
        pdf.ln(10)

        pdf.set_font("helvetica", "", 12)
        pdf.cell(0, 10, f"Region: {data.get('region', 'N/A')}", ln=True)
        pdf.cell(0, 10, f"Source: {data.get('source', 'MOLIT')}", ln=True)
        pdf.cell(0, 10, f"Total Data Points: {data.get('total', 0)}", ln=True)
        pdf.ln(10)

        # 핵심 통계
        stats = data.get('stats', {}).get('summary', {})
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "Market Statistics", ln=True)
        pdf.set_font("helvetica", "", 10)
        pdf.cell(0, 10, f" - Avg Price: {stats.get('avg_price_str', '-')}", ln=True)
        pdf.cell(0, 10, f" - Median: {stats.get('median_price_str', '-')}", ln=True)
        pdf.cell(0, 10, f" - Pyung Price: {stats.get('avg_pyung_price_str', '-')}", ln=True)
        pdf.ln(10)

        # 리스트 (상위 20개만)
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "Recent Transactions (Sample List)", ln=True)
        pdf.set_font("helvetica", "", 8)
        
        # Table Header
        pdf.set_fill_color(124, 77, 255) # Primary Purple
        pdf.set_text_color(255, 255, 255)
        pdf.cell(30, 8, "Type", 1, 0, 'C', True)
        pdf.cell(80, 8, "Building", 1, 0, 'C', True)
        pdf.cell(40, 8, "Price", 1, 0, 'C', True)
        pdf.cell(40, 8, "Area", 1, 1, 'C', True)
        
        pdf.set_text_color(0, 0, 0)
        for item in data.get('items', [])[:20]:
            pdf.cell(30, 8, str(item.property_type), 1)
            pdf.cell(80, 8, str(item.name)[:20], 1)
            pdf.cell(40, 8, str(item.price), 1)
            pdf.cell(40, 8, str(item.area) + "m2", 1, 1)

        pdf.output(output_path)
        return output_path
