from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from apple_deals.crawlers.base import ProductData
from apple_deals.db.crud import get_last_price, insert_product, upsert_if_changed
from apple_deals.db.models import Base


@pytest.fixture
def session() -> Generator[Session]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as sess:
        yield sess


def _make_product(
    sku: str = "MU9E3LZ/A", price: float = 4699000.0, source: str = "tiendas ishop"
) -> ProductData:
    return ProductData(
        reference="Mac mini: Chip M4",
        sku=sku,
        memory=None,
        storage="512 GB",
        color="Plata",
        price=price,
        url="https://co.tiendasishop.com/products/mac-mini-m4",
        source=source,
    )


def test_get_last_price_no_record(session: Session) -> None:
    result = get_last_price(session, "UNKNOWN-SKU", "tiendas ishop")
    assert result is None


def test_get_last_price_with_record(session: Session) -> None:
    insert_product(session, _make_product(price=4699000.0))
    result = get_last_price(session, "MU9E3LZ/A", "tiendas ishop")
    assert result == pytest.approx(4699000.0)


def test_insert_new_product(session: Session) -> None:
    inserted, old_price = upsert_if_changed(session, _make_product())
    assert inserted is True
    assert old_price is None


def test_skip_unchanged_price(session: Session) -> None:
    upsert_if_changed(session, _make_product(price=4699000.0))
    inserted, old_price = upsert_if_changed(session, _make_product(price=4699000.0))
    assert inserted is False
    assert old_price is None


def test_insert_changed_price(session: Session) -> None:
    upsert_if_changed(session, _make_product(price=4699000.0))
    inserted, old_price = upsert_if_changed(session, _make_product(price=4500000.0))
    assert inserted is True
    assert old_price == pytest.approx(4699000.0)


def test_old_price_matches_previous_insert(session: Session) -> None:
    upsert_if_changed(session, _make_product(price=5000000.0))
    inserted, old_price = upsert_if_changed(session, _make_product(price=4800000.0))
    assert inserted is True
    assert old_price == pytest.approx(5000000.0)


def test_deduplication_same_source_different_sku(session: Session) -> None:
    upsert_if_changed(session, _make_product(sku="SKU-A", price=1000.0))
    upsert_if_changed(session, _make_product(sku="SKU-B", price=2000.0))
    assert get_last_price(session, "SKU-A", "tiendas ishop") == pytest.approx(1000.0)
    assert get_last_price(session, "SKU-B", "tiendas ishop") == pytest.approx(2000.0)


def test_deduplication_same_sku_different_source(session: Session) -> None:
    upsert_if_changed(
        session, _make_product(sku="MU9E3LZ/A", price=4699000.0, source="tiendas ishop")
    )
    upsert_if_changed(session, _make_product(sku="MU9E3LZ/A", price=4750000.0, source="mac-center"))
    assert get_last_price(session, "MU9E3LZ/A", "tiendas ishop") == pytest.approx(4699000.0)
    assert get_last_price(session, "MU9E3LZ/A", "mac-center") == pytest.approx(4750000.0)
