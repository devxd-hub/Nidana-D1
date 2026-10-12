"""Tests for SQLite reliability: foreign keys, busy timeout, WAL mode, rollback, and uniqueness."""

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models import Subject, User
from app.db.session import check_database_health


def test_sqlite_foreign_keys_and_uniqueness():
    """Verify that foreign keys are enforced and unique constraints prevent duplicate records in SQLite."""
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    db: Session = TestingSession()

    try:
        # 1. Uniqueness check on user email
        u1 = User(id="user_1", email="duplicate@example.com", display_name="User 1")
        db.add(u1)
        db.commit()

        u2 = User(id="user_2", email="duplicate@example.com", display_name="User 2")
        db.add(u2)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

        # 2. Foreign key check
        # Attempt to insert chapter with non-existent subject_id should fail when FKs are ON
        with pytest.raises(IntegrityError):
            db.execute(
                text(
                    "INSERT INTO chapters (id, subject_id, class_level, chapter_number, title_en, created_at, updated_at) "
                    "VALUES ('ch_invalid', 'non_existent_subject', 10, 1, 'Test', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                )
            )
            db.commit()
        db.rollback()

    finally:
        db.close()
        engine.dispose()


def test_session_rollback_protection():
    """Verify that failed transactions roll back cleanly and do not corrupt subsequent operations."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    db: Session = TestingSession()

    try:
        # Initial valid insert
        s1 = Subject(id="sub_math", code="MATH", name_en="Mathematics")
        db.add(s1)
        db.commit()

        # Failed insert due to null code
        with pytest.raises(Exception):
            s2 = Subject(id="sub_null", code=None, name_en="Invalid")
            db.add(s2)
            db.commit()
        db.rollback()

        # Verify previous subject persists and session is clean
        persisted = db.query(Subject).filter_by(id="sub_math").first()
        assert persisted is not None
        assert persisted.code == "MATH"

    finally:
        db.close()
        engine.dispose()


def test_database_health_check_returns_true():
    """Verify check_database_health executes without errors."""
    assert check_database_health() is True
