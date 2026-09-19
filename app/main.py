import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from app.api.health import router as health_router
from app.api.patients import router as patients_router
from app.api.vapi import router as vapi_router
from app.core.config import get_settings
from app.core.database import create_tables
from app.core.exceptions import AppError
from app.core.logging import setup_logging

logger = logging.getLogger(__name__)
settings = get_settings()
setup_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    create_tables()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Patient registration API used by a Vapi voice assistant. All fields are validated server-side before write.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan,
)


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: object = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "data": None,
            "error": {
                "code": code,
                "message": message,
                "details": jsonable_encoder(details),
            },
        },
    )


@app.middleware("http")
async def log_requests(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    response = await call_next(request)
    logger.info(
        "request method=%s path=%s status=%s",
        request.method,
        request.url.path,
        response.status_code,
    )
    return response


@app.exception_handler(RequestValidationError)
def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    details: dict[str, str] = {}
    for error in exc.errors():
        location = ".".join(str(part) for part in error.get("loc", ()) if part != "body")
        details[location or "request"] = error.get("msg", "Invalid value")
    logger.info(
        "validation_error method=%s path=%s fields=%s",
        request.method,
        request.url.path,
        ",".join(sorted(details.keys())) or "unknown",
    )
    return error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message="Invalid patient data",
        details=details,
    )


@app.exception_handler(AppError)
def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.info(
        "app_error method=%s path=%s code=%s status=%s",
        request.method,
        request.url.path,
        exc.code,
        exc.status_code,
    )
    return error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


@app.exception_handler(StarletteHTTPException)
def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return error_response(
        status_code=exc.status_code,
        code=code,
        message=message,
        details=None,
    )


@app.exception_handler(SQLAlchemyError)
def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.exception("database_error method=%s path=%s", request.method, request.url.path)
    return error_response(
        status_code=500,
        code="DATABASE_ERROR",
        message="A database error occurred",
        details=None,
    )


@app.exception_handler(Exception)
def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_error method=%s path=%s", request.method, request.url.path)
    return error_response(
        status_code=500,
        code="INTERNAL_ERROR",
        message="An unexpected error occurred",
        details=None,
    )


app.include_router(health_router)
app.include_router(patients_router, prefix="/api/v1")
app.include_router(vapi_router, prefix="/api/v1")


@app.get("/redoc", include_in_schema=False)
def redoc() -> HTMLResponse:
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
        with_google_fonts=False,
    )


def run() -> None:
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    run()
