# Phase 1: Project Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-08
**Phase:** 1-Project Foundation
**Areas discussed:** Project layout, Secret scanning tool, DB model style, CLI skeleton depth

---

## Project Layout

| Option | Description | Selected |
|--------|-------------|----------|
| src/apple_deals/ | Modern Python best practice. Prevents accidental imports from project root. | ✓ |
| apple_deals/ (flat) | Simpler, common in smaller tools. Can shadow installed package in dev. | |

**User's choice:** src/apple_deals/

**Notes:** None — straightforward selection.

### Internal module structure

| Option | Description | Selected |
|--------|-------------|----------|
| Feature-based (crawlers/, db/, tui/, alerts/, cli/) | Each phase maps to a folder. | ✓ |
| Layer-based (models/, services/, cli/) | Technical layer split, better for larger apps. | |
| Flat | Everything at apple_deals/ level, no subfolders. | |

**User's choice:** Feature-based

---

## Secret Scanning Tool

| Option | Description | Selected |
|--------|-------------|----------|
| detect-secrets | Python-native, pip-installable, .secrets.baseline tracking, Yelp-maintained. | ✓ |
| gitleaks | Go binary, faster, 600+ rules, better for CI pipelines than dev hooks. | |

**User's choice:** detect-secrets

---

## DB Model Style

| Option | Description | Selected |
|--------|-------------|----------|
| Declarative ORM (mapped classes) | class Product(Base): ... Clean, typed, IDE-friendly. | ✓ |
| SQLAlchemy Core (Table objects) | More SQL-close, verbose, less idiomatic for a small tool. | |
| SQLModel | Pydantic-based ORM, adds a dependency, some rough edges. | |

**User's choice:** Declarative ORM

### mypy strictness

| Option | Description | Selected |
|--------|-------------|----------|
| Standard | Catches real type errors without full annotation coverage. | ✓ |
| Strict | --strict: all functions annotated, no implicit Any. More upfront work. | |

**User's choice:** Standard mode

---

## CLI Skeleton Depth

| Option | Description | Selected |
|--------|-------------|----------|
| All commands stubbed now | crawl, tui, db clean, db stats all stubbed. --help complete from day one. | ✓ |
| Entrypoint only | Each phase registers its command when implemented. --help incomplete early. | |

**User's choice:** All commands stubbed upfront

### Stub output behavior

| Option | Description | Selected |
|--------|-------------|----------|
| typer.echo + exit 1 | Explicit, CLI-idiomatic. Non-zero exit prevents CI false positives. | ✓ |
| raise NotImplementedError | Python exception with traceback. Noisy for end-users. | |
| Silent no-op | Exit 0 with no output. Could hide missing implementations. | |

**User's choice:** typer.echo("Command not yet implemented.") + raise typer.Exit(1)

---

## Claude's Discretion

None — user made explicit choices in all areas.

## Deferred Ideas

None — discussion stayed within phase scope.
