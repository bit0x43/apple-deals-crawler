import json
from pathlib import Path

import pytest

from apple_deals.crawlers.base import BaseCrawler, ProductData, parse_title

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_parse_title_modern_macbook_air() -> None:
    title = (
        "MacBook Air de 13 pulgadas: Chip M5 de Apple con CPU de 10 nucleos"
        " y GPU de 8 nucleos, 512 GB SSD - Azul cielo"
    )
    assert parse_title(title) == ("512 GB", "Azul cielo", None)


def test_parse_title_modern_mac_mini() -> None:
    title = (
        "Mac mini: Chip M4 de Apple con CPU de 10 nucleos y GPU de 10 nucleos, 512 GB SSD - Plata"
    )
    assert parse_title(title) == ("512 GB", "Plata", None)


def test_parse_title_2tb_macbook_pro() -> None:
    title = (
        "MacBook Pro de 16 pulgadas: Chip M5 Max de Apple con CPU de 18"
        " nucleos y GPU de 32 nucleos, 2 TB SSD - Negro espacial"
    )
    assert parse_title(title) == ("2 TB", "Negro espacial", None)


def test_parse_title_older_m1_mini() -> None:
    title = (
        "Mac mini (M1, 2020) Chip M1 de Apple con CPU de ocho nucleos"
        " y GPU de ocho nucleos 512 GB 8GB Wi-Fi"
    )
    assert parse_title(title) == ("512 GB", None, "8GB")


def test_parse_title_no_match() -> None:
    assert parse_title("no storage or color here") == (None, None, None)


def test_product_data_fields() -> None:
    data: ProductData = {
        "reference": "Mac mini M4",
        "sku": "MU9E3LZ/A",
        "memory": None,
        "storage": "512 GB",
        "color": "Plata",
        "price": 4699000.00,
        "url": "https://example.com/mac-mini",
        "source": "tiendas ishop",
        "in_stock": True,
    }
    assert len(data) == 9
    assert data["reference"] == "Mac mini M4"
    assert data["sku"] == "MU9E3LZ/A"
    assert data["memory"] is None
    assert data["storage"] == "512 GB"
    assert data["color"] == "Plata"
    assert data["price"] == 4699000.00
    assert data["url"] == "https://example.com/mac-mini"
    assert data["source"] == "tiendas ishop"
    assert data["in_stock"] is True


def test_base_crawler_is_abstract() -> None:
    with pytest.raises(TypeError):
        BaseCrawler()  # type: ignore[abstract]


def test_tiendasishop_fixture_parseable() -> None:
    path = FIXTURES_DIR / "tiendasishop_products.json"
    data = json.loads(path.read_text())
    assert len(data["products"]) > 0
    first = data["products"][0]
    for key in ("title", "variants", "handle"):
        assert key in first


def test_mac_center_fixture_parseable() -> None:
    path = FIXTURES_DIR / "mac_center_products.json"
    data = json.loads(path.read_text())
    assert len(data["products"]) > 0
    first = data["products"][0]
    for key in ("title", "variants", "handle"):
        assert key in first
