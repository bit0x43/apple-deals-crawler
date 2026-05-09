from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import desc, select
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
