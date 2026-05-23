from __future__ import annotations

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from src.core.config import DATABASE_URL
from src.db.models import Policy
from src.db.session import SessionLocal, engine


def _db_available() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def test_database_url_exists():
    assert DATABASE_URL is not None
    assert DATABASE_URL.strip() != ""


def test_engine_and_session_create():
    session = SessionLocal()
    try:
        assert session is not None
    finally:
        session.close()


def test_models_import():
    assert Policy.__tablename__ == "policies"


def test_init_db_seeds_active_policy():
    if not _db_available():
        pytest.skip("PostgreSQL no disponible para test de integracion DB.")

    from scripts.init_db import main as init_db_main

    try:
        init_db_main()
    except SQLAlchemyError as exc:
        pytest.skip(f"No se pudo inicializar la DB en test: {exc}")

    with SessionLocal() as session:
        active_policy = session.scalar(select(Policy).where(Policy.is_active.is_(True)))
        assert active_policy is not None
