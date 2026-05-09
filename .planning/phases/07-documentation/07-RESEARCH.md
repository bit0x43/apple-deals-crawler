# Phase 7: Documentation — Research

**Researched:** 2026-05-08
**Domain:** MkDocs + Material documentation site
**Confidence:** HIGH

## Summary

Phase 7 builds a documentation site for `apple-deals-crawler` using MkDocs with the Material theme, deployed to GitHub Pages via GitHub Actions. The site covers installation, CLI reference, configuration, and self-hosting.

**Primary recommendation:** Use `mkdocs-material==9.7.6` with `mkdocs.yml` at the project root, five doc pages in `docs/`, and GitHub Actions deploy via `mkdocs gh-deploy --force`. Add `mkdocs-typer2==0.3.0` for auto-generated CLI reference from the Typer app — eliminates manual sync and keeps the reference accurate as commands evolve.

**Key findings:**
- MkDocs Material 9.7.6 is the latest release (2026-03-19). It is now in **maintenance mode** (bug fixes until Nov 2026), but perfectly suitable for a v1 docs site. [VERIFIED: PyPI, CHANGELOG]
- `mkdocs-typer2` 0.3.0 (2026-04-23) auto-generates CLI reference from Typer apps — actively maintained, works with Typer 0.25.1 (project's version). [VERIFIED: PyPI]
- GitHub Actions deploy uses `mkdocs gh-deploy --force` with `actions/checkout@v4` and `fetch-depth: 0`. [CITED: squidfunk.github.io/mkdocs-material/publishing-your-site]
- The project uses `uv` for dependency management; `mkdocs-material` should go in a `[dependency-groups] dev` group or a dedicated `docs` group in pyproject.toml.
- MkDocs 1.6.1 ships as a dependency of mkdocs-material 9.7.6 — no separate install needed.

---

## User Constraints (from CONTEXT.md)

### Locked Decisions

#### MkDocs Setup
- **D-01:** `mkdocs.yml` at project root. Theme: `material`. Site name: `apple-deals-crawler`. Repo URL pointing to GitHub.
- **D-02:** Doc pages: `index.md` (overview), `installation.md`, `cli-reference.md`, `configuration.md`, `self-hosting.md`.
- **D-03:** Add `mkdocs-material` to dev dependencies in pyproject.toml.

#### Content Coverage (DOCS-02)
- **D-04:** Installation: `uv sync`, `playwright install chromium`, first run.
- **D-05:** CLI reference: all commands with flags — `crawl`, `tui`, `db clean [--dry-run] [--days N]`, `db stats`.
- **D-06:** Configuration: all env vars — `DATABASE_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `ALERT_THRESHOLD_PCT`, `ALERT_THRESHOLD_ABS`.
- **D-07:** Self-hosting: Docker + docker-compose setup, GitHub Actions secrets.

#### GitHub Actions Deploy (DOCS-03)
- **D-08:** `.github/workflows/docs.yml` — on push to main, run `mkdocs gh-deploy --force`. Uses `actions/checkout` with fetch-depth 0 for correct git history.

### the agent's Discretion
- Exact MkDocs Material color scheme / palette
- Whether to include a `mkdocs.yml` plugins section (search is included by default)

### Deferred Ideas (OUT OF SCOPE)
- API reference auto-generation (mkdocstrings) — not needed for a CLI tool
- Versioned docs — out of scope for v1

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DOCS-01 | MkDocs + Material theme, deployable to GitHub Pages | mkdocs-material 9.7.6 confirmed; GitHub Actions workflow template available |
| DOCS-02 | Docs cover installation, CLI reference, configuration, self-hosting | 5-page nav structure recommended; mkdocs-typer2 for auto CLI ref |
| DOCS-03 | GitHub Actions workflow auto-deploys docs on push to main | Workflow template with `gh-deploy --force`, caching, git config provided |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| mkdocs-material | 9.7.6 | Documentation theme & framework | De facto standard for Python project docs; built-in search, social cards, navigation features |
| mkdocs | 1.6.1 | Static site generator | Automatically installed as dependency of mkdocs-material; no separate install |
| mkdocs-typer2 | 0.3.0 (optional) | Auto-generate CLI reference from Typer app | Actively maintained; uses native Click walking (not deprecated legacy); produces tables |

**Installation (pyproject.toml):**
```toml
[dependency-groups]
dev = [
    # ... existing dev deps ...
    "mkdocs-material>=9.7.6",
    "mkdocs-typer2[mkdocs]>=0.3.0",
]
```

Or with `uv` directly:
```bash
uv add --group dev mkdocs-material
uv add --group dev "mkdocs-typer2[mkdocs]"
```

**Version verification:**
```bash
$ uv run python -c "import mkdocs; print(mkdocs.__version__)"
1.6.1
$ uv run python -c "import mkdocs_material; print(mkdocs_material.__version__)"
9.7.6
```

### Plugins (built into mkdocs-material)

| Plugin | Default | Purpose |
|--------|---------|---------|
| `search` | Enabled by default | Full-text search across all pages |
| `social` | Disabled by default | Generates social card preview images (requires system deps: cairo, pango) |

> **On social cards:** The `social` plugin requires system-level image processing libraries (`libcairo`, `libpango`, `libffi`). On macOS these need `brew install cairo pango gdk-pixbuf libffi`. On GitHub Actions, they need `apt-get install`. For a dev-tool docs site, social cards are nice-to-have but not essential. The plugin can be enabled with `enabled: !ENV [CI, false]` to only generate in CI. [CITED: squidfunk.github.io/mkdocs-material/plugins/social]

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| mkdocs-typer2 | Manual CLI reference in markdown | Simpler (no extra dep) but drifts from code; fine if CLI is stable. mkdocs-typer2 recommended because this project's CLI is evolving. |
| mkdocs-typer2 | typer utils docs CLI command | Typer's built-in command outputs markdown but requires manual copy-paste into docs; doesn't stay in sync. |

---

## Architecture Patterns

### System Architecture Diagram

```
┌────────────────────────────────────────────────────────┐
│                     mkdocs.yml                          │
│  (config: theme, nav, plugins, markdown_extensions)     │
└──────────┬─────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────┐    ┌────────────────────────────┐
│    docs/             │    │    pyproject.toml           │
│  ├── index.md        │    │  (dependency: mkdocs-       │
│  ├── installation.md │───▶│   material, mkdocs-typer2)  │
│  ├── cli-reference.md│    └────────────────────────────┘
│  ├── configuration.md│
│  └── self-hosting.md │              │
└──────────┬───────────┘              │
           │                          │
           ▼                          ▼
    ┌──────────────────┐     ┌──────────────────┐
    │  mkdocs build    │     │  GitHub Actions  │
    │  → site/         │     │  (docs.yml)      │
    └──────────────────┘     └────────┬─────────┘
                                      │ push to main
                                      ▼
                           ┌──────────────────────┐
                           │  mkdocs gh-deploy    │
                           │  → gh-pages branch   │
                           │  → GitHub Pages      │
                           │  (https://<user>.    │
                           │   github.io/apple-   │
                           │   deals-crawler/)    │
                           └──────────────────────┘
```

**Flow:** Developer edits markdown in `docs/` + config in `mkdocs.yml`. On push to `main`, GitHub Actions workflow installs dependencies, runs `mkdocs gh-deploy --force`, which builds the site and pushes the output to the `gh-pages` branch. GitHub Pages serves from that branch.

### Recommended Project Structure

```
project-root/
├── docs/
│   ├── assets/
│   │   └── images/          # Screenshots, diagrams (if needed)
│   ├── stylesheets/
│   │   └── extra.css        # Optional theme overrides
│   ├── index.md             # Overview / landing page
│   ├── installation.md      # Installation guide
│   ├── cli-reference.md     # CLI commands reference
│   ├── configuration.md     # Environment variables reference
│   └── self-hosting.md      # Docker + GitHub Actions self-hosting
├── .github/
│   └── workflows/
│       └── docs.yml         # GitHub Actions deploy workflow
├── mkdocs.yml               # MkDocs configuration (project root)
└── ...
```

### Navigation (recommended for mkdocs.yml)

```yaml
nav:
  - Overview: index.md
  - Installation: installation.md
  - CLI Reference: cli-reference.md
  - Configuration: configuration.md
  - Self-Hosting: self-hosting.md
```

This flat structure is appropriate for a small 5-page docs site. Sections or tabs are unnecessary overhead until the site grows to 10+ pages.

### Pattern 1: Typer CLI Reference Auto-Generation

**What:** Use `mkdocs-typer2` to automatically generate CLI reference docs from the Typer app definition. The plugin walks the Click command tree and renders commands, arguments, options, and help text as formatted tables.

**When to use:** Any MkDocs site documenting a Typer CLI. Ensures the CLI reference is always synchronized with the actual command definitions.

**Example (docs/cli-reference.md):**
```markdown
# CLI Reference

`apple-deals` is the main entrypoint for the application.

::: mkdocs-typer2
    :module: apple_deals.cli.main
    :name: apple-deals
    :pretty: true
    :engine: native
```

**mkdocs.yml plugin registration:**
```yaml
plugins:
  - search
  - mkdocs-typer2
```

**Key requirement:** The `mkdocs-typer2` plugin imports the Typer app module. This means the full project and its dependencies must be installed when building docs. Works fine with `uv run mkdocs build` or `pip install -e .` in CI.

### Pattern 2: Code Blocks with Copy Button

**What:** Enable a one-click copy button on all code blocks. Essential for installation commands and configuration examples.

**Configuration (mkdocs.yml):**
```yaml
theme:
  features:
    - content.code.copy
```

### Pattern 3: Admonitions for Callouts

**What:** Use Material-style admonitions for notes, warnings, and tips — improves scannability of installation and configuration pages.

```markdown
!!! tip "Using SQLite (default)"
    No configuration needed. The app creates the database file on first run.

!!! warning "Telegram Alerts"
    `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` must both be set for alerts to work.
    Missing credentials produce a logged warning — the crawl still runs normally.
```

**Configuration (mkdocs.yml):**
```yaml
markdown_extensions:
  - admonition
  - pymdownx.details
  - pymdownx.superfences
```

### Anti-Patterns to Avoid

- **Deeply nested navigation** — A 5-page site doesn't need sections or tabs. Keep nav flat.
- **Social cards enabled without system deps** — The `social` plugin will crash at build time if `cairo`/`pango` aren't installed. Either disable it or guard with `enabled: !ENV [CI, false]`.
- **Overriding theme defaults unnecessarily** — The Material default palette (indigo primary, blue accent) is professional and readable. Don't customize colors unless there's a brand requirement.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Documentation site | Custom HTML/CSS site generator | MkDocs + Material | MkDocs is Python-native, has built-in search, generates clean static HTML, trivial GitHub Pages deploy |
| CLI reference docs | Manually copy-paste command outputs | mkdocs-typer2 | Keeps CLI reference in sync with code; auto-updates when commands change; supports all Typer features |
| Search | Custom JS search | Built-in `search` plugin | Comes free with MkDocs; uses lunr.js; works offline; no external services |

**Key insight:** Documentation infrastructure is a solved problem. The building blocks (MkDocs + Material + gh-deploy) are mature, well-documented, and widely used across the Python ecosystem. Focus on content, not tooling.

---

## Runtime State Inventory

> This section omitted — Phase 7 is a greenfield documentation phase. No rename, refactor, or migration involved.

---

## Common Pitfalls

### Pitfall 1: Broken Internal Links
**What goes wrong:** Links between pages break silently. MkDocs defaults to warnings, not errors.
**Why it happens:** Renaming/moving doc pages without updating cross-references.
**How to avoid:** Use `mkdocs build --strict` locally before committing. This converts all link warnings to errors.
**Warning signs:** `WARNING -  Doc file 'foo.md' contains a link to 'bar.md' which is not found` during build.

### Pitfall 2: Version Pinning for Reproducible Builds
**What goes wrong:** CI builds break when `mkdocs-material` releases a breaking change.
**Why it happens:** Installing latest unpinned: `pip install mkdocs-material` gets whatever is newest.
**How to avoid:** Pin the major version in pyproject.toml (`mkdocs-material>=9.7.6,<10`) or use `pip freeze` to lock exact versions. The GitHub Actions cache key already helps with week-level cache, but pinning prevents surprises.
**Warning signs:** CI docs workflow starts failing after a new mkdocs-material release.

### Pitfall 3: Missing Image Processing Dependencies for Social Cards
**What goes wrong:** `mkdocs build` or `mkdocs gh-deploy` crashes with `OSError: cannot load library 'cairo'` or similar.
**Why it happens:** The `social` plugin requires `libcairo`, `libpango`, and `libffi` at the system level.
**How to avoid:** Either (a) don't enable the `social` plugin, or (b) guard it with `enabled: !ENV [CI, false]` so it only runs in CI where system deps are installed via `apt-get`.
**Warning signs:** Build crashes with library load errors.

### Pitfall 4: site_url Not Set
**What goes wrong:** Social cards generate with incorrect URLs; `sitemap.xml` has relative paths.
**Why it happens:** `site_url` defaults to empty in mkdocs.yml.
**How to avoid:** Always set `site_url: https://<user>.github.io/apple-deals-crawler/` (or custom domain). Required by the social plugin and sitemap generation.
**Warning signs:** Social card previews link to `file://` paths or broken URLs.

### Pitfall 5: gh-deploy Push Conflicts
**What goes wrong:** `mkdocs gh-deploy --force` fails with `[rejected] gh-pages -> gh-papers (fetch first)`.
**Why it happens:** The gh-pages branch was modified elsewhere (another workflow, manual deploy, or stale local copy).
**How to avoid:** Use `--force` flag (already in D-08). Ensure `actions/checkout@v4` has `fetch-depth: 0` (already in D-08). Only run deploy from CI, never locally.
**Warning signs:** `error: failed to push some refs to 'https://github.com/...'` in CI logs.

### Pitfall 6: mkdocs-typer2 Module Import Failures
**What goes wrong:** `mkdocs build` fails with `ModuleNotFoundError: No module named 'apple_deals'` when using mkdocs-typer2.
**Why it happens:** The plugin imports the Typer app at build time. If the project isn't installed or dependencies are missing, the import fails.
**How to avoid:** Always run `pip install -e .` or `uv sync` before `mkdocs build` in CI. The workflow must install the full project, not just mkdocs-material.

---

## Code Examples

### mkdocs.yml (recommended full configuration)

```yaml
# yaml-language-server: $schema=https://squidfunk.github.io/mkdocs-material/schema.json

site_name: apple-deals-crawler
site_description: Track daily Apple Mac prices from Colombian retailers
site_url: https://<your-username>.github.io/apple-deals-crawler/
repo_url: https://github.com/<your-username>/apple-deals-crawler
repo_name: apple-deals-crawler
edit_uri: edit/main/docs/

theme:
  name: material
  palette:
    # Light mode
    - scheme: default
      primary: indigo
      accent: blue
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    # Dark mode
    - scheme: slate
      primary: indigo
      accent: blue
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  features:
    - content.code.copy
    - content.code.annotate
    - navigation.footer
    - navigation.instant
    - navigation.instant.prefetch
    - navigation.tracking
    - search.highlight
    - search.share
    - search.suggest

plugins:
  - search
  - mkdocs-typer2

markdown_extensions:
  - admonition
  - pymdownx.details
  - pymdownx.superfences
  - pymdownx.highlight:
      anchor_linenums: true
      line_spans: __span
      pygments_lang_class: true
  - pymdownx.inlinehilite
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.snippets
  - toc:
      permalink: true

nav:
  - Overview: index.md
  - Installation: installation.md
  - CLI Reference: cli-reference.md
  - Configuration: configuration.md
  - Self-Hosting: self-hosting.md

extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/<your-username>/apple-deals-crawler

copyright: Copyright &copy; 2026 apple-deals-crawler

# Strict mode for local builds: mkdocs build --strict
# Uncomment to fail on warnings:
# strict: true
```

### GitHub Actions Workflow (.github/workflows/docs.yml)

```yaml
name: docs

on:
  push:
    branches:
      - main
    paths:
      - docs/**
      - mkdocs.yml
      - pyproject.toml
  workflow_dispatch:

permissions:
  contents: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Configure Git Credentials
        run: |
          git config user.name github-actions[bot]
          git config user.email 41898282+github-actions[bot]@users.noreply.github.com

      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv sync --group dev

      - name: Build and deploy docs
        run: uv run mkdocs gh-deploy --force
```

> **Note:** The `paths` filter is optional — without it, docs deploy on every push to main. The filter prevents unnecessary deploys when only source code changes.

### Docs Page Starter: index.md

```markdown
# apple-deals-crawler

Track daily Apple Mac prices from Colombian retailers — from your terminal.

## Features

- **Automated crawling** — Daily price collection via GitHub Actions cron
- **Dual database** — SQLite for local development, PostgreSQL for production
- **Interactive TUI** — Browse catalog and price history with Textual
- **Telegram alerts** — Get notified when prices drop below your thresholds
- **Docker support** — Deploy with docker-compose for always-on monitoring

## Quick Start

```bash
# Install the package
uv sync

# Install Playwright browsers
playwright install chromium

# Run your first crawl
uv run apple-deals crawl

# Open the interactive TUI
uv run apple-deals tui
```

## Supported Stores

| Store | URL |
|-------|-----|
| TiendaShoP | [co.tiendasishop.com](https://co.tiendasishop.com/) |
| Mac Center | [mac-center.com](https://mac-center.com/) |
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| mkdocs-material feature releases | Maintenance mode (bug fixes only) | 9.7.0 (2025-11-11) | No new features planned; security patches until Nov 2026. Still standard for Python docs. |
| mkdocs-typer (legacy) | mkdocs-typer2 (active fork) | 0.1.0 (2024-10-25) | Original `mkdocs-typer` unmaintained. `mkdocs-typer2` actively supports latest Typer features including native Click walking. |
| Social cards via external tool | Built-in `social` plugin | mkdocs-material 8.5.0 | No external tooling needed. Plugin is built-in and configurable. |
| `gh-deploy` (direct push to gh-pages) | GitHub Actions + Pages deployment | MkDocs 1.6+ | Newer approach uses `actions/upload-pages-artifact` + `actions/deploy-pages` instead of direct branch push. Simpler: `gh-deploy --force` still works fine. |

**Deprecated/outdated:**
- `mkdocs-typer` (original, not `mkdocs-typer2`): Unmaintained for over a year, incompatibilities with Typer >= 0.12. Replaced by `mkdocs-typer2`.
- The `projects` and `typeset` plugins in mkdocs-material: Deprecated since 9.7.0, considered "architectural dead ends." [CITED: mkdocs-material CHANGELOG]

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The project's GitHub username is `<your-username>` (placeholder not yet filled) | mkdocs.yml example, GitHub Pages URL | CI deploy will succeed but docs host at wrong URL until corrected |
| A2 | The Typer app's module path (`apple_deals.cli.main`) will remain stable | CLI Reference section | If the module is renamed, mkdocs-typer2 directive must be updated |

**If this table is empty:** All claims in this research were verified or cited — no user confirmation needed.

---

## Open Questions

1. **Should social cards be enabled?**
   - What we know: Built-in `social` plugin generates preview images for social media sharing. Requires system deps (cairo, pango).
   - What's unclear: Whether the benefit justifies the dependency complexity for a dev-tool CLI project.
   - Recommendation: Skip for v1. The default Open Graph fallback (title + description) is adequate. Enable in a follow-up if needed.

2. **Should docs deploy on every push to main, or only when docs/ changes?**
   - What we know: D-08 doesn't specify a `paths` filter. Deploying on every push means the docs workflow runs even for pure code changes (trivial, ~30s penalty).
   - What's unclear: Whether the developer wants CI to rebuild docs on every push or only relevant changes.
   - Recommendation: Include a `paths` filter (`docs/**`, `mkdocs.yml`, `pyproject.toml`) to skip unnecessary doc builds. The workflow can always be triggered manually via `workflow_dispatch`.

---

## Environment Availability

> This phase has no external runtime dependencies beyond Python packages managed by uv. MkDocs generates static HTML with no database, external service, or system binary requirements (unless social cards are enabled, which is not recommended for v1). All dependencies are declared in pyproject.toml and resolved by uv sync.

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python >=3.13 | mkdocs build | ✓ | 3.13.13 | — |
| uv | Installing deps, building | ✓ | 0.9.7 | pip |
| mkdocs-material | Docs build | ✓ (via uv sync) | 9.7.6 | — |
| mkdocs-typer2 | CLI ref auto-gen | ✓ (via uv sync) | 0.3.0 | Manual markdown |

**Missing dependencies with no fallback:** None

**Missing dependencies with fallback:** None

---

## Validation Architecture

> Skipped — `workflow.nyquist_validation` is explicitly `false` in `.planning/config.json`.

---

## Security Domain

> Static documentation site with no authentication, user input, or dynamic content. MkDocs generates flat HTML files from markdown. No security controls are needed beyond standard GitHub Pages configuration (repository-level Pages settings, workflow permissions scoped to `contents: write`).

### Applicable ASVS Categories

None applicable. This is a static documentation site — no authentication, session management, access control, input validation, or cryptography is involved.

### Known Threat Patterns

None — static content only.

---

## Sources

### Primary (HIGH confidence)
- **[PyPI: mkdocs-material 9.7.6](https://pypi.org/project/mkdocs-material/)** — Version verification, dependencies, release history
- **[PyPI: mkdocs-typer2 0.3.0](https://pypi.org/project/mkdocs-typer2/)** — Installation, configuration, module path requirement, engine options
- **[MkDocs Material: Publishing your site](https://squidfunk.github.io/mkdocs-material/publishing-your-site/)** — GitHub Actions workflow template
- **[MkDocs Material: Creating your site](https://squidfunk.github.io/mkdocs-material/creating-your-site/)** — Minimal mkdocs.yml config, schema.json
- **[MkDocs Material: Navigation setup](https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/)** — Navigation features (instant, tabs, sections, index pages)
- **[MkDocs Material: Code blocks](https://squidfunk.github.io/mkdocs-material/reference/code-blocks/)** — Syntax highlighting, copy button, annotations
- **[MkDocs Material: Admonitions](https://squidfunk.github.io/mkdocs-material/reference/admonitions/)** — Note/warning/tip blocks, collapsible details
- **[MkDocs Material: Content tabs](https://squidfunk.github.io/mkdocs-material/reference/content-tabs/)** — Tabbed content sections
- **[MkDocs Material: Changing colors](https://squidfunk.github.io/mkdocs-material/setup/changing-the-colors/)** — Palette configuration, light/dark toggle
- **[MkDocs Material: Social cards](https://squidfunk.github.io/mkdocs-material/setup/setting-up-social-cards/)** — Social plugin setup, image processing deps
- **[MkDocs Material: Social plugin details](https://squidfunk.github.io/mkdocs-material/plugins/social/)** — Guard with `enabled: !ENV [CI, false]`
- **[MkDocs: Deploying your docs](https://www.mkdocs.org/user-guide/deploying-your-docs/)** — gh-deploy documentation, project vs user pages
- **[mkdocs-material CHANGELOG](https://github.com/squidfunk/mkdocs-material/blob/master/CHANGELOG)** — Maintenance mode announcement, version history
- **[mkdocs-typer2 GitHub](https://github.com/syn54x/mkdocs-typer2)** — Plugin documentation, examples, engine options
- **uv dry-run install verification** — Confirmed mkdocs-material 9.7.6 + mkdocs 1.6.1 dependency chain
- **Project source inspection** — Typer app at `src/apple_deals/cli/main.py`, `app` variable, version 0.25.1

### Secondary (MEDIUM confidence)
- **[MkDocs Discussion #2369](https://github.com/mkdocs/mkdocs/discussions/2369)** — gh-deploy GitHub Actions patterns, push conflict resolution
- **[MkDocs Issue #4068](https://github.com/mkdocs/mkdocs/issues/4068)** — Proposed deprecation of gh-deploy in favor of GitHub Actions Pages deployment
- **[MkDocs PR #4101](https://github.com/mkdocs/mkdocs/pull/4101)** — Fix for `-v --strict` anchor validation bug (merged 2026-04-10)
- **[MkDocs Material Discussion #6640](https://github.com/squidfunk/mkdocs-material/discussions/6640)** — Broken link checking strategies, strict mode

---

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — Verified via PyPI, uv dry-run, and official docs
- Architecture patterns: **HIGH** — Based on official MkDocs Material docs and established Python ecosystem conventions
- Pitfalls: **HIGH** — Directly from official docs, changelogs, and community discussions

**Research date:** 2026-05-08
**Valid until:** 2026-11-30 (based on mkdocs-material maintenance window; re-check if extending beyond Nov 2026)
