"""Generic marketplace scraper that works from configurable selectors plus text fallbacks."""

from __future__ import annotations

from typing import Dict, List, Optional

from bs4 import BeautifulSoup, Tag

from .base_scraper import BaseScraper
from .utils import count_rare_skin_mentions, extract_metric, is_listing_candidate, parse_price


class GenericMarketplaceScraper(BaseScraper):
    """Scraper implementation driven by site config and robust text parsing."""

    def __init__(
        self,
        site_key: str,
        site_config: Dict,
        scraping_config: Dict,
    ):
        super().__init__(
            name=site_config["name"],
            base_url=site_config["url"],
            request_timeout=scraping_config.get("request_timeout", 10),
            request_delay=scraping_config.get("request_delay", 2),
            max_retries=scraping_config.get("max_retries", 3),
            user_agent=scraping_config.get("user_agent"),
        )
        self.site_key = site_key
        self.site_config = site_config

    def _extract_by_selector(self, node: Tag, selector_name: str) -> str:
        selector = self.site_config.get(selector_name)
        if not selector:
            return ""
        found = node.select_one(selector)
        return found.get_text(" ", strip=True) if found else ""

    def extract_listings(self, soup: BeautifulSoup) -> List[Dict]:
        candidates: List[Tag] = []

        # First pass: common listing containers used in marketplaces.
        common_blocks = soup.select("article, li, .listing, .card, .offer, .product, .item")
        for block in common_blocks:
            text = block.get_text(" ", strip=True)
            if len(text) < 20:
                continue
            if is_listing_candidate(text):
                candidates.append(block)

        # Fallback: scan all divs if no explicit listing blocks found.
        if not candidates:
            for block in soup.find_all("div"):
                text = block.get_text(" ", strip=True)
                if len(text) < 40:
                    continue
                if is_listing_candidate(text):
                    candidates.append(block)

        # Deduplicate by text body.
        deduped = []
        seen = set()
        for block in candidates:
            text = block.get_text(" ", strip=True)
            if text in seen:
                continue
            seen.add(text)
            deduped.append({"node": block, "text": text})

        return deduped

    def parse_listing(self, listing: Dict) -> Optional[Dict]:
        node = listing["node"]
        raw_text = listing["text"]

        # Prefer configured selectors, fallback to full listing text.
        price_text = self._extract_by_selector(node, "selector_price") or raw_text
        brawlers_text = self._extract_by_selector(node, "selector_brawlers") or raw_text
        level_text = self._extract_by_selector(node, "selector_level") or raw_text
        trophies_text = self._extract_by_selector(node, "selector_trophies") or raw_text
        rarity_text = self._extract_by_selector(node, "selector_rarity") or raw_text

        price_value, currency = parse_price(price_text)
        num_brawlers = extract_metric(
            brawlers_text,
            ["brawler", "characters", "personajes", "fighters"],
            default=0,
            min_value=1,
            max_value=120,
            strategy="max",
        )
        avg_brawler_level = extract_metric(
            level_text,
            ["level", "lvl", "nivel", "power"],
            default=1,
            min_value=1,
            max_value=11,
            strategy="max",
        )
        total_trophies = extract_metric(
            trophies_text,
            ["troph", "trofeo", "cups"],
            default=0,
            min_value=100,
            max_value=1000000,
            strategy="max",
        )
        rare_skins_count = extract_metric(
            rarity_text,
            ["skin", "legendary", "mythic", "epic", "rare"],
            default=count_rare_skin_mentions(rarity_text),
            min_value=0,
            max_value=500,
            strategy="max",
        )

        # Conservative defaults to pass validation and avoid nonsense rows.
        if num_brawlers <= 0:
            num_brawlers = 1

        if total_trophies <= 0:
            # If no trophy signal is found, avoid injecting very noisy rows.
            return None

        return {
            "price_original_currency": round(price_value, 2),
            "currency": currency,
            "num_brawlers": num_brawlers,
            "avg_brawler_level": max(1, min(avg_brawler_level, 11)),
            "total_trophies": max(0, total_trophies),
            "rare_skins_count": max(0, rare_skins_count),
            "legendary_skins_count": 0,
            "mythic_skins_count": 0,
            "epic_skins_count": 0,
            "rare_skins_count_simple": max(0, rare_skins_count),
        }
