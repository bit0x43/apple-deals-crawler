# Phase 9: Data Quality & Bug Fixes - Context

**Gathered:** 2026-05-11
**Status:** Implemented

## Problem

1. **Shopify sentinel prices**: Tiendas iShop API returns `99,999,999` for products
   whose real price is unavailable (pre-order/coming soon). The crawler blindly accepts
   this as real, polluting the DB with 22 fake records.

2. **Source name rot**: 61 records still use `"tiendasishop"` (no space) from the old
   naming convention, before the SOURCE constant was corrected.

## Solution

### Plan 9.1 — Sentinel Price Filter
- Add `SENTINEL_PRICE = 99_999_999` constant to `tiendasishop.py`
- Filter products where `variants[0].price >= SENTINEL_PRICE` in `_fetch_collection`
- Verified: these products have exactly 1 variant with the sentinel price — no real
  price to recover

### Plan 9.2 — DB Data Cleaning
- `_migrate_clean_sentinel_prices()`: `DELETE FROM products WHERE price >= 99999998`
- `_migrate_normalize_source()`: `UPDATE products SET source = 'tiendas ishop' WHERE source = 'tiendasishop'`
- Both run automatically in `_migrate_schema()` on next `init_db()` call
- Both accept optional `tgt_engine` parameter for test isolation
- Both are idempotent

### Plan 9.3 — Verification
- 3 new tests for sentinel filtering + 3 new DB migration tests
- DB verified: 127 records, 0 sentinel, 0 wrong sources
- Max price now 25,289,000 (was 99,999,999), avg 9,195,748 (was 22,603,087)

## Files Modified
- `src/apple_deals/crawlers/tiendasishop.py` — sentinel filter
- `src/apple_deals/db/session.py` — cleaning migrations
- `tests/test_crawlers.py` — sentinel tests
- `tests/test_db.py` — migration tests
