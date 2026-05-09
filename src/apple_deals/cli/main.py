import typer

from apple_deals.crawlers.base import BaseCrawler
from apple_deals.db.session import get_session, init_db

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
    from apple_deals.crawlers.mac_center import MacCenterCrawler
    from apple_deals.crawlers.tiendasishop import TiendasishopCrawler
    from apple_deals.db.crud import upsert_if_changed

    crawlers: list[tuple[str, BaseCrawler]] = [
        ("tiendasishop", TiendasishopCrawler()),
        ("mac-center", MacCenterCrawler()),
    ]

    session = get_session()
    try:
        for store_name, crawler in crawlers:
            products = crawler.crawl()
            inserted = sum(1 for p in products if upsert_if_changed(session, p))
            typer.echo(f"{store_name}: {len(products)} products found, {inserted} inserted")
    finally:
        session.close()


@app.command()
def tui() -> None:
    """Open the interactive terminal UI."""
    typer.echo("Command not yet implemented.")
    raise typer.Exit(1)


@db_app.command("clean")
def db_clean(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview rows to delete without deleting."
    ),
) -> None:
    """Prune records outside the retention window."""
    typer.echo("Command not yet implemented.")
    raise typer.Exit(1)


@db_app.command("stats")
def db_stats() -> None:
    """Show database statistics: row count, size, oldest/newest record."""
    typer.echo("Command not yet implemented.")
    raise typer.Exit(1)


if __name__ == "__main__":
    app()
