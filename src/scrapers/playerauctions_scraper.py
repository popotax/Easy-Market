"""PlayerAuctions scraper implementation."""

from .generic_marketplace_scraper import GenericMarketplaceScraper


class PlayerauctionsScraper(GenericMarketplaceScraper):
    """Scraper for playerauctions.com."""

    def __init__(self, site_config: dict, scraping_config: dict):
        super().__init__("playerauctions", site_config, scraping_config)
