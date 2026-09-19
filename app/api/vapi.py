import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import DuplicatePatientError
from app.core.security import verify_api_key
from app.schemas.patient import Envelope, PatientCreate, VapiCreateResult
from app.services.patient_service import create_patient

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/vapi",
    tags=["Vapi"],
    dependencies=[Depends(verify_api_key)],
)


@router.post(
    "/create-patient",
    response_model=Envelope,
    summary="Create patient (Vapi)",
)
def create_patient_from_vapi(
    payload: PatientCreate,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    try:
        patient = create_patient(db, payload)
    except DuplicatePatientError as exc:
        patient_id = str(exc.details["patient_id"]) if exc.details else ""
        logger.info("vapi_duplicate_patient patient_id=%s", patient_id)
        return {
            "data": VapiCreateResult(
                patient_id=patient_id,
                status="duplicate",
                message="A patient with this phone number already exists.",
            ),
            "error": None,
        }

    logger.info("vapi_patient_created patient_id=%s", patient.patient_id)
    return {
        "data": VapiCreateResult(
            patient_id=str(patient.patient_id),
            status="created",
            message="Patient registration completed successfully.",
        ),
        "error": None,
    }
