# Requirements: apple-deals-crawler

**Defined:** 2026-05-08
**Core Value:** Know the moment an Apple Mac drops in price in Colombia — without watching any website manually.

## v1 Requirements

### Crawling

- [ ] **CRAWL-01**: System crawls Apple Mac product prices from tiendasishop.com using Playwright
- [ ] **CRAWL-02**: System crawls Apple Mac product prices from mac-center.com using Playwright
- [ ] **CRAWL-03**: Each crawled record stores: reference, sku, memory, storage, color, price, url, source, crawled_at
- [ ] **CRAWL-04**: System skips writing a record when the price is unchanged from the previous crawl (change-only storage)
- [ ] **CRAWL-05**: GitHub Actions cron runs the crawler daily on a schedule

### Database

- [ ] **DB-01**: System uses SQLite as the default backend (zero-config, works out of the box)
- [ ] **DB-02**: System switches to PostgreSQL when DATABASE_URL env var is set (Neon serverless as primary free host)
- [ ] **DB-03**: System auto-prunes records older than configurable retention period (default: 90 days)
- [ ] **DB-04**: User can run `apple-deals db clean` to manually trigger pruning with optional --dry-run preview
- [ ] **DB-05**: User can run `apple-deals db stats` to view row count, DB size, oldest/newest record, and estimated growth rate

### TUI

- [ ] **TUI-01**: User can open an interactive TUI via `apple-deals tui`
- [ ] **TUI-02**: TUI catalog view shows current prices filterable by model and store, sortable by price
- [ ] **TUI-03**: TUI history view shows price trends per product over the rolling window
- [ ] **TUI-04**: User can toggle between catalog and history views (tab or keyboard shortcut)

### Alerts

- [ ] **ALRT-01**: System sends a Telegram message when a product's price drops below a configurable threshold (% or absolute amount)
- [ ] **ALRT-02**: Alert threshold and Telegram credentials are configurable via environment variables or config file

### CLI

- [ ] **CLI-01**: User can run `apple-deals crawl` to trigger a manual crawl
- [ ] **CLI-02**: User can run `apple-deals tui` to open the interactive terminal UI
- [ ] **CLI-03**: CLI provides --help for all commands with clear descriptions

### Documentation

- [ ] **DOCS-01**: Project has MkDocs + Material docs site deployable to GitHub Pages
- [ ] **DOCS-02**: Docs cover installation, CLI reference, configuration, and self-hosting guide
- [ ] **DOCS-03**: GitHub Actions workflow deploys docs to GitHub Pages on push to main

### Dev Practices

- [ ] **DEV-01**: Pre-commit hooks enforce secret scanning (detect-secrets or gitleaks)
- [ ] **DEV-02**: Pre-commit hooks enforce ruff for linting and formatting
- [ ] **DEV-03**: Pre-commit hooks enforce mypy for type checking
- [ ] **DEV-04**: Pre-commit hooks enforce trailing whitespace and file hygiene checks
- [ ] **DEV-05**: Docker + docker-compose setup for local dev and optional self-hosted deployment
- [ ] **DEV-06**: npx autoskills installed after stack is finalized to improve GSD planning skills

## v2 Requirements

### Alerts

- **ALRT-V2-01**: User can configure multiple Telegram recipients
- **ALRT-V2-02**: User can set per-product target price alerts

### Monitoring

- **MON-V2-01**: Crawl health dashboard in TUI (success/failure history per store)
- **MON-V2-02**: System sends Telegram alert when a crawl fails

### Data

- **DATA-V2-01**: Export price history to CSV
- **DATA-V2-02**: Weekly price summary report via Telegram

## Out of Scope

| Feature | Reason |
|---------|--------|
| Multiple Telegram recipients | v1 is single-user; multi-user adds config/auth complexity |
| Email alerts | Telegram covers the use case; email adds infrastructure with no clear gain |
| Web UI / hosted dashboard | This is a terminal tool, not a SaaS product |
| Price scraping beyond tiendasishop + mac-center | Scope is Colombia-specific; adding stores is a future concern |
| iPhone / iPad / other Apple products | Mac-only scope keeps the schema and scrapers focused |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CRAWL-01 | — | Pending |
| CRAWL-02 | — | Pending |
| CRAWL-03 | — | Pending |
| CRAWL-04 | — | Pending |
| CRAWL-05 | — | Pending |
| DB-01 | — | Pending |
| DB-02 | — | Pending |
| DB-03 | — | Pending |
| DB-04 | — | Pending |
| DB-05 | — | Pending |
| TUI-01 | — | Pending |
| TUI-02 | — | Pending |
| TUI-03 | — | Pending |
| TUI-04 | — | Pending |
| ALRT-01 | — | Pending |
| ALRT-02 | — | Pending |
| CLI-01 | — | Pending |
| CLI-02 | — | Pending |
| CLI-03 | — | Pending |
| DOCS-01 | — | Pending |
| DOCS-02 | — | Pending |
| DOCS-03 | — | Pending |
| DEV-01 | — | Pending |
| DEV-02 | — | Pending |
| DEV-03 | — | Pending |
| DEV-04 | — | Pending |
| DEV-05 | — | Pending |
| DEV-06 | — | Pending |

**Coverage:**
- v1 requirements: 28 total
- Mapped to phases: 0 (traceability updated during roadmap creation)
- Unmapped: 28 ⚠️

---
*Requirements defined: 2026-05-08*
*Last updated: 2026-05-08 after initial definition*
