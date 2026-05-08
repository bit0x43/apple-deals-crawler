# Walking Skeleton: apple-deals-crawler

**Phase:** 1 — Project Foundation
**Created:** 2026-05-08
**Status:** Defined (not yet built)

---

## What the Walking Skeleton Delivers

After Phase 1 completes, the thinnest possible end-to-end slice exists:

- `uv run apple-deals --help` lists all four commands (`crawl`, `tui`, `db clean`, `db stats`)
- `uv run apple-deals crawl` prints "Command not yet implemented." and exits with code 1
- Running any command creates `apple_deals.db` in the current directory with the `products` table
- `uv run pre-commit run --all-files` passes on a clean checkout

No scraping, no TUI rendering, no alerts — just the skeleton that all subsequent phases attach to.

---

## Architectural Decisions (Locked for v1)

### Runtime & Package Manager

| Decision | Value | Rationale |
|----------|-------|-----------|
| Language | Python 3.13 | Project constraint |
| Package manager | uv 0.9+ | Lockfile-first, fastest resolver |
| Build backend | hatchling 1.29+ | src-layout-aware by default |

### Project Layout

| Decision | Value | Rationale |
|----------|-------|-----------|
| Layout | `src/` layout | Prevents accidental shadowing of installed package |
| Package root | `src/apple_deals/` | D-01 |
| Internal structure | Feature-based submodules | D-02: `cli/`, `db/`, `crawlers/`, `tui/`, `alerts/` |
| Entry point | `apple-deals` CLI command | `pyproject.toml` `[project.scripts]` |
| Entry module | `apple_deals.cli.main:app` | Typer `app` object |

### Database

| Decision | Value | Rationale |
|----------|-------|-----------|
| Default backend | SQLite | Zero-config, works out of the box (DB-01) |
| ORM | SQLAlchemy 2.0 Declarative (`Mapped[]` style) | D-06 |
| Model | `Product` with 9 fields | D-07: reference, sku, memory, storage, color, price, url, source, crawled_at |
| DB file location | `apple_deals.db` in CWD | Simplest for Phase 1; configurable in Phase 3 |
| Schema creation | `init_db()` called in CLI callback | Automatic on first run |
| Migration tooling | None in Phase 1 | Phase 3 introduces Alembic if needed |

### CLI

| Decision | Value | Rationale |
|----------|-------|-----------|
| Framework | Typer 0.25+ | Type-hint-driven, built on Click |
| Commands | `crawl`, `tui`, `db clean`, `db stats` | D-08 |
| Stub behavior | `typer.echo("Command not yet implemented.") + raise typer.Exit(1)` | D-09 |
| Subcommand pattern | `app.add_typer(db_app, name="db")` | Typer add_typer pattern |

### Dev Tooling (Pre-commit)

| Decision | Value | Rationale |
|----------|-------|-----------|
| Secret scanning | `detect-secrets` v1.5.0 | D-03: Python-native, no binary deps |
| Lint + format | ruff v0.15.12 (hook IDs: `ruff-check`, `ruff-format`) | D-04 |
| Type checking | mypy v2.0.0 via `mirrors-mypy` (standard mode) | D-04 |
| File hygiene | `pre-commit-hooks` v6.0.0 | D-05: trailing-whitespace, end-of-file-fixer, check-added-large-files |
| Hook runner | pre-commit 4.6.0 | Installed as dev dep, run via `uv run pre-commit` |

### Directory Structure (Canonical)

```
apple-deals-crawler/
├── pyproject.toml           # uv project config; tool configs (ruff, mypy, pytest)
├── .pre-commit-config.yaml  # hook definitions
├── .secrets.baseline        # detect-secrets baseline (committed)
├── .python-version          # pins Python 3.13 for uv
├── .gitignore
├── README.md
├── src/
│   └── apple_deals/
│       ├── __init__.py
│       ├── cli/
│       │   ├── __init__.py
│       │   └── main.py      # Typer app + all stubs + init_db callback
│       ├── db/
│       │   ├── __init__.py
│       │   ├── models.py    # Product ORM model (DeclarativeBase)
│       │   └── session.py   # engine factory + init_db() + get_session()
│       ├── crawlers/
│       │   └── __init__.py
│       ├── tui/
│       │   └── __init__.py
│       └── alerts/
│           └── __init__.py
└── tests/
    ├── __init__.py
    ├── test_db.py           # DB-01: init_db() creates products table
    └── test_cli.py          # CLI-03: --help exits 0 + all commands listed
```

### What Subsequent Phases Build On

| Phase | Attaches To |
|-------|-------------|
| Phase 2 (Crawling) | `src/apple_deals/crawlers/` + replaces `crawl` stub + uses `db/session.py` |
| Phase 3 (DB Maintenance) | `db/session.py` (adds Postgres URL handling + Alembic) + replaces `db clean`/`db stats` stubs |
| Phase 4 (TUI) | `src/apple_deals/tui/` + replaces `tui` stub |
| Phase 5 (Alerts) | `src/apple_deals/alerts/` |
| Phase 6 (Automation) | `pyproject.toml` Docker + GitHub Actions config |
| Phase 7 (Docs) | `pyproject.toml` mkdocs dep + new `docs/` directory |

---

*Walking Skeleton locked at Phase 1 completion. Do not renegotiate these decisions in subsequent phases — extend, don't replace.*
