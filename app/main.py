from fastapi import FastAPI

from app.config import settings
from app.routes.report_routes import router as report_router


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Microserviço responsável por gerar relatórios administrativos com IA.",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
    }


app.include_router(report_router)