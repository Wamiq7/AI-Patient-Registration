"""Load a few fictional patients for local demos."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import SessionLocal
from app.core.validation import utc_now
from app.models.patient import Patient

FAKE_PATIENTS: list[dict[str, object]] = [
    {
        "first_name": "Alice",
        "last_name": "Demo",
        "date_of_birth": date(1988, 3, 12),
        "sex": "Female",
        "phone_number": "4155550001",
        "email": "alice.demo@example.com",
        "address_line_1": "100 Fiction Lane",
        "address_line_2": None,
        "city": "San Francisco",
        "state": "CA",
        "zip_code": "94105",
        "insurance_provider": "Demo Health Plan",
        "insurance_member_id": "DEMO-1001",
        "preferred_language": "English",
        "emergency_contact_name": "Bob Demo",
        "emergency_contact_phone": "4155550002",
    },
    {
        "first_name": "Bob",
        "last_name": "Testpatient",
        "date_of_birth": date(1976, 7, 4),
        "sex": "Male",
        "phone_number": "2125550003",
        "email": "bob.testpatient@example.com",
        "address_line_1": "50 Sample Street",
        "address_line_2": "Unit 2",
        "city": "New York",
        "state": "NY",
        "zip_code": "10001",
        "insurance_provider": None,
        "insurance_member_id": None,
        "preferred_language": "English",
        "emergency_contact_name": None,
        "emergency_contact_phone": None,
    },
    {
        "first_name": "Maria",
        "last_name": "Sample",
        "date_of_birth": date(1992, 11, 22),
        "sex": "Other",
        "phone_number": "3055550004",
        "email": None,
        "address_line_1": "9 Placeholder Ave",
        "address_line_2": None,
        "city": "Miami",
        "state": "FL",
        "zip_code": "33101-1234",
        "insurance_provider": "Example Insurance",
        "insurance_member_id": "EX12345",
        "preferred_language": "Spanish",
        "emergency_contact_name": "Carlos Sample",
        "emergency_contact_phone": "3055550005",
    },
]


def seed() -> None:
    db = SessionLocal()
    created = 0
    skipped = 0
    try:
        for item in FAKE_PATIENTS:
            exists = db.scalar(
                select(Patient).where(Patient.phone_number == item["phone_number"])
            )
            if exists is not None:
                skipped += 1
                continue
            now = utc_now()
            db.add(Patient(**item, created_at=now, updated_at=now))
            created += 1
        db.commit()
        print(f"Seed complete. created={created} skipped={skipped}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
