import re
from datetime import date, datetime, timezone

NAME_PATTERN = re.compile(r"^[A-Za-z]+(?:[ '\-][A-Za-z]+)*$")
ZIP_CODE_PATTERN = re.compile(r"^\d{5}(?:-\d{4})?$")
INSURANCE_MEMBER_ID_PATTERN = re.compile(r"^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$")
DATE_OF_BIRTH_PATTERN = re.compile(r"^\d{2}/\d{2}/\d{4}$")

ALLOWED_SEX_VALUES: tuple[str, ...] = (
    "Male",
    "Female",
    "Other",
    "Decline to Answer",
)

US_STATES: frozenset[str] = frozenset(
    {
        "AL",
        "AK",
        "AZ",
        "AR",
        "CA",
        "CO",
        "CT",
        "DE",
        "FL",
        "GA",
        "HI",
        "ID",
        "IL",
        "IN",
        "IA",
        "KS",
        "KY",
        "LA",
        "ME",
        "MD",
        "MA",
        "MI",
        "MN",
        "MS",
        "MO",
        "MT",
        "NE",
        "NV",
        "NH",
        "NJ",
        "NM",
        "NY",
        "NC",
        "ND",
        "OH",
        "OK",
        "OR",
        "PA",
        "RI",
        "SC",
        "SD",
        "TN",
        "TX",
        "UT",
        "VT",
        "VA",
        "WA",
        "WV",
        "WI",
        "WY",
        "DC",
    }
)


def utc_today() -> date:
    return datetime.now(timezone.utc).date()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def blank_to_none(value: object) -> object:
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def validate_person_name(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} is required")
    cleaned = re.sub(r"\s+", " ", value.strip())
    if not 1 <= len(cleaned) <= 50:
        raise ValueError(f"{field_name} must be between 1 and 50 characters")
    if not NAME_PATTERN.fullmatch(cleaned):
        raise ValueError(
            f"{field_name} may contain letters, spaces, hyphens, and apostrophes only"
        )
    return cleaned


def parse_date_of_birth(value: object) -> date:
    if isinstance(value, datetime):
        parsed = value.date()
    elif isinstance(value, date):
        parsed = value
    elif isinstance(value, str):
        raw = value.strip()
        if not DATE_OF_BIRTH_PATTERN.fullmatch(raw):
            raise ValueError(
                "date_of_birth must be a valid calendar date in MM/DD/YYYY format"
            )
        try:
            parsed = datetime.strptime(raw, "%m/%d/%Y").date()
        except ValueError as exc:
            raise ValueError(
                "date_of_birth must be a valid calendar date in MM/DD/YYYY format"
            ) from exc
    else:
        raise ValueError(
            "date_of_birth must be a valid calendar date in MM/DD/YYYY format"
        )

    if parsed > utc_today():
        raise ValueError("date_of_birth cannot be in the future")
    return parsed


def format_date_of_birth(value: date) -> str:
    return value.strftime("%m/%d/%Y")


def normalize_sex(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("sex must be Male, Female, Other, or Decline to Answer")
    cleaned = re.sub(r"\s+", " ", value.strip())
    for allowed in ALLOWED_SEX_VALUES:
        if cleaned.casefold() == allowed.casefold():
            return allowed
    raise ValueError("sex must be Male, Female, Other, or Decline to Answer")


def normalize_us_phone(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Phone number must be a valid U.S. 10-digit number")

    digits = re.sub(r"\D", "", value)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError("Phone number must be a valid U.S. 10-digit number")
    if digits[0] in "01" or digits[3] in "01":
        raise ValueError("Phone number must be a valid U.S. 10-digit number")
    return digits


def normalize_state(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("state must be a valid 2-letter U.S. state abbreviation")
    code = value.strip().upper()
    if code not in US_STATES:
        raise ValueError("state must be a valid 2-letter U.S. state abbreviation")
    return code


def normalize_zip_code(value: object) -> str:
    if not isinstance(value, str) or not ZIP_CODE_PATTERN.fullmatch(value.strip()):
        raise ValueError("zip_code must be in 12345 or 12345-6789 format")
    return value.strip()


def normalize_insurance_member_id(value: object) -> str | None:
    value = blank_to_none(value)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("insurance_member_id must be alphanumeric")
    cleaned = value.strip()
    if len(cleaned) > 255:
        raise ValueError("insurance_member_id must be 255 characters or fewer")
    if not INSURANCE_MEMBER_ID_PATTERN.fullmatch(cleaned):
        raise ValueError(
            "insurance_member_id may contain letters, numbers, and hyphens only"
        )
    return cleaned


def normalize_optional_text(value: object, field_name: str, max_length: int) -> str | None:
    value = blank_to_none(value)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    cleaned = re.sub(r"\s+", " ", value.strip())
    if not cleaned:
        return None
    if len(cleaned) > max_length:
        raise ValueError(f"{field_name} must be {max_length} characters or fewer")
    return cleaned


def normalize_required_text(value: object, field_name: str, max_length: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    cleaned = re.sub(r"\s+", " ", value.strip())
    if not cleaned:
        raise ValueError(f"{field_name} is required")
    if len(cleaned) > max_length:
        raise ValueError(f"{field_name} must be {max_length} characters or fewer")
    return cleaned


def normalize_preferred_language(value: object) -> str:
    cleaned = normalize_optional_text(value, "preferred_language", 100)
    return cleaned or "English"


def normalize_optional_phone(value: object) -> str | None:
    value = blank_to_none(value)
    if value is None:
        return None
    return normalize_us_phone(value)
