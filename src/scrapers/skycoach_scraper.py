"""SkyCoach scraper implementation."""

from .generic_marketplace_scraper import GenericMarketplaceScraper


class SkycoachScraper(GenericMarketplaceScraper):
    """Scraper for skycoach.gg."""

    def __init__(self, site_config: dict, scraping_config: dict):
        super().__init__("skycoach", site_config, scraping_config)
