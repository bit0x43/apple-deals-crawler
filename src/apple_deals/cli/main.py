import typer

from apple_deals.db.session import init_db

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
    typer.echo("Command not yet implemented.")
    raise typer.Exit(1)


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
