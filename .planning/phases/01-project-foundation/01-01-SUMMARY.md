---
phase: 01-project-foundation
plan: "01"
subsystem: infra
tags: [python, uv, hatchling, sqlalchemy, typer, ruff, mypy, pytest, pre-commit]

# Dependency graph
requires: []
provides:
  - pyproject.toml with full tool configuration (ruff, mypy, pytest, hatchling)
  - src/apple_deals package skeleton with stub submodules (crawlers, tui, alerts)
  - .python-version pinning Python 3.13
  - .gitignore with SQLite DB and .env exclusions
  - uv sync succeeds and package is importable
affects:
  - 01-02
  - 01-03
  - 01-04
  - all subsequent phases that build on this package structure

# Tech tracking
tech-stack:
  added:
    - uv (package manager, lockfile-first)
    - hatchling (build backend, src-layout-aware)
    - SQLAlchemy 2.0.49 (ORM)
    - Typer 0.25.1 (CLI framework)
    - ruff 0.15.12 (lint + format)
    - mypy 2.0.0 (type checking)
    - pytest 9.0.3 (test runner)
    - pre-commit 4.6.0 (hook runner)
    - detect-secrets 1.5.0 (secret scanning)
  patterns:
    - src/ layout with package at src/apple_deals/
    - Feature-based internal submodule structure (crawlers/, tui/, alerts/, cli/, db/)
    - pyproject.toml as single config file for all tools (ruff, mypy, pytest)
    - hatchling wheel packages = ["src/apple_deals"] for correct editable install

key-files:
  created:
    - pyproject.toml
    - .python-version
    - src/apple_deals/__init__.py
    - src/apple_deals/crawlers/__init__.py
    - src/apple_deals/tui/__init__.py
    - src/apple_deals/alerts/__init__.py
  modified:
    - .gitignore (added apple_deals.db and *.sqlite3 entries)

key-decisions:
  - "src/ layout chosen to prevent accidental shadowing of installed package during dev (D-01)"
  - "Feature-based submodules: crawlers/, db/, tui/, alerts/, cli/ — each maps to a future phase (D-02)"
  - "hatchling as build backend: src-layout-aware by default with packages = [src/apple_deals]"
  - "mypy in standard mode (not strict): catches real errors without requiring all annotations"
  - "SQLAlchemy mypy plugin registered: avoids false positives on ORM column attributes"

patterns-established:
  - "Pattern: pyproject.toml as single config source for ruff, mypy, pytest, and hatchling"
  - "Pattern: src/ layout with pythonpath=['src'] in pytest, mypy_path='src', ruff src=['src']"
  - "Pattern: Empty __init__.py in every package directory to prevent silent import failures"

requirements-completed:
  - DEV-01
  - DEV-02
  - DEV-03
  - DEV-04

# Metrics
duration: 8min
completed: 2026-05-08
---

# Phase 1 Plan 01: Project Foundation Summary

**pyproject.toml with uv+hatchling src-layout config, ruff/mypy/pytest tool sections, and apple_deals package skeleton with stub submodules**

## Performance

- **Duration:** 8 min
- **Started:** 2026-05-08T00:00:00Z
- **Completed:** 2026-05-08T00:08:00Z
- **Tasks:** 2
- **Files modified:** 6 (1 modified, 5 created)

## Accomplishments

- pyproject.toml created with all required tool configs: entry point, hatchling wheel config, ruff `src=["src"]`, mypy standard mode + sqlalchemy plugin, pytest `pythonpath=["src"]`
- src/apple_deals package tree created with stub __init__.py files for crawlers, tui, and alerts submodules
- .gitignore extended with project-specific entries: `apple_deals.db` and `*.sqlite3` (T-01-02 threat mitigation)
- `uv sync` completed without errors, installing 37 packages including apple-deals-crawler==0.1.0

## Task Commits

Each task was committed atomically:

1. **Task 1: Write pyproject.toml with full tool configuration** - `e47e902` (chore)
2. **Task 2: Create package tree and project support files** - `0de1799` (chore)

**Plan metadata:** (see final docs commit)

## Files Created/Modified

- `pyproject.toml` - Project metadata, entry point, build system, dev deps, ruff/mypy/pytest tool configs
- `.python-version` - Pins Python 3.13 for uv
- `.gitignore` - Extended with `apple_deals.db` and `*.sqlite3` project-specific exclusions
- `src/apple_deals/__init__.py` - Package root marker
- `src/apple_deals/crawlers/__init__.py` - Crawlers stub submodule
- `src/apple_deals/tui/__init__.py` - TUI stub submodule
- `src/apple_deals/alerts/__init__.py` - Alerts stub submodule

## Decisions Made

- Kept existing comprehensive `.gitignore` (already had .env, .venv, .mypy_cache, .pytest_cache, .ruff_cache) and appended only the project-specific `apple_deals.db` and `*.sqlite3` entries rather than replacing it — preserves all existing hygiene rules
- cli/ and db/ directories deferred to Plan 02 per plan instructions (they own those files)

## Deviations from Plan

None - plan executed exactly as written. The existing `.gitignore` already covered most Python hygiene rules, so only project-specific entries were appended.

## Issues Encountered

None. `uv sync` completed first attempt without errors.

## Known Stubs

The following submodule __init__.py files are intentional empty stubs — placeholder package markers with no implementation:

- `src/apple_deals/crawlers/__init__.py` — implementation in Phase 2
- `src/apple_deals/tui/__init__.py` — implementation in Phase 4
- `src/apple_deals/alerts/__init__.py` — implementation in Phase 5

These stubs are intentional and correct for this plan's scope.

## Threat Flags

T-01-02 (Information Disclosure — SQLite DB file) mitigated in this plan: `apple_deals.db` and `*.sqlite3` added to `.gitignore`.

T-01-01 (Information Disclosure — secrets in source) partially mitigated: detect-secrets declared as dev dependency. Full mitigation (hook installation + baseline) is Plan 03 scope.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Package skeleton is importable after `uv sync`
- All tool configurations in place for ruff, mypy, and pytest
- Plan 02 can create cli/ and db/ submodules, implement the Typer CLI stubs, SQLAlchemy models, and session
- Plan 03 can install pre-commit hooks using the dev dependencies declared in pyproject.toml

## Self-Check

- [x] pyproject.toml exists with all critical keys
- [x] .python-version contains 3.13
- [x] .gitignore contains apple_deals.db
- [x] src/apple_deals/__init__.py exists
- [x] src/apple_deals/crawlers/__init__.py exists
- [x] src/apple_deals/tui/__init__.py exists
- [x] src/apple_deals/alerts/__init__.py exists
- [x] uv sync exits 0

## Self-Check: PASSED

---
*Phase: 01-project-foundation*
*Completed: 2026-05-08*
