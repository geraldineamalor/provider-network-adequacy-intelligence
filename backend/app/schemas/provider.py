from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider_id: int

    npi: str = Field(
        pattern=r"^\d{10,20}$"
    )

    entity_type: Optional[int] = None

    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None

    organization_name: Optional[str] = None
    provider_type: Optional[str] = None
    credential: Optional[str] = None

    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None

    taxonomy_code: Optional[str] = None
    specialty: Optional[str] = None

    enumeration_date: Optional[date] = None
    last_update_date: Optional[date] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    source: str

    created_at: Optional[datetime] = None

    entity_type_code: Optional[str] = None