from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

os.environ.setdefault("VAPI_API_KEY", "")

from app.core.config import get_settings, to_sqlalchemy_url
from app.core.database import Base, get_db
from app.main import app
from app.models.patient import Patient  # noqa: F401


def _test_database_url() -> str:
    raw = os.getenv("TEST_DATABASE_URL") or get_settings().database_url
    if not raw:
        raise RuntimeError("Set DATABASE_URL or TEST_DATABASE_URL before running tests")
    return to_sqlalchemy_url(raw)


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    url = _test_database_url()
    engine_kwargs: dict[str, object] = {"future": True, "pool_pre_ping": True}
    if "pooler" in url:
        engine_kwargs["poolclass"] = NullPool
    test_engine = create_engine(url, **engine_kwargs)
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture(autouse=True)
def reset_schema(engine: Engine) -> Generator[None, None, None]:
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE patients RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def db_session(engine: Engine) -> Generator[Session, None, None]:
    session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(engine: Engine) -> Generator[TestClient, None, None]:
    session_factory = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    def override_get_db() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
