# Summary: 03-01 — DB Maintenance Layer

**Phase:** 03-database-maintenance | **Plan:** 01/02

## Files Modified

- `pyproject.toml` — added `[project.optional-dependencies] postgres = ["psycopg2-binary>=2.9.12"]`
- `src/apple_deals/db/crud.py` — added `_naive_utc_cutoff()`, `prune_old_records()`, `count_prunable()`, `get_db_stats()`

## Files Created

- `tests/test_db_crud.py` — 6 unit tests for pruning and stats functions

## Verification

- `uv run pytest tests/ -v` — 30/30 passed (all existing + 6 new)
- `uv run mypy src/apple_deals/db/crud.py --ignore-missing-imports` — no issues
- All success criteria met:
  - `[project.optional-dependencies]` with psycopg2-binary present
  - crud.py exports all three new functions
  - No `datetime.utcnow()` usage
  - Naive UTC pattern (`replace(tzinfo=None)`) enforced
  - psycopg2-binary 2.9.12 installed
