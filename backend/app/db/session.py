"""Database engine creation and session lifecycle management."""

import logging
import os
from typing import Generator
from urllib.parse import urlparse

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
db_url = settings.effective_database_url

# Ensure target directory exists for SQLite files
if db_url.startswith("sqlite"):
    # Strip sqlite:/// to get filesystem path
    raw_path = db_url.replace("sqlite:///", "")
    if "?" in raw_path:
        raw_path = raw_path.split("?")[0]
    if raw_path and raw_path != ":memory:":
        dir_name = os.path.dirname(raw_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False, "timeout": 15}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable SQLite foreign keys, WAL journal mode, and busy timeout for concurrent safety."""
    # Check if connection is sqlite3 connection
    if hasattr(dbapi_connection, "execute"):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA busy_timeout=5000;")
            cursor.close()
        except Exception as exc:
            logger.warning("Could not set SQLite PRAGMAs on connection: %s", exc)


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a thread-local database session."""
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_database_health() -> bool:
    """Safe ping to verify database connectivity without leaking internal metadata."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("Database health check ping failed: %s", str(exc))
        return False
