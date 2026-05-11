# apple-deals-crawler

A Python CLI + TUI developer tool that tracks daily prices of Apple Mac products
(MacBook Air, MacBook Pro, Mac Mini, Mac Studio) from two Colombian retailers.

## Quick Start

```bash
# Install dependencies
uv sync

# Run a crawl
uv run apple-deals crawl

# View CLI help
uv run apple-deals --help
```

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (package manager)
- Playwright browsers (installed automatically: `uv run python -m playwright install chromium`)

## CLI Commands

| Command | Description |
|---------|-------------|
| `apple-deals crawl` | Crawl product prices from all configured stores |
| `apple-deals tui` | Open the interactive terminal UI |
| `apple-deals db clean` | Prune records outside the retention window |
| `apple-deals db stats` | Show database statistics |
| `apple-deals --help` | Show full command reference |

## Configuration

Copy `.env.example` to `.env` and fill in values.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | SQLite (local file) | PostgreSQL connection string (e.g., Neon) |
| `TELEGRAM_BOT_TOKEN` | No | — | Telegram bot token for price drop alerts |
| `TELEGRAM_CHAT_ID` | No | — | Telegram chat ID for alert recipient |

The crawler works with zero configuration — SQLite is used by default and alerts
are disabled when Telegram credentials are absent.

## Daily Automation (GitHub Actions)

The project includes a GitHub Actions workflow (`.github/workflows/crawl.yml`) that:

- Triggers daily at **8:00 AM UTC** on the `schedule` event
- Can also be triggered manually via `workflow_dispatch`
- Runs `apple-deals crawl` with Playwright Chromium in the CI environment

To enable, configure the following **repository secrets** in your GitHub repo:

| Secret | Description |
|--------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (Neon recommended) |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token (optional) |
| `TELEGRAM_CHAT_ID` | Telegram chat ID (optional) |

## Docker Deployment

### Build and Run

```bash
# Build the image
docker build -t apple-deals-crawler .

# Run a crawl
docker run --env-file .env apple-deals-crawler crawl
```

### docker-compose

```bash
# Start the crawler (reads .env file)
docker-compose up crawler

# Start local PostgreSQL for development
docker-compose --profile with-db up -d postgres
```

The Docker image uses `python:3.13-slim` with uv and Playwright Chromium installed.
Chromium runs with `--ipc=host` for shared memory compatibility.

## Database

- **Default:** SQLite (zero-config, file: `apple_deals.db`)
- **Production:** PostgreSQL via `DATABASE_URL` env var (recommended: [Neon](https://neon.tech) free tier)

Records older than 90 days are automatically pruned on each crawl.

## Development

```bash
# Install dev dependencies
uv sync --group dev

# Run tests
uv run pytest

# Lint and type-check
uv run ruff check .
uv run mypy src
```

## Tech Stack

- Python 3.13, uv
- Playwright (JS-rendered scraping)
- Textual + Rich (interactive TUI)
- Typer (CLI framework)
- SQLAlchemy (ORM, SQLite + PostgreSQL)
- Docker + docker-compose
- GitHub Actions (daily cron)

## License

MIT
