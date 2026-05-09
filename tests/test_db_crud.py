from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from apple_deals.db.crud import count_prunable, get_db_stats, prune_old_records
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
