"""Web scraping modules for Brawl Stars account data"""

from .base_scraper import BaseScraper
from .eloboost24_scraper import Eloboost24Scraper
from .gamermarkt_scraper import GamermarktScraper
from .playerauctions_scraper import PlayerauctionsScraper
from .skycoach_scraper import SkycoachScraper

__all__ = [
	"BaseScraper",
	"SkycoachScraper",
	"PlayerauctionsScraper",
	"Eloboost24Scraper",
	"GamermarktScraper",
]
