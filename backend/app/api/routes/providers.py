from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.provider import ProviderResponse
from app.services.provider_service import (
    get_provider_by_npi,
    get_providers,
    get_summary,
)


router = APIRouter(
    prefix="/providers",
    tags=["providers"],
)


@router.get(
    "",
    response_model=list[ProviderResponse],
)
def list_providers(
    state: Optional[str] = Query(default=None),
    city: Optional[str] = Query(default=None),
    zip_code: Optional[str] = Query(default=None),
    taxonomy_code: Optional[str] = Query(default=None),
    entity_type: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_providers(
        db=db,
        state=state,
        city=city,
        zip_code=zip_code,
        taxonomy_code=taxonomy_code,
        entity_type=entity_type,
    )


@router.get(
    "/summary",
)
def provider_summary(
    db: Session = Depends(get_db),
):
    return get_summary(db)


@router.get(
    "/{npi}",
    response_model=ProviderResponse,
)
def provider_by_npi(
    npi: str,
    db: Session = Depends(get_db),
):
    provider = get_provider_by_npi(db, npi)

    if provider is None:
        raise HTTPException(
            status_code=404,
            detail="Provider not found",
        )

    return provider