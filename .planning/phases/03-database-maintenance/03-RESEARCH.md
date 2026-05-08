# Phase 3: Database & Maintenance - Research

**Researched:** 2026-05-08
**Domain:** SQLAlchemy 2.0 multi-backend engine, pruner, Rich CLI output
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** `session.py` already reads `DATABASE_URL` env var; when set, use it as the engine URL directly. When unset, fall back to `sqlite:///apple_deals.db`. No code change needed — just verify it works with psycopg2/asyncpg driver.
- **D-02:** Add `psycopg2-binary` as an optional dependency in pyproject.toml (`[project.optional-dependencies] postgres = ["psycopg2-binary"]`). SQLite works without it.
- **D-03:** `db clean` deletes `Product` rows where `crawled_at < now() - timedelta(days=retention_days)`. Default retention = 90 days, configurable via `--days` flag.
- **D-04:** `--dry-run` flag: query and print count of rows that WOULD be deleted, no actual DELETE.
- **D-05:** Auto-prune (DB-03) runs automatically at the end of each `crawl` command run.
- **D-06:** `db stats` prints: total row count, DB size (file size for SQLite, pg_database_size for PG), oldest crawled_at, newest crawled_at, estimated daily growth (rows in last 7 days / 7).

### Claude's Discretion

- Exact SQL/ORM query for DB size (SQLite vs PostgreSQL branch)
- Whether to use Rich table formatting for stats output

### Deferred Ideas (OUT OF SCOPE)

- Alembic migrations (not needed — schema is stable after Phase 2)
- Per-store stats breakdown (Phase 4 TUI handles visualization)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DB-02 | System switches to PostgreSQL when DATABASE_URL env var is set (Neon serverless as primary free host) | session.py already reads DATABASE_URL; psycopg2-binary 2.9.12 verified on PyPI; Neon requires `sslmode=require&channel_binding=require` in connection string |
| DB-03 | System auto-prunes records older than configurable retention period (default: 90 days) | SQLAlchemy 2.0 bulk DELETE pattern documented; datetime comparison pitfall documented; prune_old_records() added to crud.py; auto-called at crawl end |
| DB-04 | User can run `apple-deals db clean` to manually trigger pruning with optional --dry-run preview | Typer `--days int` and `--dry-run bool` option patterns verified; CLI stub already exists in cli/main.py |
| DB-05 | User can run `apple-deals db stats` to view row count, DB size, oldest/newest record, and estimated growth rate | Rich Table pattern verified; SQLite os.path.getsize pattern; PG pg_database_size SQL verified; dialect detection from engine.url |
</phase_requirements>

---

## Summary

Phase 3 is largely about filling in three stubs and adding one dependency. The `session.py` engine is already wired for dual-backend: `DATABASE_URL` env var switches from SQLite to PostgreSQL. No changes to session.py or models.py are needed. The work is: (1) add `psycopg2-binary` as an optional dep, (2) add `prune_old_records()` to `db/crud.py` with a Typer-callable interface, (3) implement `db_clean` and `db_stats` in `cli/main.py`, and (4) hook auto-prune into the `crawl` command end.

The primary technical pitfall is the datetime timezone mismatch: Phase 2 stores `crawled_at` using `datetime.now(tz=timezone.utc)`, but the `Product` model uses `DateTime` (timezone-naive). SQLite strips timezone info on roundtrip — so the value is stored and retrieved as a naive UTC datetime. The pruner must compute its cutoff as a **naive UTC datetime** to produce a correct comparison. Using `datetime.now(timezone.utc).replace(tzinfo=None)` is the correct pattern.

For the stats command, DB size requires a dialect branch: SQLite uses `os.path.getsize(engine.url.database)`, while PostgreSQL uses `SELECT pg_size_pretty(pg_database_size(current_database()))` via `text()`. The dialect can be detected with `engine.url.drivername.startswith("postgresql")`. Rich Table is the right output format — already installed as a Textual transitive dependency (Rich 15.0.0 confirmed in project virtualenv).

**Primary recommendation:** Add `prune_old_records()` to `db/crud.py`, implement CLI commands in `cli/main.py`, hook auto-prune into the `crawl` command, and add `psycopg2-binary` as an optional dep with `uv add --optional postgres psycopg2-binary`.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Engine URL switching (SQLite vs PG) | DB layer (`db/session.py`) | — | Already implemented; env var read at module load |
| Optional psycopg2 driver installation | pyproject.toml | — | Packaging concern, not runtime code |
| Row pruning logic (delete old records) | DB layer (`db/crud.py`) | — | Pure DB operation; no CLI logic belongs here |
| Auto-prune trigger at crawl end | CLI layer (`cli/main.py`) | — | D-05: crawl command calls prune after completing crawls |
| `db clean` command (manual prune) | CLI layer (`cli/main.py`) | DB layer (`db/crud.py`) | CLI owns user interaction; crud owns the DELETE |
| `db stats` command | CLI layer (`cli/main.py`) | DB layer (`db/crud.py`) | CLI owns display; DB layer owns queries |
| DB size query (dialect-specific) | DB layer or inline in stats | — | Thin enough to inline in stats command; branch on dialect name |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy | 2.0.49 (installed) | ORM, engine, bulk DELETE | Already in project; 2.0 style `delete().where()` used |
| psycopg2-binary | 2.9.12 (latest) | PostgreSQL DBAPI driver | Standard SQLAlchemy PG driver; binary wheels avoid build deps |
| Rich | 15.0.0 (installed via Textual) | Table output for stats | Already transitive dep; `Console().print(Table(...))` |
| Typer | 0.25.1 (installed) | CLI option parsing | Already project CLI framework; `typer.Option()` for --days, --dry-run |
| Python `datetime` | stdlib | UTC cutoff for pruner | No extra dep; `datetime.now(timezone.utc).replace(tzinfo=None)` |
| Python `os.path` | stdlib | SQLite file size | `os.path.getsize(engine.url.database)` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| SQLAlchemy `text()` | (part of SQLAlchemy) | Raw SQL for PG db size query | `SELECT pg_size_pretty(pg_database_size(current_database()))` |
| SQLAlchemy `func.count()` | (part of SQLAlchemy) | Total row count | `session.scalar(select(func.count()).select_from(Product))` |
| SQLAlchemy `func.min/max()` | (part of SQLAlchemy) | Oldest/newest crawled_at | `session.scalar(select(func.min(Product.crawled_at)))` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `psycopg2-binary` | `asyncpg` | asyncpg requires async SQLAlchemy; project uses sync sessions |
| `psycopg2-binary` | `pg8000` | pg8000 is pure Python (no C compile), but psycopg2-binary has wider ecosystem support |
| `os.path.getsize` for SQLite | `PRAGMA page_count * page_size` | The PRAGMA approach is more accurate for WAL-mode DBs, but overkill here |

**Installation (optional postgres extra):**
```bash
uv add --optional postgres psycopg2-binary
```

**Version verification:** [VERIFIED: pip index versions psycopg2-binary] — psycopg2-binary 2.9.12 is current as of 2026-05-08.

---

## Architecture Patterns

### System Architecture Diagram

```
                    ┌──────────────────────┐
                    │   CLI (cli/main.py)   │
                    │                      │
          ┌─────────┤  crawl()  db_clean() │
          │         │           db_stats() │
          │         └──────────────────────┘
          │                    │
          │ auto-prune          │ explicit prune / stats queries
          ▼                    ▼
   ┌─────────────┐    ┌─────────────────────┐
   │  db/crud.py │    │   db/crud.py        │
   │             │    │                     │
   │ prune_old_  │    │ prune_old_records() │
   │ records()   │    │ get_stats()         │
   └──────┬──────┘    └──────────┬──────────┘
          │                      │
          ▼                      ▼
   ┌──────────────────────────────────┐
   │        db/session.py             │
   │   engine = create_engine(URL)    │
   │   URL = DATABASE_URL or sqlite   │
   └─────────────┬────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
   [SQLite file]    [PostgreSQL/Neon]
   (default)        (when DATABASE_URL set)
```

### Recommended Project Structure (additions for Phase 3)

```
src/apple_deals/
├── db/
│   ├── models.py        # unchanged
│   ├── session.py       # unchanged (already dual-backend)
│   └── crud.py          # add prune_old_records()
├── cli/
│   └── main.py          # implement db_clean(), db_stats(), hook auto-prune in crawl()
pyproject.toml           # add [project.optional-dependencies] postgres = ["psycopg2-binary"]
```

### Pattern 1: Optional Dependency in pyproject.toml

**What:** Declare `psycopg2-binary` as an optional extra so SQLite users don't need it.
**When to use:** Any driver that is only needed for non-default backends.

```toml
# Source: uv documentation — uv add --optional flag
[project.optional-dependencies]
postgres = ["psycopg2-binary>=2.9.12"]
```

Added via:
```bash
uv add --optional postgres psycopg2-binary
```

Install for PG use:
```bash
uv sync --extra postgres
```

### Pattern 2: Bulk DELETE with SQLAlchemy 2.0

**What:** Delete rows older than a cutoff date using a single DELETE statement.
**When to use:** Any bulk deletion — avoids loading ORM objects into memory.

```python
# Source: https://docs.sqlalchemy.org/en/20/orm/queryguide/dml.html
from sqlalchemy import delete
from apple_deals.db.models import Product
from datetime import datetime, timezone, timedelta

def prune_old_records(session, retention_days: int = 90) -> int:
    """Delete records older than retention_days. Returns count deleted."""
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=retention_days)
    stmt = delete(Product).where(Product.crawled_at < cutoff)
    result = session.execute(stmt)
    session.commit()
    return result.rowcount
```

### Pattern 3: Dry-Run Count Query

**What:** Count rows that WOULD be deleted without deleting them.
**When to use:** `--dry-run` flag in `db clean`.

```python
# Source: https://docs.sqlalchemy.org/en/20/orm/queryguide/query.html
from sqlalchemy import select, func
from apple_deals.db.models import Product
from datetime import datetime, timezone, timedelta

def count_prunable(session, retention_days: int = 90) -> int:
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=retention_days)
    return session.scalar(
        select(func.count()).select_from(Product).where(Product.crawled_at < cutoff)
    )
```

### Pattern 4: DB Stats Queries (dual-backend)

**What:** Gather row count, oldest/newest crawled_at, estimated daily growth.
**When to use:** `db stats` command.

```python
# Source: https://docs.sqlalchemy.org/en/20/core/connections.html (text())
#         https://docs.sqlalchemy.org/en/20/orm/queryguide/ (func.count/min/max)
from sqlalchemy import select, func, text
from apple_deals.db.models import Product
import os
from datetime import datetime, timezone, timedelta

def get_db_stats(session, engine) -> dict:
    total = session.scalar(select(func.count()).select_from(Product))
    oldest = session.scalar(select(func.min(Product.crawled_at)))
    newest = session.scalar(select(func.max(Product.crawled_at)))

    # Rows in last 7 days / 7 = estimated daily growth
    cutoff_7d = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=7)
    recent = session.scalar(
        select(func.count()).select_from(Product).where(Product.crawled_at >= cutoff_7d)
    )
    daily_growth = round(recent / 7, 1) if recent else 0.0

    # DB size — dialect-specific branch
    is_postgres = engine.url.drivername.startswith("postgresql")
    if is_postgres:
        size_str = session.scalar(
            text("SELECT pg_size_pretty(pg_database_size(current_database()))")
        )
    else:
        db_path = engine.url.database
        try:
            size_bytes = os.path.getsize(db_path)
            size_str = f"{size_bytes / 1024:.1f} KB"
        except FileNotFoundError:
            size_str = "unknown"

    return {
        "total_rows": total,
        "oldest": oldest,
        "newest": newest,
        "daily_growth": daily_growth,
        "db_size": size_str,
    }
```

### Pattern 5: Rich Table for Stats Output

**What:** Print stats as a formatted two-column table.
**When to use:** `db stats` command — Rich already available via Textual dep.

```python
# Source: https://rich.readthedocs.io/en/stable/tables.html
from rich.console import Console
from rich.table import Table

def print_stats(stats: dict) -> None:
    table = Table(title="Database Statistics", show_header=True)
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    table.add_row("Total rows", str(stats["total_rows"]))
    table.add_row("DB size", stats["db_size"])
    table.add_row("Oldest record", str(stats["oldest"]))
    table.add_row("Newest record", str(stats["newest"]))
    table.add_row("Est. daily growth", f"{stats['daily_growth']} rows/day")

    Console().print(table)
```

### Pattern 6: Typer --days and --dry-run Options

**What:** CLI option patterns for `db clean`.
**When to use:** Implementing `db_clean()` in `cli/main.py`.

```python
# Source: Typer 0.25.1 — verified locally
@db_app.command("clean")
def db_clean(
    days: int = typer.Option(90, "--days", help="Retention window in days (default: 90)."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview rows to delete without deleting."),
) -> None:
    """Prune records outside the retention window."""
    with get_session() as session:
        if dry_run:
            count = count_prunable(session, retention_days=days)
            typer.echo(f"Would delete {count} rows older than {days} days.")
        else:
            deleted = prune_old_records(session, retention_days=days)
            typer.echo(f"Deleted {deleted} rows older than {days} days.")
```

### Pattern 7: Auto-Prune Hook in crawl()

**What:** Call `prune_old_records()` at the end of the `crawl` command (D-05).
**When to use:** Phase 3 modifies the `crawl()` command from Phase 2.

```python
# After all stores are crawled and upsert_if_changed() calls complete:
with get_session() as session:
    pruned = prune_old_records(session)
    if pruned:
        typer.echo(f"Auto-pruned {pruned} records outside the 90-day retention window.")
```

### Neon PostgreSQL Connection String

**What:** The format Neon requires — SSL is mandatory.
**When to use:** Setting `DATABASE_URL` for Neon backend.

```
postgresql+psycopg2://<USER>:<PASSWORD>@<NEON_HOST>/<DBNAME>?sslmode=require&channel_binding=require
```

The `sslmode=require` and `channel_binding=require` parameters are required by Neon. SQLAlchemy passes them through the URL as-is to psycopg2.

[CITED: https://neon.com/docs/guides/sqlalchemy]

### Anti-Patterns to Avoid

- **Using `datetime.utcnow()` for cutoff:** Deprecated in Python 3.13. Use `datetime.now(timezone.utc).replace(tzinfo=None)` instead.
- **Using `func.now()` server-side for cutoff:** `func.now()` returns different types in SQLite (string) vs PostgreSQL (timestamptz). Always compute cutoff in Python and pass as a bind parameter.
- **Loading ORM objects before bulk DELETE:** `session.query(Product).filter(...).all()` loads all rows into memory before deleting. Use `delete(Product).where(...)` for bulk operations.
- **Checking DB size with in-memory SQLite in tests:** `engine.url.database` returns `None` for `:memory:` — guard against this in tests.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PostgreSQL dialect detection | Custom URL string parsing | `engine.url.drivername.startswith("postgresql")` | SQLAlchemy URL object handles all URL variants |
| Pretty-print table output | f-string column alignment | `rich.table.Table` | Already installed; handles terminal width, color, Unicode |
| File size formatting | Manual byte-to-KB/MB math | `pg_size_pretty()` for PG, simple math for SQLite | PG has built-in; SQLite size is small enough for KB display |
| Bulk deletion with count | ORM object loop with `session.delete()` | `delete(Model).where(...)` + `result.rowcount` | Single SQL statement; no memory overhead |

**Key insight:** All required capability is in libraries already present (SQLAlchemy, Rich, Typer). This phase is implementation-only — no new major dependencies beyond psycopg2-binary.

---

## Common Pitfalls

### Pitfall 1: Timezone-Naive DateTime Comparison Mismatch

**What goes wrong:** Pruner computes cutoff as `datetime.now(timezone.utc)` (aware), then compares to `Product.crawled_at` values that SQLite returned as naive. SQLAlchemy raises `TypeError: can't compare offset-naive and offset-aware datetimes`.

**Why it happens:** Phase 2 inserts `crawled_at = datetime.now(tz=timezone.utc)`, but `models.py` declares `DateTime` (not `DateTime(timezone=True)`). SQLite strips timezone info on roundtrip — the stored value is naive UTC. PostgreSQL similarly strips with non-timezone-aware column type.

**How to avoid:** Always compute the cutoff with `.replace(tzinfo=None)`:
```python
cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=retention_days)
```

**Warning signs:** `TypeError: can't compare offset-naive and offset-aware datetimes` during test or runtime.

### Pitfall 2: SQLite engine.url.database for In-Memory DB

**What goes wrong:** Stats command calls `os.path.getsize(engine.url.database)` — if `DATABASE_URL` is `sqlite:///:memory:` (used in tests), `engine.url.database` is `":memory:"` and `os.path.getsize` raises `FileNotFoundError` (or returns size of `/` path).

**Why it happens:** `:memory:` is a special SQLite pseudo-path, not a real file.

**How to avoid:** Wrap the `getsize` call in a try/except and return `"in-memory"` or `"N/A"` for `:memory:` databases.

**Warning signs:** Tests for `db stats` fail with unexpected errors.

### Pitfall 3: session.py get_session() Returns a New Session, Not a Context Manager

**What goes wrong:** Phase 1's `get_session()` returns `SessionLocal()` — a plain Session, not a context manager. Using it as `with get_session() as session:` raises `AttributeError: __enter__`.

**Why it happens:** `sessionmaker()` produces `Session` instances; they only support context manager protocol when used as `with SessionLocal() as session:` — not `with get_session() as session:`.

**How to avoid:** Either: (a) use `session = get_session(); try: ... finally: session.close()`, or (b) use `with SessionLocal() as session:` directly, or (c) change `get_session()` to use `contextlib.contextmanager`. Review how Phase 2 uses `get_session()` and follow the same pattern for consistency.

**Warning signs:** `AttributeError: __enter__` when first running `db clean` or `db stats`.

### Pitfall 4: psycopg2-binary Not Installed When DATABASE_URL is Set

**What goes wrong:** User sets `DATABASE_URL` to a Neon URL but hasn't installed the postgres extra — `ModuleNotFoundError: No module named 'psycopg2'` at startup.

**Why it happens:** `psycopg2-binary` is optional. SQLAlchemy tries to import it lazily when the engine is first used.

**How to avoid:** Document clearly in README/docs: "If using PostgreSQL, run `uv sync --extra postgres`". Optionally add a startup guard that checks `DATABASE_URL.startswith("postgresql")` and prints a helpful error.

**Warning signs:** `ModuleNotFoundError: No module named 'psycopg2'` when DATABASE_URL is set.

---

## Code Examples

Verified patterns from official sources:

### Bulk DELETE via SQLAlchemy 2.0

```python
# Source: https://docs.sqlalchemy.org/en/20/orm/queryguide/dml.html
from sqlalchemy import delete

stmt = delete(Product).where(Product.crawled_at < cutoff)
result = session.execute(stmt)
session.commit()
deleted_count = result.rowcount
```

### PostgreSQL DB Size Query

```python
# Source: https://docs.sqlalchemy.org/en/20/core/connections.html
from sqlalchemy import text

size_pretty = session.scalar(
    text("SELECT pg_size_pretty(pg_database_size(current_database()))")
)
```

### Rich Table Output

```python
# Source: https://rich.readthedocs.io/en/stable/tables.html
from rich.console import Console
from rich.table import Table

table = Table(title="Database Statistics")
table.add_column("Metric", style="cyan")
table.add_column("Value", style="green")
table.add_row("Total rows", str(total))
Console().print(table)
```

### SQLAlchemy Aggregate Queries (ORM 2.0 style)

```python
# Source: https://docs.sqlalchemy.org/en/20/orm/queryguide/
from sqlalchemy import select, func

total = session.scalar(select(func.count()).select_from(Product))
oldest = session.scalar(select(func.min(Product.crawled_at)))
newest = session.scalar(select(func.max(Product.crawled_at)))
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `session.query(Model).filter(...).delete()` | `session.execute(delete(Model).where(...))` | SQLAlchemy 2.0 | New style returns `CursorResult` with `rowcount`; old `.delete()` still works but is legacy |
| `datetime.utcnow()` | `datetime.now(timezone.utc)` | Python 3.12+ | `utcnow()` deprecated; use timezone-aware pattern |
| Manual column alignment for CLI output | `rich.table.Table` | Rich 1.x+ | Rich is already installed; no reason to format manually |

**Deprecated/outdated:**
- `session.query(Product).filter(Product.crawled_at < cutoff).delete()`: SQLAlchemy 1.x ORM delete — functional but legacy in 2.0. Use `delete(Product).where(...)` instead.
- `datetime.utcnow()`: Deprecated in Python 3.12, will be removed in a future version. Use `datetime.now(datetime.UTC)` or `datetime.now(timezone.utc)`.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Phase 2's `crawl` command will be fully implemented before Phase 3 runs — so `db/crud.py` exists and auto-prune hook has a place to land | Architecture Patterns (Pattern 7) | If Phase 2 is incomplete, auto-prune hook has no target; Phase 3 Plan must create crud.py if absent |
| A2 | `get_session()` usage pattern from Phase 2 is plain `Session` (not context manager) — Phase 3 should follow the same pattern | Pitfall 3 | If Phase 2 changes `get_session()` to a context manager, Pattern 6/7 code must change |

---

## Open Questions

1. **How does Phase 2's `crawl` command manage session lifecycle?**
   - What we know: Phase 2 plan imports `get_session()` from session.py; `get_session()` returns `SessionLocal()` (a plain Session). Phase 2 PLAN 02-02 shows `insert_product(session, data)` receiving a session.
   - What's unclear: Does Phase 2's crawl command open one session for the whole crawl or one per upsert? The auto-prune hook must use the same session (or a fresh one after the crawl).
   - Recommendation: Plan 03-02 should open a fresh session for auto-prune after the crawl loop completes, to avoid stale state.

2. **Neon SSL: does the connection string from the user's Neon dashboard already include `sslmode=require`?**
   - What we know: Neon's dashboard provides connection strings with `sslmode=require&channel_binding=require` already appended.
   - What's unclear: If the user pastes only the base URL without SSL params, the connection will fail.
   - Recommendation: Document in Phase 3 plan that the full Neon connection string (with SSL params) must be used as `DATABASE_URL`. Add a note in docs.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 | All | ✓ | 3.13.13 | — |
| uv | Package management | ✓ | 0.9.7 | — |
| SQLAlchemy | DB operations | ✓ | 2.0.49 | — |
| Typer | CLI | ✓ | 0.25.1 | — |
| Rich | Stats table output | ✓ | 15.0.0 (via Textual) | — |
| psycopg2-binary | PostgreSQL backend | ✗ (not installed) | — | SQLite works without it; optional dep |
| PostgreSQL/Neon | PG backend testing | ✗ (no local PG) | — | All logic testable with SQLite in-memory |

**Missing dependencies with no fallback:**
- None — all blocking dependencies are present.

**Missing dependencies with fallback:**
- `psycopg2-binary`: Not installed; added as optional dep. Full PG path cannot be tested locally without a Neon connection string (environment secret).

---

## Sources

### Primary (HIGH confidence)
- `/websites/sqlalchemy_en_20` (Context7) — create_engine URL format, PostgreSQL dialect, psycopg2 connection string
- `/websites/sqlalchemy_en_20_orm` (Context7) — bulk DELETE with `delete().where()`, ORM session queries
- `/websites/sqlalchemy_en_20_core` (Context7) — `text()` for raw SQL, `connection.scalar()`
- `/websites/rich_readthedocs_io_en_stable` (Context7) — `Table`, `Console`, column styling
- [CITED: https://neon.com/docs/guides/sqlalchemy] — Neon connection string format, SSL requirements
- [VERIFIED: pip index versions psycopg2-binary] — version 2.9.12 confirmed current as of 2026-05-08
- [VERIFIED: local Python 3.13 runtime] — `datetime.now(timezone.utc).replace(tzinfo=None)` pattern confirmed
- [VERIFIED: SQLite roundtrip test] — timezone info stripped by SQLite/SQLAlchemy DateTime (non-timezone-aware)
- [VERIFIED: uv help add] — `uv add --optional postgres psycopg2-binary` syntax confirmed

### Secondary (MEDIUM confidence)
- [CITED: https://neon.com/docs/connect/connect-securely] — `channel_binding=require` recommendation for enhanced security

### Tertiary (LOW confidence)
- None.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified against PyPI and local install
- Architecture: HIGH — session.py and models.py inspected directly; patterns from official SQLAlchemy 2.0 docs
- Pitfalls: HIGH — timezone pitfall verified with live Python test; other pitfalls from direct code inspection

**Research date:** 2026-05-08
**Valid until:** 2026-06-08 (psycopg2-binary and SQLAlchemy are stable; Neon docs stable)
