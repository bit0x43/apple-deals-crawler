from __future__ import annotations

import abc
import json
import logging
import re
from typing import TypedDict

from playwright.sync_api import Page, sync_playwright

logger = logging.getLogger(__name__)


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


MAX_ENRICH_PAGES_PER_BROWSER = 15
ENRICH_PAGE_TIMEOUT_MS = 15000


def enrich_memory(products: list[ProductData], source: str) -> list[ProductData]:
    """Visit product pages to extract RAM for products missing memory info."""
    to_visit = [(i, p) for i, p in enumerate(products) if p.get("memory") is None]
    if not to_visit:
        return products

    enriched = list(products)
    logger.info("Enriching memory for %d products from %s", len(to_visit), source)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        pages_this_browser = 0
        for idx, product in to_visit:
            if not browser.is_connected():
                logger.warning("Browser disconnected, restarting...")
                browser.close()
                browser = pw.chromium.launch(headless=True)
                pages_this_browser = 0

            if pages_this_browser >= MAX_ENRICH_PAGES_PER_BROWSER:
                logger.info("Recycling browser after %d pages", pages_this_browser)
                browser.close()
                browser = pw.chromium.launch(headless=True)
                pages_this_browser = 0

            try:
                page = browser.new_page()
                page.goto(
                    product["url"], wait_until="domcontentloaded", timeout=ENRICH_PAGE_TIMEOUT_MS
                )
                memory = _extract_memory_from_page(page, source)
                if memory:
                    enriched[idx]["memory"] = memory
                    logger.debug("Enriched %s: memory=%s", product["sku"], memory)
                else:
                    logger.debug("No memory found for %s (%s)", product["sku"], product["url"])
                page.close()
                pages_this_browser += 1
            except Exception:
                logger.debug("Failed to enrich %s", product.get("sku", "?"), exc_info=True)
                continue
        browser.close()
    logger.info(
        "Memory enrichment complete for %s: %d/%d populated",
        source,
        sum(1 for p in enriched if p.get("memory")),
        len(enriched),
    )
    return enriched


MEMORY_LEGEND_KEYWORDS = ("memoria", "ram", "memory")
EXTRACTION_TIMEOUT_MS = 5000

_GB_RE = re.compile(r"(\d+)\s*GB")


def _gb(val: str) -> str:
    """Normalize a GB value to 'NGB' format (no space)."""
    m = _GB_RE.search(val)
    return f"{m.group(1)}GB" if m else val


def _extract_memory_from_page(page: Page, source: str) -> str | None:
    """Extract memory values from a product page using Playwright.

    Strategy order:
      1. <fieldset> with <legend> matching memory keywords → most precise
      2. Flat [data-title] attributes with GB values
      3. CSS swatch / option selectors
      4. JSON-LD product options
      5. Page title fallback
    """
    memory_options: list[str] = []

    # Strategy 1: fieldset with named legend (most reliable — eliminates storage false positives)
    fieldsets = page.query_selector_all("fieldset.js-product-option-form, fieldset.bottom-space")
    for fs in fieldsets:
        legend = fs.query_selector("legend")
        if not legend:
            continue
        legend_text = (legend.text_content() or "").lower().strip()
        if not any(k in legend_text for k in MEMORY_LEGEND_KEYWORDS):
            continue
        for label in fs.query_selector_all("label"):
            dt = label.get_attribute("data-title") or ""
            m = re.search(r"(\d+)\s*GB", dt)
            if m:
                memory_options.append(_gb(m.group(0)))

    # Strategy 2: flat [data-title] attributes
    if not memory_options:
        elements = page.query_selector_all("[data-title]")
        for el in elements:
            title = el.get_attribute("data-title") or ""
            m = re.search(r"(\d+)\s*GB", title)
            if m:
                memory_options.append(_gb(m.group(0)))

    # Strategy 3: CSS selectors
    if not memory_options:
        selectors = [
            ".swatch-element label",
            ".product-form__input label",
            ".option-selector__label",
            ".single-option-selector",
            "fieldset input[type=radio]",
        ]
        for selector in selectors:
            labels = page.query_selector_all(selector)
            for label in labels:
                text = label.text_content() or ""
                m = re.search(r"(\d+)\s*GB", text)
                if m:
                    memory_options.append(_gb(m.group(0)))
            if memory_options:
                break

    # Strategy 4: JSON-LD product options
    if not memory_options:
        try:
            script = page.query_selector('script[type="application/json"]')
            if script:
                raw = script.text_content() or ""
                data = json.loads(raw)
                product = data.get("product", {})
                for opt in product.get("options", []):
                    name = opt.get("name", "").lower()
                    if any(k in name for k in MEMORY_LEGEND_KEYWORDS):
                        for val in opt.get("values", []):
                            m = re.search(r"(\d+)\s*GB", val)
                            if m:
                                memory_options.append(_gb(m.group(0)))
        except Exception:
            pass

    # Strategy 5: page title fallback
    if not memory_options:
        try:
            title = page.title()
            m = re.search(r"(\d+)\s*GB\s*(?:Wi-Fi|RAM|memoria)", title, re.IGNORECASE)
            if m:
                memory_options.append(_gb(m.group(0)))
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
