from __future__ import annotations

from typing import cast

from rich.table import Table
from sqlalchemy import select
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Label, Select, Static
from textual.worker import get_current_worker

from apple_deals.db.crud import get_current_prices, get_price_history
from apple_deals.db.models import Product
from apple_deals.db.session import get_session

MODEL_CHOICES = [
    ("All", "all"),
    ("MacBook Air", "MacBook Air"),
    ("MacBook Pro", "MacBook Pro"),
    ("Mac Mini", "Mac Mini"),
    ("Mac Studio", "Mac Studio"),
]

STORE_CHOICES = [
    ("All", "all"),
    ("Tiendas iShop", "tiendas ishop"),
    ("Mac Center", "mac-center"),
]


def _storage_bytes(val: str | None) -> int:
    """Convert storage string like '512 GB' or '1 TB' to byte count for sorting."""
    if not val:
        return 0
    parts = val.split()
    if len(parts) != 2:
        return 0
    try:
        num = int(parts[0])
    except ValueError:
        return 0
    return num * 1024 if parts[1].upper() == "TB" else num


def _memory_gb(val: str | None) -> int:
    """Extract max GB from memory string like '16GB' or '16GB, 24GB'."""
    if not val:
        return 0
    import re

    nums = re.findall(r"(\d+)", val)
    return max(int(n) for n in nums) if nums else 0


class CatalogScreen(Screen):
    """Browse current prices with filterable DataTable and sort-by-price."""

    _sort_column: str | None = None
    _sort_reverse: bool = False
    _price_column_key: str = "price"
    _current_rows: list[Product] = []

    DEFAULT_CSS = """
.filters { height: auto; layout: horizontal; }
.filters Select { width: 1fr; }
"""

    def compose(self) -> ComposeResult:
        yield Header(id="catalog-header")
        with Horizontal(classes="filters"):
            yield Select(
                MODEL_CHOICES,
                prompt="Model",
                id="model-filter",
                value="all",
            )
            yield Select(
                STORE_CHOICES,
                prompt="Store",
                id="store-filter",
                value="all",
            )
            yield Select(
                [("All", "all"), ("In Stock", "in_stock"), ("Out of Stock", "out_of_stock")],
                prompt="Stock",
                id="stock-filter",
                value="all",
            )
            yield Select(
                [],
                prompt="Memory",
                id="memory-filter",
                value="all",
            )
            yield Select(
                [],
                prompt="Storage",
                id="storage-filter",
                value="all",
            )
        yield DataTable(id="catalog-table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#catalog-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_columns(
            ("Model", "model"),
            ("Store", "store"),
            ("Price (COP)", self._price_column_key),
            ("Stock", "stock"),
            ("Memory", "memory"),
            ("Storage", "storage"),
            ("Color", "color"),
        )
        self.load_data()
        self.load_filter_options()

    @work(thread=True, exclusive=True)
    async def load_data(self) -> None:
        """Fetch current prices in a thread worker to avoid blocking the UI."""
        worker = get_current_worker()
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
            self.app.call_from_thread(self._populate_table, rows)

    def _populate_table(self, rows: list[Product]) -> None:
        """Populate the DataTable with current sort preserving existing sort state."""
        self._current_rows = rows
        if self._sort_column:
            key_fn = {
                "price": lambda p: p.price,
                "memory": lambda p: _memory_gb(p.memory),
                "storage": lambda p: _storage_bytes(p.storage),
            }.get(self._sort_column)
            if key_fn:
                rows = sorted(rows, key=key_fn, reverse=self._sort_reverse)
        else:
            rows = sorted(
                rows,
                key=lambda p: (_storage_bytes(p.storage), _memory_gb(p.memory), p.price),
            )

        table = self.query_one("#catalog-table", DataTable)
        table.clear()
        for p in rows:
            stock = "\u2705 In Stock" if p.in_stock else "\u274c Out of Stock"
            table.add_row(
                p.reference,
                p.source,
                f"{p.price:,.0f}",
                stock,
                p.memory or "\u2014",
                p.storage or "\u2014",
                p.color or "\u2014",
                key=str(p.id),
            )

        if self._sort_column:
            self._apply_sort_to_table()

    @work(thread=True, exclusive=True)
    async def load_filter_options(self) -> None:
        """Fetch distinct memory and storage values from DB for filter options."""
        worker = get_current_worker()
        session = get_session()
        try:
            memories = session.scalars(
                select(Product.memory).distinct().where(Product.memory.isnot(None))
            ).all()
            storages = session.scalars(
                select(Product.storage).distinct().where(Product.storage.isnot(None))
            ).all()
        finally:
            session.close()

        if not worker.is_cancelled:
            self.app.call_from_thread(self._set_filter_options, memories, storages)

    def _set_filter_options(self, memories: list[str], storages: list[str]) -> None:
        """Populate memory and storage Select widgets from queried values."""
        memory_opts = [("All", "all")] + [(m, m) for m in sorted(set(memories))]
        storage_opts = [("All", "all")] + [(s, s) for s in sorted(set(storages))]

        self.query_one("#memory-filter", Select).set_options(memory_opts)
        self.query_one("#storage-filter", Select).set_options(storage_opts)
        self.query_one("#memory-filter", Select).value = "all"
        self.query_one("#storage-filter", Select).value = "all"

    def on_select_changed(self, event: Select.Changed) -> None:
        """Re-query data when any filter changes."""
        if event.select.id in (
            "model-filter",
            "store-filter",
            "stock-filter",
            "memory-filter",
            "storage-filter",
        ):
            self.load_data()

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        """Toggle sort on Price, Memory, or Storage column header click."""
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

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Navigate to history view for the selected product."""
        if not event.row_key.value:
            return
        try:
            product_id = int(event.row_key.value)
        except (ValueError, TypeError):
            return
        product = next((p for p in self._current_rows if p.id == product_id), None)
        if product is not None:
            api = cast(AppleDealsApp, self.app)
            api.selected_product = (product.sku, product.source, product.reference)
            api.switch_screen("history")


class HistoryScreen(Screen):
    """Show price history for a selected product."""

    def compose(self) -> ComposeResult:
        yield Header(id="history-header")
        yield Label("", id="product-title")
        yield Static("", id="history-table")
        yield Footer()

    def on_show(self) -> None:
        """Load history data every time this screen becomes visible."""
        self.load_history()

    @work(thread=True, exclusive=True)
    async def load_history(self) -> None:
        """Fetch price history in a thread worker."""
        worker = get_current_worker()

        selected: tuple[str, str, str] | None = getattr(self.app, "selected_product", None)

        if selected is None:
            self.app.call_from_thread(self._show_no_selection)
            return

        sku, source, reference = selected

        session = get_session()
        try:
            records = get_price_history(session, sku=sku, source=source, days=90)
        except Exception:
            records = []
        finally:
            session.close()

        if not worker.is_cancelled:
            self.app.call_from_thread(self._render_history, records, reference)

    def _show_no_selection(self) -> None:
        """Display placeholder when no product is selected."""
        self.query_one("#product-title", Label).update("")
        self.query_one("#history-table", Static).update(
            "No product selected. Press Tab to go back to catalog."
        )

    def _render_history(self, records: list[Product], reference: str) -> None:
        """Render price history as a Rich Table inside the Static widget."""
        self.query_one("#product-title", Label).update(reference)

        if not records:
            self.query_one("#history-table", Static).update(
                "No price history found for this product."
            )
            return

        table = Table(show_lines=True)
        table.add_column("Date", style="cyan")
        table.add_column("Price (COP)", justify="right", style="green")

        for r in records:
            date_str = r.crawled_at.strftime("%Y-%m-%d")
            price_str = f"{r.price:,.0f}"
            table.add_row(date_str, price_str)

        self.query_one("#history-table", Static).update(table)


class AppleDealsApp(App):
    """Interactive TUI for browsing Apple Mac prices."""

    TITLE = "Apple Deals"

    selected_product: tuple[str, str, str] | None = None
    """(sku, source, reference) of the product selected in catalog for history view."""

    SCREENS = {
        "catalog": CatalogScreen,
        "history": HistoryScreen,
    }

    BINDINGS = [
        Binding("tab", "switch_focus", "Toggle View", priority=True),
        ("q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        self.push_screen("catalog")

    def action_switch_focus(self) -> None:
        """Toggle between catalog and history screens."""
        current = self.screen
        if isinstance(current, CatalogScreen):
            self.switch_screen("history")
        elif isinstance(current, HistoryScreen):
            self.switch_screen("catalog")


def run_tui() -> None:
    """Launch the interactive TUI. Blocks until the user quits."""
    app = AppleDealsApp()
    app.run()
