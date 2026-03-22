import os
import jinja2
from typing import Dict, Any

class PDFGenerator:
    """분석 데이터를 HTML 템플릿에 주입하여 PDF로 변환합니다."""

    def __init__(self, template_dir: str):
        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
        self.template_name = "report.html"

    def generate(self, data: Dict[str, Any], output_path: str):
        """PDF 파일을 생성합니다."""
        template = self.env.get_template(self.template_name)
        html_out = template.render(**data)
        
        # WeasyPrint를 사용하여 PDF 변환
        # 주: 시스템에 libpango, libcairo 등이 필요합니다.
        try:
            from weasyprint import HTML
            HTML(string=html_out).write_pdf(output_path)
            return output_path
        except Exception as e:
            print(f"[PDFGenerator] Error: {e}")
            # Fallback: HTML 파일로 저장 (테스트용)
            html_path = output_path.replace(".pdf", ".html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_out)
            return html_path
