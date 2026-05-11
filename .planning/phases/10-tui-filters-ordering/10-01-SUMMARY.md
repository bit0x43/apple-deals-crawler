---
plan: "10-01"
status: complete
verification: all_pass
---

# Summary: Plan 10-01 — TUI Filters & Column Ordering

Extended the TUI catalog view with three new filter controls (Stock, Memory, Storage)
and column-based ordering for Memory and Storage columns.

## What was done

- **Task 1:** Extended `get_current_prices()` in `crud.py` with 3 new optional params
  (`in_stock_filter`, `memory_filter`, `storage_filter`) with `ilike` partial matching
- **Task 2:** Added Stock (All/In Stock/Out of Stock), Memory (dynamic), Storage (dynamic)
  `Select` widgets to `CatalogScreen.compose()`
- **Task 3:** Added `load_filter_options()` thread worker that queries distinct memory/storage
  values from DB and populates the Select widgets via `_set_filter_options()`
- **Task 4:** Replaced price-only sort with multi-column sort state (`_sort_column`/
  `_sort_reverse`) and `_apply_sort_to_table()` for Memory, Storage, and Price columns
  using numeric key functions
- **Task 5:** Updated `load_data()` to read all 5 filter values; `_populate_table()` preserves
  active sort across filter re-queries
- **Task 6:** 6 new tests covering stock, memory, storage filters (individual, combined,
  backward compatibility)

## Files modified

- `src/apple_deals/db/crud.py`
- `src/apple_deals/tui/app.py`
- `tests/test_db_crud.py`

## Verification

- ruff: all checks passed
- mypy: no issues found (15 source files)
- pytest: 82 passed in 0.67s (6 new tests for filter params)
