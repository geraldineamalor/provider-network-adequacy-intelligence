from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db

from app.services.network_adequacy_service import (
    get_zip_adequacy,
    get_zip_adequacy_summary,
)


router = APIRouter(
    prefix="/network-adequacy",
    tags=["network adequacy"],
)


@router.get("/zip")
def zip_adequacy(
    zip_code: str = Query(...),
    db: Session = Depends(get_db),
):
    return get_zip_adequacy(
        db=db,
        zip_code=zip_code,
    )


@router.get("/zip-summary")
def zip_adequacy_summary(
    db: Session = Depends(get_db),
):
    return get_zip_adequacy_summary(db)