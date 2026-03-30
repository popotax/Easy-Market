"""EloBoost24 scraper implementation."""

from .generic_marketplace_scraper import GenericMarketplaceScraper
from .base_scraper import logger


class Eloboost24Scraper(GenericMarketplaceScraper):
    """Scraper for eloboost24.eu."""

    def __init__(self, site_config: dict, scraping_config: dict):
        super().__init__("eloboost24", site_config, scraping_config)

    def scrape(self):
        rows = super().scrape()
        if rows:
            return rows

        logger.info("No rows via requests for EloBoost24; trying browser fallback...")
        html = self.fetch_page_with_browser(self.base_url, wait_seconds=10)
        if not html:
            return []

        soup = self.parse_html(html)
        raw_listings = self.extract_listings(soup)
        parsed = []
        for listing in raw_listings:
            account_data = self.parse_listing(listing)
            if account_data and self.validate_data(account_data):
                account_data["site_source"] = self.name
                from datetime import datetime

                account_data["date_scraped"] = datetime.now().isoformat()
                parsed.append(account_data)

        logger.info(f"Browser fallback extracted {len(parsed)} rows from EloBoost24")
        return parsed
