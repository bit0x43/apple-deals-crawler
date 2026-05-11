# Phase 10: TUI Filters & Ordering - Context

**Gathered:** 2026-05-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Add stock (in-stock/out-of-stock), memory capacity, and storage capacity filter controls to the catalog view in the existing TUI. Add column-based ordering for memory and storage columns alongside existing price ordering. Update the underlying `get_current_prices()` query to support the new filter dimensions.

</domain>

<decisions>
## Implementation Decisions

### Stock Filter
- **D-01:** Add a `Select` widget for stock status with options: All, In Stock, Out of Stock. Default: All.
- **D-02:** Stock filter re-queries the DB via the existing `@work(thread=True)` pattern — no client-side filtering of loaded rows.

### Memory Filter
- **D-03:** Add a `Select` widget for memory capacity with options dynamically derived from the unique memory values in the database (query distinct memory values). Include "All" as default. If memory values are normalized (e.g., "8GB", "16GB", "24GB", "32GB", "48GB"), present them as static choices.

### Storage Filter
- **D-04:** Add a `Select` widget for storage capacity with options dynamically derived from unique storage values in the database. Include "All" as default. Default static list: All, 256GB, 512GB, 1TB, 2TB.

### Column Ordering
- **D-05:** Clicking any column header (Memory or Storage) sorts by that column's values. Click again reverses direction. Uses DataTable's built-in `sort()` method (same pattern as existing Price column sort).
- **D-06:** The sort state tracks which column is active and the current direction independently. Default initial sort remains storage → memory → price.
- **D-07:** The sort order is preserved across filter changes — changing a filter re-queries but re-applies the current sort.

### Query Layer
- **D-08:** Extend `get_current_prices()` signature to accept `in_stock_filter: bool | None`, `memory_filter: str | None`, `storage_filter: str | None` parameters.
- **D-09:** Stock filter maps to `Product.in_stock == True/False`.
- **D-10:** Memory filter uses `Product.memory.ilike(f"%{value}%")` to allow partial matching.
- **D-11:** Storage filter uses `Product.storage.ilike(f"%{value}%")` for the same reason.

### Layout
- **D-12:** Filter widgets stack in a horizontal row below the Header, above the DataTable. If width is insufficient, they wrap naturally via Textual's Horizontal container with `overflow: auto`.

### the agent's Discretion
- Exact order of filter controls in the layout
- CSS styling for the filter row (sizing, spacing)
- Whether memory/storage filter values are static or dynamic-queried
- Whether to add a "Clear Filters" button

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### TUI Architecture
- `src/apple_deals/tui/app.py` — Current TUI implementation (CatalogScreen, HistoryScreen, AppleDealsApp)
- `src/apple_deals/db/crud.py` — `get_current_prices()` — query function to extend with new filter params
- `src/apple_deals/db/models.py` — Product model with in_stock, memory, storage fields

### Phase 4 Research
- `.planning/phases/04-tui/04-RESEARCH.md` — Full Textual architecture patterns, thread worker patterns, DataTable patterns

### Test Patterns
- `tests/` — Existing test suite for CLI commands

### Project Skills
- `.claude/skills/sqlalchemy/SKILL.md` — SQLAlchemy ORM patterns and best practices
- `.claude/skills/python-testing-patterns/SKILL.md` — Testing patterns for Python projects

</canonical_refs>

<specifics>
## Specific Ideas

- Memory filter could show unique values from DB at mount time via a separate `@work(thread=True)` query: `session.scalars(select(Product.memory).distinct()).all()` — then remove None and sort numerically.
- Stock filter could also use a simpler approach: two checkboxes or a toggle instead of Select. Select is preferred for consistency with existing Model and Store filters.
- Column ordering should handle the `_storage_bytes()` and `_memory_gb()` helper functions already defined in `app.py` — these exist for sorting but are only used in `_populate_table`. The DataTable sort is text-based (lexicographic), so storage values like "256GB", "1TB" won't sort correctly via `table.sort()`. A custom approach may be needed: store rows with a hidden sort key, or re-sort the underlying data and repopulate.
</specifics>

<deferred>
## Deferred Ideas

- Color filter (v2) — not enough unique values to justify filter
- Price range filter (v2) — need to determine min/max dynamically
- Multi-select filters (v2)
- Crawl health dashboard (v2 — already noted in Phase 4)

</deferred>

---

*Phase: 10-tui-filters-ordering*
*Context gathered: 2026-05-11*
