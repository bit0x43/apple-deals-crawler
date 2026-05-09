# Summary: 03-02 — DB Maintenance CLI Commands

**Phase:** 03-database-maintenance | **Plan:** 02/02

## Files Modified

- `src/apple_deals/cli/main.py` — implemented `db_clean` (--days, --dry-run), `db_stats` (Rich Table), `_auto_prune()` helper, auto-prune at end of crawl
- `tests/test_cli.py` — added 5 new tests (db_clean dry-run, default days, custom days, db_stats, auto_prune existence)

## Files Added

- `pyproject.toml` — added `rich` as direct dependency (was transitive)

## Verification

- `uv run pytest tests/ -v` — 35/35 passed
- `uv run mypy src/apple_deals/cli/main.py --ignore-missing-imports` — no issues
- `uv run apple-deals db clean --help` — shows --days and --dry-run options
- `uv run apple-deals db clean --dry-run` — "Would delete 0 rows older than 90 days."
- `uv run apple-deals db stats` — Rich Table with 87 rows, 32.0 KB, oldest/newest, ~12.4 rows/day
- `_auto_prune` importable and callable from cli.main

## Notes

- `db_clean --days` uses `typer.Option(min=1)` to prevent accidental `days=0` wiping all data (per threat model T-03-04)
- Auto-prune fires at end of every successful crawl using 90-day default retention
