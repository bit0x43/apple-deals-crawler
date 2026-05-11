from __future__ import annotations

from rich.table import Table
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
    ("Tiendasishop", "tiendasishop"),
    ("Mac Center", "mac-center"),
]


class CatalogScreen(Screen):
    """Browse current prices with filterable DataTable and sort-by-price."""

    _sort_reverse: bool = False
    _price_column_key: str = "Price (COP)"
    _current_rows: list[Product] = []

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
        yield DataTable(id="catalog-table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#catalog-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_columns("Model", "Store", "Price (COP)", "Memory", "Storage", "Color")
        self.load_data()

    @work(thread=True, exclusive=True)
    async def load_data(self) -> None:
        """Fetch current prices in a thread worker to avoid blocking the UI."""
        worker = get_current_worker()
        model_val = self.query_one("#model-filter", Select).value
        store_val = self.query_one("#store-filter", Select).value
        model_filter = None if model_val == "all" else str(model_val)
        store_filter = None if store_val == "all" else str(store_val)

        session = get_session()
        try:
            rows = get_current_prices(session, model_filter=model_filter, store_filter=store_filter)
        finally:
            session.close()

        if not worker.is_cancelled:
            self.app.call_from_thread(self._populate_table, rows)

    def _populate_table(self, rows: list[Product]) -> None:
        """Populate the DataTable with price rows, then sort default by price ASC."""
        self._current_rows = rows
        table = self.query_one("#catalog-table", DataTable)
        table.clear()
        for p in rows:
            table.add_row(
                p.reference,
                p.source,
                f"{p.price:,.0f}",
                p.memory or "\u2014",
                p.storage or "\u2014",
                p.color or "\u2014",
                key=str(p.id),
            )
        table.sort(self._price_column_key)

    def on_select_changed(self, event: Select.Changed) -> None:
        """Re-query data when either filter changes."""
        if event.select.id in ("model-filter", "store-filter"):
            self.load_data()

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        """Toggle sort on Price column header click."""
        if str(event.column_key.value) == self._price_column_key:
            self._sort_reverse = not self._sort_reverse
            self.query_one("#catalog-table", DataTable).sort(
                event.column_key, reverse=self._sort_reverse
            )

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
            app = self.app
            app.selected_product = (product.sku, product.source, product.reference)
            app.switch_screen("history")


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
        current = self.current_screen
        if isinstance(current, CatalogScreen):
            self.switch_screen("history")
        elif isinstance(current, HistoryScreen):
            self.switch_screen("catalog")


def run_tui() -> None:
    """Launch the interactive TUI. Blocks until the user quits."""
    app = AppleDealsApp()
    app.run()
