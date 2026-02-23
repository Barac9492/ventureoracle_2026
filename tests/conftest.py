"""Shared test fixtures."""

import os

import pytest

from ventureoracle.db.database import get_engine, init_db
from ventureoracle.db.models import Base


@pytest.fixture(autouse=True)
def test_db(tmp_path, monkeypatch):
    """Use a temporary SQLite database for each test."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    # Reset global state so new engine is created
    import ventureoracle.db.database as db_mod

    db_mod._engine = None
    db_mod._session_factory = None

    init_db()
    yield
    db_mod._engine = None
    db_mod._session_factory = None
