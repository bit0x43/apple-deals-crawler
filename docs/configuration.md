# Configuration

The application is configured through environment variables. No configuration files needed.

## Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | (SQLite: `apple_deals.db`) | PostgreSQL connection string for production deployments. Omit for local SQLite. |
| `TELEGRAM_BOT_TOKEN` | No | -- | Telegram bot token for price drop alerts. Required for alert functionality. |
| `TELEGRAM_CHAT_ID` | No | -- | Target chat ID for Telegram alerts. Required alongside bot token. |
| `ALERT_THRESHOLD_PCT` | No | `0.05` | Minimum price drop percentage to trigger an alert (0.05 = 5%). |
| `ALERT_THRESHOLD_ABS` | No | -- | Minimum absolute price drop in COP to trigger an alert. |

## Database Backend

By default, the app uses a local SQLite database (`apple_deals.db`). For production deployments,
set `DATABASE_URL` to a PostgreSQL connection string.

!!! tip "Neon PostgreSQL"
    [Neon](https://neon.tech) offers a free PostgreSQL tier that works well with the daily GitHub Actions cron. Neon suspends idle databases, keeping costs at zero for daily crawl workloads.

## Telegram Alerts

To enable price drop notifications, set both `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.

!!! warning "Both required"
    Alerts only work when both `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set. If either is missing, the crawl runs normally with a logged warning.

## Alert Thresholds

The alert system fires when either threshold is crossed:

- **Percentage threshold** (`ALERT_THRESHOLD_PCT`, default 5%): fires when `(old_price - new_price) / old_price >= threshold`
- **Absolute threshold** (`ALERT_THRESHOLD_ABS`): fires when `old_price - new_price >= threshold` in COP

If both are set, alerts fire when either condition is met.
