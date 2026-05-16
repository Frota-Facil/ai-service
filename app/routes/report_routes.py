from fastapi import APIRouter, HTTPException

from app.schemas.report import (
    GenerateRawReportInput,
    GenerateReportOutput,
)
from app.services.openai_service import generate_raw_report


router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


@router.post("/fleet", response_model=GenerateReportOutput)
def create_fleet_report(data: GenerateRawReportInput):
    try:
        report = generate_raw_report(data)

        return GenerateReportOutput(report=report)

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar relatório: {str(error)}",
        )