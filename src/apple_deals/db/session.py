import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from apple_deals.db.models import Base

_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///apple_deals.db")

engine = create_engine(_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    """Create all tables if they don't exist."""
    Base.metadata.create_all(engine)


def get_session() -> Session:
    """Return a new database session."""
    return SessionLocal()
