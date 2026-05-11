# Phase 11: Alert Noise Filtering — Context

**Gathered:** 2026-05-12
**Status:** Ready for planning

<domain>
## Problem Statement

The Telegram alert pipeline fires false-positive price-drop notifications for products that
are out of stock. When a product goes OOS and its price changes simultaneously, the pipeline
treats it as a legitimate price drop and sends a Telegram alert — even though the user cannot
purchase the product.

The user received 17 alerts today, all of which were false positives caused by this bug.
</domain>

<root_cause>
## Root Cause

The alert pipeline in `src/apple_deals/cli/main.py` **never checks `p.get("in_stock", True)`**
before calling `send_alert()` or `send_high_memory_alert()`.

The critical decision path:

1. Crawler returns `ProductData` with `in_stock` set from Shopify API
2. `upsert_if_changed()` inserts new record, returns `(True, old_price)` when price or stock changes
3. `cli/main.py` checks: `if old_price is not None and old_price != p["price"]:` → fires alert
4. **No `in_stock` gate anywhere in this path**

Same gap for high-memory alerts via `send_high_memory_alert()` — fires unconditionally.
</root_cause>

<affected_code>
## Affected Code

- `src/apple_deals/cli/main.py` — crawl pipeline calls `send_alert()` and `send_high_memory_alert()` without `in_stock` check
- `src/apple_deals/alerts/telegram.py` — `send_alert()` and `send_high_memory_alert()` do not inspect `in_stock` status
</affected_code>

<false_positive_vectors>
## False-Positive Vectors

| Scenario | Price Drop Alert? | High-Memory Alert? |
|----------|------------------|-------------------|
| Product goes OOS, price drops | ✅ FIRES (false) | ✅ FIRES (false) if >= 24GB |
| Product goes OOS, price = 0 | ✅ FIRES (false) | — |
| Product goes OOS, price unchanged | ❌ Correctly suppressed | ✅ FIRES (false) if >= 24GB |
| Product first seen, already OOS | ❌ Correctly suppressed | ✅ FIRES (false) if >= 24GB |
| Product in stock, price drops | ✅ FIRES (correct) | ✅ FIRES (correct) if >= 24GB |
</false_positive_vectors>

<open_questions>
## Open Questions for Research

1. **Suppress or annotate?** Should OOS products be completely excluded from alerts, or should
   the alert message include an "⚠ Out of Stock" notice and still fire?

2. **Re-stock alerts?** Should there be a separate notification when an OOS product comes back
   in stock (regardless of price change)?

3. **High-memory alerts and stock** — should high-memory alerts also gate on `in_stock`, or
   are they informational enough to keep regardless?

4. **Timing** — what's the optimal behavior when a product briefly goes OOS and comes back?
   Should there be a grace period?

5. **Alert message format** — should we add stock status to alert messages even for in-stock
   products?
</open_questions>

<research_needed>
## Research Needed

- [ ] Verify the exact `in_stock` behavior from both Shopify API crawlers
- [ ] Understand what "available: false" means in practice (temporarily OOS vs discontinued)
- [ ] Review Telegram message format for stock annotation
- [ ] Consider edge cases: pre-order products, discontinued products, temporary OOS
</research_needed>

<files_to_read>
## Files to Read Before Planning

- `src/apple_deals/cli/main.py` — crawl pipeline with alert calls
- `src/apple_deals/alerts/telegram.py` — `send_alert()`, `send_high_memory_alert()`, `_format_message()`
- `src/apple_deals/crawlers/tiendasishop.py` — `in_stock` from Shopify API
- `src/apple_deals/crawlers/mac_center.py` — `in_stock` from Shopify API
- `src/apple_deals/db/crud.py` — `upsert_if_changed()` stock tracking
</files_to_read>
