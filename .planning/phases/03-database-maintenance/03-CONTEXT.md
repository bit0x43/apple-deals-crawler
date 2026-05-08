# Phase 3: Database & Maintenance - Context

**Gathered:** 2026-05-08
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped)

<domain>
## Phase Boundary

Add PostgreSQL backend (via DATABASE_URL env var), 90-day rolling-window auto-pruner, and implement the `db clean` / `db stats` CLI commands. Same SQLAlchemy models, same session.py — just a different engine when DATABASE_URL is set. No schema changes.
</domain>

<decisions>
## Implementation Decisions

### PostgreSQL Support
- **D-01:** `session.py` already reads `DATABASE_URL` env var; when set, use it as the engine URL directly. When unset, fall back to `sqlite:///apple_deals.db`. No code change needed — just verify it works with psycopg2/asyncpg driver.
- **D-02:** Add `psycopg2-binary` as an optional dependency in pyproject.toml (`[project.optional-dependencies] postgres = ["psycopg2-binary"]`). SQLite works without it.

### Pruner
- **D-03:** `db clean` deletes `Product` rows where `crawled_at < now() - timedelta(days=retention_days)`. Default retention = 90 days, configurable via `--days` flag.
- **D-04:** `--dry-run` flag: query and print count of rows that WOULD be deleted, no actual DELETE.
- **D-05:** Auto-prune (DB-03) runs automatically at the end of each `crawl` command run.

### Stats Command
- **D-06:** `db stats` prints: total row count, DB size (file size for SQLite, pg_database_size for PG), oldest crawled_at, newest crawled_at, estimated daily growth (rows in last 7 days / 7).

### Claude's Discretion
- Exact SQL/ORM query for DB size (SQLite vs PostgreSQL branch)
- Whether to use Rich table formatting for stats output

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/apple_deals/db/models.py` — Product model with crawled_at column
- `src/apple_deals/db/session.py` — get_session(), init_db(), DATABASE_URL logic already in place
- `src/apple_deals/cli/main.py` — db clean and db stats stubs ready to implement

</code_context>

<specifics>
## Specific Ideas
- Use Rich for stats output (already a dependency via Textual)
- Neon serverless PostgreSQL is the target production host
</specifics>

<deferred>
## Deferred Ideas
- Alembic migrations (not needed — schema is stable after Phase 2)
- Per-store stats breakdown (Phase 4 TUI handles visualization)
</deferred>
