from __future__ import annotations

import sys

from playwright.sync_api import APIRequestContext, sync_playwright

from apple_deals.crawlers.base import (
    BaseCrawler,
    ProductData,
    _deduplicate,
    parse_title,
)

BASE_URL = "https://mac-center.com"
SOURCE = "mac-center"

MAC_COLLECTIONS: list[str] = [
    "macbook-air-m5",
    "macbook-air-m4",
    "macbookair",
    "macbook-pro-m5",
    "macbook-pro-m4",
    "macbook-pro",
    "mac-studio",
    "imac",
    "macmini",
]


class MacCenterCrawler(BaseCrawler):
    def crawl(self) -> list[ProductData]:
        raw: list[ProductData] = []
        with sync_playwright() as p:
            ctx = p.request.new_context(base_url=BASE_URL)
            for handle in MAC_COLLECTIONS:
                raw.extend(self._fetch_collection(ctx, handle))
        return _deduplicate(raw)

    def _fetch_collection(self, ctx: APIRequestContext, handle: str) -> list[ProductData]:
        url = f"/collections/{handle}/products.json?limit=250"
        response = ctx.get(url)
        if not response.ok:
            print(
                f"[mac-center] WARNING: {handle} returned {response.status}",
                file=sys.stderr,
            )
            return []
        products = response.json().get("products", [])
        return [self._parse_product(p) for p in products if p.get("variants")]

    def _parse_product(self, product: dict) -> ProductData:
        title: str = product["title"]
        variant: dict = product["variants"][0]
        handle: str = product["handle"]
        storage, color, memory = parse_title(title)
        return ProductData(
            reference=title,
            sku=variant["sku"],
            memory=memory,
            storage=storage,
            color=color,
            price=float(variant["price"]),
            url=f"{BASE_URL}/products/{handle}",
            source=SOURCE,
            in_stock=bool(variant.get("available", True)),
        )
