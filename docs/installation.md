# Installation

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager

## Step 1: Clone the Repository

```bash
git clone https://github.com/bit0x43/apple-deals-crawler.git
cd apple-deals-crawler
```

## Step 2: Install Dependencies

```bash
uv sync
```

## Step 3: Install Playwright Browser

The crawler uses Playwright for JavaScript-rendered pages.

```bash
playwright install chromium
```

## Step 4: Run a Crawl

```bash
uv run apple-deals crawl
```

## Step 5: Open the TUI

```bash
uv run apple-deals tui
```

## Docker Installation

```bash
docker-compose up
```

!!! note "Docker requires Docker Desktop or Docker Engine"
    The Docker setup includes Playwright and all system dependencies. No manual Playwright install needed.

!!! tip "SQLite is the default"
    No configuration needed. The app creates the database file on first run.

## Troubleshooting

- **Python version mismatch**: Ensure you have Python 3.13+ with `python3 --version`.
- **Playwright install failure**: Run `uv run python -m playwright install --with-deps chromium` to include system dependencies.
- **uv not found**: Install uv with `curl -LsSf https://astral.sh/uv/install.sh | sh`.
