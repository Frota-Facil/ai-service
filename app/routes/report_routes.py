from fastapi import APIRouter, HTTPException

from app.errors.report_errors import EmptyReportContentError, ReportGenerationError
from app.schemas.report import (
    GenerateRouteReportInput,
    GenerateRouteReportOutput,
)
from app.services.openai_service import generate_route_report


router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


@router.post("/routes", response_model=GenerateRouteReportOutput)
def create_route_report(data: GenerateRouteReportInput):
    try:
        markdown_content = generate_route_report(data)

        return GenerateRouteReportOutput(
            markdown_content=markdown_content,
        )

    except EmptyReportContentError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error

    except ReportGenerationError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao gerar relatório da rota.",
        ) from error
