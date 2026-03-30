"""Gamer Markt scraper implementation."""

from .generic_marketplace_scraper import GenericMarketplaceScraper


class GamermarktScraper(GenericMarketplaceScraper):
    """Scraper for gamermarkt.com."""

    def __init__(self, site_config: dict, scraping_config: dict):
        super().__init__("gamermarkt", site_config, scraping_config)
