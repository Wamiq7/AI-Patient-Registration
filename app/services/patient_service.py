import logging
from datetime import date
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicatePatientError, PatientNotFoundError
from app.core.validation import utc_now
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate

logger = logging.getLogger(__name__)


def _active_patient_by_id(db: Session, patient_id: UUID) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None or patient.deleted_at is not None:
        raise PatientNotFoundError()
    return patient


def find_active_by_phone(db: Session, phone_number: str) -> Patient | None:
    stmt: Select[tuple[Patient]] = select(Patient).where(
        Patient.phone_number == phone_number,
        Patient.deleted_at.is_(None),
    )
    return db.scalar(stmt)


def create_patient(db: Session, payload: PatientCreate) -> Patient:
    existing = find_active_by_phone(db, payload.phone_number)
    if existing is not None:
        logger.info(
            "patient_creation_rejected reason=duplicate patient_id=%s",
            existing.patient_id,
        )
        raise DuplicatePatientError(existing.patient_id)

    patient = Patient(**payload.model_dump())
    now = utc_now()
    patient.created_at = now
    patient.updated_at = now
    db.add(patient)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        duplicate = find_active_by_phone(db, payload.phone_number)
        if duplicate is not None:
            logger.info(
                "patient_creation_rejected reason=duplicate patient_id=%s",
                duplicate.patient_id,
            )
            raise DuplicatePatientError(duplicate.patient_id) from None
        logger.exception("patient_creation_failed reason=integrity_error")
        raise
    except SQLAlchemyError:
        db.rollback()
        logger.exception("patient_creation_failed reason=database_error")
        raise

    db.refresh(patient)
    logger.info("patient_created patient_id=%s", patient.patient_id)
    return patient


def list_patients(
    db: Session,
    last_name: str | None = None,
    date_of_birth: date | None = None,
    phone_number: str | None = None,
) -> list[Patient]:
    stmt: Select[tuple[Patient]] = select(Patient).where(Patient.deleted_at.is_(None))
    if last_name:
        stmt = stmt.where(func.lower(Patient.last_name) == last_name.lower())
    if date_of_birth is not None:
        stmt = stmt.where(Patient.date_of_birth == date_of_birth)
    if phone_number:
        stmt = stmt.where(Patient.phone_number == phone_number)
    stmt = stmt.order_by(Patient.created_at.desc())
    return list(db.scalars(stmt).all())


def get_patient(db: Session, patient_id: UUID) -> Patient:
    return _active_patient_by_id(db, patient_id)


def update_patient(db: Session, patient_id: UUID, payload: PatientUpdate) -> Patient:
    patient = _active_patient_by_id(db, patient_id)
    updates = payload.model_dump(exclude_unset=True)

    if "phone_number" in updates:
        duplicate = find_active_by_phone(db, updates["phone_number"])
        if duplicate is not None and duplicate.patient_id != patient.patient_id:
            raise DuplicatePatientError(duplicate.patient_id)

    for field_name, value in updates.items():
        setattr(patient, field_name, value)
    patient.updated_at = utc_now()

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.exception("patient_update_failed reason=integrity_error patient_id=%s", patient_id)
        phone = updates.get("phone_number", patient.phone_number)
        duplicate = find_active_by_phone(db, phone)
        if duplicate is not None and duplicate.patient_id != patient_id:
            raise DuplicatePatientError(duplicate.patient_id) from None
        raise
    except SQLAlchemyError:
        db.rollback()
        logger.exception("patient_update_failed reason=database_error patient_id=%s", patient_id)
        raise

    db.refresh(patient)
    logger.info("patient_updated patient_id=%s", patient.patient_id)
    return patient


def soft_delete_patient(db: Session, patient_id: UUID) -> None:
    patient = _active_patient_by_id(db, patient_id)
    patient.deleted_at = utc_now()
    patient.updated_at = patient.deleted_at
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("patient_delete_failed reason=database_error patient_id=%s", patient_id)
        raise
    logger.info("patient_deleted patient_id=%s", patient.patient_id)
