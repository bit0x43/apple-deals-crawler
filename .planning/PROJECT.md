# apple-deals-crawler

## What This Is

A Python CLI + TUI developer tool that tracks daily prices of Apple Mac products
(MacBook Air, MacBook Pro, Mac Mini, Mac Studio) from two Colombian retailers
(tiendasishop.com, mac-center.com). It crawls JS-rendered pages daily via GitHub
Actions, stores a 90-day rolling price history, and alerts on threshold-based price
drops and high-memory products via Telegram. Built by developers, for developers.

## Core Value

Know the moment an Apple Mac drops in price in Colombia — without watching any
website manually.

## Requirements

### Validated (v1.0)

- ✓ Crawl Apple Mac product prices from tiendasishop.com via Playwright
- ✓ Crawl Apple Mac product prices from mac-center.com via Playwright
- ✓ Full product record schema: reference, sku, memory, storage, color, price, url, source, crawled_at, in_stock
- ✓ Change-only storage (skip when price + stock unchanged)
- ✓ Daily GitHub Actions cron
- ✓ SQLite default + PostgreSQL via DATABASE_URL
- ✓ 90-day rolling auto-prune + `db clean` / `db stats` CLI
- ✓ Interactive TUI: catalog (filterable, sortable) + history views
- ✓ Telegram price drop alerts (configurable % or absolute threshold)
- ✓ Telegram high-memory alerts (>= 24GB configurable)
- ✓ Stock tracking (in_stock column, Shopify variants[0].available)
- ✓ RAM enrichment from product pages via Playwright browser
- ✓ Low-memory product filtering (< 16GB excluded)
- ✓ Docs: MkDocs + Material, GitHub Pages deploy, CI auto-deploy
- ✓ Pre-commit: detect-secrets, ruff, mypy, file hygiene
- ✓ Docker + docker-compose

### Active

- [ ] Multiple Telegram recipients (v2)
- [ ] Per-product target price alerts (v2)
- [ ] Crawl health dashboard in TUI (v2)
- [ ] Crawl failure Telegram alert (v2)
- [ ] Export price history to CSV (v2)
- [ ] Weekly price summary via Telegram (v2)

### Out of Scope

- Multiple Telegram recipients — v1 is single-user; multi-user adds config/auth complexity
- Email alerts — Telegram covers the use case; email adds infra with no clear gain
- Web UI / hosted dashboard — this is a terminal tool, not a SaaS product
- Price scraping outside Colombia — scope is tiendasishop + mac-center only

## Current State

Shipped v1.0 with 1,823 LOC Python across 14 source modules.
Tech stack: Python 3.13, Playwright, Textual + Rich, SQLAlchemy, Typer, httpx, MkDocs Material.
71 tests pass, ruff/mypy clean (2 benign TUI mypy errors).
PostgreSQL (Neon) connected and tested. GitHub Actions daily crawl active.

## Next Milestone Goals

- v1.1: Multi-recipient alerts, per-product target prices, crawl health monitoring
- v1.2: CSV export, weekly summaries, polish and hardening

## Context

- Target retailers use JavaScript rendering — Playwright required
- Neon's auto-suspend makes it ideal for daily cron ($0 idle cost, wakes on connection)
- 90-day rolling window + change-only storage keeps DB well under Neon's 512MB free tier
- SQLite default for local dev; same ORM models target both backends
- RAM enrichment opens browser per product page — acceptable for daily cron cadence

## Constraints

- **Language**: Python 3.13 — aligns with Playwright and Textual ecosystems
- **Package manager**: uv — faster than pip/poetry, lockfile-first
- **Scraping**: Playwright only — both sites are JS-rendered
- **DB default**: SQLite — zero-config for local dev
- **Secrets**: Never committed to git — enforced by pre-commit secret scanning
- **Free hosting**: Neon free tier (512MB) — rolling window + dedup keeps data under limit
- **Docs**: MkDocs Material — Python-native, deploys to GitHub Pages via Actions

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Change-only storage (dedup) | Keeps DB order-of-magnitude smaller | ✓ Good |
| Neon as default Postgres host | Serverless auto-suspend = $0 idle cost | ✓ Good |
| SQLite default, Postgres via env var | Zero-config local dev; same models via SQLAlchemy | ✓ Good |
| 90-day rolling window | Covers seasonal patterns; keeps Neon safe | ✓ Good |
| Threshold-based alerts (not any-drop) | Reduces noise; minor fluctuations shouldn't page | ✓ Good |
| MkDocs Material for docs | Python-native, excellent for CLI tools | ✓ Good |
| Pre-commit hooks from day 1 | Secret scanning + ruff + mypy enforced early | ✓ Good |
| RAM enrichment via Playwright browser | data-title attrs, swatch labels, embedded JSON | ✓ Good |
| Stock via Shopify variants[0].available | No extra HTTP calls needed | ✓ Good |
| < 16GB RAM filtered out | Focus on meaningful products | ✓ Good |

---

*Last updated: 2026-05-11 after v1.0 milestone*
