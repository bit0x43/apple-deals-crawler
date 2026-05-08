# Phase 1: Project Foundation - Research

**Researched:** 2026-05-08
**Domain:** Python project setup — uv, src layout, pre-commit, SQLAlchemy ORM, Typer CLI
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Use `src/` layout — package lives at `src/apple_deals/`, not at project root. Prevents accidental shadowing of the installed package during development.
- **D-02:** Feature-based internal structure inside `apple_deals/`: `crawlers/`, `db/`, `tui/`, `alerts/`, `cli/` submodules. Each maps to a future phase. No layer-based splitting.
- **D-03:** Secret scanning via `detect-secrets` (not gitleaks). Python-native, installs via uv/pip with no binary dependencies. Generates a `.secrets.baseline` file to track known non-secrets. Pre-commit hook is first-class.
- **D-04:** Ruff for lint + format (DEV-02). mypy for type checking (DEV-03) in **standard mode** (not strict). Standard mode catches real errors without requiring annotations everywhere; strictness can be tightened per-phase.
- **D-05:** Trailing whitespace, end-of-file newline, and large-file checks for DEV-04 (standard `pre-commit-hooks` entries).
- **D-06:** SQLAlchemy Declarative ORM — `class Product(Base): ...` style with typed columns. Not SQLAlchemy Core (Table objects) and not SQLModel. Supports both SQLite and PostgreSQL through the same model definitions.
- **D-07:** Phase 1 only defines the `Product` model (the core record schema: reference, sku, memory, storage, color, price, url, source, crawled_at). No migration tooling yet — Phase 3 adds PostgreSQL and can introduce Alembic if needed.
- **D-08:** All CLI commands stubbed in Phase 1 so `--help` is complete from day one (CLI-03). Commands to scaffold: `crawl`, `tui`, `db clean`, `db stats`.
- **D-09:** Stub output style: `typer.echo("Command not yet implemented.")` followed by `raise typer.Exit(1)`. Non-zero exit prevents CI from treating a stub call as success.

### Claude's Discretion

None declared — all material decisions are locked.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEV-01 | Pre-commit hooks — secret scanning (detect-secrets) | detect-secrets v1.5.0 pre-commit hook verified, baseline workflow documented |
| DEV-02 | Pre-commit hooks — ruff (lint + format) | ruff-pre-commit v0.15.12, hook IDs `ruff-check` + `ruff-format` verified from official README |
| DEV-03 | Pre-commit hooks — mypy (standard mode) | mirrors-mypy v2.0.0 verified; standard mode config documented; SQLAlchemy mypy plugin required |
| DEV-04 | Pre-commit hooks — trailing whitespace and file hygiene | pre-commit-hooks v6.0.0 verified; hook IDs `trailing-whitespace`, `end-of-file-fixer`, `check-added-large-files` |
| DB-01 | SQLite as default backend (zero-config) | SQLAlchemy 2.0.49 `create_engine("sqlite:///...")` + `Base.metadata.create_all(engine)` pattern verified |
| CLI-03 | `--help` for all commands | Typer 0.25.1 `app.add_typer()` subcommand pattern verified; all four commands stubbed per D-08/D-09 |
</phase_requirements>

---

## Summary

Phase 1 is a pure scaffolding phase for a greenfield Python 3.13 project. No scraping logic, no UI, no business rules — the output is a working `pyproject.toml`, pre-commit hook configuration, one SQLAlchemy ORM model, and a fully-stubbed Typer CLI where every command responds to `--help`. All choices are locked by CONTEXT.md decisions.

The stack is well-established in 2026 and all components are mutually compatible with Python 3.13. The primary integration concern is the src layout: pytest requires `pythonpath = ["src"]` in `[tool.pytest.ini_options]` to discover the package, mypy requires `mypy_path = "src"` in `[tool.mypy]`, and ruff requires `src = ["src"]` in `[tool.ruff]` for correct import classification. Missing any one of these produces hard-to-debug "module not found" errors that look like installation failures.

A secondary concern is the SQLAlchemy mypy plugin. Without it, mypy issues false positives on ORM column attributes. The plugin ships as part of SQLAlchemy itself (`sqlalchemy.ext.mypy.plugin`) and just needs to be registered in `[tool.mypy]`.

**Primary recommendation:** Scaffold all files in one wave — `pyproject.toml`, `.pre-commit-config.yaml`, the package tree, and then run `uv sync && detect-secrets scan > .secrets.baseline && pre-commit install && pre-commit run --all-files` to validate. The baseline must be committed before the detect-secrets hook can pass.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Project metadata & dependencies | Build tooling (pyproject.toml) | — | All Python project config lives in pyproject.toml per PEP 517/518/621 |
| Secret scanning | Pre-commit hook (detect-secrets) | — | Runs at commit time, never reaches CI |
| Lint + format | Pre-commit hook (ruff) | CI (future) | Enforced locally first; same ruff config used by both |
| Type checking | Pre-commit hook (mypy) | CI (future) | Standard mode; SQLAlchemy plugin required for ORM |
| File hygiene | Pre-commit hook (pre-commit-hooks) | — | Trailing whitespace, EOF newlines, large file guard |
| DB schema | SQLAlchemy ORM models (`db/models.py`) | — | Single source of truth; same models target SQLite and Postgres |
| DB initialization | `db/session.py` engine + `create_all` | CLI entrypoint (`cli/main.py`) | Engine created once; `create_all` called at app startup |
| CLI entrypoint | `cli/main.py` Typer app | `pyproject.toml` script | Script entry bridges installation to module |
| CLI subcommands | `cli/main.py` subapps | Feature modules (Phase 2+) | Stubs live in cli/ until Phase 2+ implements them |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.13.13 | Runtime | Project constraint; available via Homebrew at `/opt/homebrew/bin/python3.13` |
| uv | 0.9.7 (machine) / 0.11.12 (PyPI latest) | Package + venv manager | Project constraint; lockfile-first, fastest resolver |
| hatchling | 1.29.0 | Build backend | Default for `uv init --lib`; PEP 517 compliant; src-layout aware out of the box |
| SQLAlchemy | 2.0.49 | ORM + engine | Project constraint; 2.x Declarative style with `Mapped[]` type annotations |
| Typer | 0.25.1 | CLI framework | Project constraint; type-hint-driven, built on Click |
| pre-commit | 4.6.0 | Hook runner | Project constraint; manages isolated envs for each hook |

### Supporting (Dev Tools)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| ruff | 0.15.12 | Lint + format | All Python files in pre-commit and ad-hoc runs |
| mypy | 2.0.0 | Static type checking | Pre-commit hook (standard mode) |
| detect-secrets | 1.5.0 | Secret scanning | Pre-commit hook; baseline file must be committed first |
| pytest | 9.0.3 | Test runner | Validation architecture (Wave 0 gap — no tests yet) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| hatchling | setuptools | hatchling is src-layout-aware by default; setuptools needs explicit `find_packages` config |
| hatchling | uv_build | uv_build is newer (shown in Typer docs); hatchling is more mature and widely used |
| SQLAlchemy Declarative | SQLModel | SQLModel is a Pydantic wrapper; adds complexity; same ORM under the hood |
| mirrors-mypy hook | local mypy via uv | mirrors-mypy isolates mypy from project env; avoids version conflicts in pre-commit |

**Installation (after pyproject.toml is created):**
```bash
uv sync
uv run detect-secrets scan > .secrets.baseline
uv run pre-commit install
uv run pre-commit run --all-files
```

**Version verification:** All versions above confirmed against PyPI registry on 2026-05-08. [VERIFIED: PyPI registry]

---

## Architecture Patterns

### System Architecture Diagram

```
pyproject.toml
   |-- defines entrypoint: apple-deals -> apple_deals.cli.main:app
   |-- declares dependencies (SQLAlchemy, Typer, ...)
   |-- configures ruff / mypy / pytest

.pre-commit-config.yaml
   |-- detect-secrets  -->  .secrets.baseline (committed)
   |-- ruff-check      -->  src/apple_deals/**/*.py
   |-- ruff-format     -->  src/apple_deals/**/*.py
   |-- mypy            -->  src/apple_deals/**/*.py
   |-- pre-commit-hooks --> all files (whitespace / EOF / large-files)

[uv sync] --> .venv/
   |
   v
apple-deals (console_scripts entry)
   |
   v
src/apple_deals/cli/main.py  (Typer app)
   |-- crawl  --> stub (typer.Exit(1))
   |-- tui    --> stub (typer.Exit(1))
   |-- db     --> sub-app
         |-- clean  --> stub (typer.Exit(1))
         |-- stats  --> stub (typer.Exit(1))
   |
   (on any non-stub call) --> db/session.py
         |
         v
   create_engine("sqlite:///apple_deals.db")
         |
         v
   Base.metadata.create_all(engine)
         |
         v
   db/models.py  -->  products table (9 columns)
```

### Recommended Project Structure

```
apple-deals-crawler/
├── pyproject.toml           # uv project config, tool configs (ruff, mypy, pytest)
├── .pre-commit-config.yaml  # pre-commit hook definitions
├── .secrets.baseline        # detect-secrets baseline (committed)
├── .python-version          # pins Python 3.13 for uv
├── README.md
├── src/
│   └── apple_deals/
│       ├── __init__.py
│       ├── cli/
│       │   ├── __init__.py
│       │   └── main.py      # Typer app + subcommand registration
│       ├── db/
│       │   ├── __init__.py
│       │   ├── models.py    # Product ORM model
│       │   └── session.py   # engine factory + get_session
│       ├── crawlers/
│       │   └── __init__.py  # empty stub
│       ├── tui/
│       │   └── __init__.py  # empty stub
│       └── alerts/
│           └── __init__.py  # empty stub
└── tests/
    └── __init__.py          # empty; Wave 0 placeholder
```

### Pattern 1: pyproject.toml for uv + src layout + Typer entrypoint

**What:** Single pyproject.toml that configures the build, the entry point, and all tool settings.
**When to use:** Every Python project using uv with a src layout.

```toml
# Source: https://typer.tiangolo.com/tutorial/package + uv docs + tool configs
[project]
name = "apple-deals-crawler"
version = "0.1.0"
description = "Track daily Apple Mac prices from Colombian retailers"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "sqlalchemy>=2.0.49",
    "typer>=0.25.1",
]

[project.scripts]
apple-deals = "apple_deals.cli.main:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/apple_deals"]

[dependency-groups]
dev = [
    "pre-commit>=4.6.0",
    "ruff>=0.15.12",
    "mypy>=2.0.0",
    "detect-secrets>=1.5.0",
    "pytest>=9.0.3",
    "sqlalchemy[mypy]>=2.0.49",
]

[tool.ruff]
src = ["src"]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]

[tool.mypy]
python_version = "3.13"
mypy_path = "src"
plugins = ["sqlalchemy.ext.mypy.plugin"]
ignore_missing_imports = true
# Standard mode: disallow_untyped_defs without requiring all annotations
disallow_untyped_defs = true
warn_return_any = true
warn_unused_ignores = true

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

### Pattern 2: Typer CLI with db subapp

**What:** Main Typer app registers a `db` sub-app via `app.add_typer()`. All commands stub immediately.
**When to use:** Multi-group CLIs where `--help` must be complete before implementation.

```python
# Source: https://typer.tiangolo.com/tutorial/subcommands/add-typer
# src/apple_deals/cli/main.py
import typer

app = typer.Typer(help="Track Apple Mac prices from Colombian retailers.")
db_app = typer.Typer(help="Database maintenance commands.")
app.add_typer(db_app, name="db")


@app.command()
def crawl() -> None:
    """Crawl product prices from all configured stores."""
    typer.echo("Command not yet implemented.")
    raise typer.Exit(1)


@app.command()
def tui() -> None:
    """Open the interactive terminal UI."""
    typer.echo("Command not yet implemented.")
    raise typer.Exit(1)


@db_app.command("clean")
def db_clean(
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview rows to delete without deleting."),
) -> None:
    """Prune records outside the retention window."""
    typer.echo("Command not yet implemented.")
    raise typer.Exit(1)


@db_app.command("stats")
def db_stats() -> None:
    """Show database statistics: row count, size, oldest/newest record."""
    typer.echo("Command not yet implemented.")
    raise typer.Exit(1)


if __name__ == "__main__":
    app()
```

### Pattern 3: SQLAlchemy 2.0 Declarative ORM — Product model

**What:** Modern Annotated Declarative style with `Mapped[]` type hints. Auto-creates table on first run.
**When to use:** Any new SQLAlchemy 2.x model definition.

```python
# Source: https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html
# src/apple_deals/db/models.py
from datetime import datetime
from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    reference: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(100), nullable=False)
    memory: Mapped[str | None] = mapped_column(String(50))
    storage: Mapped[str | None] = mapped_column(String(50))
    color: Mapped[str | None] = mapped_column(String(100))
    price: Mapped[float] = mapped_column(Numeric(precision=12, scale=2), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    crawled_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
```

### Pattern 4: SQLAlchemy engine factory + session for SQLite

**What:** Module-level engine created from env var or SQLite default. `create_all` on startup.
**When to use:** Phase 1 SQLite initialization; pattern extended in Phase 3 for Postgres.

```python
# Source: https://docs.sqlalchemy.org/en/20/orm/session_basics.html
# src/apple_deals/db/session.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from apple_deals.db.models import Base

_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///apple_deals.db")

engine = create_engine(_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    """Create all tables if they don't exist."""
    Base.metadata.create_all(engine)


def get_session() -> Session:
    return SessionLocal()
```

### Pattern 5: .pre-commit-config.yaml — complete configuration

**What:** All four hook groups in order: detect-secrets first (blocks credential commits), then ruff, then mypy, then file hygiene.
**When to use:** This is the verbatim config for this project.

```yaml
# Source: https://github.com/Yelp/detect-secrets README
#         https://github.com/astral-sh/ruff-pre-commit README (v0.15.12)
#         https://github.com/pre-commit/mirrors-mypy README (v2.0.0)
#         https://github.com/pre-commit/pre-commit-hooks (v6.0.0)
default_language_version:
  python: python3.13

repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ["--baseline", ".secrets.baseline"]
        exclude: package.lock.json

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.12
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v2.0.0
    hooks:
      - id: mypy
        additional_dependencies:
          - sqlalchemy[mypy]>=2.0.49
          - typer>=0.25.1

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-added-large-files
```

### Anti-Patterns to Avoid

- **No `__init__.py` in stub submodules:** Python imports fail silently at runtime if `__init__.py` is missing in `crawlers/`, `tui/`, `alerts/`. Every directory in the package must have one.
- **Calling `create_all` inside the model module:** Engine and session creation belong in `session.py`, not alongside the model definitions. Importing `models.py` should have zero side effects.
- **Committing `.secrets.baseline` after code:** The baseline must be committed before any other commit that the detect-secrets hook will scan. Correct order: `detect-secrets scan > .secrets.baseline`, `git add .secrets.baseline`, then `pre-commit install`.
- **Skipping `src = ["src"]` in `[tool.ruff]`:** Without it, ruff treats stdlib/third-party imports as first-party, silently mis-classifying `I` rules.
- **Using `sqlalchemy2-stubs` with SQLAlchemy 2.x:** The external stubs package is for SQLAlchemy 1.x. SQLAlchemy 2.x ships with `sqlalchemy.ext.mypy.plugin` — use that instead.
- **Using `Mapped[Optional[str]]` instead of `Mapped[str | None]`:** Both work in Python 3.13 but `str | None` is the modern style SQLAlchemy docs show; `Optional` requires the `Optional` import.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CLI argument parsing + --help | Custom argparse/click wrapper | Typer | Typer generates --help from type hints; argparse requires manual help strings and lacks subcommand ergonomics |
| Secret scanning heuristics | Regex patterns in git hooks | detect-secrets | detect-secrets handles entropy analysis, keyword detection, and baseline diffing — thousands of edge cases |
| Code formatting | Custom formatter | ruff-format | Formatting is a solved problem; custom rules cause team friction |
| DB table creation | Raw `CREATE TABLE` SQL | `Base.metadata.create_all(engine)` | create_all is idempotent, dialect-agnostic, and stays in sync with ORM models automatically |
| Hook environment isolation | Shell scripts | pre-commit | pre-commit manages isolated virtualenvs per hook; shell scripts break on OS upgrades |

**Key insight:** Every item in this list has non-obvious edge cases (encoding, platform paths, quoting, concurrent writes). These libraries exist precisely because the edge cases are painful. This phase's value is in wiring them together correctly, not in reimplementing them.

---

## Common Pitfalls

### Pitfall 1: pytest cannot import the package with src layout

**What goes wrong:** `pytest` run from project root fails with `ModuleNotFoundError: No module named 'apple_deals'`.
**Why it happens:** pytest adds the current directory (not `src/`) to `sys.path`. The package is under `src/` and is not importable without either an editable install or `pythonpath` config.
**How to avoid:** Add `pythonpath = ["src"]` to `[tool.pytest.ini_options]` in `pyproject.toml`. After `uv sync` (which installs the package in editable mode by default), this is not strictly required — but the config makes tests runnable even without install.
**Warning signs:** `ModuleNotFoundError` on the first `pytest` run in CI.

### Pitfall 2: detect-secrets hook blocks the first commit because there is no baseline

**What goes wrong:** `pre-commit run --all-files` fails with `ERROR  Potential secrets baseline not found`. You cannot make the first commit.
**Why it happens:** The hook requires `.secrets.baseline` to exist before it can compare. If the file is absent, the hook errors rather than scanning from scratch.
**How to avoid:** Generate the baseline before running pre-commit: `uv run detect-secrets scan > .secrets.baseline`. Stage and commit `.secrets.baseline` before anything else, or include it in the initial scaffold commit.
**Warning signs:** `detect-secrets` hook failure on a brand-new repo.

### Pitfall 3: mypy reports errors on SQLAlchemy ORM attributes without the plugin

**What goes wrong:** mypy reports `error: Cannot determine type of "reference"` or `Incompatible types in assignment` on every ORM column.
**Why it happens:** Without `sqlalchemy.ext.mypy.plugin`, mypy cannot interpret `Mapped[str] = mapped_column(...)` as a typed attribute. It sees the descriptor assignment as an unresolvable type.
**How to avoid:** Register `plugins = ["sqlalchemy.ext.mypy.plugin"]` in `[tool.mypy]`. Install `sqlalchemy[mypy]` as a dev dependency (it ships the plugin). Also add `sqlalchemy[mypy]` to `additional_dependencies` in the mypy pre-commit hook so the isolated hook env has it too.
**Warning signs:** Dozens of mypy errors on `models.py` even with correct type annotations.

### Pitfall 4: hatchling does not find the package in src/ without explicit config

**What goes wrong:** `uv run apple-deals` fails with `No module named apple_deals` even after `uv sync`.
**Why it happens:** hatchling auto-discovers packages in the project root. With a `src/` layout, it needs to be told where to look.
**How to avoid:** Add `[tool.hatch.build.targets.wheel] packages = ["src/apple_deals"]` to `pyproject.toml`. Alternatively use the `[tool.hatch.build] sources = {"src" = ""}` form. Either works; the explicit `packages` form is easier to read.
**Warning signs:** `uv sync` completes without errors but `apple-deals --help` fails.

### Pitfall 5: pre-commit hook runs mypy on files but mypy cannot find type stubs for dependencies

**What goes wrong:** The mirrors-mypy pre-commit hook runs in an isolated virtualenv that does NOT have the project's dependencies installed, so it fails with `Cannot find implementation or library stub for module named 'sqlalchemy'`.
**Why it happens:** pre-commit creates a minimal env for each hook; it does not use the project's `.venv`.
**How to avoid:** Add `additional_dependencies` to the mypy hook entry, listing every package mypy needs to type-check: `sqlalchemy[mypy]>=2.0.49`, `typer>=0.25.1`.
**Warning signs:** mypy passes locally (where the project env is active) but fails in pre-commit.

---

## Code Examples

All patterns are in the Architecture Patterns section above. Key verified snippets:

### detect-secrets baseline initialization
```bash
# Source: https://github.com/Yelp/detect-secrets README
uv run detect-secrets scan > .secrets.baseline
git add .secrets.baseline
git commit -m "chore: add detect-secrets baseline"
pre-commit install
```

### Verify CLI entrypoint after uv sync
```bash
# Source: uv docs (confirmed via uv init --lib test)
uv sync
uv run apple-deals --help
# Expected: help text listing crawl, tui, db subcommands
```

### Run pre-commit on all files
```bash
# Source: pre-commit docs
uv run pre-commit run --all-files
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `setup.py` + `setup.cfg` | `pyproject.toml` (PEP 621) | PEP 621 standardized 2020 | Single config file, tool-agnostic |
| `Column(String)` in SQLAlchemy | `Mapped[str] = mapped_column(...)` | SQLAlchemy 2.0 (2023) | Full typing support, mypy plugin works correctly |
| `flake8` + `isort` + `black` | `ruff` (replaces all three) | ruff reached feature parity ~2023 | Single tool, 10-100x faster |
| `sqlalchemy2-stubs` (external) | `sqlalchemy.ext.mypy.plugin` (built-in) | SQLAlchemy 2.x | No separate stubs package needed |
| `poetry` | `uv` | uv GA 2024 | Significantly faster resolution and install |
| `Optional[str]` | `str \| None` (PEP 604) | Python 3.10+ | More readable; SQLAlchemy 2.x docs use this style |

**Deprecated/outdated:**
- `sqlalchemy2-stubs`: For SQLAlchemy 1.x only. Do not install for 2.x projects.
- `ruff` hook id `ruff` (old): Renamed to `ruff-check` in ruff-pre-commit. Using the old name causes hook-not-found errors.
- `declarative_base()` (function): Replaced by `class Base(DeclarativeBase): pass` in SQLAlchemy 2.0. Both work, but `DeclarativeBase` is the idiomatic 2.x approach.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `uv sync` installs the package in editable mode by default for src-layout projects | Pitfall 1 | Tests may need PYTHONPATH set explicitly; mitigated by also setting `pythonpath = ["src"]` in pytest config |
| A2 | `hatchling` is the preferred build backend for uv + src layout (not `uv_build`) | Standard Stack | No functional risk; `uv_build` would also work with same config shape |

**All other claims verified against PyPI registry, official documentation, or direct tool invocation.**

---

## Open Questions

1. **Where should `apple_deals.db` (SQLite file) be created?**
   - What we know: `sqlite:///apple_deals.db` places the file in the current working directory at runtime.
   - What's unclear: Should it default to a user data dir (e.g., `~/.local/share/apple_deals/`) or stay in the project root for dev convenience?
   - Recommendation: Use project root for Phase 1 (simplest). Phase 3 can introduce a configurable path via env var.

2. **Should `init_db()` be called automatically on CLI startup or only explicitly?**
   - What we know: D-08/D-09 stub all commands; the actual `init_db()` call will be wired in Phase 2 when `crawl` is implemented.
   - What's unclear: Whether Phase 1 should wire `init_db()` into the CLI callback.
   - Recommendation: Add a Typer app-level callback that calls `init_db()` in Phase 1, so success criterion 3 ("SQLite DB is created on first run") is satisfied even with stub commands.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 | Runtime | ✓ | 3.13.13 (Homebrew `/opt/homebrew/bin/python3.13`) | — |
| uv | Package manager | ✓ | 0.9.7 (machine) | — |
| git | pre-commit, version control | ✓ | (standard macOS install) | — |
| pre-commit | Hook runner | ✗ (not globally installed) | — | Install via `uv add --group dev pre-commit` + `uv run pre-commit install` |

**Missing dependencies with no fallback:** None that block execution.

**Missing dependencies with fallback:**
- `pre-commit` not globally installed — install as a dev dependency via uv (`uv run pre-commit` works without global install).

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` — Wave 0 gap |
| Quick run command | `uv run pytest tests/ -x -q` |
| Full suite command | `uv run pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DEV-01 | `pre-commit run --all-files` passes (detect-secrets) | smoke | `uv run pre-commit run --all-files` | ❌ Wave 0 |
| DEV-02 | `pre-commit run --all-files` passes (ruff) | smoke | `uv run pre-commit run --all-files` | ❌ Wave 0 |
| DEV-03 | `pre-commit run --all-files` passes (mypy) | smoke | `uv run pre-commit run --all-files` | ❌ Wave 0 |
| DEV-04 | `pre-commit run --all-files` passes (hygiene) | smoke | `uv run pre-commit run --all-files` | ❌ Wave 0 |
| DB-01 | SQLite file created with correct schema on first run | integration | `uv run pytest tests/test_db.py -x` | ❌ Wave 0 |
| CLI-03 | `apple-deals --help` exits 0 and lists all commands | smoke | `uv run apple-deals --help` | ❌ Wave 0 |

> Note: DEV-01 through DEV-04 share a single smoke command (`pre-commit run --all-files`). The pre-commit run itself IS the test for these requirements — no separate pytest test is needed.

### Sampling Rate

- **Per task commit:** `uv run pre-commit run --all-files`
- **Per wave merge:** `uv run pre-commit run --all-files && uv run pytest tests/ -v`
- **Phase gate:** Full suite green + `uv run apple-deals --help` lists all commands before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/__init__.py` — empty placeholder so pytest collects the directory
- [ ] `tests/test_db.py` — covers DB-01: `init_db()` creates `products` table with correct 9 columns
- [ ] `tests/test_cli.py` — covers CLI-03: `apple-deals --help` exits 0; all four command names appear in output
- [ ] `pyproject.toml [tool.pytest.ini_options]` section with `pythonpath = ["src"]` and `testpaths = ["tests"]`

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Not applicable in Phase 1 |
| V3 Session Management | No | Not applicable in Phase 1 |
| V4 Access Control | No | Not applicable in Phase 1 |
| V5 Input Validation | No | No user input in Phase 1 (stubs only) |
| V6 Cryptography | No | Not applicable in Phase 1 |
| Secret scanning | Yes | detect-secrets v1.5.0 pre-commit hook — prevents credentials from ever reaching git history |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| API keys / tokens accidentally committed | Information Disclosure | detect-secrets hook; `.secrets.baseline` committed; never store secrets in pyproject.toml or source |
| SQLite DB file committed to git | Information Disclosure | Add `*.db` and `*.sqlite3` to `.gitignore` |

---

## Sources

### Primary (HIGH confidence)

- `/websites/typer_tiangolo` (Context7) — pyproject.toml scripts, subcommands, `add_typer()` pattern
- `/websites/sqlalchemy_en_20_orm` (Context7) — Declarative Base, `mapped_column()`, `Mapped[]`, `sessionmaker`, `create_all`
- `/websites/sqlalchemy_en_20` (Context7) — mypy plugin, `create_engine` SQLite, `connect_args`
- `/pre-commit/pre-commit.com` (Context7) — `.pre-commit-config.yaml` format
- https://github.com/astral-sh/ruff-pre-commit (official README) — hook IDs `ruff-check`, `ruff-format`, version `v0.15.12`
- https://github.com/Yelp/detect-secrets (official README) — baseline workflow, hook config, version `v1.5.0`
- https://github.com/pre-commit/mirrors-mypy (official README) — hook config, `additional_dependencies`
- PyPI registry (verified 2026-05-08) — all package versions
- `uv init --lib --build-backend hatch` (direct invocation) — src layout structure, hatchling config

### Secondary (MEDIUM confidence)

- `/pytest-dev/pytest` (Context7) — `pythonpath = ["src"]` config for src layout
- https://docs.astral.sh/uv/concepts/projects/config/ (WebFetch) — `[project.scripts]`, `requires-python`
- https://docs.astral.sh/ruff/integrations/ (curl) — ruff pre-commit integration confirmation

### Tertiary (LOW confidence)

- None — all claims verified via primary or secondary sources.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified against PyPI registry on 2026-05-08
- Architecture: HIGH — patterns verified via Context7 official docs for SQLAlchemy 2.0 and Typer 0.25.x
- Pitfalls: HIGH — src-layout/pytest, detect-secrets baseline, and mypy plugin pitfalls confirmed via official documentation and direct uv invocation
- Pre-commit config: HIGH — hook IDs and versions confirmed from official READMEs

**Research date:** 2026-05-08
**Valid until:** 2026-06-08 (stable ecosystem; SQLAlchemy 2.x, Typer 0.25.x, and ruff are mature)
