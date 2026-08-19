from fastapi import APIRouter

from app.schemas.specialty import SpecialtyItem
from app.services.specialty_service import get_specialties


router = APIRouter(prefix="/specialties", tags=["Specialties"])


@router.get("", response_model=list[SpecialtyItem])
def list_specialties() -> list[dict[str, int | str]]:
    return get_specialties()