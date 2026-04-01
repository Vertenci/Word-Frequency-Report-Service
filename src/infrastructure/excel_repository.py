import os
from datetime import datetime
from openpyxl import Workbook
from src.domain.interfaces import ReportRepository


class ExcelReportRepository(ReportRepository):
    async def save_report(self, stats: dict, filename: str, total_lines: int) -> str:
        os.makedirs("result", exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in filename if c.isalnum() or c in '._-')[:50]
        output_path = f"result/report_{safe_name}_{timestamp}.xlsx"

        wb = Workbook()
        ws = wb.active
        ws.title = "Frequency Stats"

        ws.append(["Словоформа", "Кол-во во всём документе", "Кол-во в каждой строке"])

        for word_stat in stats.values():
            ws.append(word_stat.to_excel_row())

        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 40

        wb.save(output_path)
        return output_path
