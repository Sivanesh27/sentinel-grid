"""
Database connection and session manager for SQLite storage in Sentinel Grid.
"""

import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.storage.models import Base

# Database path (default: sentinel.db in backend root or environment variable)
DB_PATH = os.environ.get("SENTINEL_DB_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../sentinel.db")))
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create tables if they don't already exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency generator for FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Session:
    """Context manager for pipeline worker background tasks."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
