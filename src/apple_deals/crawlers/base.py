from __future__ import annotations

import abc
import re
from typing import TypedDict


class ProductData(TypedDict):
    reference: str
    sku: str
    memory: str | None
    storage: str | None
    color: str | None
    price: float
    url: str
    source: str


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
