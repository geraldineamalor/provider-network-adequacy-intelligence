from fastapi import APIRouter

from app.schemas.analysis import AnalysisRequest
from app.services.analysis_service import run_analysis


router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.get("/health")
def analysis_health():
    return {
        "status": "ok",
        "module": "analysis"
    }


@router.post("/")
def create_analysis(request: AnalysisRequest):
    return run_analysis(request)