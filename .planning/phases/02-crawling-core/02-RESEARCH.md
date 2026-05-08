# Phase 2: Crawling Core - Research

**Researched:** 2026-05-08
**Domain:** Web scraping — Shopify JSON API, Playwright sync, SQLAlchemy deduplication
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Shared `BaseCrawler` abstract class in `src/apple_deals/crawlers/base.py` with abstract `crawl()` method returning `list[ProductData]`.
- **D-02:** Sync Playwright (not async) — sequential 2-store crawl, simpler code, no asyncio overhead.
- **D-03:** One browser context per crawl run, reused across pages in the same store.
- **D-04:** `src/apple_deals/crawlers/tiendasishop.py` and `src/apple_deals/crawlers/mac_center.py` as separate files.
- **D-05:** `ProductData` TypedDict or dataclass as the intermediate representation between scraper output and DB insert.
- **D-06:** Deduplication logic in `src/apple_deals/db/session.py` (or a new `crud.py`): query last price for (sku, source), only insert if price changed or no prior record.
- **D-07:** `apple-deals crawl` activates both crawlers sequentially, prints per-store summary (N products found, M new/updated rows inserted).
- **D-08:** Playwright browser install handled by a post-install note in docs; assume `playwright install chromium` has been run.

### Claude's Discretion

- Exact CSS selectors for both stores (will be discovered during research/implementation)
- Error handling strategy for network failures (basic retry or fail-fast)

### Deferred Ideas (OUT OF SCOPE)

- Async Playwright (future if store count grows)
- Per-store error reporting in TUI (Phase 4)
- Crawl scheduling (Phase 6)

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CRAWL-01 | System crawls Apple Mac product prices from tiendasishop.com using Playwright | Shopify JSON API verified; collection handles documented; full data model confirmed |
| CRAWL-02 | System crawls Apple Mac product prices from mac-center.com using Playwright | Shopify JSON API verified; collection handles documented; identical data shape to CRAWL-01 |
| CRAWL-03 | Each crawled record stores: reference, sku, memory, storage, color, price, url, source, crawled_at | Title parsing strategy documented; all 9 fields mappable from JSON response |
| CRAWL-04 | System skips writing a record when price is unchanged from previous crawl | SQLAlchemy 2.0 deduplication pattern documented with scalar_one_or_none |
| CLI-01 | User can run `apple-deals crawl` to trigger a manual crawl | Existing stub in cli/main.py; integration pattern documented |

</phase_requirements>

---

## Summary

Both tiendasishop.com and mac-center.com are Shopify stores. This is a critical discovery: **Playwright is not needed for DOM scraping** — both stores expose Shopify's standard `/collections/{handle}/products.json` REST endpoint that returns structured JSON without authentication. Playwright is still the correct tool for making these requests (it maintains a browser context that shares cookies and avoids basic bot detection), but the actual data extraction is pure JSON parsing, not CSS selector hunting.

The Shopify product data model on both stores uses **one product record per SKU configuration** (not Shopify's native variant system). Memory, storage, and color are embedded in the product title string rather than in variant `option1/2/3` fields. The SKU field (`variants[0].sku`) maps directly to Apple's part number (e.g., `MDHH4E/A`). Price is in `variants[0].price` as a string like `"5999000.00"`.

The deduplication strategy is clean: query the DB for the most recent record matching `(sku, source)`, compare price, insert only if changed. SQLAlchemy 2.0's `select()` + `scalar_one_or_none()` makes this a three-line operation.

**Primary recommendation:** Use `playwright.sync_api` `APIRequestContext` (via `sync_playwright().start()` + `playwright.request.new_context()`) to call the Shopify JSON endpoints directly. This avoids full browser rendering while keeping Playwright in the stack as required, and handles cookies/headers automatically.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| HTTP requests to Shopify JSON API | Playwright APIRequestContext | — | Stays within sync Playwright stack per D-02; handles cookies, redirects, headers |
| JSON parsing + ProductData assembly | Crawler module (`crawlers/`) | — | Pure Python; no DOM involved |
| Title parsing (storage/color extraction) | Crawler module (`crawlers/`) | — | Regex on product title string |
| Deduplication (sku + source lookup) | DB layer (`db/crud.py`) | — | D-06 places this in the DB layer |
| DB insert | DB layer (`db/crud.py`) | — | Uses existing `get_session()` + SQLAlchemy ORM |
| CLI orchestration | CLI layer (`cli/main.py`) | — | Replaces stub with real crawl loop per D-07 |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| playwright (Python) | 1.59.0 | HTTP requests via APIRequestContext, browser context | Project constraint; D-02 mandates sync API |
| SQLAlchemy | 2.0.49 | ORM + deduplication queries | Already installed (Phase 1) |
| Python stdlib `re` | (stdlib) | Title string parsing for storage/color | No dependency needed; patterns are simple |
| Python stdlib `datetime` | (stdlib) | `crawled_at` timestamp | No dependency needed |

**Version verification:** playwright 1.59.0 confirmed via PyPI JSON API on 2026-05-08. [VERIFIED: PyPI registry]

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python stdlib `decimal` | (stdlib) | Price conversion from string to Decimal/float | Use `Decimal(price_str)` to avoid float precision loss before storing |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Playwright APIRequestContext | `requests` or `httpx` | Both work for Shopify JSON; Playwright keeps the stack uniform and handles JS challenges if added later |
| Title regex parsing | LLM/NLP extraction | Overkill; Apple titles follow a consistent pattern |

**Installation:**
```bash
uv add playwright
uv run playwright install chromium
```

---

## Site-Specific Findings

### tiendasishop.com — Shopify JSON API

**Base URL:** `https://co.tiendasishop.com`

**Data access method:** `/collections/{handle}/products.json?limit=250`

**Mac product collection handles (verified 2026-05-08):**
```
apl-ps-13-inch-macbook-neo
apl-ps-13-inch-macbook-air-m4
apl-ps-13-inch-macbook-air-m5
apl-ps-15-inch-macbook-air-m4     (handle: apl_ps_15-inch-macbook-air-m4)
apl-ps-15-inch-macbook-air-m5
apl-ps-14-inch-macbook-pro-m4
apl-ps-14-inch-macbook-pro-m4-pro
apl-ps-14-inch-macbook-pro-m4-max
apl-ps-14-inch-macbook-pro-m5
apl-ps-14-inch-macbook-pro-m5-pro
apl-ps-14-inch-macbook-pro-m5-max
apl-ps-16-inch-macbook-pro-m4-pro
apl-ps-16-inch-macbook-pro-m4-max
apl-ps-16-inch-macbook-pro-m5-pro
apl-ps-16-inch-macbook-pro-m5-max
apl-ps-mac-mini-m2
apl-ps-mac-mini-m2-pro
apl-ps-mac-mini-m4
apl-ps-mac-mini-m4-pro
apl-ps-2023-mac-studio-m2-max-2023
apl-ps-2023-mac-studio-m2-ultra-2023
```

**JSON response shape (verified via live fetch):**
```json
{
  "products": [
    {
      "id": 9167374221620,
      "title": "Mac mini: Chip M4 de Apple con CPU de 10 núcleos y GPU de 10 núcleos, 512 GB SSD - Plata",
      "handle": "mac-mini-m4-mu9e3lz-a",
      "product_type": "Mac mini - M4",
      "vendor": "Apple",
      "variants": [
        {
          "id": 48331489116468,
          "sku": "MU9E3LZ/A",
          "price": "4699000.00",
          "available": true,
          "option1": "Default Title",
          "option2": null,
          "option3": null
        }
      ],
      "options": [
        {
          "name": "Title",
          "values": ["Default Title"]
        }
      ]
    }
  ]
}
```

**Key data mapping:**
- `title` → `reference` (full product name)
- `variants[0].sku` → `sku` (Apple part number e.g. `MU9E3LZ/A`)
- `variants[0].price` → `price` (string `"4699000.00"`, convert to float/Decimal)
- Title suffix after ` - ` → `color` (e.g. `"Plata"`, `"Azul medianoche"`)
- Title storage pattern (e.g. `"512 GB SSD"`, `"1 TB SSD"`, `"2 TB SSD"`) → `storage`
- Memory (RAM): **NOT in title for modern products** — leave `None` or parse from title when present
- `https://co.tiendasishop.com/products/{handle}` → `url`
- `"tiendasishop"` → `source`

**Title pattern examples:**
```
"MacBook Air de 13 pulgadas: Chip M5 de Apple con CPU de 10 núcleos y GPU de 8 núcleos, 512 GB SSD - Azul cielo"
"Mac mini: Chip M4 de Apple con CPU de 10 núcleos y GPU de 10 núcleos, 512 GB SSD - Plata"
"Mac mini (M1, 2020) Chip M1 de Apple ... 512 GB 8GB Wi-Fi"   ← older models may include RAM
```

---

### mac-center.com — Shopify JSON API

**Base URL:** `https://mac-center.com`

**Data access method:** `/collections/{handle}/products.json?limit=250`

**Mac product collection handles (verified 2026-05-08):**
```
macbook-air-m5
macbook-air-m4
macbookair
macbook-pro-m5
macbook-pro-m4
macbook-pro
mac-studio
imac
macmini
```

**JSON response shape:** Identical to tiendasishop.com — same Shopify schema.

**Title pattern examples (verified via live fetch):**
```
"MacBook Pro de 16 pulgadas: Chip M5 Max de Apple con CPU de 18 núcleos y GPU de 32 núcleos, 2 TB SSD - Negro espacial"
"MacBook Air de 13 pulgadas: Chip M5 de Apple con CPU de 10 núcleos y GPU de 8 núcleos, 512 GB SSD - Blanco estrella"
"Mac mini: Chip M4 Pro de Apple con CPU de 12 núcleos y GPU de 16 núcleos, 512 GB SSD - Plata"
"Mac mini (M1, 2020) Chip M1 de Apple con CPU de ocho núcleos y GPU de ocho núcleos 512 GB 8GB Wi-Fi"
```

**Key data mapping:** Same as tiendasishop.com.
- `source` → `"mac-center"`
- `url` → `https://mac-center.com/products/{handle}`

---

## Architecture Patterns

### System Architecture Diagram

```
apple-deals crawl (CLI)
        |
        v
cli/main.py: crawl()
        |
        +---> TiendasishopCrawler(BaseCrawler).crawl()
        |           |
        |           v
        |     sync_playwright() context
        |     APIRequestContext.get(collection_url + "/products.json")
        |     response.json()["products"]
        |           |
        |           v
        |     for each product:
        |       parse_title(title) -> (storage, color, memory)
        |       build ProductData(sku, reference, price, ...)
        |           |
        |           v
        |     returns list[ProductData]
        |
        +---> MacCenterCrawler(BaseCrawler).crawl()
        |     (same flow, different collections + source + base_url)
        |
        v
cli/main.py: for each ProductData in results:
    db/crud.py: get_last_price(session, sku, source)
        |
        +-- price unchanged? --> skip (no insert)
        |
        +-- price changed or no prior record? --> db/crud.py: insert_product(session, data)
        |
        v
    typer.echo("Store X: N products, M inserted")
```

### Recommended Project Structure

```
src/apple_deals/
├── crawlers/
│   ├── __init__.py
│   ├── base.py          # BaseCrawler ABC + ProductData TypedDict
│   ├── tiendasishop.py  # TiendasishopCrawler
│   └── mac_center.py    # MacCenterCrawler
├── db/
│   ├── models.py        # (existing) Product ORM model
│   ├── session.py       # (existing) engine + get_session
│   └── crud.py          # NEW: get_last_price() + insert_product()
└── cli/
    └── main.py          # (existing stub) replace crawl() body
```

### Pattern 1: ProductData TypedDict

**What:** Intermediate data structure between scraper output and DB insert. Keeps crawlers decoupled from SQLAlchemy.
**When to use:** Return type of `BaseCrawler.crawl()`.

```python
# Source: Python docs + CONTEXT.md D-05
# src/apple_deals/crawlers/base.py
from __future__ import annotations

import abc
from typing import TypedDict


class ProductData(TypedDict):
    reference: str        # Full product title from Shopify
    sku: str              # Apple part number, e.g. "MU9E3LZ/A"
    memory: str | None    # RAM extracted from title, or None
    storage: str | None   # SSD capacity extracted from title, e.g. "512 GB"
    color: str | None     # Color extracted from title suffix, e.g. "Plata"
    price: float          # Price in COP as float, e.g. 4699000.0
    url: str              # Full product URL
    source: str           # "tiendasishop" or "mac-center"


class BaseCrawler(abc.ABC):
    @abc.abstractmethod
    def crawl(self) -> list[ProductData]:
        """Crawl all Mac products and return a list of ProductData records."""
        ...
```

### Pattern 2: Playwright sync APIRequestContext for JSON fetching

**What:** Uses Playwright's built-in HTTP client to fetch Shopify JSON endpoints. No browser rendering needed for these endpoints.
**When to use:** Fetching `/collections/{handle}/products.json` from both stores.

```python
# Source: https://github.com/microsoft/playwright/blob/main/docs/src/api/class-apirequestcontext.md
# [VERIFIED: Context7 /microsoft/playwright]
from playwright.sync_api import sync_playwright


def fetch_products_json(base_url: str, collection_handle: str) -> list[dict]:
    with sync_playwright() as p:
        # Use APIRequestContext standalone (no browser window needed)
        request_ctx = p.request.new_context(base_url=base_url)
        url = f"/collections/{collection_handle}/products.json?limit=250"
        response = request_ctx.get(url)
        if not response.ok:
            return []
        data = response.json()
        return data.get("products", [])
```

**Production pattern — one context per crawl run (D-03):**

```python
# src/apple_deals/crawlers/tiendasishop.py
from playwright.sync_api import sync_playwright, APIRequestContext

from apple_deals.crawlers.base import BaseCrawler, ProductData


MAC_COLLECTIONS = [
    "apl-ps-13-inch-macbook-air-m5",
    "apl-ps-15-inch-macbook-air-m5",
    "apl-ps-mac-mini-m4",
    "apl-ps-mac-mini-m4-pro",
    # ... full list
]

BASE_URL = "https://co.tiendasishop.com"
SOURCE = "tiendasishop"


class TiendasishopCrawler(BaseCrawler):
    def crawl(self) -> list[ProductData]:
        results: list[ProductData] = []
        with sync_playwright() as p:
            # One context shared across all collection fetches (D-03)
            ctx = p.request.new_context(base_url=BASE_URL)
            for handle in MAC_COLLECTIONS:
                products = self._fetch_collection(ctx, handle)
                results.extend(products)
        return results

    def _fetch_collection(
        self, ctx: APIRequestContext, handle: str
    ) -> list[ProductData]:
        url = f"/collections/{handle}/products.json?limit=250"
        response = ctx.get(url)
        if not response.ok:
            return []
        raw = response.json().get("products", [])
        return [self._parse_product(p) for p in raw]

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
```

### Pattern 3: Title parsing — storage, color, memory extraction

**What:** Regex-based extraction of storage, color, and memory from Shopify product titles.
**When to use:** Inside `_parse_product()` in both crawlers.

Title structure observed across both stores:
```
"{Model}: Chip {Chip} de Apple con CPU de ... [, {storage} SSD] [- {color}]"
"{Model} ({chip}, {year}) ... {storage} {memory} ..."  ← older M1 titles
```

```python
# Source: [VERIFIED: live site inspection 2026-05-08]
import re


def parse_title(title: str) -> tuple[str | None, str | None, str | None]:
    """Extract (storage, color, memory) from a Shopify product title.

    Returns (storage, color, memory) where any field may be None.

    Examples:
      "MacBook Air de 13 pulgadas: Chip M5 ... 512 GB SSD - Azul cielo"
        -> ("512 GB", "Azul cielo", None)
      "Mac mini (M1, 2020) ... 512 GB 8GB Wi-Fi"
        -> ("512 GB", None, "8GB")
    """
    # Storage: matches "256 GB", "512 GB", "1 TB", "2 TB", "4 TB", "8 TB"
    storage_match = re.search(r"(\d+\s?(?:GB|TB))\s+SSD", title)
    if not storage_match:
        # Older titles: "512 GB" without "SSD" qualifier
        storage_match = re.search(r"(\d+\s?(?:GB|TB))(?=\s+(?:\d|Wi-Fi))", title)
    storage = storage_match.group(1).strip() if storage_match else None

    # Color: everything after " - " at the end of the title
    color_match = re.search(r"\s+-\s+(.+)$", title)
    color = color_match.group(1).strip() if color_match else None

    # Memory (RAM): pattern like "8GB", "16GB", "32GB", "36GB", "48GB"
    # Only present in some older titles; modern titles omit it
    memory_match = re.search(r"(\d+GB)\s+(?:Wi-Fi|RAM|memoria)", title, re.IGNORECASE)
    if not memory_match:
        # Alternative: look for standalone "8GB" / "16GB" between storage and end
        memory_match = re.search(r",\s+(\d+GB)\b", title)
    memory = memory_match.group(1).strip() if memory_match else None

    return storage, color, memory
```

**Note on memory:** Modern Apple product titles from both stores do NOT include RAM in the title (e.g., M4, M5 products). RAM is implied by the chip tier or stored only in Apple's official spec pages. `memory=None` is correct for most current products. [VERIFIED: live site inspection]

### Pattern 4: SQLAlchemy 2.0 deduplication query

**What:** Query the last price for a `(sku, source)` pair; insert only if price differs.
**When to use:** In `db/crud.py` as `get_last_price()` and `insert_product()`.

```python
# Source: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html (scalar_one_or_none)
# [VERIFIED: Context7 /websites/sqlalchemy_en_20_orm]
# src/apple_deals/db/crud.py
from datetime import datetime, timezone

from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from apple_deals.crawlers.base import ProductData
from apple_deals.db.models import Product


def get_last_price(session: Session, sku: str, source: str) -> float | None:
    """Return the most recent price for (sku, source), or None if no record exists."""
    stmt = (
        select(Product.price)
        .where(Product.sku == sku, Product.source == source)
        .order_by(desc(Product.crawled_at))
        .limit(1)
    )
    result = session.execute(stmt).scalar_one_or_none()
    return float(result) if result is not None else None


def insert_product(session: Session, data: ProductData) -> None:
    """Insert a new product record into the DB."""
    record = Product(
        reference=data["reference"],
        sku=data["sku"],
        memory=data["memory"],
        storage=data["storage"],
        color=data["color"],
        price=data["price"],
        url=data["url"],
        source=data["source"],
        crawled_at=datetime.now(tz=timezone.utc),
    )
    session.add(record)
    session.commit()


def upsert_if_changed(session: Session, data: ProductData) -> bool:
    """Insert record only if price changed or no prior record. Returns True if inserted."""
    last_price = get_last_price(session, data["sku"], data["source"])
    if last_price is not None and last_price == data["price"]:
        return False
    insert_product(session, data)
    return True
```

### Pattern 5: CLI crawl command integration

**What:** Replace the stub `crawl()` body in `cli/main.py` with real crawl orchestration.

```python
# Source: CONTEXT.md D-07
# src/apple_deals/cli/main.py (crawl command body replacement)
@app.command()
def crawl() -> None:
    """Crawl product prices from all configured stores."""
    from apple_deals.crawlers.tiendasishop import TiendasishopCrawler
    from apple_deals.crawlers.mac_center import MacCenterCrawler
    from apple_deals.db.crud import upsert_if_changed
    from apple_deals.db.session import get_session

    crawlers = [
        ("tiendasishop", TiendasishopCrawler()),
        ("mac-center", MacCenterCrawler()),
    ]

    session = get_session()
    try:
        for store_name, crawler in crawlers:
            products = crawler.crawl()
            inserted = sum(
                1 for p in products if upsert_if_changed(session, p)
            )
            typer.echo(
                f"{store_name}: {len(products)} products found, {inserted} inserted"
            )
    finally:
        session.close()
```

### Anti-Patterns to Avoid

- **Using `page.goto()` + CSS selectors to scrape product listing pages:** Both sites have a working Shopify JSON API. DOM scraping is fragile and unnecessary here. [VERIFIED: live site inspection]
- **Using Shopify variant `option1/2/3` fields to get memory/storage/color:** These fields are `"Default Title"` / `null` on both stores. Data is in the title string.
- **Fetching collections without `?limit=250`:** Default Shopify limit is 50. Some collections have more products than that. Always request 250 (the Shopify maximum).
- **Storing price as `Decimal` in ProductData:** ProductData is a TypedDict for transport; use `float`. The ORM model maps to `Numeric(12, 2)` which handles precision at the DB level.
- **Opening a new Playwright context per collection:** Violates D-03. One `sync_playwright()` context per crawl run, shared across all `_fetch_collection()` calls.
- **Calling `session.commit()` outside `crud.py`:** Keep transaction boundaries inside `insert_product()`; the CLI layer should not manage individual commits.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP client with cookie jar | Custom requests session | Playwright APIRequestContext | Shares browser context, handles redirects, Cloudflare challenges |
| Shopify API pagination | Custom page iterator | `?limit=250` (single fetch) | All Mac collections have fewer than 250 products per collection handle |
| Product deduplication | In-memory price set | DB query via `get_last_price()` | DB is the source of truth across runs; memory state is lost between CLI invocations |
| Part number parsing | Custom SKU regex | Use `variants[0].sku` directly | Shopify stores Apple's official part number verbatim in the SKU field |

---

## Common Pitfalls

### Pitfall 1: collections.json `/collections/mac` returns 404 or wrong data

**What goes wrong:** Naive attempt to fetch `/collections/mac.json` returns 404. There is no single "Mac" collection handle on either store.
**Why it happens:** Both stores organize Mac products into many granular collection handles, one per product family/chip generation. There is no umbrella `mac` collection.
**How to avoid:** Use the explicit collection handle lists documented in this research. Maintain the list in each crawler module. When Apple releases new products, a new collection handle will appear and must be added manually.
**Warning signs:** Empty product lists, 404 responses.

### Pitfall 2: Memory (RAM) field is None for most products

**What goes wrong:** Planner or developer expects `memory` to be populated for all products and treats `None` as a parsing bug.
**Why it happens:** Modern Apple product titles on both stores (M4, M5 era) do NOT include RAM in the product title. RAM is implied by the chip tier or only visible on individual product detail pages.
**How to avoid:** Accept `memory=None` as correct for current products. The regex parser returns `None` when no RAM pattern is found. Older M1 products may include it (e.g., `"512 GB 8GB Wi-Fi"`).
**Warning signs:** All `memory` fields are `None` — this is expected, not a bug.

### Pitfall 3: Shopify products.json returns `available: false` products

**What goes wrong:** Crawled data includes out-of-stock products where `variants[0].available == false`. These still have prices and should be recorded.
**Why it happens:** Shopify returns all products in a collection regardless of availability.
**How to avoid:** Do NOT filter on `available`. Price tracking is valuable even for out-of-stock items (they may come back in stock). Record all products.
**Warning signs:** Fewer products than expected after filtering on availability.

### Pitfall 4: Price comparison float precision

**What goes wrong:** `4699000.00 == 4699000.0` works fine for whole numbers, but float comparison could produce false positives for fractional COP prices.
**Why it happens:** Shopify returns price as a string `"4699000.00"`. After `float()` conversion, Colombian peso prices are whole numbers in practice.
**How to avoid:** Use `round(last_price, 2) == round(new_price, 2)` for comparison. Alternatively, compare the raw strings before conversion.
**Warning signs:** Duplicate inserts when price hasn't changed.

### Pitfall 5: playwright install chromium not run

**What goes wrong:** `playwright.sync_api.sync_playwright()` raises `BrowserType.launch: Executable doesn't exist at ...` even though playwright is installed via uv.
**Why it happens:** `uv add playwright` installs the Python package but not the browser binaries. Browser download is a separate step.
**How to avoid:** Document in README and INSTALL: `uv run playwright install chromium`. This downloads ~130MB of Chromium binary.
**Warning signs:** `Error: browserType.launch: Executable doesn't exist` on first `apple-deals crawl`.

### Pitfall 6: Duplicate products in overlapping collections

**What goes wrong:** The same SKU appears in two collection handles (e.g., `macbook-pro-m5` and `macbook-pro` on mac-center). This causes duplicate `ProductData` records in the list returned by `crawl()`.
**Why it happens:** Shopify allows a product to belong to multiple collections.
**How to avoid:** After collecting all products across all handles, deduplicate by SKU before the DB deduplication step: `seen = set(); results = [p for p in raw if (key := (p["sku"], p["source"])) not in seen and not seen.add(key)]`.
**Warning signs:** `upsert_if_changed` inserts the same SKU twice in a single crawl run.

---

## Code Examples

### Complete working fetch (verified pattern)

```python
# Source: [VERIFIED: Context7 /microsoft/playwright — APIRequestContext sync pattern]
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    ctx = p.request.new_context(base_url="https://co.tiendasishop.com")
    response = ctx.get("/collections/apl-ps-mac-mini-m4/products.json?limit=250")
    assert response.ok
    products = response.json()["products"]
    for product in products:
        print(product["title"], product["variants"][0]["sku"], product["variants"][0]["price"])
```

### Deduplication within a single crawl run

```python
# Deduplicate before DB writes to avoid double-insert from overlapping collections
def deduplicate(products: list[ProductData]) -> list[ProductData]:
    seen: set[tuple[str, str]] = set()
    result = []
    for p in products:
        key = (p["sku"], p["source"])
        if key not in seen:
            seen.add(key)
            result.append(p)
    return result
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| DOM scraping with BeautifulSoup | Shopify JSON API | Both stores have always been Shopify | No CSS selectors needed; data is structured JSON |
| `requests.Session` for HTTP | Playwright APIRequestContext | Playwright 1.16+ | Stays in one tool stack; handles JS challenges |
| SQLAlchemy `session.query(Model)` legacy style | `select(Model.col).where(...)` 2.0 style | SQLAlchemy 2.0 (2023) | Future-proof; legacy query API will be removed in 3.0 |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | All Mac products on both stores fit within a single `?limit=250` request per collection | Pitfall 1 | If >250 products per collection, implement pagination with `page=2` parameter |
| A2 | Collection handles listed are complete for current Mac lineup | Site-Specific Findings | New product lines (Mac Studio M3, etc.) will add new handles not yet documented; crawl will miss them until handles are added |
| A3 | Memory (RAM) is not present in title for M4/M5 products | Pitfall 2 | Low risk — verified on multiple live product titles |

---

## Open Questions

1. **Should missing collection handles (e.g., new Mac Studio M3) cause a silent skip or a logged warning?**
   - What we know: The handle list is hardcoded in each crawler; unknown handles produce 404.
   - What's unclear: Error handling strategy (Claude's Discretion per CONTEXT.md).
   - Recommendation: Log a warning to stderr when a 404 is received (`typer.echo(..., err=True)`) and continue. Fail-fast only on unexpected errors (network timeout, malformed JSON).

2. **Should `crawled_at` use UTC or local time?**
   - What we know: `datetime.now(tz=timezone.utc)` is the safe choice for DB portability.
   - Recommendation: Always use UTC. The TUI (Phase 4) can convert to local time for display.

3. **What happens when `variants` list is empty?**
   - What we know: All live products observed have exactly one variant.
   - Recommendation: Guard with `if not product.get("variants"): continue` to skip malformed products.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 | Runtime | ✓ | 3.13.13 | — |
| playwright (Python pkg) | APIRequestContext | ✗ (not yet installed) | 1.59.0 on PyPI | `uv add playwright` |
| Chromium browser binary | playwright.launch() | ✗ (not yet installed) | — | `uv run playwright install chromium` |
| SQLAlchemy | ORM + queries | ✓ | 2.0.49 (Phase 1) | — |

**Missing dependencies with no fallback:**
- `playwright` Python package and Chromium binary — must be installed before `apple-deals crawl` works.

**Missing dependencies with fallback:**
- None.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml [tool.pytest.ini_options]` (exists from Phase 1) |
| Quick run command | `uv run pytest tests/ -x -q` |
| Full suite command | `uv run pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CRAWL-01 | TiendasishopCrawler.crawl() returns non-empty list with correct fields | integration (live) / unit (mocked) | `uv run pytest tests/test_crawlers.py::test_tiendasishop_parse -x` | ❌ Wave 0 |
| CRAWL-02 | MacCenterCrawler.crawl() returns non-empty list with correct fields | integration (live) / unit (mocked) | `uv run pytest tests/test_crawlers.py::test_mac_center_parse -x` | ❌ Wave 0 |
| CRAWL-03 | ProductData has all 9 required fields populated (or None where allowed) | unit | `uv run pytest tests/test_crawlers.py::test_product_data_fields -x` | ❌ Wave 0 |
| CRAWL-04 | upsert_if_changed() skips insert when price unchanged | unit | `uv run pytest tests/test_crud.py::test_deduplication -x` | ❌ Wave 0 |
| CLI-01 | `apple-deals crawl` exits 0 and prints summary lines | smoke | `uv run apple-deals crawl` | ❌ (stub currently exits 1) |

**Note on integration tests:** Live network calls in CI are fragile. Prefer unit tests that mock the Playwright `APIRequestContext.get()` return value with a captured JSON fixture. One smoke test per store against the live endpoint is sufficient for validation.

### Sampling Rate

- **Per task commit:** `uv run pytest tests/test_crawlers.py tests/test_crud.py -x -q`
- **Per wave merge:** `uv run pytest tests/ -v`
- **Phase gate:** Full suite green + `uv run apple-deals crawl` exits 0 before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_crawlers.py` — unit tests for `parse_title()` and `ProductData` assembly (CRAWL-01, CRAWL-02, CRAWL-03)
- [ ] `tests/test_crud.py` — unit tests for `get_last_price()` and `upsert_if_changed()` with in-memory SQLite (CRAWL-04)
- [ ] `tests/fixtures/tiendasishop_products.json` — captured API response for mocking
- [ ] `tests/fixtures/mac_center_products.json` — captured API response for mocking

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No auth required; Shopify JSON API is public |
| V3 Session Management | No | Stateless API crawl; no user sessions |
| V4 Access Control | No | No access control in this phase |
| V5 Input Validation | Yes | Validate/sanitize scraped strings before DB insert |
| V6 Cryptography | No | No crypto in this phase |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malformed/injected title strings from scraped HTML | Tampering | Use SQLAlchemy ORM parameterized inserts (never raw SQL with f-strings); ORM handles escaping automatically |
| Runaway crawl consuming resources | Denial of Service | Respect Shopify rate limits; 21 collection fetches + parsing is well within limits; add `time.sleep(0.5)` between stores if needed |
| Sensitive data in DB file committed to git | Information Disclosure | `.gitignore` includes `*.db` (Phase 1 established this) |

---

## Sources

### Primary (HIGH confidence)

- [VERIFIED: live site inspection 2026-05-08] `https://co.tiendasishop.com/collections.json` — collection handles enumerated
- [VERIFIED: live site inspection 2026-05-08] `https://co.tiendasishop.com/collections/apl-ps-13-inch-macbook-air-m5/products.json` — product JSON shape, title patterns, SKU format
- [VERIFIED: live site inspection 2026-05-08] `https://co.tiendasishop.com/collections/apl-ps-mac-mini-m4/products.json` — Mac mini products confirmed
- [VERIFIED: live site inspection 2026-05-08] `https://mac-center.com/pages/mac` — collection handle list for mac-center
- [VERIFIED: live site inspection 2026-05-08] `https://mac-center.com/collections/macmini/products.json` — Mac mini JSON shape identical
- [VERIFIED: live site inspection 2026-05-08] `https://mac-center.com/collections/macbook-air-m5/products.json` — MacBook Air M5 titles confirmed
- [VERIFIED: Context7 /microsoft/playwright] — `sync_playwright`, `APIRequestContext.get()`, `response.json()`, sync patterns
- [VERIFIED: Context7 /websites/sqlalchemy_en_20_orm] — `select().where().order_by(desc()).limit()`, `scalar_one_or_none()`
- [VERIFIED: PyPI registry 2026-05-08] — playwright 1.59.0

### Secondary (MEDIUM confidence)

- [CITED: https://github.com/microsoft/playwright/blob/main/docs/src/api/class-apirequestcontext.md] — APIRequestContext `new_context(base_url=)` and standalone usage pattern

### Tertiary (LOW confidence)

- None — all critical claims verified via live inspection or official documentation.

---

## Metadata

**Confidence breakdown:**
- Site data model: HIGH — verified via live JSON API fetches from both stores
- Playwright sync patterns: HIGH — verified via Context7 official docs
- SQLAlchemy deduplication: HIGH — verified via Context7 official docs
- Collection handle completeness: MEDIUM — enumerated from live data but new Apple products will require updates
- Title parsing regex: MEDIUM — tested against observed title patterns; edge cases possible for unreleased models

**Research date:** 2026-05-08
**Valid until:** 2026-06-08 (Shopify API schema is stable; collection handles change with new product releases)
