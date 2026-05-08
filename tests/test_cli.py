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


def test_crawl_stub_exits_one() -> None:
    """apple-deals crawl exits 1 with stub message."""
    result = runner.invoke(app, ["crawl"])
    assert result.exit_code == 1
    assert "Command not yet implemented." in result.output


def test_tui_stub_exits_one() -> None:
    """apple-deals tui exits 1 with stub message."""
    result = runner.invoke(app, ["tui"])
    assert result.exit_code == 1
    assert "Command not yet implemented." in result.output
