from pydantic import BaseModel, Field

from app.data.specialties import Specialty


class AnalysisRequest(BaseModel):
    state: str = Field(..., min_length=2)
    counties: list[str] = Field(..., min_length=1)
    specialties: list[Specialty] = Field(..., min_length=1)