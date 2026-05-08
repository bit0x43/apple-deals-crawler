# apple-deals-crawler — Project Instructions

## What this project is
A Python-based web crawler and CLI tool that tracks daily prices of Apple Mac products 
(MacBook Air, MacBook Pro, Mac Mini, Mac Studio) from Colombian retailers:
- https://co.tiendasishop.com/
- https://mac-center.com/

This is a developer tool, built by developers, for developers.
Licensed under MIT.

## Core capabilities
- Daily automated crawling via GitHub Actions (cron)
- JavaScript-rendered page support via Playwright
- Dual DB support: SQLite (default, local) and PostgreSQL (production/Docker)
- Beautiful interactive TUI using Textual + Rich
- Price drop alerts via Telegram
- Dockerized for deployment

## Product schema (minimum per record)
Each crawled record must store: reference, sku, memory, storage, color, price, url,
source (store), crawled_at (timestamp).

## Tech stack
- Python 3.13
- uv (package manager)
- Playwright (JS-rendered scraping)
- Textual + Rich (interactive TUI)
- Typer (CLI entrypoint)
- SQLite (default) / PostgreSQL (optional via env var)
- Docker + docker-compose
- GitHub Actions (daily schedule)

## Tone & conventions
- This is a dev tool: CLI output should be precise, readable, and opinionated
- Prefer explicit over implicit
- All user-facing text in English
- Keep it simple, composable, and well-documented