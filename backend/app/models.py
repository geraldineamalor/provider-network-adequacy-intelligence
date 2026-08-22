from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class Provider(Base):
    __tablename__ = "providers"

    provider_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # NPI is an identifier, not a number.
    npi = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )

    entity_type = Column(Integer, nullable=True)

    first_name = Column(String(100), nullable=True)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)

    organization_name = Column(String(255), nullable=True)
    provider_type = Column(String(50), nullable=True)

    credential = Column(String(100), nullable=True)

    address = Column(String(300), nullable=True)
    city = Column(String(150), nullable=True, index=True)
    state = Column(String(100), nullable=True, index=True)
    zip_code = Column(String(20), nullable=True)

    taxonomy_code = Column(
        String(50),
        nullable=True,
        index=True,
    )

    specialty = Column(String(200), nullable=True)

    enumeration_date = Column(Date, nullable=True)
    last_update_date = Column(Date, nullable=True)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    source = Column(
        String(100),
        nullable=False,
        default="NPPES",
    )

    created_at = Column(
        DateTime,
        nullable=True,
    )

    entity_type_code = Column(
        String(1),
        nullable=True,
    )

    locations = relationship(
        "ProviderLocation",
        back_populates="provider",
        cascade="all, delete-orphan",
    )


class ProviderLocation(Base):
    __tablename__ = "provider_locations"

    location_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    provider_id = Column(
        Integer,
        ForeignKey(
            "providers.provider_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    address = Column(String(500), nullable=True)
    city = Column(String(150), nullable=True)
    state = Column(String(150), nullable=True, index=True)
    zip_code = Column(String(20), nullable=True, index=True)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    provider = relationship(
        "Provider",
        back_populates="locations",
    )