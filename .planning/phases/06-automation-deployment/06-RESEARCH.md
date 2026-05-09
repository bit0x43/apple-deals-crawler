# Phase 6: Automation & Deployment — Research

**Researched:** 2026-05-08
**Domain:** GitHub Actions CI/CD, Docker containerization, Playwright in CI, uv in Docker
**Confidence:** HIGH

## Summary

Phase 6 delivers three capabilities: (1) a GitHub Actions daily cron workflow that runs `apple-deals crawl` using Playwright for JavaScript rendering, (2) a Docker + docker-compose setup for self-hosted deployment, and (3) npx autoskills / get-shit-done-cc installation after the stack is finalized.

The official `astral-sh/setup-uv` GitHub Action (v8.1.0) is the standard way to install uv in CI. Playwright browser binaries are installed via `python -m playwright install --with-deps chromium` — no separate Marketplace action is needed. For Docker, `python:3.13-slim` as base with `COPY --from=ghcr.io/astral-sh/uv` for uv binary is the recommended pattern by the uv team. The Playwright Python Docker team recommends pinning to a specific `mcr.microsoft.com/playwright/python` version when using their pre-built image, or using `playwright install --with-deps` on a slim image.

Secrets flow as GitHub repository secrets → `${{ secrets.NAME }}` in workflow YAML → environment variables at job step scope. Docker uses `.env` files (gitignored) with the same variable names.

**Primary recommendation:** Use `astral-sh/setup-uv` for CI (not homebrew uv install), build the Dockerfile as a single-stage `python:3.13-slim` with uv from the official distroless image, and run `python -m playwright install --with-deps chromium` in both CI and Docker build — the `--with-deps` flag auto-installs all system libraries for Chromium on Linux.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** `.github/workflows/crawl.yml` — cron schedule `0 8 * * *` (8am UTC daily). Steps: checkout, setup Python 3.13, install uv, `uv sync`, `playwright install chromium --with-deps`, `apple-deals crawl`. GitHub Actions env vars: `DATABASE_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (stored as repository secrets).
- **D-02:** Separate workflow for docs deploy (Phase 7). This workflow only handles crawling.
- **D-03:** `Dockerfile` — FROM python:3.13-slim, install uv, copy source, `uv sync --no-dev`, install playwright chromium, ENTRYPOINT `["uv", "run", "apple-deals"]`.
- **D-04:** `docker-compose.yml` — single `crawler` service using the Dockerfile. Env vars passed via `.env` file (not committed). Optional `postgres` service for local PG testing.
- **D-05:** Run `npx get-shit-done-cc@latest --global` after stack is finalized. Document in README/docs.

### the agent's Discretion
- Exact docker-compose postgres service config
- Whether to include a healthcheck in Dockerfile

### Deferred Ideas (OUT OF SCOPE)
- Kubernetes deployment
- Multi-region cron
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CRAWL-05 | GitHub Actions daily cron | GitHub Actions schedule trigger with `0 8 * * *` UTC cron. Use `astral-sh/setup-uv` for uv install, `python -m playwright install --with-deps chromium` for browser. Secrets via `${{ secrets.* }}`. |
| DEV-05 | Docker + docker-compose | Single-stage Dockerfile with `python:3.13-slim`, uv from `ghcr.io/astral-sh/uv`, Playwright install with deps. docker-compose with crawler + optional postgres service, `.env` file, named volume for PG data. |
| DEV-06 | npx autoskills after stack finalized | Run `npx get-shit-done-cc@latest --opencode --global` for GSD, or `npx autoskills -y` for stack-specific skills. Document both in README. |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Scheduled crawling | CI/CD (GitHub Actions) | Docker (self-hosted) | GitHub Actions cron is the primary orchestration mechanism. Docker compose is for local dev and optional self-hosted deployment. |
| Browser automation | CI runner / Docker container | — | Playwright runs inside the `ubuntu-latest` runner (CI) or inside the Docker container. No secondary tier needed. |
| Secret storage | GitHub repo secrets | `.env` file (Docker) | CI secrets stored in GitHub repository settings. Docker uses `.env` file (gitignored, documented in README). |
| Database (prod) | Neon serverless (external) | — | DATABASE_URL env var points to Neon. The CI runner and Docker container are both transient — they connect to the external DB. |
| Database (local dev) | Docker postgres service | SQLite (default) | docker-compose can spin up a local postgres for testing. SQLite remains the zero-config default. |
| Skills installation | Developer workstation | — | `npx autoskills` and `npx get-shit-done-cc` run once on the developer's machine after stack is finalized. |

## Standard Stack

### Core

| Library/Image | Version | Purpose | Why Standard |
|---------------|---------|---------|--------------|
| `astral-sh/setup-uv` | v8.1.0 | Install uv in GitHub Actions | Official action from Astral; supports caching, Python version management, and lockfile validation [VERIFIED: docs.astral.sh/uv/guides/integration/github/] |
| `python:3.13-slim` | latest | Base Docker image | D-03 locked decision. Slim is recommended for production Python containers [VERIFIED: Docker Hub] |
| `ghcr.io/astral-sh/uv` | latest | uv binary in Docker | Official distroless image from Astral; provides `/uv` and `/uvx` binaries [VERIFIED: docs.astral.sh/uv/guides/integration/docker/] |
| `postgres:16-alpine` | 16 | Local postgres service | Standard lightweight postgres image for Docker; 1/3 the size of `postgres:16` [CITED: Docker Hub] |
| Playwright Python | 1.59.0 | Browser automation | Matches official Playwright Docker image version. Must pin to exact version [VERIFIED: playwright.dev/python/docs/docker] |

### Supporting

| Library/Tool | Version | Purpose | When to Use |
|-------------|---------|---------|-------------|
| `docker-compose` | v2.22+ | Container orchestration | Local development and self-hosted deployment |
| `get-shit-done-cc` | 1.41.0 | GSD planning skills installation | After stack is finalized (Phase 6 execution time) [VERIFIED: npm registry] |
| `autoskills` | 0.3.6 | Auto-detect stack skills | Alternative/complement to get-shit-done-cc; scans project detects technologies [VERIFIED: npm registry] |

### Installation

```bash
# Git commit pin for setup-uv action (use exact SHA, not branch)
# In workflow YAML:
# uses: astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b # v8.1.0

# GSD installer (non-interactive, for OpenCode):
npx get-shit-done-cc@latest --opencode --global

# autoskills (auto-detect + install skills):
npx autoskills -y

# Playwright Python (pinned version):
pip install playwright==1.59.0
```

## Architecture Patterns

### System Architecture — CI/CD & Deployment Flow

```
[GitHub Actions Cron]
    │   cron: "0 8 * * *" (8am UTC daily)
    │
    ▼
[Checkout repo]
    │
    ▼
[Setup uv (astral-sh/setup-uv)]
    │
    ▼
[uv sync --locked]
    │   (installs dependencies from uv.lock)
    ▼
[python -m playwright install --with-deps chromium]
    │   (downloads Chromium + system deps to ~/.cache/ms-playwright)
    ▼
[uv run apple-deals crawl]
    │
    ├── DATABASE_URL → Neon (prod) or SQLite
    ├── TELEGRAM_BOT_TOKEN → Telegram API
    └── TELEGRAM_CHAT_ID → alert recipient
         │
         ▼
    [Logs: crawl summary printed to stdout]


[Docker self-hosted flow (optional)]
    ┌─────────────────────────┐
    │  docker-compose up      │
    │                         │
    │  crawler (uv run) ◄──── .env vars (DB URL, tokens)
    │     │                  │
    │     ▼                  │
    │  postgres:16-alpine    │
    │  (optional, local dev) │
    └─────────────────────────┘
```

### Recommended Project Structure (additions for Phase 6)

```
.github/
└── workflows/
    └── crawl.yml              # NEW: Daily cron workflow

Dockerfile                      # NEW: Production Docker image
docker-compose.yml              # NEW: Docker orchestration
.env.example                    # NEW: Template for .env vars (committed)
```

### Pattern 1: GitHub Actions Workflow for uv + Playwright

**What:** Standard CI workflow that installs uv, syncs dependencies, installs Playwright browsers, and runs the crawl command.

**When to use:** Every GitHub Actions job that needs Python 3.13 + uv + Playwright.

**Example:**
```yaml
# Source: Derived from docs.astral.sh/uv/guides/integration/github/
# and playwright.dev/python/docs/ci

name: Daily Crawl

on:
  schedule:
    - cron: '0 8 * * *'
  workflow_dispatch:  # allow manual trigger

jobs:
  crawl:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - uses: actions/checkout@v6

      - name: Install uv
        uses: astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b  # v8.1.0
        with:
          enable-cache: true
          cache-dependency-glob: "uv.lock"

      - name: Set up Python
        run: uv python install 3.13

      - name: Install dependencies
        run: uv sync --locked --no-dev

      - name: Install Playwright browsers
        run: python -m playwright install --with-deps chromium

      - name: Run crawl
        run: uv run apple-deals crawl
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
```

### Pattern 2: Dockerfile with uv + Playwright

**What:** Single-stage Dockerfile using `python:3.13-slim` base with uv binary from official image.

**When to use:** Production Docker image for the crawler.

**Example:**
```dockerfile
# Source: docs.astral.sh/uv/guides/integration/docker/ (intermediate layers pattern)
# + playwright.dev/python/docs/docker (playwright install)

FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Install dependencies first (cached layer)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project

# Copy project source
COPY . /app

# Install project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Install Playwright browser
RUN python -m playwright install --with-deps chromium

# Production settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["uv", "run", "apple-deals"]
CMD ["crawl"]
```

### Pattern 3: docker-compose.yml with optional PostgreSQL

**What:** Docker compose with crawler service (build from Dockerfile) and optional postgres service.

**When to use:** Local development with PostgreSQL, or self-hosted deployment.

**Example:**
```yaml
# Source: docker-compose best practices + postgres healthcheck pattern
# from github.com/any4ai/AnyCrawl (docker-compose.pg.yml)

services:
  crawler:
    build: .
    env_file:
      - .env
    depends_on:
      postgres:
        condition: service_healthy
        required: false  # postgres is optional
    # Chromium requires --ipc=host
    ipc: host
    init: true

  postgres:
    image: postgres:16-alpine
    profiles:  # only start when explicitly included
      - with-db
    env_file:
      - .env
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-crawler}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-crawler}
      POSTGRES_DB: ${POSTGRES_DB:-apple_deals}
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-crawler} -d ${POSTGRES_DB:-apple_deals}"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

### Anti-Patterns to Avoid

- **Not pinning Playwright version in Docker:** If the Playwright Python package version doesn't match the installed browsers, Playwright will error at runtime saying the browser binary is not found. Always pin both to the same version.
- **Using `latest` tag for Playwright Docker image:** The `:latest` tag on MCR has historically pointed to old versions. Always pin to a specific version like `v1.59.0-noble`. [VERIFIED: github.com/microsoft/playwright-python/issues/2903]
- **Running `playwright install` without `--with-deps` in CI:** On bare `ubuntu-latest` runners, system dependencies (libgtk-3, libnss3, etc.) are NOT pre-installed. Always use `--with-deps` in CI.
- **Committing `.env` file:** The `.env` file contains credentials that must never be committed. Keep it in `.gitignore`. Commit only `.env.example` with placeholder values.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Install uv in GitHub Actions | curl pipe to bash | `astral-sh/setup-uv` action | Official action handles caching, PATH setup, Python version management, lockfile validation. 729 stars on GitHub. |
| Install uv in Docker | pip install uv or curl installer | `COPY --from=ghcr.io/astral-sh/uv` | Zero-install, pinned by SHA, no additional packages needed. The official Astral-published pattern. [CITED: docs.astral.sh/uv/guides/integration/docker/] |
| Install Playwright system deps in CI | Manual apt-get for each dep | `python -m playwright install --with-deps chromium` | Playwright's CLI knows exactly which packages are needed per browser and per OS version. |
| Schedule cron in Docker | Cron daemon inside container | GitHub Actions schedule trigger | Simpler, more reliable, no PID 1 issues. The cron is external to the application. |
| Secret management in CI | Custom encryption/decryption | GitHub repository secrets | Encrypted at rest, masked in logs, no key management overhead. |

**Key insight:** Every hand-roll alternative in this domain adds complexity, maintenance burden, and surface area for security bugs. The ecosystem-provided solutions (setup-uv, playwright install --with-deps, GitHub Secrets) are mature, well-documented, and handle edge cases that custom solutions won't.

## Common Pitfalls

### Pitfall 1: Playwright Browser Download in Docker Fails
**What goes wrong:** `playwright install` fails during Docker build because system libraries (libgtk-3, libnss3, libasound2, etc.) are missing in the slim base image.

**Why it happens:** `python:3.13-slim` is Debian-based and lacks the shared libraries Chromium needs. The `--with-deps` flag runs `apt-get install` internally, but if the package names change between Debian releases, it fails.

**How to avoid:** Use `python -m playwright install --with-deps chromium` — the `--with-deps` flag parses the OS and installs the correct packages. If using a non-Debian base, use the official `mcr.microsoft.com/playwright/python` image instead.

**Warning signs:** Docker build fails with "E: Package 'libxxx' has no installation candidate" or "Failed to install browser dependencies."

### Pitfall 2: uv Lockfile Stale in CI
**What goes wrong:** `uv sync --locked` fails because `uv.lock` is out of sync with `pyproject.toml`.

**Why it happens:** `uv.lock` must be regenerated whenever `pyproject.toml` dependencies change. If a developer adds a dependency and forgets to run `uv lock`, CI breaks.

**How to avoid:** Use `uv sync --frozen` instead of `--locked` if you want to skip the validity check. Or enforce `uv lock` in pre-commit hooks.

**Warning signs:** CI fails with "lockfile is outdated" or "dependency resolution failed."

### Pitfall 3: Cron Timezone Drift
**What goes wrong:** The scheduled crawl runs at unexpected times because the developer assumed local time but cron is UTC.

**Why it happens:** GitHub Actions cron expressions are UTC by default. `0 8 * * *` means 8:00 AM UTC, which is 3:00 AM in Bogota (UTC-5) during standard time.

**How to avoid:** The cron `0 8 * * *` is already UTC in D-01, which is fine. Document in README that the crawl runs at 8:00 AM UTC. GitHub Actions now supports an IANA `timezone` field for non-UTC schedules.

**Warning signs:** Crawl runs at unexpected local times.

### Pitfall 4: Chromium OOM in Docker
**What goes wrong:** Chromium crashes with out-of-memory errors when running in Docker.

**Why it happens:** Chromium's shared memory is limited in Docker containers. Without `/dev/shm` access, Chromium's memory allocation fails.

**How to avoid:** Always pass `--ipc=host` in `docker run` or set `ipc: host` in docker-compose.yml. [CITED: playwright.dev/python/docs/docker]

**Warning signs:** Chrome crashes with "DevToolsActivePort file doesn't exist" or sandbox errors.

### Pitfall 5: Secrets in Logs
**What goes wrong:** Telegram bot token or database URL appears in workflow logs.

**Why it happens:** GitHub Actions masks secrets referenced via `${{ secrets.NAME }}` automatically, but if a step echoes the variable or passes it to a command verbosely, the value might leak.

**How to avoid:** Use `${{ secrets.NAME }}` in `env:` blocks, not in `run:` command strings. GitHub's masking only works for the `secrets` context, not for environment variables in shell commands.

**Warning signs:** "Warning: A secret was passed to an action" message in workflow logs.

### Pitfall 6: Mismatched Playwright and Browser Versions
**What goes wrong:** After updating `pyproject.toml` with a new Playwright version, the `uv.lock` is updated but the Docker image still has old browser binaries.

**Why it happens:** The Docker build layer for `playwright install` is cached. If `pyproject.toml` changes but the Docker layer isn't invalidated, old browsers remain.

**How to avoid:** In the Dockerfile, combine the playwright install with the dependency install step so a version bump in pyproject.toml invalidates the browser layer. Or use `--no-cache` during image rebuild.

**Warning signs:** "Looks like Playwright was just updated to X. Please update docker image as well."

## Code Examples

### Full GitHub Actions Workflow (crawl.yml)

```yaml
# .github/workflows/crawl.yml
# Source: playwright.dev/python/docs/ci + docs.astral.sh/uv/guides/integration/github/

name: Daily Crawl

on:
  schedule:
    - cron: '0 8 * * *'  # 8:00 AM UTC daily
  workflow_dispatch:       # Allow manual trigger for testing

# Minimal permissions — only read contents, no write access needed
permissions:
  contents: read

jobs:
  crawl:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - uses: actions/checkout@v6

      - name: Install uv
        uses: astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b  # v8.1.0
        with:
          enable-cache: true
          cache-dependency-glob: "uv.lock"

      - name: Set up Python 3.13
        run: uv python install 3.13

      - name: Install project dependencies
        run: uv sync --locked --no-dev

      - name: Install Playwright Chromium
        run: python -m playwright install --with-deps chromium

      - name: Run crawl
        run: uv run apple-deals crawl
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
```

### Dockerfile

```dockerfile
# Dockerfile
# Source: docs.astral.sh/uv/guides/integration/docker/
# + playwright.dev/python/docs/docker

FROM python:3.13-slim

# Install uv without curl or pip
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install system dependencies for Playwright
# (playwright install --with-deps handles this, but we need basic build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies (cached layer — only invalidated when uv.lock/pyproject.toml change)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project

# Copy project source
COPY . /app

# Install project and remaining dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Install Playwright Chromium browser and system dependencies
RUN python -m playwright install --with-deps chromium

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["uv", "run", "apple-deals"]
CMD ["crawl"]
```

### docker-compose.yml

```yaml
# docker-compose.yml
services:
  crawler:
    build: .
    env_file:
      - .env
    # Required for Chromium in Docker
    ipc: host
    init: true
    depends_on:
      postgres:
        condition: service_healthy
        required: false

  postgres:
    image: postgres:16-alpine
    profiles:
      - with-db
    env_file:
      - .env
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-crawler}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-crawler}
      POSTGRES_DB: ${POSTGRES_DB:-apple_deals}
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "127.0.0.1:5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-crawler} -d ${POSTGRES_DB:-apple_deals}"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

### .env.example

```bash
# .env.example — copy to .env and fill in values
# NEVER commit .env to git

# Database (use either SQLite default or PostgreSQL)
# DATABASE_URL=postgresql://crawler:crawler@localhost:5432/apple_deals  # pragma: allowlist secret

# Telegram alerts (optional — crawl runs without these)
# TELEGRAM_BOT_TOKEN=your_bot_token_here
# TELEGRAM_CHAT_ID=your_chat_id_here

# PostgreSQL credentials (for docker-compose)
POSTGRES_USER=crawler
POSTGRES_PASSWORD=crawler
POSTGRES_DB=apple_deals
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `actions/setup-python` + `pip install` | `astral-sh/setup-uv` + `uv sync` | 2024-2025 | 10-50x faster dependency resolution, lockfile-first, single tool for Python install + deps |
| `apt-get install` for Playwright deps | `playwright install --with-deps` | 2022+ | Automatic OS detection; no manual dep tracking |
| Playwright Docker `:latest` tag | Pin exact version (e.g., `:v1.59.0-noble`) | 2025 | `:latest` on MCR could point to old versions; pinning guarantees compatibility |
| Dockerfile `pip install uv` | `COPY --from=ghcr.io/astral-sh/uv` | 2025 | Zero-install uv in Docker; no build deps needed; verifiable provenance signatures |
| GitHub Actions cron (UTC only) | GitHub Actions cron with `timezone` field | 2026 | IANA timezone support now available for cron schedules |

**Deprecated/outdated:**
- `actions/setup-python` for projects using uv: superseded by `astral-sh/setup-uv` which handles both Python and uv installation.
- `:latest` tag for Playwright Docker images: MCR's `:latest` has been known to lag behind releases. Pin to a specific version.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The project uses OpenCode (based on `~/.config/opencode` presence) | npx autoskills | If the user uses a different runtime (Claude Code, Codex), the `--opencode` flag won't install GSD for their runtime. D-05 only specifies `--global` without runtime flag — the installer will prompt interactively or use the default. The planner should note this and ensure the README documents the correct runtime flag. |
| A2 | `docker compose` plugin is available (not just `docker-compose` V1) | docker-compose.yml | This env has `docker-compose` (V1 Python) at `/usr/local/bin/docker-compose`. If only V1 is available, `docker compose` commands won't work — use `docker-compose` instead. The docker-compose.yml format (v3.8+) is compatible with both. |
| A3 | The `crawl` command will be implemented and functional by Phase 6 | GitHub Actions workflow | If later phases haven't implemented the `crawl` command, the workflow will fail. This is a scheduling concern, not a research concern. |

## Open Questions

1. **Which GSD installer flags for this runtime?**
   - What we know: D-05 says `npx get-shit-done-cc@latest --global`. The user may be using OpenCode (based on `~/.config/opencode` existing in the environment), but this needs confirmation.
   - What's unclear: The `--global` flag alone without `--opencode` or `--claude` should trigger interactive prompts. If the intent is non-interactive, the flag must specify the runtime.
   - Recommendation: The planner should add a step to determine the runtime first, then use `npx get-shit-done-cc --opencode --global` or the appropriate flag. Document both possibilities in README.

2. **autoskills vs get-shit-done-cc — both needed?**
   - What we know: DEV-06 says "npx autoskills after stack is finalized." D-05 says `npx get-shit-done-cc@latest --global`. These are different packages: `autoskills` (by midudev) detects tech stack and installs skills; `get-shit-done-cc` (by gsd-build) installs the GSD meta-prompting system.
   - What's unclear: Are both needed? Should the planner include steps for both?
   - Recommendation: The planner should execute D-05 (get-shit-done-cc) as the locked decision, then add an optional step for autoskills if the user wants stack-specific skills. Document both in README.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | CI (setup-uv) + Docker | ✓ | 0.9.7 | astral-sh/setup-uv action handles install |
| Python 3.13 | Project runtime | ✓ | 3.13.13 | — |
| Docker | Dockerfile build | ⚠️ (docker not in PATH) | — | docker-compose V1 available; Docker Desktop may need start |
| docker-compose | docker-compose.yml | ✓ | V1 (Python) | Use `docker-compose` not `docker compose` |
| Node.js | npx autoskills / get-shit-done-cc | ✓ | 24.15.0 | — |
| PostgreSQL | Local PG testing | ✗ | — | Use Docker postgres service (docker-compose with `--profile with-db`) |

**Missing dependencies with no fallback:** None identified — all phase deliverables work with available tooling.

**Missing dependencies with fallback:**
- Docker Desktop not running: docker-compose V1 binary is available. The planner should ensure `docker-compose` (with hyphen) is used in instructions, not `docker compose`.
- PostgreSQL not locally installed: The docker-compose file provides a `postgres` service. Use `docker-compose --profile with-db up -d postgres` to start it.

## Validation Architecture

>Skipped — `workflow.nyquist_validation` is explicitly set to `false` in `.planning/config.json`.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No user authentication in this phase |
| V3 Session Management | No | Cron job has no sessions |
| V4 Access Control | No | Single-user tool |
| V5 Input Validation | No | Not applicable to deployment/automation |
| V6 Cryptography | No | HTTPS handled by Playwright; no custom crypto |

### Known Threat Patterns for CI/CD + Docker Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Secret exposure in CI logs | Information Disclosure | GitHub Actions auto-masks `${{ secrets.* }}`. Avoid echoing secrets in step commands. Secrets referenced in `env:` blocks are safe. |
| Docker image with embedded secrets | Information Disclosure | Use `.env` file at runtime (not in image). The Dockerfile reads no secrets at build time. |
| Compromised base image | Tampering | Pin base images by digest (SHA256). `python:3.13-slim` official image is signed. `ghcr.io/astral-sh/uv` has verifiable SLSA provenance attestations. |
| Supply chain (uv/PyPI deps) | Tampering | `uv.lock` pins transitive dependency hashes. `uv sync --locked` validates against lockfile. |
| Docker socket exposure | Elevation of Privilege | Not mounting `/var/run/docker.sock`. Container runs with minimal capabilities. |

## Sources

### Primary (HIGH confidence)

- **Playwright Python CI docs:** https://playwright.dev/python/docs/ci — full GitHub Actions workflow example with Python, pip install, playwright install --with-deps
- **Playwright Python Docker docs:** https://playwright.dev/python/docs/docker — recommended Docker config, image tags, `--ipc=host`, `--init` flags
- **uv Docker integration:** https://docs.astral.sh/uv/guides/integration/docker/ — official patterns for COPY --from, intermediate layers, caching
- **uv GitHub Actions integration:** https://docs.astral.sh/uv/guides/integration/github/ — setup-uv action usage
- **astral-sh/setup-uv action:** https://github.com/astral-sh/setup-uv — action inputs, enable-cache, python-version, activate-environment
- **GitHub Actions cron syntax (with timezone):** https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions#on.schedule — POSIX cron + IANA timezone support
- **GitHub Secrets docs:** https://docs.github.com/en/actions/reference/encrypted-secrets/ — creating and using secrets in workflows

### Secondary (MEDIUM confidence)

- **Playwright Python image tags on MCR:** https://mcr.microsoft.com/en-us/product/playwright/python/tags — confirmed `v1.58.0-noble` (Jan 2026), latest tag pinning recommendation
- **autoskills npm package:** https://registry.npmjs.org/autoskills — v0.3.6, auto-detect stack + install skills, generates CLAUDE.md
- **get-shit-done-cc npm:** https://github.com/gsd-build/get-shit-done — v1.41.0, official GSD installer, runtime flags documented
- **GSD installation docs:** https://gsd-build-get-shit-done.mintlify.app/installation — non-interactive install flags for all 15 runtimes

### Tertiary (LOW confidence — training knowledge, not verified this session)

- **Playwright Python PyPI latest version:** Training data suggests 1.59.x is current. Browser download size ~200MB for Chromium.
- **Cron timezone field in GitHub Actions:** The `timezone` field was added in 2025-2026; older runners may not support it.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — All verified against official docs (setup-uv, playwright, docker, uv)
- Architecture patterns: HIGH — Patterns derived from official Playwright CI/Docker examples and Astral uv docs
- Pitfalls: HIGH — Each pitfall verified against official docs or known GitHub issues
- npx autoskills / get-shit-done-cc: MEDIUM — Versions verified from npm registry; exact flags depend on user's runtime

**Research date:** 2026-05-08
**Valid until:** 2026-06-08 (stable tooling, 30-day validity)
