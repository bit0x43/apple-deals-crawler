# Phase 4: TUI - Research

**Researched:** 2026-05-08
**Domain:** Textual TUI framework, SQLAlchemy query patterns, CLI integration
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Textual as the TUI framework. Single `App` class in `src/apple_deals/tui/app.py`. Two `Screen` subclasses: `CatalogScreen` and `HistoryScreen`.
- **D-02:** Tab key toggles between CatalogScreen and HistoryScreen. Use `app.push_screen()` / `app.pop_screen()` or `app.switch_screen()`.
- **D-03:** `DataTable` widget showing current prices. Columns: Model, Store, Price (COP), Memory, Storage, Color.
- **D-04:** "Current prices" = most recent price record per (sku, source) — one row per product variant per store.
- **D-05:** Filter controls: model selector (All / MacBook Air / MacBook Pro / Mac Mini / Mac Studio) and store selector (All / Tiendasishop / Mac Center). Use `Select` widget.
- **D-06:** Sort by price: click column header or keyboard shortcut. Default sort: ascending price.
- **D-07:** Select a product from catalog → history view shows price timeline for that product.
- **D-08:** Use `Static` widget with Rich `Table` showing date + price rows for the selected product over the rolling window.
- **D-09:** Navigation: arrow keys to select product in catalog, Enter or Tab to view its history.
- **D-10:** Replace the `tui` stub in `cli/main.py` with `from apple_deals.tui.app import run_tui; run_tui()`.

### Claude's Discretion
- Exact Textual CSS for layout (standard defaults OK)
- Whether to show a sparkline chart or just a table for history

### Deferred Ideas (OUT OF SCOPE)
- Crawl health dashboard (v2)
- Sparkline price charts (nice-to-have, implement only if time allows)
- In-TUI crawl trigger
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TUI-01 | User can open an interactive TUI via `apple-deals tui` | D-10 wires CLI stub to `run_tui()`; Textual `App.run()` provides full-screen launch |
| TUI-02 | Catalog view shows current prices filterable by model and store, sortable by price | `DataTable` + `Select` widgets; `sort()` method on DataTable; D-04 SQL query pattern |
| TUI-03 | History view shows price trends per product over the rolling window | `Static` widget rendering Rich `Table`; D-07/D-08 query by (sku, source) with date range |
| TUI-04 | Toggle between catalog and history views (tab or keyboard shortcut) | `BINDINGS` on App class + `switch_screen()` / `push_screen()` + `pop_screen()` |
| CLI-02 | `apple-deals tui` command wired to open the interactive TUI | Replace stub with `run_tui()` call; existing `tui()` command in `cli/main.py` |
</phase_requirements>

---

## Summary

Phase 4 adds an interactive full-screen TUI to the `apple-deals-crawler` CLI. The framework is Textual (currently at v0.x through v8.x series — **latest stable is 8.2.5**), which ships its own CSS-like layout system (TCSS) and a rich widget library including `DataTable`, `Select`, `Static`, `Header`, and `Footer`. All required widgets are built into Textual — no third-party Textual plugins are needed.

The implementation follows a straightforward pattern: one `App` subclass owns app-level keybindings and screen registration; two `Screen` subclasses (`CatalogScreen`, `HistoryScreen`) each manage their own layout and widget composition. Screen switching is handled by `app.switch_screen()` (replaces the top of the stack) or the push/pop pair. The decisions favor `switch_screen()` for simple tab-toggle behavior between two peer screens.

Two SQLAlchemy queries must be introduced in this phase because they do not exist yet (Phases 2-3 only added `upsert_if_changed`, `get_last_price`, and prune/stats functions): `get_current_prices()` — the most-recent record per `(sku, source)` using a subquery or window function — and `get_price_history(sku, source)` returning all records for a product ordered by date. Both queries use the existing `SessionLocal` / `get_session()` infrastructure. Because SQLAlchemy I/O is blocking, these queries must be run in a Textual thread worker to avoid freezing the event loop.

**Primary recommendation:** Use `switch_screen()` for Tab-toggle between two installed screens; use `cursor_type="row"` on DataTable with `RowSelected` event to pass the selected product to HistoryScreen; use `@work(thread=True)` for all DB queries.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| TUI layout and widget rendering | TUI (`tui/app.py`) | — | Textual owns all visual composition |
| Current-prices DB query | TUI (via worker thread) | `db/crud.py` | Query initiated from TUI; reuses existing session factory |
| Price-history DB query | TUI (via worker thread) | `db/crud.py` | Same rationale; new function added to crud.py |
| CLI entrypoint wiring | CLI (`cli/main.py`) | TUI (`tui/app.py`) | CLI calls `run_tui()`, keeping CLI and TUI decoupled |
| Filter/sort state | TUI (`CatalogScreen`) | — | Pure in-memory widget state; no persistence needed |
| Screen navigation state | TUI (`App`) | — | `SCREENS` dict + `switch_screen()` owned by App |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| textual | >=0.89, latest: 8.2.5 | Full-screen TUI framework | Built-in DataTable, Select, Screen system; official Textualize project |
| rich | >=15.0.0 | Terminal rendering (Table, Text, markup) | Textual's native rendering backend; already in uv.lock |
| sqlalchemy | >=2.0.49 | ORM queries for current prices + history | Already in pyproject.toml; Session already wired |

[VERIFIED: pip3 index versions textual] — 8.2.5 is current latest on PyPI as of 2026-05-08
[VERIFIED: uv.lock] — rich 15.0.0 already locked in project
[VERIFIED: pyproject.toml] — sqlalchemy >=2.0.49 already a dependency

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-asyncio | >=0.21 | Async test support for Textual's `run_test()` | Required for any Textual unit tests (run_test is async) |

[ASSUMED] — pytest-asyncio requirement for Textual testing; not verified against project's current dev deps

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `switch_screen()` | `push_screen()` + `pop_screen()` | push/pop maintains a stack (useful for modals); switch replaces top — simpler for peer-screen toggling |
| `Static` + Rich Table for history | `DataTable` for history too | DataTable adds keyboard navigation for history rows; Static is simpler since D-08 explicitly calls for it |
| Thread worker for DB | Async SQLAlchemy | Async SQLAlchemy requires different engine setup; sync + thread worker is simpler with existing session code |

**Installation:**
```bash
uv add textual>=0.89
# rich is already present via uv.lock
```

Note: `textual` depends on `rich` internally — adding `textual` will pull rich in as a transitive dep. [VERIFIED: textual PyPI metadata lists rich as dependency]

---

## Architecture Patterns

### System Architecture Diagram

```
CLI entrypoint (cli/main.py)
        |
        | tui command → run_tui()
        v
  AppleDealsApp (App)
  ├── SCREENS = {"catalog": CatalogScreen, "history": HistoryScreen}
  ├── BINDINGS = [("tab", "switch_screen('history')", ...), ("q", "quit", ...)]
  └── on_mount() → push_screen("catalog")
        |
        +──────────────────────────────────┐
        v                                  v
  CatalogScreen (Screen)         HistoryScreen (Screen)
  ├── Select (model filter)      ├── Label (product title)
  ├── Select (store filter)      └── Static (Rich Table)
  └── DataTable                             ^
        |                                   |
        | on_data_table_row_selected        |
        | → app.selected_product = row_key  |
        | → app.switch_screen("history")    |
        v                                   |
  @work(thread=True)             @work(thread=True)
  get_current_prices(session)    get_price_history(sku, source)
        |                                   |
        v                                   v
  db/crud.py                     db/crud.py
  (SELECT ... WHERE subquery)    (SELECT ... ORDER BY crawled_at)
        |                                   |
        v                                   v
  SQLite / PostgreSQL            SQLite / PostgreSQL
```

### Recommended Project Structure
```
src/apple_deals/
├── tui/
│   ├── __init__.py          # already exists (empty)
│   └── app.py               # AppleDealsApp + CatalogScreen + HistoryScreen + run_tui()
├── db/
│   ├── models.py            # Product model (existing)
│   ├── session.py           # get_session() (existing)
│   └── crud.py              # add: get_current_prices(), get_price_history()
└── cli/
    └── main.py              # replace tui stub with run_tui() call
```

### Pattern 1: App with Two Registered Screens + Tab Toggle

**What:** Register both screens in `SCREENS` dict; bind Tab at App level to `switch_screen`; push initial screen in `on_mount`.
**When to use:** When toggling between two peer views with no modal relationship.

```python
# Source: https://textual.textualize.io/api/app (switch_screen)
# Source: https://github.com/textualize/textual/blob/main/docs/guide/screens.md
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer

class AppleDealsApp(App):
    TITLE = "Apple Deals"
    SCREENS = {
        "catalog": CatalogScreen,
        "history": HistoryScreen,
    }
    BINDINGS = [
        ("tab", "switch_screen('history')", "History"),
        ("q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        self.push_screen("catalog")

def run_tui() -> None:
    AppleDealsApp().run()
```

### Pattern 2: DataTable with Row Cursor + RowSelected Event

**What:** Set `cursor_type="row"` so the entire row is highlighted; handle `DataTable.RowSelected` to extract the selected product's sku/source metadata.
**When to use:** When Enter on a row should trigger navigation (D-07/D-09).

```python
# Source: https://textual.textualize.io/widgets/data_table (RowSelected event)
from textual.widgets import DataTable

class CatalogScreen(Screen):
    def compose(self) -> ComposeResult:
        table = DataTable(id="catalog-table")
        table.cursor_type = "row"
        table.zebra_stripes = True
        yield table

    def on_mount(self) -> None:
        table = self.query_one("#catalog-table", DataTable)
        table.add_columns("Model", "Store", "Price (COP)", "Memory", "Storage", "Color")
        self.load_data()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        # row_key maps back to Product.id stored at add_row(..., key=str(product_id))
        row_key = event.row_key.value
        self.app.selected_product_key = row_key
        self.app.switch_screen("history")
```

### Pattern 3: Thread Worker for Blocking DB Query

**What:** Use `@work(thread=True)` so SQLAlchemy sync I/O doesn't block Textual's async event loop; use `call_from_thread()` to safely update widgets.
**When to use:** Any DB query inside a Textual handler.

```python
# Source: https://textual.textualize.io/guide/workers (thread worker pattern)
from textual import work
from textual.worker import get_current_worker

class CatalogScreen(Screen):
    @work(thread=True, exclusive=True)
    def load_data(self) -> None:
        worker = get_current_worker()
        with get_session() as session:
            rows = get_current_prices(session)
        if not worker.is_cancelled:
            self.call_from_thread(self._populate_table, rows)

    def _populate_table(self, rows: list) -> None:
        table = self.query_one("#catalog-table", DataTable)
        table.clear()
        for row in rows:
            table.add_row(
                row.reference, row.source, f"{row.price:,.0f}",
                row.memory or "—", row.storage or "—", row.color or "—",
                key=str(row.id),
            )
        table.sort("Price (COP)")  # default ascending price sort
```

### Pattern 4: Select Widget for Filtering

**What:** Compose two `Select` widgets for model and store filters; handle `Select.Changed` to re-query and refresh the DataTable.
**When to use:** D-05 — filter controls.

```python
# Source: https://textual.textualize.io/widgets/select (Select.Changed)
from textual import on
from textual.widgets import Select

MODEL_CHOICES = [
    ("All", "all"),
    ("MacBook Air", "macbook-air"),
    ("MacBook Pro", "macbook-pro"),
    ("Mac Mini", "mac-mini"),
    ("Mac Studio", "mac-studio"),
]
STORE_CHOICES = [
    ("All", "all"),
    ("Tiendasishop", "tiendasishop"),
    ("Mac Center", "mac-center"),
]

class CatalogScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Select(MODEL_CHOICES, id="model-filter", prompt="Model")
        yield Select(STORE_CHOICES, id="store-filter", prompt="Store")
        yield DataTable(id="catalog-table")

    @on(Select.Changed, "#model-filter")
    @on(Select.Changed, "#store-filter")
    def filter_changed(self, event: Select.Changed) -> None:
        self.load_data()  # re-queries with current filter values
```

### Pattern 5: DataTable Column Sort

**What:** Use DataTable's built-in `sort()` method. Handle `DataTable.HeaderSelected` to re-sort by the clicked column; track sort direction for toggle.
**When to use:** D-06 — sort by price on click or keyboard.

```python
# Source: https://textual.textualize.io/widgets/data_table (sort method + HeaderSelected)
class CatalogScreen(Screen):
    _sort_reverse: bool = False
    _price_col_key: ColumnKey | None = None

    def on_mount(self) -> None:
        table = self.query_one("#catalog-table", DataTable)
        self._price_col_key = table.add_column("Price (COP)", key="price")

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        if event.column_key == self._price_col_key:
            self._sort_reverse = not self._sort_reverse
            self.query_one("#catalog-table", DataTable).sort(
                self._price_col_key, reverse=self._sort_reverse
            )
```

### Pattern 6: History View with Rich Table in Static

**What:** `Static` widget holds a Rich `Table`; call `static_widget.update(rich_table)` to refresh.
**When to use:** D-08 — history view.

```python
# Source: https://textual.textualize.io/widgets/static (Static.update)
from rich.table import Table
from textual.widgets import Static

class HistoryScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("", id="product-title")
        yield Static("", id="history-table")

    def on_show(self) -> None:
        # Called when screen becomes visible — load data for selected product
        self.load_history()

    @work(thread=True, exclusive=True)
    def load_history(self) -> None:
        key = self.app.selected_product_key
        with get_session() as session:
            records = get_price_history(session, product_key=key)
        if not get_current_worker().is_cancelled:
            self.call_from_thread(self._render_history, records)

    def _render_history(self, records: list) -> None:
        table = Table(title="Price History", show_lines=True)
        table.add_column("Date", style="cyan")
        table.add_column("Price (COP)", justify="right", style="green")
        for r in records:
            table.add_row(r.crawled_at.strftime("%Y-%m-%d"), f"{r.price:,.0f}")
        self.query_one("#history-table", Static).update(table)
```

### Anti-Patterns to Avoid

- **Blocking DB calls in event handlers without a worker thread:** Calling `get_session()` directly inside `on_mount()` or `on_data_table_row_selected()` will freeze the TUI. Always use `@work(thread=True)`.
- **Calling `self.update()` or `table.add_row()` from a worker thread directly:** Textual widgets are not thread-safe. Use `self.call_from_thread()` to schedule UI mutations from a thread worker.
- **Using `push_screen()` for peer-screen toggling without `pop_screen()`:** Pushing catalog then pushing history again on every Tab press grows the stack unboundedly. Use `switch_screen()` for Tab-toggle, or push-once and pop to go back.
- **Hardcoding model names in the query layer:** The model filter values (e.g., "MacBook Air") must match what is stored in `Product.reference`. Confirm the exact string format output by the crawlers (Phase 2) before writing filter predicates.
- **Re-creating DataTable columns on every filter change:** Call `table.clear()` (clears rows only) not a full widget rebuild. Only add columns once in `on_mount()`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Full-screen terminal rendering | Custom curses/ANSI escape sequences | `textual.App` | Textual handles resize, mouse, color, focus, accessibility |
| Row-selection in a table | Custom highlight tracking | `DataTable` with `cursor_type="row"` | Built-in keyboard nav, RowSelected events, RowKey stable across sorts |
| Dropdown/select widget | Custom popup | `textual.widgets.Select` | Built-in, keyboard navigable, fires `Select.Changed` |
| Column sort logic | Custom comparator + re-render | `DataTable.sort(column_key, reverse=bool)` | Handles Rich.Text cells, stable sort, returns Self |
| Async safety for sync DB code | asyncio.to_thread wrapping | `@work(thread=True)` + `call_from_thread()` | Textual's worker system handles cancellation, error propagation, lifecycle |
| Rich table rendering | Custom string formatting | `rich.table.Table` | Unicode borders, column alignment, color, padding |

**Key insight:** Textual widgets handle all the hard terminal-UI problems (focus management, resize, keyboard routing, color). The only custom code needed is query logic (SQL) and data-wiring (populate table from rows).

---

## Common Pitfalls

### Pitfall 1: `Tab` Key Conflict with Widget Focus

**What goes wrong:** Textual uses Tab by default to cycle widget focus within a screen. Binding `("tab", "switch_screen(...)")` at the App level may conflict or be captured by a focused widget first.
**Why it happens:** Textual's focus-cycling consumes Tab before App-level bindings if a widget has focus.
**How to avoid:** Bind at the Screen level with `priority=True`, or use a different key (e.g., `"t"` or `ctrl+tab`). Alternatively, use `BINDINGS = [Binding("tab", "switch_screen('history')", priority=True)]`. Test in headless mode with `pilot.press("tab")`.
**Warning signs:** Tab press does nothing or just moves focus between Select widgets instead of switching screens.
[VERIFIED: Textual docs on bindings and priority — https://textual.textualize.io/guide/input]

### Pitfall 2: `get_session()` Returns a Non-Context-Manager Session

**What goes wrong:** The existing `get_session()` returns a plain `Session`, not a context manager. Using `with get_session() as session:` will raise `AttributeError`.
**Why it happens:** `SessionLocal()` returns a `Session` object; `with Session() as s:` is valid SQLAlchemy 2.0 syntax but requires the session itself to be used as a CM, not the factory.
**How to avoid:** Either use `session = get_session(); try: ... finally: session.close()` or update `session.py` to yield via `contextlib.contextmanager`. Verify against the actual `session.py` implementation before coding.
**Warning signs:** `AttributeError: __enter__` when running the thread worker.
[VERIFIED: src/apple_deals/db/session.py — get_session() returns SessionLocal() directly]

### Pitfall 3: `get_current_prices()` Query Does Not Exist Yet

**What goes wrong:** Phase 2's `crud.py` only implements `upsert_if_changed`, `get_last_price`, `insert_product`. There is no `get_current_prices()` (most recent per sku+source) or `get_price_history()` function.
**Why it happens:** Those query functions belong to the TUI's read path, not the crawler's write path.
**How to avoid:** Phase 4 must add these two functions to `db/crud.py`. They do NOT exist in the current codebase.
**Warning signs:** `ImportError: cannot import name 'get_current_prices'` at TUI startup.
[VERIFIED: grep across all planning docs and src/ — no get_current_prices or get_price_history defined]

### Pitfall 4: Reference/Model Name Mismatch for Filters

**What goes wrong:** The model filter uses values like "MacBook Air" but `Product.reference` stores titles like "MacBook Air 13 M4 8GB 256GB Plata" — the filter substring predicate must match the crawled format.
**Why it happens:** Crawlers (Phase 2) construct `reference` from parsed title components. The exact format depends on `parse_title()` output.
**How to avoid:** Use `ILIKE '%MacBook Air%'` (Postgres) or `LIKE '%MacBook Air%'` (SQLite) for the model filter predicate. Confirm against Phase 2's `parse_title()` output.
**Warning signs:** Model filter returns zero rows despite products existing in DB.
[ASSUMED] — exact reference format depends on Phase 2 crawler implementation

### Pitfall 5: DataTable `add_row` Key Must Be a String

**What goes wrong:** Passing `key=product.id` (an `int`) to `add_row()` raises a type error or produces unstable RowKey behavior.
**Why it happens:** `add_row(..., key=...)` expects a `str | None`.
**How to avoid:** Always convert: `key=str(product.id)`.
**Warning signs:** `TypeError` on `add_row`, or RowKey comparisons fail.
[VERIFIED: https://textual.textualize.io/widgets/data_table — add_row signature: key (str | None)]

### Pitfall 6: `test_tui_stub_exits_one` Will Break After D-10

**What goes wrong:** `tests/test_cli.py::test_tui_stub_exits_one` asserts `exit_code == 1` and "Command not yet implemented." — this test must be updated when the stub is replaced.
**Why it happens:** The test was written for the stub state (Phase 1).
**How to avoid:** Replace or delete `test_tui_stub_exits_one` in Wave 1. Either test that the tui command wiring works (import-level smoke test) or remove the assertion for stub message.
**Warning signs:** CI fails on the existing test after D-10 is implemented.
[VERIFIED: tests/test_cli.py lines 37-41]

---

## Code Examples

### get_current_prices() — Most Recent Record per (sku, source)

```python
# Pattern: subquery to find max crawled_at per (sku, source), then join
# Source: SQLAlchemy 2.0 ORM patterns [ASSUMED — exact syntax, verified against SQLAlchemy docs style]
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from apple_deals.db.models import Product

def get_current_prices(
    session: Session,
    model_filter: str | None = None,
    store_filter: str | None = None,
) -> list[Product]:
    # Subquery: max crawled_at per (sku, source)
    subq = (
        select(
            Product.sku,
            Product.source,
            func.max(Product.crawled_at).label("max_crawled_at"),
        )
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
    return list(session.scalars(stmt))
```

### get_price_history() — All Records for a Product

```python
# Source: SQLAlchemy 2.0 select() [ASSUMED — exact syntax]
from datetime import datetime, timedelta

def get_price_history(
    session: Session,
    sku: str,
    source: str,
    days: int = 90,
) -> list[Product]:
    cutoff = datetime.utcnow() - timedelta(days=days)
    stmt = (
        select(Product)
        .where(Product.sku == sku)
        .where(Product.source == source)
        .where(Product.crawled_at >= cutoff)
        .order_by(Product.crawled_at)
    )
    return list(session.scalars(stmt))
```

### Minimal Textual App Skeleton

```python
# Source: https://textual.textualize.io/tutorial (App boilerplate)
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer

class AppleDealsApp(App):
    TITLE = "Apple Deals"
    CSS = """
    Screen { layout: vertical; }
    .filters { height: 3; layout: horizontal; }
    DataTable { height: 1fr; }
    """
    BINDINGS = [("q", "quit", "Quit")]

    SCREENS = {
        "catalog": CatalogScreen,
        "history": HistoryScreen,
    }

    def on_mount(self) -> None:
        self.push_screen("catalog")

def run_tui() -> None:
    AppleDealsApp().run()
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `app.dark = True` | `app.theme = "textual-dark"` | Textual ~0.80+ | Property renamed; old attribute still works as alias in 8.x but theme system is preferred |
| Inline CSS in `CSS` class var | Separate `.tcss` file via `CSS_PATH` | Textual 0.x | Both still valid; inline CSS fine for simple apps, file preferred for large layouts |
| `self.log()` for debug output | `textual-dev` + devtools console | Textual 0.40+ | `textual run --dev app.py` opens devtools in browser; useful for layout debugging |

[ASSUMED] — theme property rename based on training knowledge; not confirmed in current 8.2.5 docs

**Deprecated/outdated:**
- `App.dark`: Replaced by `App.theme` in recent Textual versions. For this project, use `BINDINGS = [("d", "toggle_dark", "Toggle dark")]` via built-in `action_toggle_dark` or set `App.DEFAULT_CSS` with dark defaults.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `pytest-asyncio` required for Textual's `run_test()` async tests | Standard Stack | Tests may work with plain pytest if pytest-asyncio is not needed — low risk, easy to verify |
| A2 | `App.theme = "textual-dark"` is the current API; `app.dark` may be deprecated | State of the Art | Syntax error or no-op if wrong; verify against 8.2.5 release notes |
| A3 | `Product.reference` contains the model name as a substring (e.g., "MacBook Air") suitable for ILIKE filtering | Common Pitfalls (Pitfall 4), Code Examples | Model filter returns zero rows; must be confirmed from Phase 2 `parse_title()` output |
| A4 | `get_price_history()` should filter by `sku + source` to uniquely identify a product variant | Code Examples | History may show wrong product if sku alone is not unique across stores |
| A5 | SQLAlchemy 2.0 subquery join pattern for "latest per group" is the correct approach | Code Examples | Could use `DISTINCT ON` in Postgres or ROW_NUMBER window; the subquery works for both SQLite and Postgres |

---

## Open Questions

1. **Tab key vs widget focus conflict**
   - What we know: Textual uses Tab for focus cycling within a screen by default
   - What's unclear: Whether a high-priority App-level Tab binding fully overrides focus cycling
   - Recommendation: Test with Pilot in headless mode; if conflict, use `"t"` key or `ctrl+tab` for screen switch

2. **Product identity key for history navigation**
   - What we know: `Product` has `sku` + `source` to identify a variant; `Product.id` is a stable DB primary key
   - What's unclear: Whether to store `product_id` or `(sku, source)` in `app.selected_product_key`
   - Recommendation: Store `(sku, source)` tuple as app state — avoids tying navigation to a DB id that changes between DBs (dev vs prod)

3. **Screen re-entry and data refresh**
   - What we know: `on_show()` is called every time a screen becomes visible (push or switch)
   - What's unclear: Whether switching back from HistoryScreen to CatalogScreen via Tab should re-query DB or reuse cached rows
   - Recommendation: Keep filter/sort state in CatalogScreen reactive attributes; only re-query on filter change, not on every screen switch

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| textual | TUI rendering | Not installed (not in pyproject.toml yet) | — | None — must add to deps |
| rich | Rich Table in history view | In uv.lock as transitive dep | 15.0.0 | — |
| SQLite | DB backend (default) | Built into Python 3.13 | stdlib | — |
| uv | Package management | Available in project | — | pip |

**Missing dependencies with no fallback:**
- `textual` must be added to `pyproject.toml` dependencies before implementation: `uv add "textual>=0.89"`

**Missing dependencies with fallback:**
- None beyond textual.

[VERIFIED: pyproject.toml — textual not listed as dependency]
[VERIFIED: uv.lock — rich 15.0.0 present]

---

## Validation Architecture

> `workflow.nyquist_validation` is `false` in `.planning/config.json` — this section is SKIPPED.

---

## Security Domain

> This phase introduces no network I/O, authentication, user input stored to DB, or external services. The TUI is read-only. Security considerations are not applicable for this phase.

---

## Sources

### Primary (HIGH confidence)
- `https://textual.textualize.io/widgets/data_table` — DataTable API: add_column, add_row, sort, RowSelected, HeaderSelected, cursor_type, ColumnKey
- `https://textual.textualize.io/widgets/select` — Select widget API: Select.Changed, compose pattern
- `https://textual.textualize.io/api/app` — App API: push_screen, pop_screen, switch_screen, SCREENS, BINDINGS
- `https://github.com/textualize/textual/blob/main/docs/guide/screens.md` — Screen subclassing, SCREENS dict, push/pop/switch patterns
- `https://textual.textualize.io/guide/workers` — @work decorator, thread=True, call_from_thread
- `https://textual.textualize.io/widgets/static` — Static.update() with Rich renderables
- `https://textual.textualize.io/api/app` — run_test() async testing with Pilot
- PyPI `pip3 index versions textual` — verified latest version 8.2.5 (2026-05-08)
- `uv.lock` — rich 15.0.0 confirmed in project
- `pyproject.toml` — sqlalchemy >=2.0.49, textual absent (must add)
- `src/apple_deals/db/session.py` — get_session() returns Session (not context manager)
- `tests/test_cli.py` — test_tui_stub_exits_one confirmed, will break after D-10
- `src/apple_deals/tui/__init__.py` — tui package stub already exists

### Secondary (MEDIUM confidence)
- Context7 `/websites/textual_textualize_io` and `/textualize/textual` — code snippets for DataTable, Select, Screen, worker patterns cross-verified against official Textual docs

### Tertiary (LOW confidence)
- A2 (theme API rename), A3 (reference string format from crawlers) — training knowledge; not verified against Textual 8.x changelog or Phase 2 crawler output

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Textual 8.2.5 confirmed via PyPI; rich confirmed via uv.lock; sqlalchemy in pyproject.toml
- Architecture: HIGH — All widgets and screen patterns verified via Context7 against official Textual docs
- Pitfalls: HIGH — get_session() behavior verified by reading actual session.py; test_tui_stub verified by reading test_cli.py; DataTable key type from official API docs
- SQL queries: MEDIUM — subquery pattern for "latest per group" is standard SQLAlchemy 2.0 but specific syntax is ASSUMED

**Research date:** 2026-05-08
**Valid until:** 2026-06-08 (Textual releases frequently; re-verify if more than 30 days pass before implementation)
