from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

SQLITE_URL = "sqlite:///database.db"

engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables() -> None:
    # Ensure model classes are imported so metadata includes all tables.
    import api.models as models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
