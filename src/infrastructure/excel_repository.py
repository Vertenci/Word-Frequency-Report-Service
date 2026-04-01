import os
from datetime import datetime
from openpyxl import Workbook
from src.domain.interfaces import ReportRepository


class ExcelReportRepository(ReportRepository):
    async def save_report(self, stats: dict, filename: str, total_lines: int) -> str:
        os.makedirs("result", exist_ok=True)

        base_name = os.path.splitext(filename)[0]
        safe_name = "".join(c for c in base_name if c.isalnum() or c in '._-')

        if len(safe_name) > 50:
            safe_name = safe_name[:50]

        timestamp = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")

        output_path = f"result/report_{safe_name}_{timestamp}.xlsx"

        wb = Workbook()
        ws = wb.active
        ws.title = "Frequency Stats"

        ws.append(["Словоформа", "Кол-во во всём документе", "Кол-во в каждой строке"])

        sorted_stats = sorted(stats.items(), key=lambda x: x[0])

        for lemma, word_stat in sorted_stats:
            while len(word_stat.line_counts) < total_lines:
                word_stat.line_counts.append(0)

            ws.append(word_stat.to_excel_row())

        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 40

        wb.save(output_path)
        return output_path
