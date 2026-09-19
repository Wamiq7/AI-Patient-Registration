from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer, field_validator, model_validator

from app.core.validation import (
    format_date_of_birth,
    normalize_insurance_member_id,
    normalize_optional_phone,
    normalize_optional_text,
    normalize_preferred_language,
    normalize_required_text,
    normalize_sex,
    normalize_state,
    normalize_us_phone,
    normalize_zip_code,
    parse_date_of_birth,
    validate_person_name,
)


class ErrorBody(BaseModel):
    code: str = Field(examples=["VALIDATION_ERROR"])
    message: str = Field(examples=["Invalid patient data"])
    details: dict[str, Any] | None = Field(
        default=None,
        examples=[{"first_name": "first_name may contain letters, spaces, hyphens, and apostrophes only"}],
    )


class Envelope(BaseModel):
    data: Any | None = None
    error: ErrorBody | None = None


class PatientBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    first_name: str = Field(
        ...,
        description="Letters, spaces, hyphens, and apostrophes. 1-50 characters.",
        examples=["Mary Jane"],
    )
    last_name: str = Field(
        ...,
        description="Letters, spaces, hyphens, and apostrophes. 1-50 characters.",
        examples=["O'Connor"],
    )
    date_of_birth: date = Field(
        ...,
        description="Date of birth in MM/DD/YYYY format. Must be a real past calendar date.",
        examples=["01/15/1990"],
    )
    sex: str = Field(
        ...,
        description="One of: Male, Female, Other, Decline to Answer.",
        examples=["Male"],
    )
    phone_number: str = Field(
        ...,
        description="U.S. phone number. Formatting is accepted and stored as 10 digits.",
        examples=["(415) 555-1234"],
    )
    email: EmailStr | None = Field(
        default=None,
        description="Optional email address.",
        examples=["john@example.com"],
    )
    address_line_1: str = Field(
        ...,
        description="Primary street address.",
        examples=["123 Main Street"],
    )
    address_line_2: str | None = Field(
        default=None,
        description="Optional apartment, suite, or additional address line.",
        examples=["Apt 4B"],
    )
    city: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="City name. 1-100 characters.",
        examples=["San Francisco"],
    )
    state: str = Field(
        ...,
        description="Two-letter U.S. state abbreviation, including DC.",
        examples=["CA"],
    )
    zip_code: str = Field(
        ...,
        description="ZIP code in 12345 or 12345-6789 format.",
        examples=["94105"],
    )
    insurance_provider: str | None = Field(
        default=None,
        description="Optional insurance provider name.",
        examples=["Example Insurance"],
    )
    insurance_member_id: str | None = Field(
        default=None,
        description="Optional alphanumeric insurance member ID. Hyphens allowed.",
        examples=["ABC-12345"],
    )
    preferred_language: str | None = Field(
        default="English",
        description="Preferred language. Defaults to English when omitted.",
        examples=["English"],
    )
    emergency_contact_name: str | None = Field(
        default=None,
        description="Optional emergency contact name.",
        examples=["Jane Smith"],
    )
    emergency_contact_phone: str | None = Field(
        default=None,
        description="Optional U.S. emergency contact phone number.",
        examples=["4155555678"],
    )

    @field_validator("first_name")
    @classmethod
    def validate_first_name(cls, value: str) -> str:
        return validate_person_name(value, "first_name")

    @field_validator("last_name")
    @classmethod
    def validate_last_name(cls, value: str) -> str:
        return validate_person_name(value, "last_name")

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def validate_date_of_birth(cls, value: object) -> date:
        return parse_date_of_birth(value)

    @field_validator("sex")
    @classmethod
    def validate_sex(cls, value: str) -> str:
        return normalize_sex(value)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        return normalize_us_phone(value)

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: object) -> object:
        if isinstance(value, str) and value.strip() == "":
            return None
        return value

    @field_validator("address_line_1")
    @classmethod
    def validate_address_line_1(cls, value: str) -> str:
        return normalize_required_text(value, "address_line_1", 255)

    @field_validator("address_line_2", mode="before")
    @classmethod
    def validate_address_line_2(cls, value: object) -> str | None:
        return normalize_optional_text(value, "address_line_2", 255)

    @field_validator("city")
    @classmethod
    def validate_city(cls, value: str) -> str:
        return normalize_required_text(value, "city", 100)

    @field_validator("state")
    @classmethod
    def validate_state(cls, value: str) -> str:
        return normalize_state(value)

    @field_validator("zip_code")
    @classmethod
    def validate_zip_code(cls, value: str) -> str:
        return normalize_zip_code(value)

    @field_validator("insurance_provider", mode="before")
    @classmethod
    def validate_insurance_provider(cls, value: object) -> str | None:
        return normalize_optional_text(value, "insurance_provider", 255)

    @field_validator("insurance_member_id", mode="before")
    @classmethod
    def validate_insurance_member_id(cls, value: object) -> str | None:
        return normalize_insurance_member_id(value)

    @field_validator("preferred_language", mode="before")
    @classmethod
    def validate_preferred_language(cls, value: object) -> str:
        return normalize_preferred_language(value)

    @field_validator("emergency_contact_name", mode="before")
    @classmethod
    def validate_emergency_contact_name(cls, value: object) -> str | None:
        return normalize_optional_text(value, "emergency_contact_name", 255)

    @field_validator("emergency_contact_phone", mode="before")
    @classmethod
    def validate_emergency_contact_phone(cls, value: object) -> str | None:
        return normalize_optional_phone(value)


class PatientCreate(PatientBase):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
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
            ]
        },
    )


class PatientUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    sex: str | None = None
    phone_number: str | None = None
    email: EmailStr | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    insurance_provider: str | None = None
    insurance_member_id: str | None = None
    preferred_language: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None

    @model_validator(mode="after")
    def validate_update_payload(self) -> "PatientUpdate":
        provided = self.model_dump(exclude_unset=True)
        if not provided:
            raise ValueError("At least one field must be provided")
        required_if_present = {
            "first_name",
            "last_name",
            "date_of_birth",
            "sex",
            "phone_number",
            "address_line_1",
            "city",
            "state",
            "zip_code",
        }
        for field_name in required_if_present:
            if field_name in provided and provided[field_name] is None:
                raise ValueError(f"{field_name} cannot be null")
        return self

    @field_validator("first_name")
    @classmethod
    def validate_first_name(cls, value: str | None) -> str | None:
        return validate_person_name(value, "first_name") if value is not None else None

    @field_validator("last_name")
    @classmethod
    def validate_last_name(cls, value: str | None) -> str | None:
        return validate_person_name(value, "last_name") if value is not None else None

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def validate_date_of_birth(cls, value: object) -> date | None:
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return None
        return parse_date_of_birth(value)

    @field_validator("sex")
    @classmethod
    def validate_sex(cls, value: str | None) -> str | None:
        return normalize_sex(value) if value is not None else None

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str | None) -> str | None:
        return normalize_us_phone(value) if value is not None else None

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: object) -> object:
        if isinstance(value, str) and value.strip() == "":
            return None
        return value

    @field_validator("address_line_1")
    @classmethod
    def validate_address_line_1(cls, value: str | None) -> str | None:
        return normalize_required_text(value, "address_line_1", 255) if value is not None else None

    @field_validator("address_line_2", mode="before")
    @classmethod
    def validate_address_line_2(cls, value: object) -> str | None:
        return normalize_optional_text(value, "address_line_2", 255)

    @field_validator("city")
    @classmethod
    def validate_city(cls, value: str | None) -> str | None:
        return normalize_required_text(value, "city", 100) if value is not None else None

    @field_validator("state")
    @classmethod
    def validate_state(cls, value: str | None) -> str | None:
        return normalize_state(value) if value is not None else None

    @field_validator("zip_code")
    @classmethod
    def validate_zip_code(cls, value: str | None) -> str | None:
        return normalize_zip_code(value) if value is not None else None

    @field_validator("insurance_provider", mode="before")
    @classmethod
    def validate_insurance_provider(cls, value: object) -> str | None:
        return normalize_optional_text(value, "insurance_provider", 255)

    @field_validator("insurance_member_id", mode="before")
    @classmethod
    def validate_insurance_member_id(cls, value: object) -> str | None:
        return normalize_insurance_member_id(value)

    @field_validator("preferred_language", mode="before")
    @classmethod
    def validate_preferred_language(cls, value: object) -> str | None:
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return None
        return normalize_preferred_language(value)

    @field_validator("emergency_contact_name", mode="before")
    @classmethod
    def validate_emergency_contact_name(cls, value: object) -> str | None:
        return normalize_optional_text(value, "emergency_contact_name", 255)

    @field_validator("emergency_contact_phone", mode="before")
    @classmethod
    def validate_emergency_contact_phone(cls, value: object) -> str | None:
        return normalize_optional_phone(value)


class PatientListFilters(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    last_name: str | None = Field(default=None, examples=["Smith"])
    date_of_birth: date | None = Field(default=None, examples=["01/15/1990"])
    phone_number: str | None = Field(default=None, examples=["4155551234"])

    @field_validator("last_name", mode="before")
    @classmethod
    def validate_last_name(cls, value: object) -> str | None:
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return None
        if not isinstance(value, str):
            raise ValueError("last_name must be a string")
        return value.strip()

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def validate_date_of_birth(cls, value: object) -> date | None:
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return None
        return parse_date_of_birth(value)

    @field_validator("phone_number", mode="before")
    @classmethod
    def validate_phone_number(cls, value: object) -> str | None:
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return None
        return normalize_us_phone(value)


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    patient_id: UUID
    first_name: str
    last_name: str
    date_of_birth: date
    sex: str
    phone_number: str
    email: str | None
    address_line_1: str
    address_line_2: str | None
    city: str
    state: str
    zip_code: str
    insurance_provider: str | None
    insurance_member_id: str | None
    preferred_language: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @field_serializer("date_of_birth")
    def serialize_date_of_birth(self, value: date) -> str:
        return format_date_of_birth(value)


class DeleteMessage(BaseModel):
    message: str = "Patient deleted successfully"


class VapiCreateResult(BaseModel):
    patient_id: str
    status: str
    message: str


class HealthStatus(BaseModel):
    status: str = Field(examples=["ok"])
