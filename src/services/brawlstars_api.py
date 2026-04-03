"""Client for Brawl Stars official player API."""

from __future__ import annotations

from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass
class BrawlStarsClient:
    token: str
    timeout: int = 20
    max_retries: int = 3

    def __post_init__(self) -> None:
        self.base_url = "https://api.brawlstars.com/v1"
        self.session = requests.Session()
        retry = Retry(
            total=self.max_retries,
            read=self.max_retries,
            connect=self.max_retries,
            backoff_factor=0.4,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET"]),
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/json",
            }
        )

    @staticmethod
    def normalize_tag(tag: str) -> str:
        clean = tag.strip().upper().replace(" ", "")
        if clean.startswith("#"):
            clean = clean[1:]
        return clean

    def get_player(self, tag: str) -> dict:
        normalized = self.normalize_tag(tag)
        endpoint = f"{self.base_url}/players/%23{normalized}"
        response = self.session.get(endpoint, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
