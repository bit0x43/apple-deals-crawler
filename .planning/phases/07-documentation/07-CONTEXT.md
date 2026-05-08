# Phase 7: Documentation - Context

**Gathered:** 2026-05-08
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped)

<domain>
## Phase Boundary

MkDocs + Material theme docs site covering installation, CLI reference, configuration, and self-hosting. GitHub Actions workflow deploys to GitHub Pages on push to main.
</domain>

<decisions>
## Implementation Decisions

### MkDocs Setup
- **D-01:** `mkdocs.yml` at project root. Theme: `material`. Site name: `apple-deals-crawler`. Repo URL pointing to GitHub.
- **D-02:** Doc pages: `index.md` (overview), `installation.md`, `cli-reference.md`, `configuration.md`, `self-hosting.md`.
- **D-03:** Add `mkdocs-material` to dev dependencies in pyproject.toml.

### Content Coverage (DOCS-02)
- **D-04:** Installation: `uv sync`, `playwright install chromium`, first run.
- **D-05:** CLI reference: all commands with flags — `crawl`, `tui`, `db clean [--dry-run] [--days N]`, `db stats`.
- **D-06:** Configuration: all env vars — `DATABASE_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `ALERT_THRESHOLD_PCT`, `ALERT_THRESHOLD_ABS`.
- **D-07:** Self-hosting: Docker + docker-compose setup, GitHub Actions secrets.

### GitHub Actions Deploy (DOCS-03)
- **D-08:** `.github/workflows/docs.yml` — on push to main, run `mkdocs gh-deploy --force`. Uses `actions/checkout` with fetch-depth 0 for correct git history.

### Claude's Discretion
- Exact MkDocs Material color scheme / palette
- Whether to include a `mkdocs.yml` plugins section (search is included by default)

</decisions>

<deferred>
## Deferred Ideas
- API reference auto-generation (mkdocstrings) — not needed for a CLI tool
- Versioned docs — out of scope for v1
</deferred>
