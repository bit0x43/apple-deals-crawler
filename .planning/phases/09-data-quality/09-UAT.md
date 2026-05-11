# Phase 9: Data Quality & Bug Fixes — UAT Report

**Date:** 2026-05-11
**Status:** ALL VERIFIED

---

## UAT Criteria

| # | Criteria | Result | Evidence |
|---|----------|--------|----------|
| 1 | No sentinel prices (>= 99,999,998) in DB | ✅ PASS | 0 sentinel-price records |
| 2 | Source names normalized | ✅ PASS | 0 records with `source = "tiendasishop"` |
| 3 | Tiendas iShop crawler filters sentinel products | ✅ PASS | `test_tiendasishop_sentinel_constant` + `test_tiendasishop_parse_product_filters_sentinel` pass |
| 4 | DB migrations are idempotent | ✅ PASS | `test_migrate_clean_is_idempotent` passes |
| 5 | DB migration tests pass | ✅ PASS | `test_migrate_clean_sentinel_prices` + `test_migrate_normalize_source` pass |
| 6 | All 76 tests pass | ✅ PASS | `pytest tests/ -v` = 76 passed |
| 7 | mypy clean | ✅ PASS | 0 errors |
| 8 | ruff clean | ✅ PASS | All checks passed |
| 9 | TUI loads and displays catalog | ✅ PASS | Pilot test: CatalogScreen, 64 rows |
| 10 | TUI Tab switch works | ✅ PASS | Catalog ↔ History |
| 11 | TUI Quit works | ✅ PASS | `q` exits cleanly |
| 12 | Regex bug in `_extract_memory_from_page` fixed | ✅ PASS | `r"(\d+)\s*GB)\s*"` → `r"(\d+)\s*GB\s*"` (removed extra `)`) |
| 13 | Memory extraction selectors expanded | ✅ PASS | Added fieldset+legend strategy, `.option-selector__label`, `.single-option-selector`, `fieldset input[type=radio]` |
| 14 | TUI default sort = storage → memory → price | ✅ PASS | `_populate_table` sorts by `(storage_bytes, memory_gb, price)` |
| 15 | Price column header click still toggles | ✅ PASS | `on_data_table_header_selected` handles price key |
| 16 | Memory enrichment via live crawl verified | ✅ PASS | `uv run apple-deals crawl` — 64/64 products enriched (100%) |
| 17 | Enrichment browser resilience | ✅ PASS | Browser recycles every 15 pages; health check with auto-restart; `domcontentloaded` (not `networkidle`); 15s per-page timeout |
| 18 | Memory values normalized to NoSpaceGB format | ✅ PASS | `_gb()` helper ensures "16GB" not "16 GB" |
| 19 | GitHub Actions cleanup step added | ✅ PASS | `db clean` step runs after crawl in `crawl.yml` |
| 20 | Memory extraction uses fieldset+legend | ✅ PASS | Targets `<fieldset><legend>Memoria</legend></fieldset>` — no storage false positives |

---

## DB Health

| Metric | Value |
|--------|-------|
| Total records | 64 |
| Unique products | 64 |
| Memory populated | 64/64 (100%) |
| Sentinel prices | 0 |
| Wrong source names | 0 |
| Sources | `tiendas ishop` (42), `mac-center` (22) |
| Price range | 2,599,000 — 25,289,000 COP |
| Crawl duration | ~2-3 min (full enrichment) |

---

## Memory Distribution

| Memory | Count | Products |
|--------|-------|----------|
| 16GB, 24GB | 37 | MacBook Air/Pro base M4/M5 |
| 24GB | 11 | Higher-end configs |
| 16GB, 24GB, 8GB | 2 | MacBook Air M4 (8GB still listed) |
| 24GB, 48GB | 5 | M5 Pro/Max configs |
| 36GB | 3 | Pro/Max configs |
| 36GB, 48GB | 3 | M5 Max configs |
| 32GB | 1 | Mac Studio base |
| 32GB, 36GB, 64GB, 96GB | 2 | Mac Studio M4 Max / M3 Ultra |

---

## TUI Sort Verification

Sort order confirmed: storage (asc) → memory (asc) → price (asc).

Products with null storage/memory appear first (sorted as 0).

---

## Enrichment Architecture

### Extraction strategy (in order):
1. **Fieldset+legend** (`<fieldset class="js-product-option-form"><legend>Memoria</legend>`) — most precise, no storage false positives
2. Flat `[data-title]` attributes with GB values
3. CSS swatch / option selectors
4. JSON-LD product options (`product.options.filter(name ~ "memoria|ram|memory")`)
5. Page `<title>` fallback

### Browser lifecycle:
- Recycles every 15 pages to prevent memory pressure
- `browser.is_connected()` health check between every product
- Auto-restart on browser crash
- `domcontentloaded` (not `networkidle`) — 5-10x faster page loads
- 15s per-page timeout

### Normalization:
- `_gb()` helper ensures all values stored as "NGB" (e.g. "96GB" not "96 GB")

---

## GitHub Actions Workflow

The crawl workflow (`.github/workflows/crawl.yml`) now includes an explicit cleanup step:

```yaml
- name: Run crawl
  run: uv run apple-deals crawl

- name: Prune old records (90-day retention)
  run: uv run apple-deals db clean
```
