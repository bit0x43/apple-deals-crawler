import logging

import typer
from rich.console import Console
from rich.table import Table

from apple_deals.crawlers.base import BaseCrawler
from apple_deals.db.crud import count_prunable, get_db_stats, prune_old_records
from apple_deals.db.session import engine, get_session, init_db
from apple_deals.tui.app import run_tui

logger = logging.getLogger(__name__)

app = typer.Typer(help="Track Apple Mac prices from Colombian retailers.")
db_app = typer.Typer(help="Database maintenance commands.")
app.add_typer(db_app, name="db")


@app.callback()
def main() -> None:
    """Initialize the database on every invocation."""
    init_db()


@app.command()
def crawl() -> None:
    """Crawl product prices from all configured stores."""
    from apple_deals.alerts.telegram import send_alert
    from apple_deals.crawlers.mac_center import MacCenterCrawler
    from apple_deals.crawlers.tiendasishop import TiendasishopCrawler
    from apple_deals.db.crud import upsert_if_changed

    crawlers: list[tuple[str, BaseCrawler]] = [
        ("tiendasishop", TiendasishopCrawler()),
        ("mac-center", MacCenterCrawler()),
    ]

    session = get_session()
    total_alerts = 0
    try:
        for store_name, crawler in crawlers:
            products = crawler.crawl()
            store_inserted = 0
            store_alerts = 0
            for p in products:
                inserted, old_price = upsert_if_changed(session, p)
                if inserted:
                    store_inserted += 1
                    if old_price is not None and old_price != p["price"]:
                        if send_alert(p, old_price, p["price"]):
                            store_alerts += 1
            total_alerts += store_alerts
            typer.echo(
                f"{store_name}: {len(products)} products found, "
                f"{store_inserted} inserted, {store_alerts} alerts fired"
            )
    finally:
        session.close()

    if total_alerts == 0:
        logger.info("No price drops detected this crawl.")
    _auto_prune()


def _auto_prune() -> None:
    """Run automatic 90-day retention prune. Called at end of each successful crawl."""
    session = get_session()
    try:
        pruned = prune_old_records(session, retention_days=90)
        if pruned:
            typer.echo(f"Auto-pruned {pruned} records outside the 90-day retention window.")
    finally:
        session.close()


@app.command()
def tui() -> None:
    """Open the interactive terminal UI."""
    run_tui()


@db_app.command("clean")
def db_clean(
    days: int = typer.Option(90, "--days", help="Retention window in days (default: 90).", min=1),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview rows to delete without deleting."
    ),
) -> None:
    """Prune records outside the retention window."""
    session = get_session()
    try:
        if dry_run:
            count = count_prunable(session, retention_days=days)
            typer.echo(f"Would delete {count} rows older than {days} days.")
        else:
            deleted = prune_old_records(session, retention_days=days)
            typer.echo(f"Deleted {deleted} rows older than {days} days.")
    finally:
        session.close()


@db_app.command("stats")
def db_stats() -> None:
    """Show database statistics: row count, size, oldest/newest record."""
    session = get_session()
    try:
        stats = get_db_stats(session, engine)
    finally:
        session.close()

    table = Table(title="Database Statistics", show_header=True)
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    table.add_row("Total rows", str(stats["total_rows"]))
    table.add_row("DB size", stats["db_size"])
    table.add_row("Oldest record", str(stats["oldest"]) if stats["oldest"] else "\u2014")
    table.add_row("Newest record", str(stats["newest"]) if stats["newest"] else "\u2014")
    table.add_row("Est. daily growth", f"{stats['daily_growth']} rows/day")

    Console().print(table)


if __name__ == "__main__":
    app()
