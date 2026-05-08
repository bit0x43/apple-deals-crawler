# Phase 1: Project Foundation - Context

**Gathered:** 2026-05-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish the repo structure, dev tooling (pre-commit hooks), SQLite DB models via SQLAlchemy ORM, and a fully-stubbed Typer CLI entrypoint — everything subsequent phases build on. No business logic, no scrapers, no TUI rendering.

</domain>

<decisions>
## Implementation Decisions

### Project Layout
- **D-01:** Use `src/` layout — package lives at `src/apple_deals/`, not at project root. Prevents accidental shadowing of the installed package during development.
- **D-02:** Feature-based internal structure inside `apple_deals/`: `crawlers/`, `db/`, `tui/`, `alerts/`, `cli/` submodules. Each maps to a future phase. No layer-based splitting.

### Pre-commit Tooling
- **D-03:** Secret scanning via `detect-secrets` (not gitleaks). Python-native, installs via uv/pip with no binary dependencies. Generates a `.secrets.baseline` file to track known non-secrets. Pre-commit hook is first-class.
- **D-04:** Ruff for lint + format (DEV-02). mypy for type checking (DEV-03) in **standard mode** (not strict). Standard mode catches real errors without requiring annotations everywhere; strictness can be tightened per-phase.
- **D-05:** Trailing whitespace, end-of-file newline, and large-file checks for DEV-04 (standard `pre-commit-hooks` entries).

### DB Models
- **D-06:** SQLAlchemy Declarative ORM — `class Product(Base): ...` style with typed columns. Not SQLAlchemy Core (Table objects) and not SQLModel. Supports both SQLite and PostgreSQL through the same model definitions.
- **D-07:** Phase 1 only defines the `Product` model (the core record schema: reference, sku, memory, storage, color, price, url, source, crawled_at). No migration tooling yet — Phase 3 adds PostgreSQL and can introduce Alembic if needed.

### CLI Skeleton
- **D-08:** All CLI commands stubbed in Phase 1 so `--help` is complete from day one (CLI-03). Commands to scaffold: `crawl`, `tui`, `db clean`, `db stats`.
- **D-09:** Stub output style: `typer.echo("Command not yet implemented.")` followed by `raise typer.Exit(1)`. Non-zero exit prevents CI from treating a stub call as success.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project & Requirements
- `.planning/ROADMAP.md` — Phase 1 goal, requirements (DEV-01..04, DB-01, CLI-03), and success criteria
- `.planning/REQUIREMENTS.md` — Full v1 requirement definitions with IDs
- `.planning/PROJECT.md` — Key decisions, constraints, and tech stack rationale

### Tech Stack (no external docs yet — stack defined in PROJECT.md)
- No external ADRs or specs exist. All constraints are captured in `.planning/PROJECT.md` and decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None yet — greenfield project.

### Established Patterns
- None yet — this phase establishes the patterns all subsequent phases follow.

### Integration Points
- `pyproject.toml` — uv project config with `[project.scripts] apple-deals = "apple_deals.cli.main:app"` entry point (to be created in this phase).
- `.pre-commit-config.yaml` — pre-commit hooks config (to be created in this phase).

</code_context>

<specifics>
## Specific Ideas

- No specific UI references or "I want it like X" moments — standard Python CLI project conventions apply.
- `apple-deals` is the CLI command name (hyphenated). Python module is `apple_deals` (underscored).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1-Project Foundation*
*Context gathered: 2026-05-08*
