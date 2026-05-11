from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, desc, func, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from apple_deals.crawlers.base import ProductData
from apple_deals.db.models import Product


def get_last_price(session: Session, sku: str, source: str) -> float | None:
    stmt = (
        select(Product.price)
        .where(Product.sku == sku, Product.source == source)
        .order_by(desc(Product.crawled_at))
        .limit(1)
    )
    result = session.execute(stmt).scalar_one_or_none()
    return float(result) if result is not None else None


def insert_product(session: Session, data: ProductData) -> None:
    record = Product(
        reference=data["reference"],
        sku=data["sku"],
        memory=data["memory"],
        storage=data["storage"],
        color=data["color"],
        price=data["price"],
        url=data["url"],
        source=data["source"],
        crawled_at=datetime.now(tz=UTC),
    )
    session.add(record)
    session.commit()


def upsert_if_changed(session: Session, data: ProductData) -> bool:
    last_price = get_last_price(session, data["sku"], data["source"])
    if last_price is not None and round(last_price, 2) == round(data["price"], 2):
        return False
    insert_product(session, data)
    return True


def _naive_utc_cutoff(retention_days: int) -> datetime:
    return (datetime.now(tz=UTC) - timedelta(days=retention_days)).replace(tzinfo=None)


def prune_old_records(session: Session, retention_days: int = 90) -> int:
    cutoff = _naive_utc_cutoff(retention_days)
    result = session.execute(delete(Product).where(Product.crawled_at < cutoff))
    session.commit()
    return result.rowcount  # type: ignore[attr-defined,no-any-return]


def count_prunable(session: Session, retention_days: int = 90) -> int:
    cutoff = _naive_utc_cutoff(retention_days)
    count = session.scalar(
        select(func.count()).select_from(Product).where(Product.crawled_at < cutoff)
    )
    return count or 0


def get_db_stats(session: Session, engine: Engine) -> dict:
    total = session.scalar(select(func.count()).select_from(Product)) or 0
    oldest = session.scalar(select(func.min(Product.crawled_at)))
    newest = session.scalar(select(func.max(Product.crawled_at)))

    cutoff_7d = _naive_utc_cutoff(7)
    recent = (
        session.scalar(
            select(func.count()).select_from(Product).where(Product.crawled_at >= cutoff_7d)
        )
        or 0
    )
    daily_growth = round(recent / 7, 1) if recent else 0.0

    is_postgres = engine.url.drivername.startswith("postgresql")
    if is_postgres:
        size_str = (
            session.scalar(text("SELECT pg_size_pretty(pg_database_size(current_database()))"))
            or "unknown"
        )
    else:
        db_path = engine.url.database
        if db_path == ":memory:" or db_path is None:
            size_str = "in-memory"
        else:
            try:
                size_bytes = os.path.getsize(db_path)
                size_str = f"{size_bytes / 1024:.1f} KB"
            except FileNotFoundError:
                size_str = "unknown"

    return {
        "total_rows": total,
        "oldest": oldest,
        "newest": newest,
        "daily_growth": daily_growth,
        "db_size": size_str,
    }


def get_current_prices(
    session: Session,
    model_filter: str | None = None,
    store_filter: str | None = None,
) -> list[Product]:
    subq = (
        select(
            Product.sku,
            Product.source,
            func.max(Product.crawled_at).label("max_crawled_at"),
        )
        .group_by(Product.sku, Product.source)
        .subquery()
    )
    stmt = (
        select(Product)
        .join(
            subq,
            (Product.sku == subq.c.sku)
            & (Product.source == subq.c.source)
            & (Product.crawled_at == subq.c.max_crawled_at),
        )
        .order_by(Product.price)
    )
    if model_filter and model_filter != "all":
        stmt = stmt.where(Product.reference.ilike(f"%{model_filter}%"))
    if store_filter and store_filter != "all":
        stmt = stmt.where(Product.source == store_filter)
    return list(session.scalars(stmt))


def get_price_history(
    session: Session,
    sku: str,
    source: str,
    days: int = 90,
) -> list[Product]:
    stmt = (
        select(Product)
        .where(Product.sku == sku)
        .where(Product.source == source)
        .order_by(Product.crawled_at)
    )
    if days > 0:
        cutoff = (datetime.now(tz=UTC) - timedelta(days=days)).replace(tzinfo=None)
        stmt = stmt.where(Product.crawled_at >= cutoff)
    return list(session.scalars(stmt))
