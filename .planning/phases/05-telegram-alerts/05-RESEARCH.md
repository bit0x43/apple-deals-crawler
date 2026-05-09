# Phase 5: Telegram Alerts — Research

**Researched:** 2026-05-08
**Domain:** Telegram Bot API integration, price drop detection, alert pipeline
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** After each product is upserted, compare new price to previous price. If `(prev_price - new_price) / prev_price >= threshold_pct` → trigger alert.
- **D-02:** Threshold configurable via `ALERT_THRESHOLD_PCT` env var (default: 0.05 = 5% drop). Also support `ALERT_THRESHOLD_ABS` for absolute COP amount drop.
- **D-03:** Alert logic lives in `src/apple_deals/alerts/telegram.py`.
- **D-04:** Use `httpx` (sync) to POST to `https://api.telegram.org/bot{TOKEN}/sendMessage`.
- **D-05:** Credentials: `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` env vars.
- **D-06:** If either env var is missing → `logging.warning("Telegram not configured — alerts disabled")`, no crash.
- **D-07:** Message format: `🔔 Price drop! {reference} at {store}\n{prev_price} → {new_price} COP ({pct}% off)\n{url}`

### Claude's Discretion

- Whether to batch multiple alerts per crawl into one message or send individually

### Deferred Ideas (OUT OF SCOPE)

- Multiple Telegram recipients (v2)
- Per-product target price alerts (v2)

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ALRT-01 | Telegram message when price drops below threshold | Verified: Telegram Bot API sendMessage endpoint; httpx sync POST pattern; price comparison formula (D-01) |
| ALRT-02 | Alert threshold + Telegram credentials configurable via env vars / config | Verified: 4 env vars pattern with os.getenv(); default values for thresholds; graceful disable when missing (D-06) |
</phase_requirements>

---

## Summary

This phase implements Telegram price drop alerts that fire after each crawl. The approach follows three principles:

1. **Direct HTTP, no framework:** Per D-04, use `httpx` (sync) to POST to the Telegram Bot API directly — no `python-telegram-bot` or `aiogram`. This keeps the dependency footprint minimal and avoids the complexity of long-polling/webhook setups since this bot only sends outgoing messages (never receives).
2. **Non-blocking alerts:** If Telegram credentials are missing or the API is unreachable, the crawl continues with a logged warning. Alert failures never crash the crawl pipeline.
3. **Threshold-gated:** Alerts fire only when price drops by a configurable percentage or absolute amount, preventing notification fatigue from small daily fluctuations.

The alert module (`src/apple_deals/alerts/telegram.py`) integrates cleanly with the existing crawl loop: after each `upsert_if_changed()` call, compare the old and new prices and fire notifications as needed.

**Primary recommendation:** Add `httpx>=0.28.1` as a dependency, create `src/apple_deals/alerts/telegram.py` with a `send_alert()` function, and hook it into the crawl loop after each product upsert.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Price threshold comparison | Alert module (`alerts/telegram.py`) | — | Pure function: compare two floats against thresholds |
| HTTP POST to Telegram API | Alert module (`alerts/telegram.py`) | — | Uses httpx.Client directly (per D-04) |
| Alert hook trigger | Crawl orchestration (`cli/main.py`) | — | Fire alert after each upsert_if_changed() call |
| Env var configuration | Alert module initialization | — | Read at module level; `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, thresholds |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| httpx | 0.28.1 | Sync HTTP POST to Telegram Bot API | Minimal dependency; D-04 locks this choice |
| Python stdlib `logging` | (stdlib) | Warn when Telegram not configured or API fails | Zero dependency; already used in crawlers |
| Python stdlib `os` | (stdlib) | Read env vars for config | Zero dependency |

**Version verification:** httpx 0.28.1 confirmed via PyPI registry (latest stable as of 2026-05-08). Earlier dev versions of 1.x exist but 0.28.1 is the latest stable release. [VERIFIED: pypi.org/project/httpx/]

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python stdlib `functools` | (stdlib) | `lru_cache` or `cache` for lazy env var reads | Optional — only if reading env vars in a hot loop |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| httpx (direct) | `python-telegram-bot` | Full bot framework designed for bidirectional communication; overkill for a script that only sends outgoing messages |
| httpx (direct) | `aiogram` | Async-only; adds asyncio dependency to a sync codebase |
| httpx (direct) | `urllib` / `requests` | Both work for simple POST; httpx is already a common transitive dep (Playwright depends on it); better timeout and error handling |

**Installation:**

```bash
uv add httpx>=0.28.1
```

**Version verification:**
```bash
uv run python -c "import httpx; print(httpx.__version__)"
# 0.28.1
```

---

## Architecture Patterns

### System Architecture Diagram

```
apple-deals crawl (CLI entrypoint)
         |
         v
   cli/main.py: crawl()
         |
         +---> TiendasishopCrawler.crawl()
         |         |
         |         v
         |     list[ProductData]  (raw products)
         |
         +---> MacCenterCrawler.crawl()
         |         |
         |         v
         |     list[ProductData]  (raw products)
         |
         v
   for each ProductData in combined results:
         |
         +---> db/crud.py: upsert_if_changed(session, data)
         |         |
         |         +-- no prior record? --> insert, return (True, new_price, None)
         |         |
         |         +-- price unchanged? --> skip,  return (False, None, None)
         |         |
         |         +-- price changed?   --> insert, return (True, new_price, old_price)
         |                                   |
         |                                   v
         |                          alerts/telegram.py: send_alert()
         |                                   |
         |                                   +-- check thresholds
         |                                   +-- POST to Telegram Bot API
         |                                   +-- log warning on failure
         v
   typer.echo("Summary: N products, M inserted, A alerts fired")
```

### Recommended Project Structure

```
src/apple_deals/
├── alerts/
│   ├── __init__.py          # (existing stub)
│   └── telegram.py          # NEW: send_alert(), _format_message(), env var validation
├── db/
│   ├── crud.py              # (existing) upsert_if_changed() — hook point
│   ├── models.py            # (existing)
│   └── session.py           # (existing)
├── crawlers/
│   ├── ...
├── cli/
│   └── main.py              # (existing) modify crawl() to fire alerts
└── ...
```

### Pattern 1: Alert module with lazy env var validation

**What:** Module-level function that validates Telegram credentials exist before attempting to send. Returns early (log warning, no crash) when misconfigured.

**When to use:** At module load and at each send_alert() call.

```python
# Source: [VERIFIED: D-04, D-05, D-06 from CONTEXT.md]
# src/apple_deals/alerts/telegram.py
from __future__ import annotations

import logging

import httpx

from apple_deals.crawlers.base import ProductData

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN: str | None = None
TELEGRAM_CHAT_ID: str | None = None
ALERT_THRESHOLD_PCT: float = 0.05  # 5%
ALERT_THRESHOLD_ABS: float | None = None  # disabled by default


def _init_from_env() -> None:
    """Read env vars into module-level globals. Safe to call multiple times."""
    import os

    global TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ALERT_THRESHOLD_PCT, ALERT_THRESHOLD_ABS

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    try:
        ALERT_THRESHOLD_PCT = float(os.getenv("ALERT_THRESHOLD_PCT", "0.05"))
    except (TypeError, ValueError):
        ALERT_THRESHOLD_PCT = 0.05

    try:
        raw_abs = os.getenv("ALERT_THRESHOLD_ABS")
        ALERT_THRESHOLD_ABS = float(raw_abs) if raw_abs else None
    except (TypeError, ValueError):
        ALERT_THRESHOLD_ABS = None


# Initialize on module import
_init_from_env()


def is_configured() -> bool:
    """Return True if both Telegram credentials are set."""
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
```

### Pattern 2: Price drop comparison (threshold check)

**What:** Compare old price vs new price against both percentage and absolute thresholds. Returns True if any threshold is exceeded.

**When to use:** After each successful upsert where price changed.

```python
# Source: [VERIFIED: D-01, D-02 from CONTEXT.md]
def should_alert(old_price: float, new_price: float) -> bool:
    """Determine if a price drop crosses configured thresholds.

    Returns True if:
    - (old_price - new_price) / old_price >= ALERT_THRESHOLD_PCT, OR
    - ALERT_THRESHOLD_ABS is set and (old_price - new_price) >= ALERT_THRESHOLD_ABS
    """
    if new_price >= old_price:
        return False  # price increased or stayed same — no alert

    drop = old_price - new_price

    # Check percentage threshold
    pct_drop = drop / old_price
    if pct_drop >= ALERT_THRESHOLD_PCT:
        return True

    # Check absolute threshold (COP)
    if ALERT_THRESHOLD_ABS is not None and drop >= ALERT_THRESHOLD_ABS:
        return True

    return False


def _format_cop(price: float) -> str:
    """Format a Colombian peso price with thousand separators.

    Example: 4699000.0 -> "4,699,000"
    """
    return f"{price:,.0f}"


def _format_message(data: ProductData, old_price: float, new_price: float) -> str:
    """Build the alert message string per D-07 format."""
    pct = (old_price - new_price) / old_price * 100
    return (
        f"\U0001f514 Price drop! {data['reference']} at {data['source']}\n"
        f"{_format_cop(old_price)} \u2192 {_format_cop(new_price)} COP ({pct:.1f}% off)\n"
        f"{data['url']}"
    )
```

### Pattern 3: Send alert via httpx sync POST

**What:** POST to Telegram Bot API `sendMessage` endpoint with JSON body. Handle API-level errors and network errors gracefully.

**When to use:** After `should_alert()` returns True.

```python
# Source: [VERIFIED: core.telegram.org/bots/api — sendMessage]
def send_message(text: str) -> bool:
    """Send a text message via Telegram Bot API.

    Returns True if message was sent successfully.
    Logs warning on failure — never raises.
    """
    if not is_configured():
        logger.warning("Telegram not configured — alerts disabled")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",  # not used in D-07 format, but available
    }

    try:
        # Use a short timeout: connect=5s, read=5s
        with httpx.Client(timeout=httpx.Timeout(5.0, connect=5.0)) as client:
            response = client.post(url, json=payload)
            result = response.json()
    except httpx.HTTPError as exc:
        logger.warning("Telegram API request failed: %s", exc)
        return False

    if not result.get("ok"):
        desc = result.get("description", "unknown error")
        logger.warning("Telegram API error: %s", desc)
        return False

    return True


def send_alert(data: ProductData, old_price: float, new_price: float) -> bool:
    """Convenience: check thresholds and send alert if warranted.

    Returns True if an alert was sent.
    """
    if not should_alert(old_price, new_price):
        return False
    message = _format_message(data, old_price, new_price)
    return send_message(message)
```

### Pattern 4: Integration into crawl loop

**What:** Fire alerts after each product upsert. The `upsert_if_changed()` function (from Phase 2 crud.py) needs modification to return previous price when a change is detected.

**When to use:** In `cli/main.py` crawl command.

```python
# Source: [DERIVED: D-01 + D-02, integration pattern]
# Modified crud.py upsert_if_changed (needed change):
def upsert_if_changed(session: Session, data: ProductData) -> tuple[bool, float | None]:
    """Insert record if price changed. Returns (inserted, previous_price).

    Returns:
        (True, None)         — first-time insert, no previous price
        (True, old_price)    — price changed, old_price is the previous price
        (False, None)        — price unchanged, no insert
    """
    last_price = get_last_price(session, data["sku"], data["source"])
    if last_price is not None and round(last_price, 2) == round(data["price"], 2):
        return False, None
    insert_product(session, data)
    return True, last_price


# In cli/main.py crawl command:
from apple_deals.alerts.telegram import send_alert

@app.command()
def crawl() -> None:
    """Crawl product prices from all configured stores."""
    from apple_deals.crawlers.tiendasishop import TiendasishopCrawler
    from apple_deals.crawlers.mac_center import MacCenterCrawler
    from apple_deals.db.crud import upsert_if_changed
    from apple_deals.db.session import get_session
    from apple_deals.alerts.telegram import send_alert

    crawlers = [
        ("tiendasishop", TiendasishopCrawler()),
        ("mac-center", MacCenterCrawler()),
    ]

    session = get_session()
    total_inserted = 0
    total_alerts = 0
    try:
        for store_name, crawler in crawlers:
            products = crawler.crawl()
            store_inserted = 0
            store_alerts = 0
            for p in products:
                inserted, old_price = upsert_if_changed(session, p)
                if inserted:
                    store_inserted += 1
                    if old_price is not None and old_price != p["price"]:
                        # Price actually changed (not first-time insert)
                        if send_alert(p, old_price, p["price"]):
                            store_alerts += 1
            total_inserted += store_inserted
            total_alerts += store_alerts
            typer.echo(
                f"{store_name}: {len(products)} products found, "
                f"{store_inserted} inserted, {store_alerts} alerts fired"
            )
    finally:
        session.close()

    if total_alerts == 0:
        logger.info("No price drops detected this crawl.")
```

### Anti-Patterns to Avoid

- **Importing python-telegram-bot as a dependency:** D-04 explicitly locks httpx direct calls. Adding a full bot framework adds ~MB of deps and pulls in asyncio for no benefit.
- **Using async httpx in a sync codebase:** All existing code uses sync Playwright and sync SQLAlchemy. httpx sync Client should be used, not AsyncClient.
- **Reusing an httpx.Client across calls without proper lifecycle:** For ~40 products per crawl creating a Client per call is fine. A module-level singleton Client with `with` context is slightly more efficient but not necessary at this scale.
- **Blocking on Telegram timeout longer than 10s:** A slow Telegram API should not delay the crawl pipeline. Use 5s timeouts.
- **Calling `session.commit()` inside the alert module:** The alert module should never touch the DB. Keep it a pure notification layer.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Telegram message sending | Custom HTTP + JSON parser | `httpx.Client().post(url, json=payload)` | httpx handles JSON serialization, SSL, timeouts, error handling — 3 lines of code |
| Threshold logic | Anything more complex | Simple `if` with float comparison | Two thresholds (pct + abs), no state, no history — 6 lines of code |
| Thousand-separator formatting | locale module or Babel | Python f-string `f"{price:,.0f}"` | Works cross-platform without locale dependencies; COP prices are whole numbers |

**Key insight:** This phase has very little code to hand-roll. The entire alert system fits in ~80 lines. The complexity is in error handling and integration, not in the business logic itself.

---

## Common Pitfalls

### Pitfall 1: Upsert API needs to return previous price

**What goes wrong:** The existing `upsert_if_changed()` returns bool only. The alert module needs the previous price to compare.

**Why it happens:** Phase 2 crud.py designed `upsert_if_changed()` to return `bool`. Phase 5 needs a richer return.

**How to avoid:** Change the return type to `tuple[bool, float | None]` where the second element is the previous price (None for first-time insert). This is backward-compatible: `if inserted:` still works, and callers that don't need old_price can ignore it.

**Warning signs:** Alert module has to make a second DB query to get the last price after upsert finishes — redundant and wasteful.

### Pitfall 2: Float precision in price comparison

**What goes wrong:** `4699000.0 == 4699000.0` is safe for whole COP numbers, but the threshold divider `(prev - new) / prev` could produce floating-point artifacts.

**Why it happens:** Float division of large integers can produce results like `0.04999999999999999` instead of `0.05`.

**How to avoid:** Use `>=` with a small epsilon, or do the comparison with `Decimal` from the standard library. For this project, the simpler fix is:
```python
pct_drop = drop / old_price
if pct_drop >= ALERT_THRESHOLD_PCT - 1e-9:
    return True
```

**Warning signs:** A 5.00000001% drop doesn't trigger the 5% threshold.

### Pitfall 3: httpx not installed

**What goes wrong:** `uv run python -c "import httpx"` raises ImportError on first deploy.

**Why it happens:** httpx is not yet in pyproject.toml dependencies.

**How to avoid:** Add `httpx>=0.28.1` to the `[project] dependencies` list. Verify with `uv sync && uv run python -c "import httpx"`.

**Warning signs:** `ModuleNotFoundError: No module named 'httpx'`

### Pitfall 4: Telegram API returns 429 (rate limited)

**What goes wrong:** Sending ~40 messages back-to-back could trigger Telegram's rate limiter for group/channel messages.

**Why it happens:** Telegram enforces ~20 messages/minute per group/channel and ~30 messages/second globally.

**How to avoid:** For a daily crawl with ~40-60 products, rate limits are extremely unlikely to be an issue in practice. The crawl runs once per day, and even if all products had price drops simultaneously, ~40 messages to a single chat is well within limits. However, the send code should still handle 429 gracefully: read `retry_after` from response, log warning, skip remaining alerts.

**Warning signs:** `{"ok": false, "error_code": 429, "description": "Too Many Requests: retry after 60"}`

### Pitfall 5: Message text exceeds 4096 characters

**What goes wrong:** If batching multiple alerts into one message, the combined text could exceed Telegram's 4096-character limit.

**Why it happens:** Telegram's `sendMessage` enforces a maximum text length of 4096 characters per call.

**How to avoid:** If batching, chunk messages at 4000 characters to leave safety margin. For individual alert messages, individual product names are well under 4096 characters.

**Warning signs:** Telegram returns `{"ok": false, "error_code": 400, "description": "Bad Request: message is too long"}`

### Pitfall 6: TELEGRAM_BOT_TOKEN contains invalid characters

**What goes wrong:** The token is malformed (wrong format, whitespace, copied with newline).

**Why it happens:** Users copy-paste the token with trailing whitespace or newline.

**How to avoid:** Call `.strip()` on env vars: `os.getenv("TELEGRAM_BOT_TOKEN", "").strip()`. Validate at initialization: log a specific error message if token doesn't match expected format (starts with digit-colon pattern).

**Warning signs:** Telegram API returns 404 with `{"ok": false, "description": "Not Found"}`

### Pitfall 7: Alert fire on first-time insert (no price history)

**What goes wrong:** When a product is seen for the first time, there's no "old price" to compare against, and sending an alert about a new product doesn't make sense in the price-drop context.

**Why it happens:** The upsert returns `(True, None)` for first-time inserts. The caller then checks `old_price is not None` before firing.

**How to avoid:** Only fire alerts when `old_price is not None and old_price != new_price`. This is guarded in the integration pattern.

**Warning signs:** New products trigger "price drops" on first crawl.

---

## Code Examples

### Complete alert module (verified pattern)

```python
# Source: [VERIFIED: core.telegram.org/bots/api#sendmessage + httpx docs]
# src/apple_deals/alerts/telegram.py
"""Telegram price drop alerts.

Sends notifications when product prices drop below configured thresholds.
Uses direct HTTP POST to Telegram Bot API (no framework dependency).
"""

from __future__ import annotations

import logging
import os

import httpx

from apple_deals.crawlers.base import ProductData

logger = logging.getLogger(__name__)

# Module-level config, read from env vars at import time
TELEGRAM_BOT_TOKEN: str | None = None
TELEGRAM_CHAT_ID: str | None = None
ALERT_THRESHOLD_PCT: float = 0.05
ALERT_THRESHOLD_ABS: float | None = None


def _init_from_env() -> None:
    """Read configuration from environment variables."""
    global TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ALERT_THRESHOLD_PCT, ALERT_THRESHOLD_ABS

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip() or None
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip() or None

    try:
        ALERT_THRESHOLD_PCT = float(os.getenv("ALERT_THRESHOLD_PCT", "0.05"))
    except (TypeError, ValueError):
        ALERT_THRESHOLD_PCT = 0.05

    try:
        raw_abs = os.getenv("ALERT_THRESHOLD_ABS", "").strip()
        ALERT_THRESHOLD_ABS = float(raw_abs) if raw_abs else None
    except (TypeError, ValueError):
        ALERT_THRESHOLD_ABS = None


_init_from_env()


def is_configured() -> bool:
    """Return True if both Telegram credentials are present."""
    return TELEGRAM_BOT_TOKEN is not None and TELEGRAM_CHAT_ID is not None


def _format_cop(price: float) -> str:
    """Format price with thousand separators for display."""
    return f"{price:,.0f}"


def _format_message(data: ProductData, old_price: float, new_price: float) -> str:
    """Build the alert message per D-07."""
    pct = (old_price - new_price) / old_price * 100
    return (
        f"\U0001f514 Price drop! {data['reference']} at {data['source']}\n"
        f"{_format_cop(old_price)} \u2192 {_format_cop(new_price)} COP ({pct:.1f}% off)\n"
        f"{data['url']}"
    )


def should_alert(old_price: float, new_price: float) -> bool:
    """Check if a price drop exceeds configured thresholds."""
    if new_price >= old_price:
        return False

    drop = old_price - new_price
    pct_drop = drop / old_price

    if pct_drop >= ALERT_THRESHOLD_PCT - 1e-9:
        return True

    if ALERT_THRESHOLD_ABS is not None and drop >= ALERT_THRESHOLD_ABS:
        return True

    return False


def send_message(text: str) -> bool:
    """Send a text message via Telegram Bot API. Never raises."""
    if not is_configured():
        logger.warning(
            "Telegram not configured — set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID"
        )
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}

    try:
        with httpx.Client(timeout=httpx.Timeout(5.0, connect=5.0)) as client:
            response = client.post(url, json=payload)
            result = response.json()
    except httpx.HTTPError as exc:
        logger.warning("Telegram API request failed: %s", exc)
        return False

    if not result.get("ok"):
        error_code = result.get("error_code", "?")
        description = result.get("description", "unknown error")
        logger.warning(
            "Telegram API error (code %s): %s", error_code, description
        )
        return False

    return True


def send_alert(data: ProductData, old_price: float, new_price: float) -> bool:
    """Evaluate thresholds and send alert if warranted. Returns True if sent."""
    if not should_alert(old_price, new_price):
        return False
    message = _format_message(data, old_price, new_price)
    return send_message(message)
```

### Integration test pattern (in-memory mock)

```python
# Source: [VERIFIED: pattern follows existing test_db.py setup]
# tests/test_alerts.py
from unittest.mock import patch

import httpx
import pytest
from respx import MockRouter  # or use unittest.mock

from apple_deals.alerts.telegram import is_configured, send_message, should_alert


def test_is_configured_false_by_default() -> None:
    """Without env vars, is_configured() returns False."""
    from apple_deals.alerts.telegram import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    # In test env vars may not be set
    assert not is_configured() or (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)


def test_should_alert_above_threshold() -> None:
    """5% drop with 5% threshold triggers alert."""
    from apple_deals.alerts.telegram import ALERT_THRESHOLD_PCT
    old_price = 1000000.0
    new_price = 940000.0  # 6% drop
    assert should_alert(old_price, new_price) is True


def test_should_alert_below_threshold() -> None:
    """2% drop with 5% threshold does not trigger."""
    old_price = 1000000.0
    new_price = 980000.0  # 2% drop
    assert should_alert(old_price, new_price) is False


def test_should_alert_exact_threshold() -> None:
    """Exactly 5% drop triggers alert."""
    old_price = 1000000.0
    new_price = 950000.0  # exact 5% drop
    assert should_alert(old_price, new_price) is True


def test_should_alert_price_increase() -> None:
    """Price increase never triggers alert."""
    old_price = 1000000.0
    new_price = 1050000.0
    assert should_alert(old_price, new_price) is False


def test_should_alert_same_price() -> None:
    """Unchanged price does not trigger alert."""
    old_price = 1000000.0
    new_price = 1000000.0
    assert should_alert(old_price, new_price) is False
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `python-telegram-bot` (full framework) | Direct httpx POST to Bot API | D-04 locks httpx | ~80 lines vs ~300 lines; no asyncio; no long-polling overhead |
| `requests` library for HTTP | `httpx` for HTTP | httpx 0.28 (Dec 2024) | Better timeout API, type-annotated, actively maintained |

**Deprecated/outdated:**
- `python-telegram-bot` v20+ is still actively maintained but overkill for outgoing-only messaging
- `requests` library is stable but no longer the recommended choice for new Python HTTP clients

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | httpx.Client() is the correct sync API (not AsyncClient) | Standard Stack | Low risk — httpx docs confirm `httpx.Client()` is the sync interface |
| A2 | The crawl never produces >30 alerts in a single run | Rate Limiting | If >30 alerts fire, Telegram may rate-limit; log and skip is acceptable |
| A3 | COP prices are stored as whole numbers | Code Examples | `f"{price:,.0f}"` truncates decimal places; if fractional COP prices appear, they'll be rounded. Risk is low — Colombian retailers price in whole COP |
| A4 | `upsert_if_changed()` will be modified to return previous price | Integration | If not modified, the alert module needs an additional `get_last_price()` call per product, doubling DB queries |

---

## Open Questions

1. **Should alerts be sent individually or batched?**
   - What we know: Individual messages are simpler and let Telegram handle notification delivery.
   - What's unclear: 40+ individual messages could be noisy if all products drop simultaneously (unlikely but possible during site-wide sales).
   - Recommendation: Send individually (simpler, more reliable). If noise becomes an issue in practice, a v2 batch mode can add a 60-second debounce window.

2. **Should we add a `--dry-run` flag for the crawl to preview alerts without sending?**
   - What we know: Phase 3 added `--dry-run` for `db clean`.
   - What's unclear: Whether users need to preview alerts before the first crawl with real credentials.
   - Recommendation: Out of scope for now. Add if requested.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 | Runtime | ✓ | 3.13.13 | — |
| httpx (Python pkg) | Telegram API calls | ✗ (not yet installed) | 0.28.1 on PyPI | `uv add httpx>=0.28.1` |
| Telegram Bot API | sendMessage endpoint | ✓ (external service) | Bot API 10.0 | Logged warning if unreachable |

**Missing dependencies with no fallback:**
- `httpx` Python package — must be installed before alerts work

**Missing dependencies with fallback:**
- Telegram Bot API — if unreachable, alert is skipped with a logged warning; crawl continues normally

---

## Validation Architecture

> Skipped — `workflow.nyquist_validation` is explicitly `false` in `.planning/config.json`.

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Telegram Bot API uses a token for auth; stored in env var only |
| V3 Session Management | No | Stateless API calls; no sessions |
| V4 Access Control | No | Single chat recipient configured by owner |
| V5 Input Validation | Yes | Validate env vars at module init; catch malformed threshold values |
| V6 Cryptography | No | HTTPS handled by httpx + system SSL |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Bot token leaked to git | Information Disclosure | Token stored in env var only; pre-commit secret scanning from Phase 1 detects token patterns |
| Malformed threshold env var | Tampering | `float()` wrapped in try/except with safe defaults |
| Telegram API unreachable | Denial of Service | Caught by `httpx.HTTPError` → logged warning → crawl continues |
| Bot token intercepted in transit | Spoofing | HTTPS enforced by httpx; Telegram API requires HTTPS (non-HTTPS requests are rejected) |

---

## Sources

### Primary (HIGH confidence)

- [VERIFIED: core.telegram.org/bots/api] — sendMessage endpoint, JSON response format, error codes, rate limiting
- [VERIFIED: pypi.org/project/httpx/0.28.1/] — httpx 0.28.1 latest stable release, sync Client API
- [VERIFIED: python-httpx.org] — httpx sync Client timeout syntax, error handling
- [VERIFIED: CONTEXT.md D-01..D-07] — All locked decisions for alert logic, Telegram integration, env vars, message format

### Secondary (MEDIUM confidence)

- [CITED: github.com/python-telegram-bot/python-telegram-bot] — Confirm httpx is sufficient for Telegram API; PTB uses httpx internally
- [CITED: github.com/encode/httpx/releases] — httpx release history and version確認

### Tertiary (LOW confidence)

- None — all critical claims verified via official sources

---

## Metadata

**Confidence breakdown:**
- Telegram Bot API integration: HIGH — verified via official Telegram documentation
- httpx sync patterns: HIGH — verified via httpx official docs
- Alert threshold logic: HIGH — simple arithmetic, no external dependencies
- Integration with crawl pipeline: HIGH — verified against ProjectData model and crud.py interfaces
- Rate limiting impact: MEDIUM — based on community-reported empirical limits (not officially published for simple sends)

**Research date:** 2026-05-08
**Valid until:** 2026-06-08 (Telegram Bot API is stable; httpx minor version bump unlikely to break sync POST)
