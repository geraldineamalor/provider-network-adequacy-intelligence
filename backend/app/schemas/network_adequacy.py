from typing import Optional

from pydantic import BaseModel


class LocationSummaryResponse(BaseModel):
    total_locations: int
    locations_with_coordinates: int
    locations_without_coordinates: int
    coordinate_coverage_percentage: float


class ProviderLocationResponse(BaseModel):
    location_id: int
    provider_id: int
    npi: str

    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    specialty: Optional[str] = None