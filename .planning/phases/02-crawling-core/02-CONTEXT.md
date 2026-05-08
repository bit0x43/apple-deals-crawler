# Phase 2: Crawling Core - Context

**Gathered:** 2026-05-08
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped — yolo mode)

<domain>
## Phase Boundary

Both scrapers crawl live product pages from tiendasishop.com and mac-center.com using Playwright, persist records with deduplication (change-only storage), and are invocable via `apple-deals crawl`. No TUI, no alerts — just data in the DB.

</domain>

<decisions>
## Implementation Decisions

### Crawler Architecture
- **D-01:** Shared `BaseCrawler` abstract class in `src/apple_deals/crawlers/base.py` with abstract `crawl()` method returning `list[ProductData]`. Both store crawlers inherit from it.
- **D-02:** Sync Playwright (not async) — sequential 2-store crawl, simpler code, no asyncio overhead.
- **D-03:** One browser context per crawl run, reused across pages in the same store.
- **D-04:** `src/apple_deals/crawlers/tiendasishop.py` and `src/apple_deals/crawlers/mac_center.py` as separate files.

### Data Model
- **D-05:** Use a `ProductData` TypedDict or dataclass as the intermediate representation between scraper output and DB insert — keeps crawlers decoupled from SQLAlchemy.
- **D-06:** Deduplication logic lives in `src/apple_deals/db/session.py` (or a new `crud.py`): query last price for (sku, source), only insert if price changed or no prior record.

### CLI Integration
- **D-07:** `apple-deals crawl` activates both crawlers sequentially, prints per-store summary (N products found, M new/updated rows inserted).
- **D-08:** Playwright browser install handled by a post-install note in docs; assume `playwright install chromium` has been run.

### Claude's Discretion
- Exact CSS selectors for both stores (will be discovered during research/implementation)
- Error handling strategy for network failures (basic retry or fail-fast)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/apple_deals/db/models.py` — `Product` ORM model with all 9 required fields + id PK
- `src/apple_deals/db/session.py` — `get_session()` and `init_db()` already working
- `src/apple_deals/cli/main.py` — `crawl` command stub ready to implement

### Integration Points
- CLI `crawl` command stub in `cli/main.py` — replace stub body with real crawl logic
- `get_session()` from `session.py` — use for DB writes

</code_context>

<specifics>
## Specific Ideas

- Target URLs: https://co.tiendasishop.com/ and https://mac-center.com/
- Both sites are JS-rendered — Playwright required, requests/BS4 won't work
- Product fields: reference (product name), sku, memory, storage, color, price, url, source, crawled_at

</specifics>

<deferred>
## Deferred Ideas

- Async Playwright (future if store count grows)
- Per-store error reporting in TUI (Phase 4)
- Crawl scheduling (Phase 6)

</deferred>
