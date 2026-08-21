from pydantic import BaseModel, Field


# ML-2 inference contract (v3.2-specialty-context-merged).
# The trained model uses these five numeric features, in this exact order:
#   population, zip_provider_share_of_state, individual_provider_ratio,
#   organization_provider_ratio, specialty_diversity.
# zip_code and primary_taxonomy are metadata and must NOT be used as model features.


class MLInferenceRequest(BaseModel):
    zip_code: str = Field(..., description="ZIP code (metadata only, not a model feature)")
    population: int = Field(..., ge=0, description="Population for the ZIP area")
    zip_provider_share_of_state: float = Field(
        ..., ge=0.0, le=1.0, description="ZIP share of state providers (0.0 to 1.0)"
    )
    individual_provider_ratio: float = Field(
        ..., ge=0.0, le=1.0, description="Individual provider ratio (0.0 to 1.0)"
    )
    organization_provider_ratio: float = Field(
        ..., ge=0.0, le=1.0, description="Organization provider ratio (0.0 to 1.0)"
    )
    specialty_diversity: float = Field(
        ..., ge=0.0, le=1.0, description="Specialty diversity ratio (0.0 to 1.0)"
    )
    primary_taxonomy: str = Field(
        ..., description="Raw NPPES taxonomy code (PRIMARY_TAXONOMY)"
    )


class MLInferenceResponse(BaseModel):
    access_gap_score: float = Field(..., ge=0.0, le=1.0)
    gap_category: str
    prediction: int
    confidence: float = Field(..., ge=0.0, le=1.0)
    explanation: list[str]
    model_version: str
    recommendation: str