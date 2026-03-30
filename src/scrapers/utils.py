"""Utility helpers for scraping and parsing marketplace listing text."""

import re
from typing import Tuple


CURRENCY_PATTERNS = [
    (r"\$\s*([\d.,]+)", "USD"),
    (r"€\s*([\d.,]+)", "EUR"),
    (r"£\s*([\d.,]+)", "GBP"),
]


def normalize_numeric_string(value: str) -> str:
    """Normalize mixed numeric separators to a parseable decimal string."""
    cleaned = re.sub(r"[^\d,\.]", "", value)
    if cleaned.count(",") > 0 and cleaned.count(".") > 0:
        # Assume the last separator is decimal, remove the others.
        last_sep = max(cleaned.rfind(","), cleaned.rfind("."))
        int_part = re.sub(r"[\.,]", "", cleaned[:last_sep])
        dec_part = re.sub(r"[\.,]", "", cleaned[last_sep + 1 :])
        return f"{int_part}.{dec_part}" if dec_part else int_part
    if cleaned.count(",") > 0 and cleaned.count(".") == 0:
        # Comma as decimal separator.
        return cleaned.replace(",", ".")
    if cleaned.count(".") > 1 and cleaned.count(",") == 0:
        # Handle thousands separators like 31.200 -> 31200.
        parts = cleaned.split(".")
        if all(len(p) == 3 for p in parts[1:]):
            return "".join(parts)
    return cleaned


def safe_float(value: str, default: float = 0.0) -> float:
    """Convert string to float safely."""
    try:
        return float(normalize_numeric_string(value))
    except (TypeError, ValueError):
        return default


def safe_int(value: str, default: int = 0) -> int:
    """Convert string to int safely."""
    try:
        return int(round(safe_float(value, default=float(default))))
    except (TypeError, ValueError):
        return default


def parse_price(text: str) -> Tuple[float, str]:
    """Parse likely listing price from text."""
    prices: list[tuple[float, str]] = []
    for pattern, currency in CURRENCY_PATTERNS:
        for match in re.finditer(pattern, text):
            price = safe_float(match.group(1), default=0.0)
            if price > 0:
                prices.append((price, currency))

    if prices:
        # If there is a discounted and original price, keep the lowest positive one.
        selected = min(prices, key=lambda x: x[0])
        return selected

    # Fallback: any number with USD default.
    any_number = re.search(r"([\d.,]{2,})", text)
    if any_number:
        return safe_float(any_number.group(1), default=0.0), "USD"
    return 0.0, "USD"


def _token_to_int(token: str) -> int:
    token = token.strip()
    multiplier = 1
    if token.lower().endswith("k"):
        multiplier = 1000
        token = token[:-1]
    elif token.lower().endswith("m"):
        multiplier = 1000000
        token = token[:-1]
    return int(round(safe_float(token, default=0.0) * multiplier))


def metric_candidates(text: str, keywords: list[str]) -> list[int]:
    """Return candidate numeric values found near metric keywords."""
    candidates: list[int] = []
    lowered = text.lower()
    for keyword in keywords:
        idx = lowered.find(keyword)
        if idx == -1:
            continue
        start = max(0, idx - 40)
        end = min(len(text), idx + 40)
        window = text[start:end]
        for match in re.finditer(r"(\d[\d.,]*\s*[kKmM]?)", window):
            value = _token_to_int(match.group(1))
            if value > 0:
                candidates.append(value)
    return candidates


def extract_metric(
    text: str,
    keywords: list[str],
    default: int = 0,
    min_value: int | None = None,
    max_value: int | None = None,
    strategy: str = "max",
) -> int:
    """Extract a number near one of keywords from text with filtering strategy."""
    candidates = metric_candidates(text, keywords)

    if min_value is not None:
        candidates = [v for v in candidates if v >= min_value]
    if max_value is not None:
        candidates = [v for v in candidates if v <= max_value]

    if candidates:
        if strategy == "min":
            return min(candidates)
        if strategy == "first":
            return candidates[0]
        return max(candidates)

    # Fallback: pick first plausible number.
    fallback = re.search(r"(\d{1,7})", text)
    if fallback:
        return safe_int(fallback.group(1), default=default)
    return default


def count_rare_skin_mentions(text: str) -> int:
    """Estimate rare skin count by keyword mentions."""
    keywords = ["legendary", "mythic", "epic", "rare", "skin"]
    lowered = text.lower()
    count = sum(lowered.count(k) for k in keywords)
    return min(count, 100)


def is_listing_candidate(text: str) -> bool:
    """Check if a block likely represents a marketplace listing."""
    lowered = text.lower()
    has_price = bool(re.search(r"(\$|€|£)\s*\d", text))
    has_game_hint = "brawl" in lowered or "account" in lowered
    has_stat_hint = any(k in lowered for k in ["troph", "brawler", "skin", "level"]) 
    return has_price and (has_game_hint or has_stat_hint)
