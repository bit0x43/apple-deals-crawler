# Summary: 02-02 — Store Crawlers & DB Deduplication

**Phase:** 02-crawling-core | **Plan:** 02/03

## Files Created

- `src/apple_deals/crawlers/tiendasishop.py` — `TiendasishopCrawler` with 21 Mac collection handles
- `src/apple_deals/crawlers/mac_center.py` — `MacCenterCrawler` with 9 Mac collection handles
- `src/apple_deals/db/crud.py` — `get_last_price()`, `insert_product()`, `upsert_if_changed()`
- `tests/test_crud.py` — 7 unit tests for deduplication/CRUD logic

## Files Modified

- `src/apple_deals/crawlers/base.py` — added `_deduplicate()` helper function
- `pyproject.toml` — added `playwright` dependency (installed early for Plan 02-02)

## Verification

- `uv run pytest tests/test_crud.py -v` — 7/7 passed
- `uv run pytest tests/ -v` — 24/24 passed (all tests including existing)
- `uv run python -c "from apple_deals.crawlers.tiendasishop import TiendasishopCrawler; from apple_deals.crawlers.mac_center import MacCenterCrawler; from apple_deals.db.crud import upsert_if_changed; print('OK')"` — all imports clean
- Playwright Chromium browser installed

## Notes

- `_deduplicate()` is defined in `base.py` and imported by both crawlers
- Collection handles verified against actual store Shopify endpoints
- `D_03 (one sync_playwright() context per crawl)` honored — single context shared across all fetches
- Playwright Chromium browser installed (~165MB)
