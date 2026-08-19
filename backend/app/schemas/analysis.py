from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    state: str = Field(..., min_length=2)
    counties: list[str] = Field(..., min_length=1)
    specialties: list[str] = Field(..., min_length=1)