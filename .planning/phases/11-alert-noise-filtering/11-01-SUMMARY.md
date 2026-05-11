---
plan: "11-01"
status: complete
verification: all_pass
---

# Summary: Plan 11-01 — Alert Noise Filtering

Added `in_stock` gating to the Telegram alert pipeline to suppress false-positive alerts
for out-of-stock products.

## What was done

- **Task 1:** Added `if not data.get("in_stock", True): return False` guard at start of
  `send_alert()` in `telegram.py` — suppresses price-drop alerts for OOS products
- **Task 2:** Added same guard to `send_high_memory_alert()` — suppresses high-memory alerts
  for OOS products
- **Task 3:** Added 4 new tests:
  - `test_send_alert_suppresses_out_of_stock`
  - `test_send_alert_fires_for_in_stock`
  - `test_send_high_memory_alert_suppresses_out_of_stock`
  - `test_send_high_memory_alert_fires_for_in_stock`

## Files modified

- `src/apple_deals/alerts/telegram.py`
- `tests/test_alerts.py`

## Verification

- ruff: all checks passed
- mypy: no issues found
- pytest: 86 passed (4 new tests)

## Impact

- Out-of-stock products no longer trigger price-drop alerts
- Out-of-stock products no longer trigger high-memory alerts
- Backward compatible — missing `in_stock` field defaults to True (alert fires)
- User's 17 false-positive alerts problem is now fixed
