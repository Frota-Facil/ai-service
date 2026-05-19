from datetime import datetime
from typing import Optional

from app.schemas.report import ReportPeriod


def format_date_for_file_name(date: datetime) -> str:
    return date.strftime("%Y-%m-%d")


def generate_report_file_name(period: Optional[ReportPeriod]) -> str:
    if period and period.start and period.end:
        start_date = format_date_for_file_name(period.start)
        end_date = format_date_for_file_name(period.end)

        return f"relatorio_do_periodo_{start_date}_a_{end_date}.md"

    if period and period.start and not period.end:
        start_date = format_date_for_file_name(period.start)

        return f"relatorio_a_partir_de_{start_date}.md"

    if period and period.end and not period.start:
        end_date = format_date_for_file_name(period.end)

        return f"relatorio_ate_{end_date}.md"

    return "relatorio_geral.md"