from typing import Any

from sqlalchemy import create_engine, inspect, text

from apple_deals.db.models import Base


def test_init_db_creates_products_table() -> None:
    """init_db() creates the products table in an in-memory SQLite DB."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    table_names = inspect(engine).get_table_names()
    assert "products" in table_names


def test_products_table_has_correct_columns() -> None:
    """Products table has all required columns."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    columns = {col["name"] for col in inspect(engine).get_columns("products")}
    required = {
        "id",
        "reference",
        "sku",
        "memory",
        "storage",
        "color",
        "price",
        "url",
        "source",
        "in_stock",
        "crawled_at",
    }
    assert required == columns


def test_nullable_fields() -> None:
    """memory, storage, color are nullable; required fields are not."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    columns = {col["name"]: col for col in inspect(engine).get_columns("products")}
    # nullable fields
    assert columns["memory"]["nullable"] is True
    assert columns["storage"]["nullable"] is True
    assert columns["color"]["nullable"] is True
    # non-nullable fields
    assert columns["reference"]["nullable"] is False
    assert columns["sku"]["nullable"] is False
    assert columns["url"]["nullable"] is False
    assert columns["source"]["nullable"] is False


def _count_rows(engine: Any, table: str = "products") -> int:
    with engine.connect() as conn:
        return conn.execute(text(f"SELECT count(*) FROM {table}")).scalar() or 0


def test_migrate_clean_sentinel_prices() -> None:
    from datetime import UTC, datetime

    from sqlalchemy import create_engine

    from apple_deals.db.models import Product
    from apple_deals.db.session import _migrate_clean_sentinel_prices

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = __import__("sqlalchemy.orm").orm.sessionmaker(bind=engine)

    with session_factory() as session:
        session.add(
            Product(
                reference="Normal",
                sku="SKU001",
                price=4_699_000,
                url="https://a",
                source="test",
                crawled_at=datetime.now(UTC),
            )
        )
        session.add(
            Product(
                reference="Sentinel",
                sku="SKU002",
                price=99_999_999,
                url="https://b",
                source="test",
                crawled_at=datetime.now(UTC),
            )
        )
        session.commit()

    assert _count_rows(engine) == 2
    _migrate_clean_sentinel_prices(tgt_engine=engine)
    assert _count_rows(engine) == 1

    with engine.connect() as conn:
        remaining = conn.execute(text("SELECT reference FROM products")).scalar()
    assert remaining == "Normal"


def test_migrate_normalize_source() -> None:
    from datetime import UTC, datetime

    from sqlalchemy import create_engine

    from apple_deals.db.models import Product
    from apple_deals.db.session import _migrate_normalize_source

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = __import__("sqlalchemy.orm").orm.sessionmaker(bind=engine)

    with session_factory() as session:
        session.add(
            Product(
                reference="Old name",
                sku="SKU001",
                price=1_000_000,
                url="https://a",
                source="tiendasishop",
                crawled_at=datetime.now(UTC),
            )
        )
        session.add(
            Product(
                reference="Correct",
                sku="SKU002",
                price=2_000_000,
                url="https://b",
                source="tiendas ishop",
                crawled_at=datetime.now(UTC),
            )
        )
        session.add(
            Product(
                reference="Mac",
                sku="SKU003",
                price=3_000_000,
                url="https://c",
                source="mac-center",
                crawled_at=datetime.now(UTC),
            )
        )
        session.commit()

    _migrate_normalize_source(tgt_engine=engine)

    with engine.connect() as conn:
        results = conn.execute(
            text("SELECT reference, source FROM products ORDER BY reference")
        ).all()
    assert len(results) == 3
    for ref, src in results:
        assert src != "tiendasishop", f"{ref} still has old source name"


def test_migrate_clean_is_idempotent() -> None:
    from datetime import UTC, datetime

    from sqlalchemy import create_engine

    from apple_deals.db.models import Product
    from apple_deals.db.session import _migrate_clean_sentinel_prices

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = __import__("sqlalchemy.orm").orm.sessionmaker(bind=engine)

    with session_factory() as session:
        session.add(
            Product(
                reference="Only normal",
                sku="SKU001",
                price=4_699_000,
                url="https://a",
                source="test",
                crawled_at=datetime.now(UTC),
            )
        )
        session.commit()

    _migrate_clean_sentinel_prices(tgt_engine=engine)
    _migrate_clean_sentinel_prices(tgt_engine=engine)

    assert _count_rows(engine) == 1
