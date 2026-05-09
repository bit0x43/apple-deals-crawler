from typer.testing import CliRunner

from apple_deals.cli.main import app

runner = CliRunner()


def test_help_exits_zero() -> None:
    """apple-deals --help exits 0."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0


def test_help_lists_main_commands() -> None:
    """--help output lists crawl, tui, and db."""
    result = runner.invoke(app, ["--help"])
    assert "crawl" in result.output
    assert "tui" in result.output
    assert "db" in result.output


def test_db_help_lists_subcommands() -> None:
    """apple-deals db --help lists clean and stats."""
    result = runner.invoke(app, ["db", "--help"])
    assert result.exit_code == 0
    assert "clean" in result.output
    assert "stats" in result.output


def test_crawl_exits_zero() -> None:
    """apple-deals crawl exits 0 (crawl command implemented)."""
    result = runner.invoke(app, ["crawl"])
    assert result.exit_code == 0
    assert "tiendasishop" in result.output
    assert "mac-center" in result.output


def test_tui_stub_exits_one() -> None:
    """apple-deals tui exits 1 with stub message."""
    result = runner.invoke(app, ["tui"])
    assert result.exit_code == 1
    assert "Command not yet implemented." in result.output


def test_db_clean_dry_run_reports_without_deleting() -> None:
    """apple-deals db clean --dry-run reports count without deleting."""
    result = runner.invoke(app, ["db", "clean", "--dry-run"])
    assert result.exit_code == 0
    assert "Would delete" in result.output


def test_db_clean_default_days_90() -> None:
    """apple-deals db clean shows 90-day default in output."""
    result = runner.invoke(app, ["db", "clean"])
    assert result.exit_code == 0
    assert "90 days" in result.output


def test_db_clean_custom_days() -> None:
    """apple-deals db clean --days 30 shows custom retention."""
    result = runner.invoke(app, ["db", "clean", "--days", "30"])
    assert result.exit_code == 0
    assert "30 days" in result.output


def test_db_stats_prints_table() -> None:
    """apple-deals db stats prints statistics table."""
    result = runner.invoke(app, ["db", "stats"])
    assert result.exit_code == 0
    assert "Database Statistics" in result.output
    assert "Total rows" in result.output
    assert "DB size" in result.output


def test_auto_prune_helper_exists() -> None:
    """_auto_prune function exists and is importable from cli.main."""
    from apple_deals.cli.main import _auto_prune

    assert callable(_auto_prune)
