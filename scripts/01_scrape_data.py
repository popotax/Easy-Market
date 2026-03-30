"""Run all marketplace scrapers and save raw CSV files."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scrapers import (
    Eloboost24Scraper,
    GamermarktScraper,
    PlayerauctionsScraper,
    SkycoachScraper,
)


def load_config(config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def scraper_factory(site_key: str, site_config: dict, scraping_config: dict):
    mapping = {
        "skycoach": SkycoachScraper,
        "playerauctions": PlayerauctionsScraper,
        "eloboost24": Eloboost24Scraper,
        "gamermarkt": GamermarktScraper,
    }
    scraper_cls = mapping.get(site_key)
    if scraper_cls is None:
        raise ValueError(f"Unknown scraper site key: {site_key}")
    return scraper_cls(site_config=site_config, scraping_config=scraping_config)


def write_rows_to_csv(output_path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    config = load_config(ROOT / "config" / "config.yaml")

    scraping_config = config["scraping"]
    marketplaces = scraping_config["marketplaces"]

    output_cfg = config["output"]
    raw_dir = ROOT / output_cfg["raw_data_dir"].replace("./", "")
    raw_dir.mkdir(parents=True, exist_ok=True)

    scrape_date = datetime.now().strftime("%Y-%m-%d")
    pattern = output_cfg.get("raw_csv_pattern", "{site}_{date}.csv")

    all_rows = []

    for site_key, site_config in marketplaces.items():
        print(f"[INFO] Running scraper: {site_config['name']} ({site_key})")
        scraper = scraper_factory(site_key, site_config, scraping_config)
        rows = scraper.scrape()

        if not rows:
            print(f"[WARN] No rows extracted for {site_key}")
            continue

        file_name = pattern.format(site=site_key, date=scrape_date)
        output_path = raw_dir / file_name
        write_rows_to_csv(output_path, rows)

        print(f"[OK] Saved {len(rows)} rows -> {output_path}")
        all_rows.extend(rows)

    if not all_rows:
        print("[ERROR] No data extracted from any marketplace")
        return 1

    combined_path = raw_dir / f"all_sites_{scrape_date}.csv"
    write_rows_to_csv(combined_path, all_rows)
    print(f"[OK] Saved combined dataset ({len(all_rows)} rows) -> {combined_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
