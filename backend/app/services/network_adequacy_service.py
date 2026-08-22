from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Provider, ProviderLocation


def get_location_summary(db: Session) -> dict:
    """
    Returns overall provider location and coordinate coverage.
    """

    total_locations = db.scalar(
        select(func.count(ProviderLocation.location_id))
    ) or 0

    locations_with_coordinates = db.scalar(
        select(func.count(ProviderLocation.location_id))
        .where(
            ProviderLocation.latitude.is_not(None),
            ProviderLocation.longitude.is_not(None),
        )
    ) or 0

    locations_without_coordinates = (
        total_locations - locations_with_coordinates
    )

    coverage_percentage = (
        (locations_with_coordinates / total_locations) * 100
        if total_locations
        else 0
    )

    return {
        "total_locations": total_locations,
        "locations_with_coordinates": locations_with_coordinates,
        "locations_without_coordinates": locations_without_coordinates,
        "coordinate_coverage_percentage": round(
            coverage_percentage,
            2,
        ),
    }


def get_provider_locations(
    db: Session,
    state: Optional[str] = None,
    city: Optional[str] = None,
    zip_code: Optional[str] = None,
):
    """
    Returns provider locations with geographic coordinates.
    """

    query = (
        select(
            ProviderLocation.location_id,
            ProviderLocation.provider_id,
            Provider.npi,
            ProviderLocation.address,
            ProviderLocation.city,
            ProviderLocation.state,
            ProviderLocation.zip_code,
            ProviderLocation.latitude,
            ProviderLocation.longitude,
            Provider.specialty,
        )
        .join(
            Provider,
            Provider.provider_id == ProviderLocation.provider_id,
        )
        .where(
            ProviderLocation.latitude.is_not(None),
            ProviderLocation.longitude.is_not(None),
        )
    )

    if state:
        query = query.where(
            ProviderLocation.state == state.upper()
        )

    if city:
        query = query.where(
            ProviderLocation.city == city.upper()
        )

    if zip_code:
        query = query.where(
            ProviderLocation.zip_code == zip_code
        )

    query = query.order_by(
        ProviderLocation.location_id
    )

    return db.execute(query).mappings().all()
def get_zip_adequacy(
    db: Session,
    zip_code: str,
) -> dict:
    """
    Calculates basic provider network adequacy for a ZIP code.
    """

    provider_count = db.scalar(
        select(func.count(func.distinct(Provider.provider_id)))
        .join(
            ProviderLocation,
            Provider.provider_id == ProviderLocation.provider_id,
        )
        .where(
            ProviderLocation.zip_code.like(f"{zip_code}%")
        )
    ) or 0

    location_count = db.scalar(
        select(func.count(ProviderLocation.location_id))
        .where(
            ProviderLocation.zip_code.like(f"{zip_code}%")
        )
    ) or 0

    if provider_count == 0:
        status = "UNDERSERVED"
    elif provider_count < 5:
        status = "MODERATE"
    else:
        status = "ADEQUATE"

    return {
        "zip_code": zip_code,
        "provider_count": provider_count,
        "location_count": location_count,
        "status": status,
    }
def get_zip_adequacy_summary(db: Session) -> list[dict]:
    """
    Returns provider network adequacy summary for all ZIP codes.
    """

    rows = db.execute(
        select(
            ProviderLocation.zip_code,
            func.count(func.distinct(Provider.provider_id)).label(
                "provider_count"
            ),
            func.count(ProviderLocation.location_id).label(
                "location_count"
            ),
        )
        .join(
            Provider,
            Provider.provider_id == ProviderLocation.provider_id,
        )
        .where(
            ProviderLocation.zip_code.is_not(None)
        )
        .group_by(
            ProviderLocation.zip_code
        )
        .order_by(
            ProviderLocation.zip_code
        )
    ).all()

    result = []

    for zip_code, provider_count, location_count in rows:

        if provider_count == 0:
            status = "UNDERSERVED"
        elif provider_count < 5:
            status = "MODERATE"
        else:
            status = "ADEQUATE"

        result.append(
            {
                "zip_code": zip_code,
                "provider_count": provider_count,
                "location_count": location_count,
                "status": status,
            }
        )

    return result