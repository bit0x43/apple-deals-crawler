import os

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from apple_deals.db.models import Base

_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///apple_deals.db")

engine = create_engine(_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    """Create all tables if they don't exist. Migrate existing DBs."""
    Base.metadata.create_all(engine)
    _migrate_schema()


SENTINEL_PRICE = 99_999_999


def _migrate_schema() -> None:
    """Add columns for schema changes that create_all doesn't handle."""
    if not _table_exists("products"):
        return
    inspector = inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("products")}
    if "in_stock" not in columns:
        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE products ADD COLUMN in_stock BOOLEAN DEFAULT 1 NOT NULL")
            )
    _migrate_clean_sentinel_prices()
    _migrate_normalize_source()


def _table_exists(name: str) -> bool:
    inspector = inspect(engine)
    return name in inspector.get_table_names()


def _migrate_clean_sentinel_prices(tgt_engine: Engine | None = None) -> None:
    """Delete records with Shopify sentinel placeholder prices."""
    eng = tgt_engine or engine
    with eng.begin() as conn:
        result = conn.execute(
            text("DELETE FROM products WHERE price >= :sentinel"),
            {"sentinel": SENTINEL_PRICE},
        )
    if result.rowcount:
        logger = __import__("logging").getLogger(__name__)
        logger.info("Cleaned %d sentinel-price records", result.rowcount)


def _migrate_normalize_source(tgt_engine: Engine | None = None) -> None:
    """Normalize tiendasishop source name (old format) to 'tiendas ishop'."""
    eng = tgt_engine or engine
    with eng.begin() as conn:
        result = conn.execute(
            text("UPDATE products SET source = :new_name WHERE source = :old_name"),
            {"new_name": "tiendas ishop", "old_name": "tiendasishop"},
        )
    if result.rowcount:
        logger = __import__("logging").getLogger(__name__)
        logger.info("Normalized %d records to 'tiendas ishop'", result.rowcount)


def get_session() -> Session:
    """Return a new database session."""
    return SessionLocal()
