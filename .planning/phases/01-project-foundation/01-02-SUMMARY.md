---
phase: 01-project-foundation
plan: "02"
subsystem: db+cli
tags: [python, sqlalchemy, typer, sqlite, pytest, tdd]

# Dependency graph
requires:
  - 01-01 (pyproject.toml, package skeleton, uv sync)
provides:
  - src/apple_deals/db/models.py (Product ORM model with 10 columns)
  - src/apple_deals/db/session.py (engine factory, init_db, get_session)
  - src/apple_deals/cli/main.py (Typer app with all stubs + DB init callback)
  - tests/test_db.py (3 DB schema tests)
  - tests/test_cli.py (5 CLI behavior tests)
affects:
  - 01-03 (pre-commit hooks will run mypy/ruff against these files)
  - 02-xx (crawlers will call get_session() and insert Product records)
  - 04-xx (TUI will query via get_session())

# Tech tracking
tech-stack:
  added:
    - SQLAlchemy 2.0 DeclarativeBase + Mapped[] ORM style (first use in codebase)
    - Typer app.add_typer() subcommand pattern
    - typer.testing.CliRunner for in-process CLI testing
  patterns:
    - TDD RED/GREEN per task (tests written before implementation)
    - @app.callback() wires init_db() to every CLI invocation
    - models.py has zero side effects at import time (engine/session in session.py only)
    - In-memory SQLite (sqlite:///:memory:) for unit tests (no filesystem artifacts)

key-files:
  created:
    - src/apple_deals/db/__init__.py
    - src/apple_deals/db/models.py
    - src/apple_deals/db/session.py
    - src/apple_deals/cli/__init__.py
    - src/apple_deals/cli/main.py
    - tests/__init__.py
    - tests/test_db.py
    - tests/test_cli.py
  modified: []

key-decisions:
  - "init_db() wired via @app.callback() so DB is created on every CLI invocation including stubs (per Open Question Q2 recommendation in RESEARCH.md)"
  - "In-memory SQLite used in tests to avoid filesystem artifacts and test isolation"
  - "DeclarativeBase class style (not declarative_base() function) per SQLAlchemy 2.x idioms"

# Metrics
duration: 2min
completed: 2026-05-08
---

# Phase 1 Plan 02: Walking Skeleton Summary

**SQLAlchemy DeclarativeBase Product model + Typer CLI stubs wired to SQLite init via @app.callback(), 8 tests green**

## Performance

- **Duration:** 2 min
- **Started:** 2026-05-08T23:01:56Z
- **Completed:** 2026-05-08T23:03:42Z
- **Tasks:** 2
- **Files modified:** 8 created

## Accomplishments

- Product ORM model created with 10 columns (id + reference, sku, memory, storage, color, price, url, source, crawled_at) using SQLAlchemy 2.0 DeclarativeBase + Mapped[] style
- session.py with module-level engine, init_db() (create_all), and get_session() factory
- CLI entrypoint with Typer app registering db_app sub-app; all four commands stubbed (crawl, tui, db clean, db stats)
- @app.callback() wires init_db() to every CLI invocation — apple_deals.db created automatically on first run
- 8 tests passing: 3 DB schema tests + 5 CLI behavior tests
- Walking Skeleton complete: `uv run apple-deals --help` lists all commands, DB created on invocation

## Task Commits

1. **Task 1: Product ORM model and session factory** — `4c8c006` (feat)
2. **Task 2: CLI entrypoint with stubs and init_db callback** — `5a3f29a` (feat)

## Files Created

- `src/apple_deals/db/__init__.py` — package marker
- `src/apple_deals/db/models.py` — Product ORM model (10 columns, zero import side effects)
- `src/apple_deals/db/session.py` — engine factory, init_db(), get_session()
- `src/apple_deals/cli/__init__.py` — package marker
- `src/apple_deals/cli/main.py` — Typer app with db subapp, callback, and all stubs
- `tests/__init__.py` — package marker for pytest
- `tests/test_db.py` — 3 tests verifying products table schema and nullability
- `tests/test_cli.py` — 5 tests verifying help output and stub exit codes

## Test Output

```
============================= test session starts ==============================
platform darwin -- Python 3.13.13, pytest-9.0.3, pluggy-1.6.0
collected 8 items

tests/test_cli.py::test_help_exits_zero PASSED                           [ 12%]
tests/test_cli.py::test_help_lists_main_commands PASSED                  [ 25%]
tests/test_cli.py::test_db_help_lists_subcommands PASSED                 [ 37%]
tests/test_cli.py::test_crawl_stub_exits_one PASSED                      [ 50%]
tests/test_cli.py::test_tui_stub_exits_one PASSED                        [ 62%]
tests/test_db.py::test_init_db_creates_products_table PASSED             [ 75%]
tests/test_db.py::test_products_table_has_correct_columns PASSED         [ 87%]
tests/test_db.py::test_nullable_fields PASSED                            [100%]

============================== 8 passed in 0.34s ===============================
```

## CLI Help Output

```
 Usage: apple-deals [OPTIONS] COMMAND [ARGS]...

 Track Apple Mac prices from Colombian retailers.

╭─ Options ──────────────────────────────────────────────────────────╮
│ --install-completion   Install completion for the current shell.   │
│ --show-completion      Show completion for the current shell.      │
│ --help                 Show this message and exit.                 │
╰────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────╮
│ crawl  Crawl product prices from all configured stores.            │
│ tui    Open the interactive terminal UI.                           │
│ db     Database maintenance commands.                              │
╰────────────────────────────────────────────────────────────────────╯
```

## DB Creation Confirmed

`apple_deals.db` (8192 bytes) created in project root after first `uv run apple-deals crawl` invocation. Schema verified: 10 columns (id, reference, sku, memory, storage, color, price, url, source, crawled_at).

## Decisions Made

- **init_db() via @app.callback():** Wired init_db() to the app-level Typer callback so every CLI invocation (including stubs) triggers DB creation. This satisfies the "DB created on first run" success criterion without modifying each stub command.
- **In-memory SQLite for tests:** Tests use `sqlite:///:memory:` and create_all directly (not via init_db()) to avoid filesystem artifacts and ensure test isolation.
- **DeclarativeBase class inheritance:** Used `class Base(DeclarativeBase): pass` (SQLAlchemy 2.x idiomatic) not the deprecated `declarative_base()` function.

## Deviations from Plan

None — plan executed exactly as written. Both tasks followed the TDD RED/GREEN cycle as specified. All implementation matches the exact code patterns in RESEARCH.md.

## Known Stubs

The following commands are intentional stubs — they exit 1 with "Command not yet implemented." and will be implemented in later phases:

- `apple-deals crawl` — Phase 2 (Crawling Core)
- `apple-deals tui` — Phase 4 (TUI)
- `apple-deals db clean` — Phase 3 (Database & Maintenance)
- `apple-deals db stats` — Phase 3 (Database & Maintenance)

These stubs are intentional and correct for this plan's scope.

## Threat Flags

No new threat surface introduced beyond what was declared in the plan's threat model:
- T-01-03: apple_deals.db already covered by .gitignore (from Plan 01)
- T-01-04: DATABASE_URL env var accepted by design for Phase 3 Postgres migration
- T-01-05: init_db() / create_all is idempotent — no elevation risk

## Self-Check

- [x] src/apple_deals/db/models.py exists with `class Product(Base)`
- [x] src/apple_deals/db/session.py exists with `def init_db` and `def get_session`
- [x] src/apple_deals/cli/main.py exists with `@app.callback()` and all stubs
- [x] tests/test_db.py exists (3 tests)
- [x] tests/test_cli.py exists (5 tests)
- [x] `uv run pytest tests/ -x -q` exits 0 (8 tests)
- [x] `uv run apple-deals --help` exits 0 with crawl, tui, db listed
- [x] `uv run apple-deals db --help` exits 0 with clean, stats listed
- [x] apple_deals.db created in project root after CLI invocation
- [x] models.py has zero side effects (no create_all or init_db calls)
- [x] commit 4c8c006 exists (Task 1)
- [x] commit 5a3f29a exists (Task 2)

## Self-Check: PASSED

---
*Phase: 01-project-foundation*
*Completed: 2026-05-08*
