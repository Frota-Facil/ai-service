from fastapi import APIRouter, HTTPException

from app.schemas.report import (
    GenerateMarkdownReportOutput,
    GenerateRawReportInput,
)
from app.services.openai_service import generate_markdown_report
from app.utils.file_name import generate_report_file_name
from app.errors.report_errors import EmptyReportContentError


router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


@router.post("/fleet", response_model=GenerateMarkdownReportOutput)
def create_fleet_report(data: GenerateRawReportInput):
    try:
        markdown_content = generate_markdown_report(data)
        file_name = generate_report_file_name(data.period)

        return GenerateMarkdownReportOutput(
            file_name=file_name,
            content_type="text/markdown",
            markdown_content=markdown_content,
        )
    except EmptyReportContentError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar relatório: {str(error)}",
        )