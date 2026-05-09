from __future__ import annotations

import sys

from playwright.sync_api import APIRequestContext, sync_playwright

from apple_deals.crawlers.base import (
    BaseCrawler,
    ProductData,
    _deduplicate,
    parse_title,
)

BASE_URL = "https://co.tiendasishop.com"
SOURCE = "tiendasishop"

MAC_COLLECTIONS: list[str] = [
    "apl-ps-13-inch-macbook-neo",
    "apl-ps-13-inch-macbook-air-m4",
    "apl-ps-13-inch-macbook-air-m5",
    "apl-ps-15-inch-macbook-air-m4",
    "apl-ps-15-inch-macbook-air-m5",
    "apl-ps-14-inch-macbook-pro-m4",
    "apl-ps-14-inch-macbook-pro-m4-pro",
    "apl-ps-14-inch-macbook-pro-m4-max",
    "apl-ps-14-inch-macbook-pro-m5",
    "apl-ps-14-inch-macbook-pro-m5-pro",
    "apl-ps-14-inch-macbook-pro-m5-max",
    "apl-ps-16-inch-macbook-pro-m4-pro",
    "apl-ps-16-inch-macbook-pro-m4-max",
    "apl-ps-16-inch-macbook-pro-m5-pro",
    "apl-ps-16-inch-macbook-pro-m5-max",
    "apl-ps-mac-mini-m2",
    "apl-ps-mac-mini-m2-pro",
    "apl-ps-mac-mini-m4",
    "apl-ps-mac-mini-m4-pro",
    "apl-ps-2023-mac-studio-m2-max-2023",
    "apl-ps-2023-mac-studio-m2-ultra-2023",
]


class TiendasishopCrawler(BaseCrawler):
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
                f"[tiendasishop] WARNING: {handle} returned {response.status}",
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
        )
