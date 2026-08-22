from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Provider, ProviderLocation


def get_providers(
    db: Session,
    state: Optional[str] = None,
    city: Optional[str] = None,
    zip_code: Optional[str] = None,
    taxonomy_code: Optional[str] = None,
    entity_type: Optional[int] = None,
) -> list[Provider]:

    query = (
        select(Provider)
        .join(ProviderLocation)
        .distinct()
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

    if taxonomy_code:
        query = query.where(
            Provider.taxonomy_code == taxonomy_code
        )

    if entity_type is not None:
        query = query.where(
            Provider.entity_type == entity_type
        )

    query = query.order_by(Provider.provider_id)

    return list(db.scalars(query).all())

def get_provider_by_npi(
    db: Session,
    npi: str,
) -> Optional[Provider]:

    query = select(Provider).where(
        Provider.npi == npi
    )

    return db.scalar(query)


def get_summary(db: Session) -> dict:

    total_providers = db.scalar(
        select(func.count(Provider.provider_id))
    ) or 0

    total_locations = db.scalar(
        select(func.count(ProviderLocation.location_id))
    ) or 0

    state_rows = db.execute(
        select(
            ProviderLocation.state,
            func.count(func.distinct(Provider.provider_id)),
        )
        .join(Provider)
        .where(ProviderLocation.state.is_not(None))
        .group_by(ProviderLocation.state)
    ).all()

    zip_rows = db.execute(
        select(
            ProviderLocation.zip_code,
            func.count(func.distinct(Provider.provider_id)),
        )
        .join(Provider)
        .where(ProviderLocation.zip_code.is_not(None))
        .group_by(ProviderLocation.zip_code)
    ).all()

    taxonomy_rows = db.execute(
        select(
            Provider.taxonomy_code,
            func.count(Provider.provider_id),
        )
        .where(Provider.taxonomy_code.is_not(None))
        .group_by(Provider.taxonomy_code)
    ).all()

    specialty_rows = db.execute(
        select(
            Provider.specialty,
            func.count(Provider.provider_id),
        )
        .where(Provider.specialty.is_not(None))
        .group_by(Provider.specialty)
    ).all()

    return {
        "total_providers": total_providers,
        "total_locations": total_locations,
        "provider_count_by_state": {
            state: count for state, count in state_rows
        },
        "provider_count_by_zip": {
            zip_code: count for zip_code, count in zip_rows
        },
        "provider_count_by_taxonomy": {
            taxonomy: count for taxonomy, count in taxonomy_rows
        },
        "provider_count_by_specialty": {
            specialty: count for specialty, count in specialty_rows
        },
    }