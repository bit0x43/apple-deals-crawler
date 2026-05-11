# Plan: Sentinel Price Fix & Data Cleaning

**Wave:** 1
**Plan ID:** 09-data-quality
**Depends on:** None
**Files modified:**
- `src/apple_deals/crawlers/tiendasishop.py`
- `src/apple_deals/db/session.py`
- `tests/test_crawlers.py`
- `tests/test_db.py`

## Tasks

### Task 9.1: Add sentinel price filter to Tiendas iShop crawler

<read_first>
- `src/apple_deals/crawlers/tiendasishop.py`
- `tests/test_crawlers.py`
</read_first>

<action>
Add SENTINEL_PRICE = 99_999_999 constant. Filter out products in _fetch_collection
where variants[0].price >= SENTINEL_PRICE.
</action>

<acceptance_criteria>
- tiendasishop.py defines SENTINEL_PRICE = 99_999_999
- Products with price 99,999,999 are excluded from crawl results
- Tests verify sentinel products are filtered out, normal products pass through
- `uv run pytest tests/test_crawlers.py -v` shows 2 new tests passing
</acceptance_criteria>

### Task 9.2: Add DB cleaning migrations

<read_first>
- `src/apple_deals/db/session.py`
- `tests/test_db.py`
</read_first>

<action>
Add _migrate_clean_sentinel_prices() and _migrate_normalize_source() to session.py.
Both accept optional tgt_engine for test isolation. Wire into _migrate_schema().
</action>

<acceptance_criteria>
- Sentinel-price records (>= 99,999,998) are deleted from DB
- Source name "tiendasishop" is normalized to "tiendas ishop"
- Running migrations twice is idempotent
- `uv run pytest tests/test_db.py -v` shows 3 new tests passing
</acceptance_criteria>

## Verification

```bash
uv run pytest tests/ -v
uv run mypy src/apple_deals/
uv run ruff check src/apple_deals/ tests/
```

## Must Haves
- No products with price >= 99,999,999 in DB
- No records with source "tiendasishop"
- All tests pass
- mypy: 0 errors
- ruff: clean
