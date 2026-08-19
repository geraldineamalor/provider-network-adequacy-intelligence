from app.schemas.analysis import AnalysisRequest
from app.services.data_service import get_provider_data


def run_analysis(request: AnalysisRequest) -> dict:
    """
    Run provider network adequacy analysis.
    """

    provider_data = get_provider_data(
        state=request.state,
        counties=request.counties,
        specialties=request.specialties,
    )

    return {
        "status": "success",
        "area": {
            "state": request.state,
            "counties": request.counties,
        },
        "specialties": request.specialties,
        "provider_data": provider_data,
        "message": "Analysis service is ready for data integration.",
    }