from __future__ import annotations

import logging
import os

import httpx

from apple_deals.crawlers.base import ProductData

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN: str | None = None
TELEGRAM_CHAT_ID: str | None = None
ALERT_THRESHOLD_PCT: float = 0.05
ALERT_THRESHOLD_ABS: float | None = None


def _init_from_env() -> None:
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
    return TELEGRAM_BOT_TOKEN is not None and TELEGRAM_CHAT_ID is not None


def _format_cop(price: float) -> str:
    return f"{price:,.0f}"


def _format_message(data: ProductData, old_price: float, new_price: float) -> str:
    pct = (old_price - new_price) / old_price * 100
    return (
        f"\U0001f514 Price drop! {data['reference']} at {data['source']}\n"
        f"{_format_cop(old_price)} \u2192 {_format_cop(new_price)} COP ({pct:.1f}% off)\n"
        f"{data['url']}"
    )


def should_alert(old_price: float, new_price: float) -> bool:
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
    if not is_configured():
        logger.warning("Telegram not configured \u2014 set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
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
        logger.warning("Telegram API error (code %s): %s", error_code, description)
        return False

    return True


def send_alert(data: ProductData, old_price: float, new_price: float) -> bool:
    if not should_alert(old_price, new_price):
        return False
    message = _format_message(data, old_price, new_price)
    return send_message(message)
