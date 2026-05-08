# apple-deals-crawler

## What This Is

A Python CLI + TUI developer tool that tracks daily prices of Apple Mac products
(MacBook Air, MacBook Pro, Mac Mini, Mac Studio) from two Colombian retailers
(tiendasishop.com, mac-center.com). It crawls JS-rendered pages daily via GitHub
Actions, stores a 90-day rolling price history, and alerts on threshold-based price
drops via Telegram. Built by developers, for developers.

## Core Value

Know the moment an Apple Mac drops in price in Colombia — without watching any
website manually.

## Requirements

### Validated

(None yet — ship to validate)

### Active

**Crawling**
- [ ] Crawl Apple Mac product prices from tiendasishop.com (Playwright)
- [ ] Crawl Apple Mac product prices from mac-center.com (Playwright)
- [ ] Store per-record schema: reference, sku, memory, storage, color, price, url, source, crawled_at
- [ ] Change-only storage: only write a new row when price actually changes (dedup)
- [ ] GitHub Actions daily cron trigger

**Database**
- [ ] SQLite as default (zero-config, rapid local dev)
- [ ] PostgreSQL support via DATABASE_URL env var (production target: Neon serverless)
- [ ] 90-day rolling window: auto-prune records older than 90 days (configurable)
- [ ] `db clean` CLI command with --dry-run preview
- [ ] `db stats` CLI command (row count, DB size, oldest/newest record, estimated growth)

**TUI**
- [ ] Catalog view: browse current prices, filter by model/store, sort by price
- [ ] History view: price trends per product over time (tab/toggle from catalog)
- [ ] Built with Textual + Rich

**Alerts**
- [ ] Telegram price drop alerts (single recipient)
- [ ] Threshold-based: alert only when price drops by configurable % or absolute amount

**CLI**
- [ ] Typer-based entrypoint
- [ ] Commands: crawl, tui, db clean, db stats

**Documentation**
- [ ] MkDocs + Material theme, deployed to GitHub Pages
- [ ] Covers: installation, CLI reference, configuration, self-hosting guide

**Dev practices**
- [ ] Pre-commit hooks: secret scanning (detect-secrets/gitleaks), ruff (lint+format), mypy, file hygiene
- [ ] Docker + docker-compose for local dev and optional self-hosted deployment
- [ ] npx autoskills installed after stack is finalized (improves GSD planning skills)

### Out of Scope

- Multiple Telegram recipients — v1 targets single-user; multi-user adds auth complexity
- Email alerts — Telegram covers the use case; email adds infra with no clear gain
- Web UI / hosted dashboard — this is a terminal tool, not a SaaS product
- Price scraping outside Colombia — scope is tiendasishop + mac-center only

## Context

- Target retailers use JavaScript rendering — Playwright required (no simple requests/BS4)
- Colombian retailers may change DOM structure; scrapers need to be resilient and easy to update
- Neon's auto-suspend makes it ideal for a daily cron workload (wakes on first connection, $0 idle cost)
- Rolling window + change-only storage keeps the DB well under Neon's 512MB free tier
- SQLite is the default for local/rapid dev; same ORM models target both backends
- GitHub Actions provides the scheduled cron and CI pipeline without needing a server
- Docker provides an optional self-hosted path for users who want always-on monitoring

## Constraints

- **Language**: Python 3.13 — existing decision, aligns with Playwright and Textual ecosystems
- **Package manager**: uv — faster than pip/poetry, lockfile-first
- **Scraping**: Playwright only — both target sites are JS-rendered
- **DB default**: SQLite — zero-config required for local dev and onboarding
- **Secrets**: Never committed to git — enforced by pre-commit secret scanning hooks
- **Free hosting**: Neon free tier (512MB) — rolling window + dedup must keep data well under limit
- **Documentation**: MkDocs Material — Python-native, deploys to GitHub Pages via Actions

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Change-only storage (dedup) | Keeps DB order-of-magnitude smaller; 20 products × 2 stores rarely change daily | — Pending |
| Neon as default Postgres host | Serverless auto-suspend = $0 idle cost; works perfectly with daily cron cold starts | — Pending |
| SQLite default, Postgres via env var | Lets developers start with zero config; same models target both via SQLAlchemy | — Pending |
| 90-day rolling window | Covers seasonal price patterns; keeps Neon free tier safe | — Pending |
| Threshold-based alerts (not any-drop) | Reduces noise; minor daily fluctuations shouldn't page the user | — Pending |
| MkDocs Material for docs | Python-native, excellent for CLI tools, trivial GitHub Pages deploy | — Pending |
| Pre-commit hooks from day 1 | Secret scanning + ruff + mypy enforced early prevents technical debt and credential leaks | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-08 after initialization*
