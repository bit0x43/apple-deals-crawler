import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from apple_deals.db.models import Base

_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///apple_deals.db")

engine = create_engine(_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    """Create all tables if they don't exist. Migrate existing DBs."""
    Base.metadata.create_all(engine)
    _migrate_schema()


def _migrate_schema() -> None:
    """Add columns for schema changes that create_all doesn't handle."""
    inspector = inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("products")}
    if "in_stock" not in columns:
        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE products ADD COLUMN in_stock BOOLEAN DEFAULT 1 NOT NULL")
            )


def get_session() -> Session:
    """Return a new database session."""
    return SessionLocal()
