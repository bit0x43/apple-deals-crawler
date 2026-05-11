from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest

from apple_deals.alerts.telegram import (
    _format_cop,
    _format_message,
    is_configured,
    send_alert,
    send_message,
    should_alert,
)
from apple_deals.crawlers.base import ProductData


def _make_product(price: float = 1000000.0) -> ProductData:
    return ProductData(
        reference="Mac mini: Chip M4",
        sku="MU9E3LZ/A",
        memory=None,
        storage="512 GB",
        color="Plata",
        price=price,
        url="https://co.tiendasishop.com/products/mac-mini-m4",
        source="tiendas ishop",
    )


def test_is_configured_false_without_env_vars() -> None:
    assert is_configured() is False


def test_should_alert_above_threshold() -> None:
    assert should_alert(1000000.0, 940000.0) is True


def test_should_alert_below_threshold() -> None:
    assert should_alert(1000000.0, 980000.0) is False


def test_should_alert_exact_threshold() -> None:
    assert should_alert(1000000.0, 950000.0) is True


def test_should_alert_price_increase() -> None:
    assert should_alert(1000000.0, 1050000.0) is False


def test_should_alert_same_price() -> None:
    assert should_alert(1000000.0, 1000000.0) is False


def test_format_cop_thousands() -> None:
    assert _format_cop(4699000.0) == "4,699,000"


def test_format_cop_small_number() -> None:
    assert _format_cop(1000.0) == "1,000"


def test_format_message_contains_all_fields() -> None:
    data = _make_product(price=4400000.0)
    msg = _format_message(data, 4699000.0, 4400000.0)

    assert "\U0001f514" in msg
    assert "Mac mini: Chip M4" in msg
    assert "tiendas ishop" in msg

    assert "tiendasishop.com" in msg


def test_send_message_not_configured() -> None:
    assert send_message("test") is False


def test_send_message_success() -> None:
    with (
        patch("apple_deals.alerts.telegram.is_configured", return_value=True),
        patch("apple_deals.alerts.telegram.TELEGRAM_BOT_TOKEN", "123:valid-token"),
        patch("apple_deals.alerts.telegram.TELEGRAM_CHAT_ID", "98765"),
        patch.object(httpx.Client, "post") as mock_post,
    ):
        mock_response = mock_post.return_value
        mock_response.json.return_value = {"ok": True}

        result = send_message("hello")

    assert result is True
    mock_post.assert_called_once()


def test_send_message_http_error() -> None:
    with (
        patch("apple_deals.alerts.telegram.is_configured", return_value=True),
        patch("apple_deals.alerts.telegram.TELEGRAM_BOT_TOKEN", "123:valid-token"),
        patch("apple_deals.alerts.telegram.TELEGRAM_CHAT_ID", "98765"),
        patch.object(httpx.Client, "post") as mock_post,
    ):
        mock_post.side_effect = httpx.HTTPError("Connection failed")

        result = send_message("hello")

    assert result is False


def test_send_message_api_error() -> None:
    with (
        patch("apple_deals.alerts.telegram.is_configured", return_value=True),
        patch("apple_deals.alerts.telegram.TELEGRAM_BOT_TOKEN", "123:valid-token"),
        patch("apple_deals.alerts.telegram.TELEGRAM_CHAT_ID", "98765"),
        patch.object(httpx.Client, "post") as mock_post,
    ):
        mock_response = mock_post.return_value
        mock_response.json.return_value = {
            "ok": False,
            "error_code": 429,
            "description": "Too Many Requests: retry after 60",
        }

        result = send_message("hello")

    assert result is False


def test_send_alert_fires_when_below_threshold() -> None:
    with patch("apple_deals.alerts.telegram.send_message", return_value=True) as mock_send:
        data = _make_product(price=940000.0)
        result = send_alert(data, 1000000.0, 940000.0)

    assert result is True
    mock_send.assert_called_once()


def test_send_alert_does_not_fire_above_threshold() -> None:
    with patch("apple_deals.alerts.telegram.send_message") as mock_send:
        data = _make_product(price=990000.0)
        result = send_alert(data, 1000000.0, 990000.0)

    assert result is False
    mock_send.assert_not_called()


def test_send_alert_price_increase_no_alert() -> None:
    with patch("apple_deals.alerts.telegram.send_message") as mock_send:
        data = _make_product(price=1050000.0)
        result = send_alert(data, 1000000.0, 1050000.0)

    assert result is False
    mock_send.assert_not_called()


def test_alert_pipeline_price_drop_below_threshold() -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from apple_deals.db.crud import upsert_if_changed
    from apple_deals.db.models import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    data_old = _make_product(price=1000000.0)
    data_new = _make_product(price=900000.0)

    with (
        patch("apple_deals.alerts.telegram.send_message", return_value=True) as mock_send,
        Session(engine) as session,
    ):
        inserted, old_price = upsert_if_changed(session, data_old)
        assert inserted is True
        assert old_price is None

        from apple_deals.alerts.telegram import send_alert

        inserted, old_price = upsert_if_changed(session, data_new)
        assert inserted is True
        assert old_price is not None
        assert old_price == pytest.approx(1000000.0)

        result = send_alert(data_new, old_price, data_new["price"])
        assert result is True
        mock_send.assert_called_once()
        call_arg = mock_send.call_args[0][0]
        assert "10.0% off" in call_arg


def test_alert_pipeline_price_drop_above_threshold() -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from apple_deals.db.crud import upsert_if_changed
    from apple_deals.db.models import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    data_old = _make_product(price=1000000.0)
    data_new = _make_product(price=980000.0)

    with (
        patch("apple_deals.alerts.telegram.send_message") as mock_send,
        Session(engine) as session,
    ):
        upsert_if_changed(session, data_old)
        inserted, old_price = upsert_if_changed(session, data_new)
        assert inserted is True
        assert old_price is not None

        from apple_deals.alerts.telegram import send_alert

        result = send_alert(data_new, old_price, data_new["price"])
        assert result is False
        mock_send.assert_not_called()


def test_alert_pipeline_new_product_no_alert() -> None:
    from apple_deals.alerts.telegram import send_alert

    data = _make_product(price=1000000.0)
    with patch("apple_deals.alerts.telegram.send_message") as mock_send:
        result = send_alert(data, 1000000.0, 1000000.0)
        assert result is False
        mock_send.assert_not_called()
