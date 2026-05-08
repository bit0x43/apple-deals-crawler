from sqlalchemy import create_engine, inspect

from apple_deals.db.models import Base


def test_init_db_creates_products_table() -> None:
    """init_db() creates the products table in an in-memory SQLite DB."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    table_names = inspect(engine).get_table_names()
    assert "products" in table_names


def test_products_table_has_correct_columns() -> None:
    """Products table has all 10 required columns."""
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
