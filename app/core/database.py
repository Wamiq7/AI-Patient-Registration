from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()
database_url = settings.sqlalchemy_database_url

engine_kwargs: dict[str, object] = {
    "pool_pre_ping": True,
    "future": True,
}
if "pooler" in database_url or "neon.tech" in database_url:
    engine_kwargs["poolclass"] = NullPool

engine = create_engine(database_url, **engine_kwargs)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    from app.models.patient import Patient  # noqa: F401

    Base.metadata.create_all(bind=engine)
