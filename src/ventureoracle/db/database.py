"""Database connection and session management."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ventureoracle.config import get_settings

_engine = None
_session_factory = None


def get_engine():
    """Get or create the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        db_url = settings.database_url

        # Ensure the directory exists for SQLite
        if db_url.startswith("sqlite:///"):
            db_path = Path(db_url.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)

        _engine = create_engine(db_url, echo=False)
    return _engine


def get_session_factory():
    """Get or create the session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine())
    return _session_factory


def get_session() -> Session:
    """Get a new database session."""
    factory = get_session_factory()
    return factory()


def init_db():
    """Create all tables."""
    from ventureoracle.db.models import Base

    Base.metadata.create_all(get_engine())
