import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import DatabaseUnavailableError
from app.schemas.patient import Envelope, HealthStatus

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=Envelope, summary="Health")
def health() -> dict[str, object]:
    return {"data": HealthStatus(status="ok"), "error": None}


@router.get("/health/db", response_model=Envelope, summary="Database health")
def health_db(db: Annotated[Session, Depends(get_db)]) -> dict[str, object]:
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("database_health_check_failed")
        raise DatabaseUnavailableError() from None
    return {"data": HealthStatus(status="ok"), "error": None}
