# Phase 6: Automation & Deployment - Context

**Gathered:** 2026-05-08
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped)

<domain>
## Phase Boundary

GitHub Actions daily cron workflow that runs `apple-deals crawl`, Docker + docker-compose setup for self-hosted deployment, and npx autoskills installation for GSD planning skills.
</domain>

<decisions>
## Implementation Decisions

### GitHub Actions
- **D-01:** `.github/workflows/crawl.yml` — cron schedule `0 8 * * *` (8am UTC daily). Steps: checkout, setup Python 3.13, install uv, `uv sync`, `playwright install chromium --with-deps`, `apple-deals crawl`. GitHub Actions env vars: `DATABASE_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (stored as repository secrets).  # pragma: allowlist secret
- **D-02:** Separate workflow for docs deploy (Phase 7). This workflow only handles crawling.

### Docker
- **D-03:** `Dockerfile` — FROM python:3.13-slim, install uv, copy source, `uv sync --no-dev`, install playwright chromium, ENTRYPOINT `["uv", "run", "apple-deals"]`.
- **D-04:** `docker-compose.yml` — single `crawler` service using the Dockerfile. Env vars passed via `.env` file (not committed). Optional `postgres` service for local PG testing.

### npx autoskills
- **D-05:** Run `npx get-shit-done-cc@latest --global` after stack is finalized. Document in README/docs.

### Claude's Discretion
- Exact docker-compose postgres service config
- Whether to include a healthcheck in Dockerfile

</decisions>

<deferred>
## Deferred Ideas
- Kubernetes deployment (out of scope)
- Multi-region cron (out of scope)
</deferred>
