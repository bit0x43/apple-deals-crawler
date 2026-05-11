# apple-deals-crawler

Track daily Apple Mac prices from Colombian retailers -- from your terminal.

## Features

- **Automated crawling** -- Daily price collection via GitHub Actions cron
- **Dual database** -- SQLite for local development, PostgreSQL for production
- **Interactive TUI** -- Browse catalog and price history with Textual
- **Telegram alerts** -- Get notified when prices drop below your thresholds
- **Docker support** -- Deploy with docker-compose for always-on monitoring

## Quick Start

```bash
uv sync
playwright install chromium
uv run apple-deals crawl
uv run apple-deals tui
```

## Supported Stores

| Store | URL |
|-------|-----|
| Tiendas iShop | co.tiendasishop.com |
| Mac Center | mac-center.com |

## Next Steps

- [Installation](installation.md) -- Full setup guide
- [CLI Reference](cli-reference.md) -- Command documentation
- [Configuration](configuration.md) -- Environment variables reference
- [Self-Hosting](self-hosting.md) -- Docker and GitHub Actions setup
