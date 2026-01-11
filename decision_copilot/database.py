# coding: utf-8
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from decision_copilot.models import Base


@dataclass(frozen=True)
class DatabaseConfig:
    """SQLite configuration for local-first development."""
    sqlite_path: Path = None


def build_sqlite_url(sqlite_path: Path) -> str:
    # Ensure parent directory exists.
    sqlite_path = sqlite_path.expanduser().resolve()
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{sqlite_path.as_posix()}"


def make_engine(cfg: DatabaseConfig) -> Engine:
    if not cfg.sqlite_path:
        raise RuntimeError("DECISION_COPILOT_DB is not set.")

    url = build_sqlite_url(cfg.sqlite_path)

    # check_same_thread=False is important if you later have worker threads/processes
    # interacting with SQLite from different contexts.
    return create_engine(
        url,
        future=True,
        echo=False,
        connect_args={"check_same_thread": False},
    )


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )


def init_db(engine: Engine) -> None:
    """Create all tables (no migrations in the MVP)."""
    Base.metadata.create_all(bind=engine)
