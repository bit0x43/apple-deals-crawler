# Roadmap: apple-deals-crawler

**Milestone:** v1.0 — Core crawler, TUI, alerts, docs
**Structure:** Vertical MVP — each phase delivers a working slice
**Granularity:** Standard (5-8 phases)
**Requirements:** 28 v1 requirements | 7 phases | 100% coverage ✓

---

## Phases Overview

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 1 | ~~Project Foundation~~ ✅ | Repo + tooling + DB models + CLI skeleton | DEV-01..04, DB-01, CLI-03 | 6 | 4 |
| 2 | Crawling Core | Working crawlers with change-only storage | CRAWL-01..04, CLI-01 | 5 | 4 |
| 3 | Database & Maintenance | Postgres support + pruner + maintenance CLI | DB-02..05 | 4 | 4 |
| 4 | TUI | Interactive catalog + history views | TUI-01..04, CLI-02 | 5 | 5 |
| 5 | Telegram Alerts | Threshold-based price drop notifications | ALRT-01..02 | 2 | 3 |
| 6 | Automation & Deployment | GitHub Actions cron + Docker | CRAWL-05, DEV-05..06 | 3 | 4 |
| 7 | Documentation | MkDocs docs site on GitHub Pages | DOCS-01..03 | 3 | 3 |

---

### Phase 1: Project Foundation
**Goal:** Establish repo structure, dev tooling, DB models, and CLI entrypoint — everything subsequent phases build on.
**Mode:** mvp
**Plans:** 3 plans

**Requirements:**
- DEV-01: Pre-commit hooks — secret scanning
- DEV-02: Pre-commit hooks — ruff (lint + format)
- DEV-03: Pre-commit hooks — mypy
- DEV-04: Pre-commit hooks — file hygiene
- DB-01: SQLite default backend
- CLI-03: --help for all commands

**Plans:**
- [ ] 01-01-PLAN.md — Project scaffold: pyproject.toml, package tree, .python-version, .gitignore
- [ ] 01-02-PLAN.md — DB models + session + CLI entrypoint + tests (Walking Skeleton)
- [ ] 01-03-PLAN.md — Pre-commit hooks, secrets baseline, validate all hooks pass

**Success Criteria:**
1. `pre-commit run --all-files` passes on a clean checkout
2. `apple-deals --help` lists all commands
3. SQLite DB is created on first run with correct schema
4. `uv run apple-deals` works with no environment setup beyond `uv sync`

---

### Phase 2: Crawling Core
**Goal:** Both scrapers crawl live product pages, persist records with deduplication, and are invocable via CLI.
**Mode:** mvp
**Plans:** 3 plans

**Requirements:**
- CRAWL-01: Crawl tiendasishop.com (Playwright)
- CRAWL-02: Crawl mac-center.com (Playwright)
- CRAWL-03: Full product record schema stored per crawl
- CRAWL-04: Change-only storage (skip unchanged prices)
- CLI-01: `apple-deals crawl` command

**Plans:**
- [ ] 02-01-PLAN.md — ProductData TypedDict + BaseCrawler ABC + parse_title() + JSON fixtures + unit tests
- [ ] 02-02-PLAN.md — TiendasishopCrawler + MacCenterCrawler + db/crud.py + deduplication unit tests
- [ ] 02-03-PLAN.md — CLI crawl command wiring + playwright dependency + live crawl verification

**Success Criteria:**
1. `apple-deals crawl` fetches products from both stores and prints a summary
2. Running the same crawl twice produces no duplicate rows when prices haven't changed
3. Records contain all required fields: reference, sku, memory, storage, color, price, url, source, crawled_at
4. Crawl completes without Playwright errors on both target URLs

---

### Phase 3: Database & Maintenance
**Goal:** PostgreSQL backend support + rolling-window pruner + maintenance CLI commands.
**Mode:** mvp
**Plans:** 2 plans

**Requirements:**
- DB-02: PostgreSQL via DATABASE_URL env var (Neon)
- DB-03: 90-day rolling window auto-prune
- DB-04: `apple-deals db clean` with --dry-run
- DB-05: `apple-deals db stats`

**Plans:**
- [ ] 03-01-PLAN.md — psycopg2-binary optional dep + db/crud.py (prune_old_records, count_prunable, get_db_stats) + unit tests
- [ ] 03-02-PLAN.md — Implement db_clean (--days, --dry-run), db_stats (Rich table), _auto_prune hook in crawl()

**Success Criteria:**
1. Setting DATABASE_URL to a Neon connection string switches backend with no code changes
2. `apple-deals db clean --dry-run` reports rows to be pruned without deleting
3. `apple-deals db clean` deletes rows outside the retention window
4. `apple-deals db stats` prints row count, DB size, oldest/newest record, and growth estimate

---

### Phase 4: TUI
**Goal:** Interactive terminal UI with catalog browser and price history views.
**Mode:** mvp

**Requirements:**
- TUI-01: `apple-deals tui` opens interactive TUI
- TUI-02: Catalog view: filter by model/store, sort by price
- TUI-03: History view: price trends over rolling window
- TUI-04: Toggle between views (tab or keyboard shortcut)
- CLI-02: `apple-deals tui` command

**Success Criteria:**
1. `apple-deals tui` opens a full-screen Textual application
2. Catalog view shows all current prices, filterable by model and store
3. Pressing Tab (or equivalent) switches to history view showing trend per product
4. History view shows correct price changes over time for a product with known history
5. TUI exits cleanly on `q` or `Ctrl+C`

---

### Phase 5: Telegram Alerts
**Goal:** Threshold-based price drop detection and Telegram notification on each crawl.
**Mode:** mvp

**Plans:** 2 plans

**Requirements:**
- ALRT-01: Telegram message when price drops below threshold
- ALRT-02: Alert threshold + Telegram credentials configurable via env vars / config

**Plans:**
- [ ] 05-01-PLAN.md — Alert module core: telegram.py with threshold logic, message formatting, env var config, httpx send; unit tests
- [ ] 05-02-PLAN.md — Crawl pipeline integration: crud.py enriched return type, crawl() alert wiring, integration tests

**Wave structure:**
| Wave | Plans | Description |
|------|-------|-------------|
| 1 | 05-01 | Alert module core — standalone, unit-testable |
| 2 | 05-02 | Integration — depends on 05-01 for send_alert function |

**Success Criteria:**
1. Simulating a price drop below threshold sends a Telegram message to the configured chat
2. Price changes above threshold produce no alert
3. TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID missing → crawl runs normally with a logged warning (no crash)

---

### Phase 6: Automation & Deployment
**Goal:** Daily GitHub Actions cron, Docker setup, and npx autoskills installation.
**Mode:** mvp
**Plans:** 3 plans

**Requirements:**
- CRAWL-05: GitHub Actions daily cron
- DEV-05: Docker + docker-compose
- DEV-06: npx autoskills after stack finalized

**Plans:**
- [ ] 06-01-PLAN.md — GitHub Actions daily cron workflow (crawl.yml)
- [ ] 06-02-PLAN.md — Docker + docker-compose setup (Dockerfile, compose, .env.example)
- [ ] 06-03-PLAN.md — npx autoskills installation + README documentation

**Success Criteria:**
1. GitHub Actions workflow triggers daily and `apple-deals crawl` runs successfully in CI
2. `docker-compose up` starts a working environment with no manual steps beyond env vars
3. npx autoskills is installed and GSD planning skills reflect the final stack
4. Secrets are passed as GitHub Actions environment secrets (no credentials in repo)

**Wave structure:**
| Wave | Plans | Description |
|------|-------|-------------|
| 1 | 06-01, 06-02 | Infrastructure: CI workflow + Docker files (independent, parallel) |
| 2 | 06-03 | Finalization: npx install + README (after stack finalized) |

---

### Phase 7: Documentation
**Goal:** MkDocs + Material docs site with full user guide, deployed to GitHub Pages.
**Mode:** mvp
**Plans:** 1 plan

**Requirements:**
- DOCS-01: MkDocs + Material theme, deployable to GitHub Pages
- DOCS-02: Docs cover installation, CLI reference, configuration, self-hosting
- DOCS-03: GitHub Actions workflow auto-deploys docs on push to main

**Plans:**
- [ ] 07-01-PLAN.md — MkDocs setup, 5 doc pages, GitHub Actions deploy, build validation

**Success Criteria:**
1. `mkdocs serve` renders the docs site locally without errors
2. GitHub Actions deploys docs to GitHub Pages on every push to main
3. Docs include working installation instructions, full CLI reference, and self-hosting guide
4. No broken links in the deployed docs site (mkdocs strict mode or link checker)

---

## Requirement Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DEV-01 | Phase 1 | Pending |
| DEV-02 | Phase 1 | Pending |
| DEV-03 | Phase 1 | Pending |
| DEV-04 | Phase 1 | Pending |
| DB-01 | Phase 1 | Pending |
| CLI-03 | Phase 1 | Pending |
| CRAWL-01 | Phase 2 | Pending |
| CRAWL-02 | Phase 2 | Pending |
| CRAWL-03 | Phase 2 | Pending |
| CRAWL-04 | Phase 2 | Pending |
| CLI-01 | Phase 2 | Pending |
| DB-02 | Phase 3 | Pending |
| DB-03 | Phase 3 | Pending |
| DB-04 | Phase 3 | Pending |
| DB-05 | Phase 3 | Pending |
| TUI-01 | Phase 4 | Pending |
| TUI-02 | Phase 4 | Pending |
| TUI-03 | Phase 4 | Pending |
| TUI-04 | Phase 4 | Pending |
| CLI-02 | Phase 4 | Pending |
| ALRT-01 | Phase 5 | Pending |
| ALRT-02 | Phase 5 | Pending |
| CRAWL-05 | Phase 6 | Pending |
| DEV-05 | Phase 6 | Pending |
| DEV-06 | Phase 6 | Pending |
| DOCS-01 | Phase 7 | Pending |
| DOCS-02 | Phase 7 | Pending |
| DOCS-03 | Phase 7 | Pending |

**Coverage:** 28 / 28 ✓

---
*Roadmap created: 2026-05-08*
*Last updated: 2026-05-08 — Phase 6 plans created (3 plans, 2 waves)*
