# Summary: 02-03 — CLI Crawl Command & Live Verification

**Phase:** 02-crawling-core | **Plan:** 03/03

## Files Modified

- `src/apple_deals/cli/main.py` — implemented `crawl()` command wiring both store crawlers and crud layer
- `tests/test_cli.py` — updated `test_crawl_stub_exits_one` to `test_crawl_exits_zero`

## Live Crawl Results

| Store | Products Found | First Insert | Second Insert |
|-------|---------------|-------------|---------------|
| tiendasishop | 61 | 61 | 0 |
| mac-center | 26 | 26 | 0 |

- 87 total records persisted with all required fields (reference, sku, memory, storage, color, price, url, source, crawled_at)
- 100% dedup rate on second crawl — change-only storage confirmed
- Sample: `MacBook Neo 13" A18 Pro | MHFF4E/A | COP 2,599,000 | tiendasishop` (storage=256 GB, color=Índigo, memory=None)

## Verification

- `uv run pytest tests/ -v` — 24/24 passed
- `uv run apple-deals crawl` — exits 0 with two summary lines

## Notes

- Some older collection handles on tiendasishop returned 404s (expected — M2/M2 Pro Mac mini collections may have been removed after M4 launch)
- All mac-center collections returned successfully
- Lazy imports in crawl() avoid playwright import at module load time
