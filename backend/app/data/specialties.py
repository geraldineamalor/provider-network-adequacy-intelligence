from enum import Enum


class Specialty(str, Enum):
    CARDIOLOGY = "Cardiology"
    PEDIATRICS = "Pediatrics"
    ORTHOPEDICS = "Orthopedics"
    DERMATOLOGY = "Dermatology"
    FAMILY_MEDICINE = "Family Medicine"
    PSYCHIATRY = "Psychiatry"
    NEUROLOGY = "Neurology"
    ONCOLOGY = "Oncology"
    INTERNAL_MEDICINE = "Internal Medicine"
    EMERGENCY_MEDICINE = "Emergency Medicine"
    OBSTETRICS_GYNECOLOGY = "Obstetrics & Gynecology"
    ENDOCRINOLOGY = "Endocrinology"


CANONICAL_SPECIALTIES: tuple[Specialty, ...] = tuple(Specialty)

CANONICAL_SPECIALTY_NAMES: tuple[str, ...] = tuple(
    specialty.value for specialty in Specialty
)