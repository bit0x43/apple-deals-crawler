from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from apple_deals.db.crud import (
    count_prunable,
    get_current_prices,
    get_db_stats,
    get_price_history,
    prune_old_records,
)
from apple_deals.db.models import Base, Product


@pytest.fixture()
def db_session() -> Generator[tuple[Session, Engine]]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session, engine
    session.close()


def _insert_product(session: Session, days_ago: int) -> None:
    crawled_at = (datetime.now(tz=UTC) - timedelta(days=days_ago)).replace(tzinfo=None)
    session.add(
        Product(
            reference="MacBook Air 13",
            sku="MXD33LL/A",
            price=4_999_000.0,
            url="https://example.com",
            source="test",
            crawled_at=crawled_at,
        )
    )
    session.commit()


def test_prune_old_records_deletes_old_rows(db_session: tuple[Session, Engine]) -> None:
    session, _ = db_session
    _insert_product(session, days_ago=100)
    deleted = prune_old_records(session, retention_days=90)
    assert deleted == 1


def test_prune_old_records_keeps_recent_rows(db_session: tuple[Session, Engine]) -> None:
    session, _ = db_session
    _insert_product(session, days_ago=10)
    deleted = prune_old_records(session, retention_days=90)
    assert deleted == 0


def test_prune_returns_zero_for_empty_table(db_session: tuple[Session, Engine]) -> None:
    session, _ = db_session
    deleted = prune_old_records(session, retention_days=90)
    assert deleted == 0


def test_count_prunable_does_not_delete(db_session: tuple[Session, Engine]) -> None:
    session, _ = db_session
    _insert_product(session, days_ago=100)
    count = count_prunable(session, retention_days=90)
    assert count == 1
    # Row should still be present after count
    from sqlalchemy import func, select

    remaining = session.scalar(select(func.count()).select_from(Product))
    assert remaining == 1


def test_get_db_stats_empty_table(db_session: tuple[Session, Engine]) -> None:
    session, engine = db_session
    stats = get_db_stats(session, engine)
    assert stats["total_rows"] == 0
    assert stats["oldest"] is None
    assert stats["newest"] is None
    assert stats["daily_growth"] == 0.0
    assert stats["db_size"] == "in-memory"


def test_get_db_stats_with_rows(db_session: tuple[Session, Engine]) -> None:
    session, engine = db_session
    _insert_product(session, days_ago=100)
    _insert_product(session, days_ago=1)
    stats = get_db_stats(session, engine)
    assert stats["total_rows"] == 2
    assert stats["oldest"] is not None
    assert stats["newest"] is not None
    assert stats["oldest"] < stats["newest"]


# --- TUI query tests ---


@pytest.fixture()
def tui_session() -> Generator[Session]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _seed(
    session: Session,
    reference: str = "MacBook Air 13 M4",
    sku: str = "MXD33LL/A",
    price: float = 4_999_000.0,
    source: str = "tiendasishop",
    days_ago: int = 0,
) -> Product:
    crawled_at = (datetime.now(tz=UTC) - timedelta(days=days_ago)).replace(tzinfo=None)
    p = Product(
        reference=reference,
        sku=sku,
        memory=None,
        storage="512 GB",
        color="Plata",
        price=price,
        url="https://example.com/mba",
        source=source,
        crawled_at=crawled_at,
    )
    session.add(p)
    session.commit()
    return p


def test_get_current_prices_returns_most_recent_per_sku_source(
    tui_session: Session,
) -> None:
    _seed(tui_session, sku="SKU001", days_ago=100)
    _seed(tui_session, sku="SKU001", price=3_000_000.0, days_ago=1)
    _seed(tui_session, sku="SKU002", days_ago=1)
    result = get_current_prices(tui_session)
    assert len(result) == 2
    prices = {r.sku: r.price for r in result}
    assert prices["SKU001"] == 3_000_000.0


def test_get_current_prices_filters_by_model(tui_session: Session) -> None:
    _seed(tui_session, reference="MacBook Air 13 M4", sku="SKU001")
    _seed(tui_session, reference="Mac mini M4", sku="SKU002")
    result = get_current_prices(tui_session, model_filter="MacBook Air")
    assert len(result) == 1
    assert result[0].reference == "MacBook Air 13 M4"


def test_get_current_prices_filters_by_store(tui_session: Session) -> None:
    _seed(tui_session, source="tiendasishop", sku="SKU001")
    _seed(tui_session, source="mac-center", sku="SKU002")
    result = get_current_prices(tui_session, store_filter="mac-center")
    assert len(result) == 1
    assert result[0].source == "mac-center"


def test_get_current_prices_no_filter_returns_all(tui_session: Session) -> None:
    _seed(tui_session, sku="SKU001")
    _seed(tui_session, sku="SKU002")
    result = get_current_prices(tui_session)
    assert len(result) == 2


def test_get_current_prices_empty_table(tui_session: Session) -> None:
    assert get_current_prices(tui_session) == []


def test_get_price_history_returns_ordered_by_crawled_at(
    tui_session: Session,
) -> None:
    _seed(tui_session, sku="SKU001", days_ago=10)
    _seed(tui_session, sku="SKU001", price=3_000_000.0, days_ago=5)
    _seed(tui_session, sku="SKU001", price=2_500_000.0, days_ago=1)
    result = get_price_history(tui_session, "SKU001", "tiendasishop")
    assert len(result) == 3
    assert result[0].crawled_at <= result[1].crawled_at <= result[2].crawled_at


def test_get_price_history_filters_by_sku_and_source(tui_session: Session) -> None:
    _seed(tui_session, sku="SKU001", source="tiendasishop")
    _seed(tui_session, sku="SKU002", source="tiendasishop")
    _seed(tui_session, sku="SKU001", source="mac-center")
    result = get_price_history(tui_session, "SKU001", "tiendasishop")
    assert len(result) == 1
    assert result[0].sku == "SKU001"
    assert result[0].source == "tiendasishop"


def test_get_price_history_rolling_window(tui_session: Session) -> None:
    _seed(tui_session, sku="SKU001", days_ago=10)
    _seed(tui_session, sku="SKU001", price=3_000_000.0, days_ago=200)
    result = get_price_history(tui_session, "SKU001", "tiendasishop", days=90)
    assert len(result) == 1


def test_get_price_history_empty_table(tui_session: Session) -> None:
    assert get_price_history(tui_session, "SKU001", "tiendasishop") == []
