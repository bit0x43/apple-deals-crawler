# Phase 4: TUI - Context

**Gathered:** 2026-05-08
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped)

<domain>
## Phase Boundary

Build a full-screen interactive TUI using Textual + Rich: a catalog view showing current prices (filterable by model/store, sortable by price) and a history view showing price trends per product over time. Toggle between views with Tab. Exit with q or Ctrl+C.
</domain>

<decisions>
## Implementation Decisions

### Framework & Structure
- **D-01:** Textual as the TUI framework. Single `App` class in `src/apple_deals/tui/app.py`. Two `Screen` subclasses: `CatalogScreen` and `HistoryScreen`.
- **D-02:** Tab key toggles between CatalogScreen and HistoryScreen. Use `app.push_screen()` / `app.pop_screen()` or `app.switch_screen()`.

### Catalog View
- **D-03:** `DataTable` widget showing current prices. Columns: Model, Store, Price (COP), Memory, Storage, Color.
- **D-04:** "Current prices" = most recent price record per (sku, source) — one row per product variant per store.
- **D-05:** Filter controls: model selector (All / MacBook Air / MacBook Pro / Mac Mini / Mac Studio) and store selector (All / Tiendasishop / Mac Center). Use `Select` widget.
- **D-06:** Sort by price: click column header or keyboard shortcut. Default sort: ascending price.

### History View
- **D-07:** Select a product from catalog → history view shows price timeline for that product.
- **D-08:** Use `Static` widget with Rich `Table` showing date + price rows for the selected product over the rolling window.
- **D-09:** Navigation: arrow keys to select product in catalog, Enter or Tab to view its history.

### CLI Integration
- **D-10:** Replace the `tui` stub in `cli/main.py` with `from apple_deals.tui.app import run_tui; run_tui()`.

### Claude's Discretion
- Exact Textual CSS for layout (standard defaults OK)
- Whether to show a sparkline chart or just a table for history

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/apple_deals/db/models.py` — Product model
- `src/apple_deals/db/session.py` — get_session()
- `src/apple_deals/cli/main.py` — tui stub to replace
- Textual + Rich already in dependencies (added in Phase 1 pyproject.toml)

</code_context>

<specifics>
## Specific Ideas
- Use Textual's built-in dark theme
- Keep the TUI read-only — no editing, just browsing
</specifics>

<deferred>
## Deferred Ideas
- Crawl health dashboard (v2)
- Sparkline price charts (nice-to-have, implement only if time allows)
- In-TUI crawl trigger
</deferred>
