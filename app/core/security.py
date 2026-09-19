import hmac
from typing import Annotated

from fastapi import Header

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError


def verify_vapi_api_key(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> None:
    expected = get_settings().vapi_api_key
    if not expected:
        return
    provided = x_api_key or ""
    if len(provided) != len(expected) or not hmac.compare_digest(provided, expected):
        raise UnauthorizedError()
