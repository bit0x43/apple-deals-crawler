# Phase 10: TUI Filters & Ordering - Research

**Researched:** 2026-05-11
**Domain:** Textual TUI — DataTable sort, Select widget, filter controls, thread workers
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Add a `Select` widget for stock status with options: All, In Stock, Out of Stock. Default: All.
- **D-02:** Stock filter re-queries the DB via the existing `@work(thread=True)` pattern — no client-side filtering.
- **D-03:** Add a `Select` widget for memory capacity with options dynamically derived from unique DB values. Include "All" as default.
- **D-04:** Add a `Select` widget for storage capacity with options dynamically derived from unique DB values. Include "All" as default.
- **D-05:** Clicking any column header (Memory or Storage) sorts by that column's values. Click again reverses direction. Uses DataTable's built-in `sort()` method (same pattern as existing Price column sort).
- **D-06:** The sort state tracks which column is active and the current direction independently. Default initial sort remains storage → memory → price.
- **D-07:** The sort order is preserved across filter changes — changing a filter re-queries but re-applies the current sort.
- **D-08:** Extend `get_current_prices()` signature to accept `in_stock_filter: bool | None`, `memory_filter: str | None`, `storage_filter: str | None` parameters.
- **D-09:** Stock filter maps to `Product.in_stock == True/False`.
- **D-10:** Memory filter uses `Product.memory.ilike(f"%{value}%")` for partial matching.
- **D-11:** Storage filter uses `Product.storage.ilike(f"%{value}%")` for same reason.
- **D-12:** Filter widgets stack in a horizontal row below the Header, above the DataTable. If width insufficient, they wrap naturally via Textual's Horizontal container with `overflow: auto`.

### the agent's Discretion
- Exact order of filter controls in the layout
- CSS styling for the filter row (sizing, spacing)
- Whether memory/storage filter values are static or dynamic-queried
- Whether to add a "Clear Filters" button

### Deferred Ideas (OUT OF SCOPE)
- Color filter (v2)
- Price range filter (v2)
- Multi-select filters (v2)
- Crawl health dashboard (v2)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TUI-05 | Catalog view can be filtered by stock, memory, and storage | D-01 through D-04 define Select widgets; D-08 through D-11 define query param extensions |
| TUI-06 | Catalog view can be ordered by memory or storage columns (in addition to price) | D-05/D-06 define sort behavior; DataTable's `sort()` with `key=` custom callable solves lexicographic sorting issue |
| TUI-07 | Filter state and sort state compose correctly (filters re-query, sort re-applies) | D-07 requires sort preservation across filter changes; tracked via `_sort_column` + `_sort_reverse` |
</phase_requirements>

---

## Summary

Phase 10 adds three new `Select` filter widgets (Stock, Memory, Storage) and column-based ordering for the Memory and Storage columns to the catalog view. This brings the filter row from 2 to 5 `Select` widgets and adds custom sort logic for non-numeric columns.

**The central technical challenge** is that DataTable's default lexicographic sort is wrong for memory/storage values — "16GB" < "8GB" and "1TB" < "256GB" under string comparison. Textual's DataTable `sort()` method has supported a `key` parameter since v0.41.0 [VERIFIED: textual.textualize.io/widgets/data_table/#sorting], which solves this: pass `_memory_gb()` or `_storage_bytes()` as the key function. The existing helper functions in `app.py` parse these values correctly.

**Secondary challenge** is managing sort state across filter re-queries. The current `_populate_table()` always re-sorts to the default order (storage→memory→price). To preserve sort across filters (D-07), the implementation must: (1) track the active sort column and direction, (2) clear rows after query, (3) re-populate with current sort applied.

**Dynamic filter options** for Memory and Storage `Select` widgets are loaded at mount time via a thread worker querying `DISTINCT` values from the database. `Select.set_options()` replaces options in-place [VERIFIED: textual.textualize.io/widgets/select/]. Note that `set_options()` resets the selection, so "All" must be re-applied as default after loading.

**Primary recommendation:** Use `DataTable.sort(column_key, key=parser_func, reverse=bool)` for all sort operations (including upgrading Price to use a numeric key). Track `_sort_column: str | None` and `_sort_reverse: bool`. On filter change, re-query, then re-sort based on tracked state.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Filter Select widgets (Stock/Memory/Storage) | TUI (`CatalogScreen`) | — | Widget composition owned by CatalogScreen; same pattern as existing Model/Store filters |
| Filter state management | TUI (`CatalogScreen` attributes) | — | In-memory widget state; no persistence needed |
| Sort state tracking | TUI (`CatalogScreen` attributes) | — | Tracks `_sort_column` + `_sort_reverse`; re-applied after filter re-queries |
| Dynamic filter options query (DISTINCT memory/storage) | TUI (via `@work(thread=True)`) | `db/crud.py` | Thread-safe DB query, UI callback via `call_from_thread` |
| Extended `get_current_prices()` | `db/crud.py` | — | New filter params added to existing query function |
| DB query for current prices | TUI (via `@work(thread=True)`) | `db/crud.py` | Same existing thread worker pattern |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| textual | 8.2.5 [VERIFIED: pip] | TUI framework | DataTable.sort(key=), Select.set_options(), thread workers — all verified in installed version |
| sqlalchemy | >=2.0.49 [VERIFIED: pyproject.toml] | ORM queries | `select(Product.memory).distinct()` for filter options; `ilike()` for filter predicates |
| rich | 15.0.0 [VERIFIED: uv.lock] | Terminal rendering | Underpins Textual rendering |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 9.0.3+ | Test framework | Writing unit tests for CRUD extensions and sort helper functions |

**Installation:**
No new dependencies needed — textual, sqlalchemy, and rich are already in `pyproject.toml`.

**Version verification:**
```bash
uv run python -c "import textual; print(textual.__version__)"  # 8.2.5
```

---

## Architecture Patterns

### System Architecture Diagram

```
CatalogScreen (Screen)
│
├── Header
│
├── Horizontal.filters
│   ├── Select (Model)          # existing
│   ├── Select (Store)          # existing
│   ├── Select (Stock)          # NEW - All/In Stock/Out of Stock
│   ├── Select (Memory)         # NEW - dynamically loaded from DB
│   └── Select (Storage)        # NEW - dynamically loaded from DB
│
├── DataTable (catalog-table)
│   └── Columns: Model, Store, Price (COP), Stock, Memory, Storage, Color
│       click header → on_data_table_header_selected()
│         → price:   table.sort("price", key=parse_int)
│         → memory:  table.sort("memory", key=_memory_gb)
│         → storage: table.sort("storage", key=_storage_bytes)
│
└── Footer
         │
         │ Select.Changed → re-query with all filter params
         │               → re-apply current sort (D-07)
         v
    @work(thread=True)
    load_data()
         │
         │ session = get_session()
         │ rows = get_current_prices(session,
         │     model_filter, store_filter,
         │     in_stock_filter,      ← NEW
         │     memory_filter,        ← NEW
         │     storage_filter)       ← NEW
         v
    _populate_table(rows)
         │
         │ Apply current sort (default or user-selected)
         v
    DataTable (re-populated)

    @work(thread=True)
    load_filter_options()          ← NEW worker
         │
         │ Query DISTINCT Product.memory
         │ Query DISTINCT Product.storage
         v
    Select.set_options() on Memory + Storage widgets
```

### Recommended Project Structure (no changes — all editing existing files)

```
src/apple_deals/
├── tui/
│   └── app.py              # Edit: add filters, sort state, helper workers
├── db/
│   ├── models.py           # No changes needed
│   ├── session.py          # No changes needed
│   └── crud.py             # Edit: extend get_current_prices()
```

### Pattern 1: DataTable Sort with Custom Key Function

**What:** Use `DataTable.sort(column_key, key=parser_func, reverse=bool)` to sort columns where the display string doesn't sort correctly lexicographically.

**When to use:** For Memory and Storage columns where "16GB" < "8GB" under string sort. Also recommended for Price column where "9,999,000" < "10,000,000" under string sort.

**Source:** [VERIFIED: textual.textualize.io/widgets/data_table/#sorting — "By both Column and Key function"]

```python
# Sorting memory column with custom key
table.sort("memory", key=_memory_gb, reverse=self._sort_reverse)

# Sorting storage column with custom key
table.sort("storage", key=_storage_bytes, reverse=self._sort_reverse)

# Sorting price with custom key (recommended upgrade)
table.sort("price", key=lambda p: int(p.replace(",", "")), reverse=self._sort_reverse)
```

The `key` function receives only values from the specified columns as positional arguments. For a single column, it receives the cell value directly.

### Pattern 2: Dynamic Select Options via Thread Worker

**What:** At mount time, run a thread worker to query distinct values from DB, then call `Select.set_options()` to populate.

**When to use:** D-03/D-04 — memory and storage filter options loaded from database.

**Source:** [VERIFIED: textual.textualize.io/widgets/select/#set_options]

```python
def on_mount(self) -> None:
    # ... existing setup ...
    self.load_filter_options()

@work(thread=True, exclusive=True)
async def load_filter_options(self) -> None:
    """Fetch distinct memory/storage values from DB."""
    worker = get_current_worker()
    session = get_session()
    try:
        memories = session.scalars(
            select(Product.memory)
            .distinct()
            .where(Product.memory.isnot(None))
            .order_by(Product.memory)
        ).all()
        storages = session.scalars(
            select(Product.storage)
            .distinct()
            .where(Product.storage.isnot(None))
            .order_by(Product.storage)
        ).all()
    finally:
        session.close()

    if not worker.is_cancelled:
        self.call_from_thread(self._set_filter_options, memories, storages)

def _set_filter_options(self, memories: list[str], storages: list[str]) -> None:
    """Populate memory and storage Select widgets from queried values."""
    memory_select = self.query_one("#memory-filter", Select)
    storage_select = self.query_one("#storage-filter", Select)

    memory_options = [("All", "all")] + [(m, m) for m in sorted(set(memories))]
    storage_options = [("All", "all")] + [(s, s) for s in sorted(set(storages))]

    memory_select.set_options(memory_options)
    storage_select.set_options(storage_options)

    # set_options() resets selection — re-apply "all" default
    memory_select.value = "all"
    storage_select.value = "all"
```

**Important:** `set_options()` resets the selection to blank (if `allow_blank`) or first option. After `set_options()`, the `value` must be explicitly set back to the desired default.

### Pattern 3: Sort State Management for Filter Persistence

**What:** Track active sort column and direction; re-apply after filter re-queries (D-07).

**When to use:** Always — ensures sort order doesn't reset when user changes a filter.

```python
class CatalogScreen(Screen):
    _sort_column: str | None = None   # None = default sort
    _sort_reverse: bool = False

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        col = event.column_key.value
        if col in ("price", "memory", "storage"):
            if self._sort_column == col:
                self._sort_reverse = not self._sort_reverse
            else:
                self._sort_column = col
                self._sort_reverse = False
            self._apply_sort_to_table()

    def _apply_sort_to_table(self) -> None:
        """Apply current sort state to the DataTable."""
        table = self.query_one("#catalog-table", DataTable)
        col = self._sort_column
        if col == "memory":
            table.sort(col, key=_memory_gb, reverse=self._sort_reverse)
        elif col == "storage":
            table.sort(col, key=_storage_bytes, reverse=self._sort_reverse)
        elif col == "price":
            table.sort(col, key=lambda p: int(p.replace(",", "")), reverse=self._sort_reverse)
        # col is None → don't call sort, keep default row order from _populate_table

    def _populate_table(self, rows: list[Product]) -> None:
        """Populate DataTable with sorted rows, preserving current sort."""
        if self._sort_column:
            # User has actively selected a sort column
            key_fn = {
                "price": lambda p: p.price,
                "memory": lambda p: _memory_gb(p.memory),
                "storage": lambda p: _storage_bytes(p.storage),
            }.get(self._sort_column)
            if key_fn:
                rows = sorted(rows, key=key_fn, reverse=self._sort_reverse)
        else:
            # Default sort: storage → memory → price
            rows = sorted(
                rows,
                key=lambda p: (_storage_bytes(p.storage), _memory_gb(p.memory), p.price),
            )

        self._current_rows = rows
        table = self.query_one("#catalog-table", DataTable)
        table.clear()
        for p in rows:
            stock = "✅ In Stock" if p.in_stock else "❌ Out of Stock"
            table.add_row(
                p.reference, p.source, f"{p.price:,.0f}",
                stock, p.memory or "—", p.storage or "—", p.color or "—",
                key=str(p.id),
            )
        # Now re-apply DataTable sort if column is set (otherwise rows are already in order)
        if self._sort_column:
            self._apply_sort_to_table()
```

### Pattern 4: Extended get_current_prices() with Filter Params

**What:** Add three new optional filter parameters to the existing query function.

**When to use:** D-08 through D-11.

```python
def get_current_prices(
    session: Session,
    model_filter: str | None = None,
    store_filter: str | None = None,
    in_stock_filter: bool | None = None,     # NEW
    memory_filter: str | None = None,        # NEW
    storage_filter: str | None = None,       # NEW
) -> list[Product]:
    subq = (
        select(Product.sku, Product.source, func.max(Product.crawled_at).label("max_crawled_at"))
        .group_by(Product.sku, Product.source)
        .subquery()
    )
    stmt = (
        select(Product)
        .join(
            subq,
            (Product.sku == subq.c.sku)
            & (Product.source == subq.c.source)
            & (Product.crawled_at == subq.c.max_crawled_at),
        )
        .order_by(Product.price)
    )
    if model_filter and model_filter != "all":
        stmt = stmt.where(Product.reference.ilike(f"%{model_filter}%"))
    if store_filter and store_filter != "all":
        stmt = stmt.where(Product.source == store_filter)
    if in_stock_filter is not None:             # NEW
        stmt = stmt.where(Product.in_stock == in_stock_filter)
    if memory_filter and memory_filter != "all":  # NEW
        stmt = stmt.where(Product.memory.ilike(f"%{memory_filter}%"))
    if storage_filter and storage_filter != "all":  # NEW
        stmt = stmt.where(Product.storage.ilike(f"%{storage_filter}%"))
    return list(session.scalars(stmt))
```

### Anti-Patterns to Avoid

- **Calling `DataTable.sort()` without a custom key for memory/storage:** Results in incorrect ordering ("1TB" sorts before "256GB"). Always use `key=_storage_bytes` or `key=_memory_gb`.
- **Setting `Select.value` before `set_options()` completes:** The dynamic filter options are loaded asynchronously. The initial mount-time `value="all"` in `compose()` works because `allow_blank=True` is default. After `set_options()`, explicitly set `value` back.
- **Re-creating filter Select widgets on every filter change:** Use `set_options()` to update in-place, not remove/re-mount.
- **Missing the `_sort_reverse` toggle on first click of a new column:** When user clicks a different column, direction should reset to ascending (not inherit previous column's direction). D-06 requires independent direction tracking.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Custom sort for non-numeric columns | Custom sort comparator class | `DataTable.sort(key=_memory_gb)` | DataTable supports `key=callable` since v0.41.0; receives cell values as positional args |
| Dynamic Select options | Remove/re-mount Select widget | `Select.set_options()` | Built-in, repopulates option list, preserves widget ID and position |
| Sort state management | Custom sorted list + manual re-render | `DataTable.sort()` for initial pass, then re-query + re-sort | DataTable.sort() handles stable sort, row key preservation; re-sorting Python list before populating handles complex sorts |

**Key insight:** DataTable's `sort()` with `key=` parameter handles all the complex sorting. The only custom logic needed is the parser functions (`_memory_gb`, `_storage_bytes`) which already exist.

---

## Runtime State Inventory

> Not applicable — this is a TUI features phase, not a rename/refactor/migration phase.

---

## Common Pitfalls

### Pitfall 1: Lexicographic Sort on Memory/Storage Columns

**What goes wrong:** "16GB" sorts before "8GB" and "1TB" sorts before "256GB" because string comparison compares character-by-character.

**Why it happens:** DataTable's default `sort()` without a `key` parameter compares cell values as strings.

**How to avoid:** Always pass `key=_memory_gb` or `key=_storage_bytes` when sorting Memory or Storage columns:

```python
table.sort("memory", key=_memory_gb, reverse=bool)
table.sort("storage", key=_storage_bytes, reverse=bool)
```

**Warning signs:** "1TB" appears before "256GB" in ascending sort, "16GB" before "8GB".
[VERIFIED: textual.textualize.io/widgets/data_table/#sorting — "correct sorting may require your key function to undo your formatting"]

### Pitfall 2: set_options() Resets Select Value

**What goes wrong:** After calling `Select.set_options()`, the selection reverts to blank or first option, losing the "All" default.

**Why it happens:** `set_options()` is documented to reset the selection [VERIFIED: textual.textualize.io/widgets/select/#set_options — "This will reset the selection"].

**How to avoid:** Always set `Select.value` explicitly after calling `set_options()`:

```python
select.set_options(options)
select.value = "all"  # re-apply default
```

**Warning signs:** Memory/Storage filter defaults show a blank entry instead of "All" after initial load.

### Pitfall 3: Calling `_storage_bytes()` or `_memory_gb()` with None

**What goes wrong:** `_storage_bytes(None)` returns `0` (early return check works). `_memory_gb(None)` returns `0` (early return works). But if the DB stores unexpected format like "256GB" (no space) for storage, `_storage_bytes` returns 0.

**Why it happens:** `_storage_bytes` splits on space and expects 2 parts. "256GB" splits to ["256GB"] which has `len(parts) != 2`.

**How to avoid:** Verify the storage format in actual data. If storage values may be stored without a space (e.g., "256GB" instead of "256 GB"), add a fallback:

```python
def _storage_bytes(val: str | None) -> int:
    if not val:
        return 0
    import re
    nums = re.findall(r"(\d+)", val)
    if not nums:
        return 0
    val_upper = val.upper()
    return int(nums[0]) * 1024 if "TB" in val_upper else int(nums[0])
```

**Warning signs:** Storage sort produces incorrect ordering, or all None/variant-format entries sink to bottom.

### Pitfall 4: Filter Worker Triggers Before Dynamic Options Are Loaded

**What goes wrong:** The user changes a filter (selects a stock value) before the Memory/Storage `Select` widgets finish loading their options. The `on_select_changed` handler fires, re-queries, but the Memory/Storage filter values are still "all" (default) so the query is correct — no actual bug, just a cosmetic ordering issue.

**Why it happens:** Both `load_data()` and `load_filter_options()` run as async workers.

**How to avoid:** Ensure `load_filter_options()` completes before or concurrently with the initial `load_data()`. Since `load_filter_options()` uses `exclusive=True`, only one instance runs at a time. The initial `load_data()` in `on_mount()` will use default "all" values for new filters, which is correct. No synchronization needed — the system is inherently correct since "all" is the initial value for all filters.

### Pitfall 5: `_memory_gb` Receives Wrong Values from DataTable.sort() Key Function

**What goes wrong:** The `key` function passed to DataTable.sort() is called with cell values. When called as `table.sort("memory", key=_memory_gb)`, the function receives the string value from the "memory" column cell (e.g., "16GB"). Since `_memory_gb` takes a single string and extracts the number, it works correctly. But if the cell contains emoji or other Rich renderables, the raw renderable is passed, not the plain text.

**How to avoid:** Ensure the "memory" and "storage" columns contain plain strings, not Rich `Text` objects. Currently they do:

```python
table.add_row(..., p.memory or "—", p.storage or "—", ...)
```

These are plain strings. Safe to use with `key=_memory_gb`. The emoji in the "Stock" column (✅/❌) is fine because stock is not sortable.
[VERIFIED: reading src/apple_deals/tui/app.py lines 126-137]

### Pitfall 6: Sorting After `clear()` + Repopulate

**What goes wrong:** Calling `table.clear()` removes all rows but preserves columns. After re-adding rows, calling `table.sort()` works correctly because sort operates on the internal `_data` dict which is rebuilt by `add_row()`. However, `table.sort()` sorts the *current* row order, so rows must be populated first, then sorted.

**How to avoid:** Order of operations: (1) `table.clear()`, (2) `table.add_row(...)` for all rows, (3) `table.sort(...)` if applying a sort. Do NOT sort before adding rows.
[VERIFIED: textual.textualize.io/widgets/data_table/ — `clear()` preserves columns but removes rows]

---

## Code Examples

### Sorting Memory and Storage Columns with Custom Keys

```python
# Source: [VERIFIED: textual.textualize.io/widgets/data_table/#sorting]
from textual.screen import Screen
from textual.widgets import DataTable
from apple_deals.tui.app import _memory_gb, _storage_bytes

class CatalogScreen(Screen):
    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        col = event.column_key.value
        table = self.query_one("#catalog-table", DataTable)

        if col == "memory":
            table.sort(col, key=_memory_gb, reverse=self._sort_reverse)
        elif col == "storage":
            table.sort(col, key=_storage_bytes, reverse=self._sort_reverse)
        elif col == "price":
            table.sort(col, key=lambda p: int(p.replace(",", "")), reverse=self._sort_reverse)
```

### Dynamic Select Population from DB

```python
# Source: [VERIFIED: textual.textualize.io/widgets/select/#set_options]
#        + [VERIFIED: textual.textualize.io/guide/workers — thread worker pattern]
from textual import work
from textual.worker import get_current_worker
from sqlalchemy import select

@work(thread=True, exclusive=True)
async def load_filter_options(self) -> None:
    worker = get_current_worker()
    session = get_session()
    try:
        memories = session.scalars(
            select(Product.memory)
            .distinct()
            .where(Product.memory.isnot(None))
        ).all()
        storages = session.scalars(
            select(Product.storage)
            .distinct()
            .where(Product.storage.isnot(None))
        ).all()
    finally:
        session.close()
    if not worker.is_cancelled:
        self.call_from_thread(self._set_filter_options, memories, storages)

def _set_filter_options(self, memories: list[str], storages: list[str]) -> None:
    memory_opts = [("All", "all")] + [(m, m) for m in sorted(set(memories))]
    storage_opts = [("All", "all")] + [(s, s) for s in sorted(set(storages))]

    self.query_one("#memory-filter", Select).set_options(memory_opts)
    self.query_one("#storage-filter", Select).set_options(storage_opts)
    # set_options() resets value — re-apply default
    self.query_one("#memory-filter", Select).value = "all"
    self.query_one("#storage-filter", Select).value = "all"
```

### Thread Worker for Filter Data Loading (Full Pattern)

```python
# Source: [VERIFIED: src/apple_deals/tui/app.py lines 97-116 — existing pattern]
@work(thread=True, exclusive=True)
async def load_data(self) -> None:
    """Fetch current prices with all active filters in a thread worker."""
    worker = get_current_worker()

    # Collect filter values from all 5 Select widgets
    model_val = self.query_one("#model-filter", Select).value
    store_val = self.query_one("#store-filter", Select).value
    stock_val = self.query_one("#stock-filter", Select).value
    memory_val = self.query_one("#memory-filter", Select).value
    storage_val = self.query_one("#storage-filter", Select).value

    model_filter = None if model_val == "all" else str(model_val)
    store_filter = None if store_val == "all" else str(store_val)
    in_stock_filter = {"in_stock": True, "out_of_stock": False}.get(str(stock_val))
    memory_filter = None if memory_val == "all" else str(memory_val)
    storage_filter = None if storage_val == "all" else str(storage_val)

    session = get_session()
    try:
        rows = get_current_prices(
            session,
            model_filter=model_filter,
            store_filter=store_filter,
            in_stock_filter=in_stock_filter,
            memory_filter=memory_filter,
            storage_filter=storage_filter,
        )
    except Exception:
        rows = []
    finally:
        session.close()

    if not worker.is_cancelled:
        self.call_from_thread(self._populate_table, rows)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| DataTable.sort() without key (lexicographic) | DataTable.sort(key=callable) | Textual v0.41.0 | Custom sort for non-numeric columns is now a one-liner |
| Manual table rebuild for filter changes | Select.set_options() for dynamic options | Textual ~0.24.0 | Options update in-place without widget replacement |

[VERIFIED: textual.textualize.io/widgets/data_table/#sorting]
[VERIFIED: textual.textualize.io/widgets/select/#set_options]
[VERIFIED: Textual 8.2.5 installed]

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `_storage_bytes()` handles actual storage values correctly (format "512 GB" with space) | Standard Stack, Code Examples | Verify against actual DB data. If format is "256GB" (no space), function returns 0 for those entries and sort breaks. |
| A2 | Memory/storage filter values stored as plain strings in DataTable cells, not Rich renderables | Pitfall 5 | The `key` function receives the raw cell value; if cells contain Rich Text objects instead of strings, the sort key function would fail |
| A3 | SELECT DISTINCT returns None-filtered values that can be cleanly turned into Select options | Code Examples | If NULL values slip through or empty strings exist, options list would include them |

---

## Open Questions

1. **Actual storage format in DB — space-separated or not?**
   - What we know: `_storage_bytes()` expects "512 GB" (split on space, 2 parts)
   - What's unclear: Some crawlers may store as "256GB" without space
   - Recommendation: Check a few actual DB records. If format is inconsistent, update `_storage_bytes()` to use regex-based parsing (like `_memory_gb`) instead of space splitting.

2. **Price column sort — should it be upgraded to use a numeric key?**
   - What we know: Current price sort uses DataTable.sort() with no key, comparing comma-formatted strings. This works for similar-length prices (all 7-8 digit COP values) but breaks for cross-length comparisons.
   - What's unclear: Whether D-05's "same pattern as existing" means we should fix price sort too, or leave it as-is.
   - Recommendation: Upgrade price sort to use `key=lambda p: int(p.replace(",", ""))` for correctness. It's consistent with the custom-key approach for memory/storage and avoids a subtle bug.

3. **Sort state across filter re-query — DataTable.sort() vs Python sorted() for re-population?**
   - What we know: D-07 requires sort persistence. After re-query, `_populate_table` must re-apply the sort.
   - What's unclear: Should we (A) sort the Python list before populating and also re-call DataTable.sort(), or (B) only sort the Python list and skip DataTable.sort()?
   - Recommendation: Use approach A — sort Python list before add_row (for correct ordering during populating), then call DataTable.sort() with the custom key (for DataTable's internal state consistency). The `_apply_sort_to_table` method handles this.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| textual | TUI rendering | ✓ | 8.2.5 | — |
| rich | Terminal rendering | ✓ | 15.0.0 | — |
| sqlalchemy | DB queries | ✓ | >=2.0.49 | — |
| SQLite | DB backend (default) | ✓ | stdlib | — |
| pytest | Testing | ✓ | 9.0.3+ | — |
| uv | Package management | ✓ | — | pip |

**Missing dependencies with no fallback:** None — all required dependencies are already available.

**Missing dependencies with fallback:** None.

---

## Validation Architecture

> `workflow.nyquist_validation` is `false` in `.planning/config.json` — this section is SKIPPED.

---

## Security Domain

> This phase adds filter controls and column ordering to an existing read-only TUI. No network I/O, no user input stored to DB, no authentication. Security considerations are not applicable for this phase.

---

## Sources

### Primary (HIGH confidence)
- `src/apple_deals/tui/app.py` — Current TUI implementation (lines 1-266) — confirmed `_memory_gb`, `_storage_bytes` functions, existing worker pattern, Select+DataTable composition [VERIFIED: direct read]
- `src/apple_deals/db/crud.py` — `get_current_prices()` signature and implementation [VERIFIED: direct read]
- `src/apple_deals/db/models.py` — `Product` model schema with `in_stock`, `memory`, `storage` fields [VERIFIED: direct read]
- `src/apple_deals/pyproject.toml` — textual>=0.89, sqlalchemy>=2.0.49 confirmed in deps [VERIFIED: direct read]
- `uv run python -c "import textual; print(textual.__version__)"` — 8.2.5 installed [VERIFIED: runtime check]
- `textual.textualize.io/widgets/data_table/#sorting` — DataTable.sort() accepts `key=callable`, documented behavior [VERIFIED: official docs fetch]
- `textual.textualize.io/widgets/select/#set_options` — Select.set_options() resets selection [VERIFIED: official docs fetch]

### Secondary (MEDIUM confidence)
- GitHub PR #3090 (Textualize/textual) — DataTable sort by function, `key` parameter API design [VERIFIED: GitHub search]
- GitHub Discussion #2934 (Textualize/textual) — `set_options()` recommended over remove/re-mount for dynamic Select [VERIFIED: davep (Textual maintainer) answer]

### Tertiary (LOW confidence)
- A1, A3 — Format assumptions about actual storage/memory values in DB; not verified against actual data snapshot [ASSUMED based on _seed() test data format]

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Textual 8.2.5 confirmed; all required APIs verified in official docs
- Architecture: HIGH — All patterns (sort with key, set_options, thread worker) documented and already used in existing codebase
- Pitfalls: HIGH — DataTable custom sort, set_options reset, and helper function behaviors verified via docs and code reading
- Sort logic: MEDIUM — Custom key pattern verified via docs; exact `_storage_bytes` format match depends on actual DB data (A1)

**Research date:** 2026-05-11
**Valid until:** 2026-06-11 (Textual releases frequently; re-verify if more than 30 days pass)
