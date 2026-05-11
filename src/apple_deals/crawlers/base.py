from __future__ import annotations

import abc
import json
import re
from typing import TypedDict

from playwright.sync_api import Page, sync_playwright


class ProductData(TypedDict):
    reference: str
    sku: str
    memory: str | None
    storage: str | None
    color: str | None
    price: float
    url: str
    source: str
    in_stock: bool


def parse_title(title: str) -> tuple[str | None, str | None, str | None]:
    storage_match = re.search(r"(\d+\s?(?:GB|TB))\s+SSD", title)
    if not storage_match:
        storage_match = re.search(r"(\d+\s?GB)(?=\s+(?:\d|Wi-Fi))", title)
    storage = storage_match.group(1).strip() if storage_match else None

    color_match = re.search(r"\s+-\s+(.+)$", title)
    color = color_match.group(1).strip() if color_match else None

    memory_match = re.search(r"(\d+GB)\s+(?:Wi-Fi|RAM|memoria)", title, re.IGNORECASE)
    if not memory_match:
        memory_match = re.search(r",\s+(\d+GB)\b", title)
    memory = memory_match.group(1).strip() if memory_match else None

    return storage, color, memory


def parse_memory_gb(memory: str) -> list[int]:
    """Extract numeric GB values from a memory string like '16GB, 24GB'."""
    return [int(m) for m in re.findall(r"(\d+)\s*GB", memory.upper())]


def has_low_memory(memory: str | None, min_gb: int = 16) -> bool:
    """Return True if the product has memory below min_gb."""
    if memory is None:
        return False
    values = parse_memory_gb(memory)
    if not values:
        return False
    return max(values) < min_gb


def has_high_memory(memory: str | None, threshold: int = 24) -> bool:
    """Return True if any memory option meets or exceeds the threshold."""
    if memory is None:
        return False
    values = parse_memory_gb(memory)
    if not values:
        return False
    return max(values) >= threshold


def enrich_memory(products: list[ProductData], source: str) -> list[ProductData]:
    """Visit product pages to extract RAM for products missing memory info."""
    to_visit = [(i, p) for i, p in enumerate(products) if p.get("memory") is None]
    if not to_visit:
        return products

    enriched = list(products)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for idx, product in to_visit:
            try:
                page = browser.new_page()
                page.goto(product["url"], wait_until="networkidle", timeout=20000)
                memory = _extract_memory_from_page(page, source)
                if memory:
                    enriched[idx]["memory"] = memory
                page.close()
            except Exception:
                continue
        browser.close()
    return enriched


def _extract_memory_from_page(page: Page, source: str) -> str | None:
    """Extract memory values from a product page using Playwright."""
    memory_options: list[str] = []

    elements = page.query_selector_all("[data-title]")
    for el in elements:
        title = el.get_attribute("data-title") or ""
        m = re.search(r"(\d+)\s*GB", title)
        if m:
            memory_options.append(m.group(0).strip())

    if not memory_options:
        for selector in [".swatch-element label", ".product-form__input label"]:
            labels = page.query_selector_all(selector)
            for label in labels:
                text = label.text_content() or ""
                m = re.search(r"(\d+)\s*GB", text)
                if m:
                    memory_options.append(m.group(0).strip())

    if not memory_options:
        try:
            script = page.query_selector('script[type="application/json"]')
            if script:
                raw = script.text_content() or ""
                data = json.loads(raw)
                product = data.get("product", {})
                for opt in product.get("options", []):
                    if "memoria" in opt.get("name", "").lower():
                        for val in opt.get("values", []):
                            m = re.search(r"(\d+)\s*GB", val)
                            if m:
                                memory_options.append(m.group(0).strip())
        except Exception:
            pass

    if not memory_options:
        try:
            title = page.title()
            m = re.search(r"(\d+)\s*GB)\s*(?:Wi-Fi|RAM|memoria)", title, re.IGNORECASE)
            if m:
                memory_options.append(m.group(0).strip())
        except Exception:
            pass

    if memory_options:
        return ", ".join(sorted(set(memory_options)))
    return None


class BaseCrawler(abc.ABC):
    @abc.abstractmethod
    def crawl(self) -> list[ProductData]: ...


def _deduplicate(products: list[ProductData]) -> list[ProductData]:
    seen: set[tuple[str, str]] = set()
    result: list[ProductData] = []
    for p in products:
        key = (p["sku"], p["source"])
        if key not in seen:
            seen.add(key)
            result.append(p)
    return result
