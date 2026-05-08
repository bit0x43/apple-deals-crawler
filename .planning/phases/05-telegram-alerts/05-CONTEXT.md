# Phase 5: Telegram Alerts - Context

**Gathered:** 2026-05-08
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped)

<domain>
## Phase Boundary

Detect price drops below a configurable threshold after each crawl and send a Telegram message via the Bot API. Credentials and threshold configured via env vars. Missing credentials = logged warning, no crash.
</domain>

<decisions>
## Implementation Decisions

### Alert Logic
- **D-01:** After each product is upserted, compare new price to previous price. If `(prev_price - new_price) / prev_price >= threshold_pct` → trigger alert.
- **D-02:** Threshold configurable via `ALERT_THRESHOLD_PCT` env var (default: 0.05 = 5% drop). Also support `ALERT_THRESHOLD_ABS` for absolute COP amount drop.
- **D-03:** Alert logic lives in `src/apple_deals/alerts/telegram.py`.

### Telegram Integration
- **D-04:** Use `httpx` (sync) to POST to `https://api.telegram.org/bot{TOKEN}/sendMessage`.
- **D-05:** Credentials: `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` env vars.
- **D-06:** If either env var is missing → `logging.warning("Telegram not configured — alerts disabled")`, no crash.
- **D-07:** Message format: `🔔 Price drop! {reference} at {store}\n{prev_price} → {new_price} COP ({pct}% off)\n{url}`

### Claude's Discretion
- Whether to batch multiple alerts per crawl into one message or send individually

</decisions>

<code_context>
## Existing Code Insights
- `src/apple_deals/alerts/__init__.py` — stub module ready
- `src/apple_deals/db/crud.py` — upsert_if_changed() returns old+new price (hook point for alerts)
</code_context>

<deferred>
## Deferred Ideas
- Multiple Telegram recipients (v2)
- Per-product target price alerts (v2)
</deferred>
