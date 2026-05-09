# Summary: 02-01 — Crawler Contract & Test Fixtures

**Phase:** 02-crawling-core | **Plan:** 01/03

## Files Created

- `src/apple_deals/crawlers/base.py` — `ProductData` TypedDict, `BaseCrawler` ABC, `parse_title()`
- `tests/fixtures/tiendasishop_products.json` — 2 products (Mac mini M4, MacBook Air M5)
- `tests/fixtures/mac_center_products.json` — 2 products (Mac mini M4 Pro, MacBook Pro M5 Max)
- `tests/test_crawlers.py` — 9 unit tests covering parse_title, ProductData, BaseCrawler ABC, fixture parseability

## Verification

- `uv run pytest tests/test_crawlers.py -v` — 9/9 passed
- `uv run mypy src/apple_deals/crawlers/base.py` — no issues found
- `uv run python -c "from apple_deals.crawlers.base import ProductData, BaseCrawler, parse_title; print('OK')"` — imports clean

## Notes

- `parse_title()` correctly extracts storage/color/memory from both modern M4/M5 titles and older M1-era titles
- All downstream plans (02-02, 02-03) import from `base.py` and use the JSON fixtures
