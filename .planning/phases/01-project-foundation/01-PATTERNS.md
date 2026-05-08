# Phase 1: Project Foundation - Pattern Map

**Mapped:** 2026-05-08
**Files analyzed:** 11 (new files to create)
**Analogs found:** 0 / 11 — greenfield project; no existing source code

> **Greenfield note:** This is a brand-new repository with no Python source files.
> No codebase analogs exist. This document records the **canonical first-instance
> patterns** that Phase 1 establishes. Every subsequent phase copies from these
> patterns. All excerpts below are sourced from RESEARCH.md (verified against
> official documentation — see Sources section of RESEARCH.md).

---

## File Classification

| New File | Role | Data Flow | Closest Analog | Match Quality |
|----------|------|-----------|----------------|---------------|
| `pyproject.toml` | config | — | none (greenfield) | none |
| `.pre-commit-config.yaml` | config | — | none (greenfield) | none |
| `.python-version` | config | — | none (greenfield) | none |
| `src/apple_deals/__init__.py` | package-init | — | none (greenfield) | none |
| `src/apple_deals/cli/__init__.py` | package-init | — | none (greenfield) | none |
| `src/apple_deals/cli/main.py` | entrypoint / controller | request-response | none (greenfield) | none |
| `src/apple_deals/db/__init__.py` | package-init | — | none (greenfield) | none |
| `src/apple_deals/db/models.py` | model | CRUD | none (greenfield) | none |
| `src/apple_deals/db/session.py` | service / utility | CRUD | none (greenfield) | none |
| `src/apple_deals/crawlers/__init__.py` | package-init (stub) | — | none (greenfield) | none |
| `src/apple_deals/tui/__init__.py` | package-init (stub) | — | none (greenfield) | none |
| `src/apple_deals/alerts/__init__.py` | package-init (stub) | — | none (greenfield) | none |
| `tests/__init__.py` | test placeholder | — | none (greenfield) | none |

---

## Pattern Assignments

### `pyproject.toml` (config)

**Analog:** none — first instance. This file IS the canonical pattern for the project.

**Full pattern** (RESEARCH.md Pattern 1):
```toml
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
disallow_untyped_defs = true
warn_return_any = true
warn_unused_ignores = true

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

**Critical constraints:**
- `[tool.hatch.build.targets.wheel] packages = ["src/apple_deals"]` is REQUIRED — without it hatchling cannot find the package in `src/` and `uv run apple-deals` fails.
- `src = ["src"]` in `[tool.ruff]` is REQUIRED — without it ruff mis-classifies import groups for `I` (isort) rules.
- `mypy_path = "src"` is REQUIRED — without it mypy cannot find the `apple_deals` package.
- `pythonpath = ["src"]` in `[tool.pytest.ini_options]` is REQUIRED — without it pytest cannot import the package.
- `sqlalchemy[mypy]>=2.0.49` must appear in BOTH `[dependency-groups] dev` AND as `additional_dependencies` in the mypy pre-commit hook entry.

---

### `.pre-commit-config.yaml` (config)

**Analog:** none — first instance. Canonical hook order: detect-secrets → ruff → mypy → file-hygiene.

**Full pattern** (RESEARCH.md Pattern 5):
```yaml
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

**Critical constraints:**
- `.secrets.baseline` MUST be generated and committed BEFORE running `pre-commit install` or any pre-commit pass. Command: `uv run detect-secrets scan > .secrets.baseline`.
- mypy hook MUST have `additional_dependencies` listing `sqlalchemy[mypy]` and `typer` — the isolated pre-commit env does not inherit the project's `.venv`.
- Hook ID is `ruff-check` (not the old `ruff`) — the old ID causes a hook-not-found error.

---

### `.python-version` (config)

**Full pattern:**
```
3.13
```

This pins the runtime for uv. Single line, no trailing content.

---

### `src/apple_deals/__init__.py` (package-init)

**Full pattern:**
```python
```

Empty file. Marks `apple_deals` as a Python package. No imports, no side effects.

---

### `src/apple_deals/cli/__init__.py` (package-init)

**Full pattern:**
```python
```

Empty file. Marks `cli/` as a subpackage.

---

### `src/apple_deals/cli/main.py` (entrypoint / controller, request-response)

**Analog:** none — first instance. This is the canonical Typer CLI pattern for the project.

**Full pattern** (RESEARCH.md Pattern 2):
```python
import typer

app = typer.Typer(help="Track Apple Mac prices from Colombian retailers.")
db_app = typer.Typer(help="Database maintenance commands.")
app.add_typer(db_app, name="db")


@app.callback()
def main() -> None:
    """apple-deals: CLI entrypoint."""
    from apple_deals.db.session import init_db
    init_db()


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

**Critical constraints:**
- The `@app.callback()` is how `init_db()` gets called on startup — satisfies success criterion "SQLite DB is created on first run" (DB-01) even with all stub commands.
- Stub output MUST be `typer.echo("Command not yet implemented.")` followed by `raise typer.Exit(1)`. Non-zero exit prevents CI from treating a stub call as success (D-09).
- `db` subapp is registered via `app.add_typer(db_app, name="db")` — this is what makes `apple-deals db --help` work (D-08).

---

### `src/apple_deals/db/__init__.py` (package-init)

**Full pattern:**
```python
```

Empty file. Marks `db/` as a subpackage.

---

### `src/apple_deals/db/models.py` (model, CRUD)

**Analog:** none — first instance. This is the canonical SQLAlchemy 2.0 Declarative ORM pattern for the project.

**Full pattern** (RESEARCH.md Pattern 3):
```python
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

**Critical constraints:**
- Use `Mapped[str | None]` (not `Mapped[Optional[str]]`) for nullable columns — matches SQLAlchemy 2.x docs and avoids extra import.
- Use `class Base(DeclarativeBase): pass` (not the legacy `declarative_base()` function call) — SQLAlchemy 2.x idiomatic form.
- `models.py` MUST have zero side effects on import — no engine creation, no `create_all`, no session creation. Those live exclusively in `session.py`.
- The SQLAlchemy mypy plugin (`sqlalchemy.ext.mypy.plugin`) in `pyproject.toml` is what makes mypy accept `Mapped[str] = mapped_column(...)` without false positives.
- Do NOT use `sqlalchemy2-stubs` — that package is for SQLAlchemy 1.x only.

---

### `src/apple_deals/db/session.py` (service / utility, CRUD)

**Analog:** none — first instance. This is the canonical engine + session factory pattern for the project.

**Full pattern** (RESEARCH.md Pattern 4):
```python
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

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

**Critical constraints:**
- `sqlite:///apple_deals.db` (three slashes) creates the file in the current working directory — correct for Phase 1 local dev use.
- `DATABASE_URL` env var is the Phase 3 extension point for PostgreSQL/Neon — the `os.getenv` fallback handles this with no code changes.
- `Base.metadata.create_all(engine)` is idempotent — safe to call every time the app starts.
- Phase 1 keeps `get_session()` simple (returns a raw session). Phase 3 will add context manager / dependency injection patterns.

---

### `src/apple_deals/crawlers/__init__.py` (package-init, stub)

**Full pattern:**
```python
```

Empty file. Marks `crawlers/` as a subpackage. Phase 2 adds crawlers here.

---

### `src/apple_deals/tui/__init__.py` (package-init, stub)

**Full pattern:**
```python
```

Empty file. Marks `tui/` as a subpackage. Phase 4 adds TUI here.

---

### `src/apple_deals/alerts/__init__.py` (package-init, stub)

**Full pattern:**
```python
```

Empty file. Marks `alerts/` as a subpackage. Phase 5 adds alert logic here.

---

### `tests/__init__.py` (test placeholder)

**Full pattern:**
```python
```

Empty file. Required for pytest to collect the `tests/` directory as a package.

---

## Shared Patterns

### Python import style
**Apply to:** All `.py` files in `src/apple_deals/`

- Standard library imports first, third-party second, first-party (`apple_deals.*`) third.
- Ruff `I` rules enforce this automatically — no manual sorting needed.
- Use `from __future__ import annotations` only if needed for forward references; not required in Python 3.13.
- Use absolute imports from `apple_deals.*` (never relative `from ..db import`).

### Type annotation style
**Apply to:** All function signatures in `src/apple_deals/`

- All function definitions MUST have type annotations on parameters and return values (enforced by mypy `disallow_untyped_defs = true`).
- Use `str | None` not `Optional[str]`.
- Use `-> None` explicitly on functions that return nothing.

### Stub command pattern
**Source:** `src/apple_deals/cli/main.py` (Phase 1 canonical)
**Apply to:** Any new command added before its implementation phase

```python
@app.command()
def command_name() -> None:
    """One-line description shown in --help."""
    typer.echo("Command not yet implemented.")
    raise typer.Exit(1)
```

### DB model column pattern
**Source:** `src/apple_deals/db/models.py` (Phase 1 canonical)
**Apply to:** Any new SQLAlchemy model added in future phases

```python
# Nullable column
field: Mapped[str | None] = mapped_column(String(100))

# Required column
field: Mapped[str] = mapped_column(String(255), nullable=False)

# Timestamp with DB-side default
created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
```

---

## No Analog Found

All 13 files have no existing codebase analog — this is a greenfield project. The patterns above are sourced from RESEARCH.md which verified them against official documentation. Planner should use RESEARCH.md patterns directly for all files in this phase.

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| All 13 files listed above | various | various | Greenfield — no prior Python source exists in the repo |

---

## Anti-Patterns (from RESEARCH.md — do not implement)

| Anti-Pattern | Correct Pattern |
|-------------|-----------------|
| `create_all` called inside `models.py` | `create_all` lives only in `session.py:init_db()` |
| Missing `__init__.py` in any submodule | Every directory under `src/apple_deals/` needs one |
| Committing `.secrets.baseline` after code | Generate baseline first, commit it, then install hooks |
| `src = ["src"]` absent from `[tool.ruff]` | Always include — required for correct import classification |
| `sqlalchemy2-stubs` installed | Never install — for 1.x only; 2.x uses built-in plugin |
| `Mapped[Optional[str]]` | Use `Mapped[str | None]` — modern style, no extra import |
| `declarative_base()` function | Use `class Base(DeclarativeBase): pass` — 2.x idiom |
| Hook ID `ruff` in pre-commit | Use `ruff-check` — renamed; old ID causes hook-not-found |

---

## Metadata

**Analog search scope:** entire repository (no Python source files exist)
**Files scanned:** 0 Python source files (greenfield)
**Pattern sources:** RESEARCH.md (verified against official SQLAlchemy 2.x, Typer 0.25.x, ruff, pre-commit, detect-secrets documentation — 2026-05-08)
**Pattern extraction date:** 2026-05-08
