from copy import deepcopy
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.patient import Patient

PATIENTS_URL = "/api/v1/patients"
VAPI_URL = "/api/v1/vapi/create-patient"


def valid_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "first_name": "John",
        "last_name": "Smith",
        "date_of_birth": "01/15/1990",
        "sex": "Male",
        "phone_number": "4155551234",
        "email": "john@example.com",
        "address_line_1": "123 Main Street",
        "address_line_2": None,
        "city": "San Francisco",
        "state": "CA",
        "zip_code": "94105",
        "insurance_provider": "Example Insurance",
        "insurance_member_id": "ABC12345",
        "preferred_language": "English",
        "emergency_contact_name": "Jane Smith",
        "emergency_contact_phone": "4155555678",
    }
    payload.update(overrides)
    return payload


def created_patient(client: TestClient, **overrides: object) -> dict[str, object]:
    response = client.post(PATIENTS_URL, json=valid_payload(**overrides))
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["error"] is None
    return body["data"]


def test_create_valid_patient(client: TestClient) -> None:
    data = created_patient(
        client,
        first_name="Mary Jane",
        last_name="O'Connor",
        phone_number="(415) 555-1234",
        preferred_language=None,
    )
    assert UUID(data["patient_id"])
    assert data["first_name"] == "Mary Jane"
    assert data["last_name"] == "O'Connor"
    assert data["phone_number"] == "4155551234"
    assert data["date_of_birth"] == "01/15/1990"
    assert data["state"] == "CA"
    assert data["preferred_language"] == "English"
    assert data["deleted_at"] is None


def test_create_missing_required_field(client: TestClient) -> None:
    payload = valid_payload()
    del payload["first_name"]
    response = client.post(PATIENTS_URL, json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["data"] is None
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_create_invalid_first_name(client: TestClient) -> None:
    response = client.post(PATIENTS_URL, json=valid_payload(first_name="John123"))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_invalid_last_name(client: TestClient) -> None:
    response = client.post(PATIENTS_URL, json=valid_payload(last_name="Sm@th"))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_invalid_dob(client: TestClient) -> None:
    response = client.post(PATIENTS_URL, json=valid_payload(date_of_birth="02/30/1990"))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_future_dob(client: TestClient) -> None:
    response = client.post(PATIENTS_URL, json=valid_payload(date_of_birth="01/01/2099"))
    assert response.status_code == 422
    assert "future" in str(response.json()["error"]["details"]).lower()


def test_create_invalid_sex(client: TestClient) -> None:
    response = client.post(PATIENTS_URL, json=valid_payload(sex="Unknown"))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_invalid_phone(client: TestClient) -> None:
    response = client.post(PATIENTS_URL, json=valid_payload(phone_number="123"))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_invalid_email(client: TestClient) -> None:
    response = client.post(PATIENTS_URL, json=valid_payload(email="not-an-email"))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_invalid_state(client: TestClient) -> None:
    response = client.post(PATIENTS_URL, json=valid_payload(state="ZZ"))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_invalid_zip(client: TestClient) -> None:
    response = client.post(PATIENTS_URL, json=valid_payload(zip_code="1234"))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_invalid_emergency_phone(client: TestClient) -> None:
    response = client.post(PATIENTS_URL, json=valid_payload(emergency_contact_phone="555"))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_list_patients(client: TestClient) -> None:
    created_patient(client, phone_number="4155551001", last_name="Smith")
    created_patient(client, phone_number="4155551002", last_name="Demo")
    response = client.get(PATIENTS_URL)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2


def test_filter_by_last_name(client: TestClient) -> None:
    created_patient(client, phone_number="4155551001", last_name="Smith")
    created_patient(client, phone_number="4155551002", last_name="Demo")
    response = client.get(PATIENTS_URL, params={"last_name": "smith"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["last_name"] == "Smith"


def test_filter_by_dob(client: TestClient) -> None:
    created_patient(client, phone_number="4155551001", date_of_birth="01/15/1990")
    created_patient(client, phone_number="4155551002", date_of_birth="03/12/1988")
    response = client.get(PATIENTS_URL, params={"date_of_birth": "01/15/1990"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["date_of_birth"] == "01/15/1990"


def test_filter_by_phone(client: TestClient) -> None:
    created_patient(client, phone_number="4155551001")
    created_patient(client, phone_number="4155551002")
    response = client.get(PATIENTS_URL, params={"phone_number": "(415) 555-1002"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["phone_number"] == "4155551002"


def test_get_patient(client: TestClient) -> None:
    created = created_patient(client)
    response = client.get(f"{PATIENTS_URL}/{created['patient_id']}")
    assert response.status_code == 200
    assert response.json()["data"]["patient_id"] == created["patient_id"]


def test_get_patient_not_found(client: TestClient) -> None:
    response = client.get(f"{PATIENTS_URL}/{uuid4()}")
    assert response.status_code == 404
    body = response.json()
    assert body["data"] is None
    assert body["error"]["code"] == "PATIENT_NOT_FOUND"
    assert body["error"]["message"] == "Patient not found"


def test_partial_update(client: TestClient) -> None:
    created = created_patient(client)
    response = client.put(
        f"{PATIENTS_URL}/{created['patient_id']}",
        json={"email": "newemail@example.com", "phone_number": "4155559999"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["email"] == "newemail@example.com"
    assert data["phone_number"] == "4155559999"
    assert data["first_name"] == "John"
    assert data["updated_at"] != created["updated_at"]


def test_invalid_update(client: TestClient) -> None:
    created = created_patient(client)
    response = client.put(
        f"{PATIENTS_URL}/{created['patient_id']}",
        json={"email": "not-an-email"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_update_patient_not_found(client: TestClient) -> None:
    response = client.put(f"{PATIENTS_URL}/{uuid4()}", json={"city": "Oakland"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PATIENT_NOT_FOUND"


def test_soft_delete(client: TestClient, db_session: Session) -> None:
    created = created_patient(client)
    patient_id = created["patient_id"]
    response = client.delete(f"{PATIENTS_URL}/{patient_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["data"]["message"] == "Patient deleted successfully"

    db_session.expire_all()
    row = db_session.get(Patient, UUID(patient_id))
    assert row is not None
    assert row.deleted_at is not None


def test_deleted_patient_not_returned_in_list(client: TestClient) -> None:
    created = created_patient(client)
    client.delete(f"{PATIENTS_URL}/{created['patient_id']}")
    response = client.get(PATIENTS_URL)
    assert response.status_code == 200
    assert response.json()["data"] == []


def test_deleted_patient_cannot_be_fetched(client: TestClient) -> None:
    created = created_patient(client)
    client.delete(f"{PATIENTS_URL}/{created['patient_id']}")
    response = client.get(f"{PATIENTS_URL}/{created['patient_id']}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PATIENT_NOT_FOUND"


def test_deleted_patient_cannot_be_deleted_again(client: TestClient) -> None:
    created = created_patient(client)
    first = client.delete(f"{PATIENTS_URL}/{created['patient_id']}")
    second = client.delete(f"{PATIENTS_URL}/{created['patient_id']}")
    assert first.status_code == 200
    assert second.status_code == 404
    assert second.json()["error"]["code"] == "PATIENT_NOT_FOUND"


def test_duplicate_phone_number(client: TestClient) -> None:
    first = created_patient(client, phone_number="4155551234")
    second_payload = valid_payload(first_name="Jane", phone_number="415-555-1234")
    response = client.post(PATIENTS_URL, json=second_payload)
    assert response.status_code == 409
    body = response.json()
    assert body["data"] is None
    assert body["error"]["code"] == "DUPLICATE_PATIENT"
    assert body["error"]["details"]["patient_id"] == first["patient_id"]


def test_duplicate_allowed_after_soft_delete(client: TestClient) -> None:
    created = created_patient(client, phone_number="4155551234")
    client.delete(f"{PATIENTS_URL}/{created['patient_id']}")
    response = client.post(PATIENTS_URL, json=valid_payload(phone_number="4155551234"))
    assert response.status_code == 201
    assert response.json()["data"]["patient_id"] != created["patient_id"]


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"data": {"status": "ok"}, "error": None}


def test_database_health_endpoint(client: TestClient) -> None:
    response = client.get("/health/db")
    assert response.status_code == 200
    assert response.json() == {"data": {"status": "ok"}, "error": None}


def test_vapi_create_patient(client: TestClient) -> None:
    response = client.post(VAPI_URL, json=valid_payload(phone_number="4155554321"))
    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["data"]["status"] == "created"
    assert body["data"]["message"] == "Patient registration completed successfully."
    assert UUID(body["data"]["patient_id"])


def test_vapi_duplicate_patient(client: TestClient) -> None:
    created = created_patient(client, phone_number="4155554321")
    response = client.post(VAPI_URL, json=valid_payload(phone_number="4155554321"))
    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["data"]["status"] == "duplicate"
    assert body["data"]["patient_id"] == created["patient_id"]


def test_vapi_validation_error(client: TestClient) -> None:
    payload = deepcopy(valid_payload())
    payload["state"] = "California"
    response = client.post(VAPI_URL, json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_docs_available(client: TestClient) -> None:
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200
    assert client.get("/openapi.json").status_code == 200
