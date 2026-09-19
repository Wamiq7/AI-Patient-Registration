from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.patient import (
    DeleteMessage,
    Envelope,
    PatientListFilters,
    PatientResponse,
    PatientUpdate,
)
from app.services.patient_service import (
    get_patient,
    list_patients,
    soft_delete_patient,
    update_patient,
)

router = APIRouter(prefix="/patients", tags=["Patients"])


def _patient_envelope(patient: object) -> dict[str, object]:
    return {"data": PatientResponse.model_validate(patient), "error": None}


@router.get(
    "",
    response_model=Envelope,
    summary="List patients",
)
def list_patients_endpoint(
    db: Annotated[Session, Depends(get_db)],
    last_name: Annotated[str | None, Query(examples=["Smith"])] = None,
    date_of_birth: Annotated[str | None, Query(examples=["01/15/1990"])] = None,
    phone_number: Annotated[str | None, Query(examples=["4155551234"])] = None,
) -> dict[str, object]:
    try:
        filters = PatientListFilters.model_validate(
            {
                "last_name": last_name,
                "date_of_birth": date_of_birth,
                "phone_number": phone_number,
            }
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc

    patients = list_patients(
        db,
        last_name=filters.last_name,
        date_of_birth=filters.date_of_birth,
        phone_number=filters.phone_number,
    )
    return {
        "data": [PatientResponse.model_validate(patient) for patient in patients],
        "error": None,
    }


@router.get(
    "/{patient_id}",
    response_model=Envelope,
    summary="Get patient",
)
def get_patient_endpoint(
    patient_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    patient = get_patient(db, patient_id)
    return _patient_envelope(patient)


@router.put(
    "/{patient_id}",
    response_model=Envelope,
    summary="Update patient",
)
def update_patient_endpoint(
    patient_id: UUID,
    payload: PatientUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    patient = update_patient(db, patient_id, payload)
    return _patient_envelope(patient)


@router.delete(
    "/{patient_id}",
    response_model=Envelope,
    summary="Delete patient",
)
def delete_patient_endpoint(
    patient_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    soft_delete_patient(db, patient_id)
    return {"data": DeleteMessage(), "error": None}
