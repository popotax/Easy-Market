"""Data cleaning pipeline for raw marketplace account data."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


DEFAULT_EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 1.09,
    "GBP": 1.28,
}


@dataclass
class CleaningReport:
    input_rows: int
    after_dropna_rows: int
    after_dedup_rows: int
    after_outlier_rows: int
    output_rows: int


class DataCleaner:
    """Clean and normalize scraped account data for ML."""

    required_columns = [
        "price_original_currency",
        "currency",
        "num_brawlers",
        "avg_brawler_level",
        "total_trophies",
        "rare_skins_count",
        "site_source",
        "date_scraped",
    ]

    def __init__(
        self,
        min_price_usd: float = 5.0,
        max_price_usd: float = 5000.0,
        max_trophies: int = 150000,
        max_progress_per_brawler: int = 15,
        high_brawler_threshold: int = 80,
        min_trophies_for_high_brawlers: int = 2000,
        exchange_rates: dict[str, float] | None = None,
    ):
        self.min_price_usd = min_price_usd
        self.max_price_usd = max_price_usd
        self.max_trophies = max_trophies
        self.max_progress_per_brawler = max_progress_per_brawler
        self.high_brawler_threshold = high_brawler_threshold
        self.min_trophies_for_high_brawlers = min_trophies_for_high_brawlers
        self.exchange_rates = exchange_rates or DEFAULT_EXCHANGE_RATES

    def load_raw_files(self, paths: Iterable[Path]) -> pd.DataFrame:
        frames = []
        for path in paths:
            df = pd.read_csv(path)
            if df.empty:
                continue
            frames.append(df)
        if not frames:
            return pd.DataFrame(columns=self.required_columns)
        combined = pd.concat(frames, ignore_index=True)
        return combined

    def normalize_currency(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["currency"] = out["currency"].astype(str).str.upper().str.strip()
        out["price_original_currency"] = pd.to_numeric(
            out["price_original_currency"], errors="coerce"
        )

        def to_usd(row) -> float:
            rate = self.exchange_rates.get(row["currency"], 1.0)
            return float(row["price_original_currency"] * rate)

        out["price_usd"] = out.apply(to_usd, axis=1)
        return out

    def clean(self, df: pd.DataFrame) -> tuple[pd.DataFrame, CleaningReport]:
        if df.empty:
            return df, CleaningReport(0, 0, 0, 0, 0)

        out = df.copy()
        input_rows = len(out)

        # Ensure all required columns exist.
        for col in self.required_columns:
            if col not in out.columns:
                out[col] = 0

        # Normalize numeric columns.
        numeric_cols = [
            "price_original_currency",
            "num_brawlers",
            "avg_brawler_level",
            "total_trophies",
            "rare_skins_count",
            "legendary_skins_count",
            "mythic_skins_count",
            "epic_skins_count",
            "rare_skins_count_simple",
        ]
        for col in numeric_cols:
            if col in out.columns:
                out[col] = pd.to_numeric(out[col], errors="coerce")

        out = self.normalize_currency(out)

        # Apply hard sanity bounds before modeling. These remove parsing artifacts
        # (for example, trophies at 1,000,000 or skin-like counters in the millions).
        out["num_brawlers"] = out["num_brawlers"].clip(lower=1, upper=150)
        out["total_trophies"] = out["total_trophies"].clip(lower=0, upper=self.max_trophies)

        max_progress = (out["num_brawlers"].fillna(0) * self.max_progress_per_brawler).clip(lower=0)
        out["rare_skins_count"] = out["rare_skins_count"].clip(lower=0)
        out["rare_skins_count"] = out[["rare_skins_count"]].join(max_progress.rename("max_progress"))[
            ["rare_skins_count", "max_progress"]
        ].min(axis=1)

        # Drop rows with core missing values.
        core_cols = ["price_usd", "num_brawlers", "total_trophies", "site_source"]
        out = out.dropna(subset=core_cols)
        after_dropna_rows = len(out)

        # Remove duplicates by core identity signature.
        dedup_subset = [
            "site_source",
            "price_usd",
            "num_brawlers",
            "total_trophies",
            "rare_skins_count",
        ]
        out = out.drop_duplicates(subset=dedup_subset, keep="first")
        after_dedup_rows = len(out)

        # Outlier and validity filters.
        out = out[
            (out["price_usd"] >= self.min_price_usd)
            & (out["price_usd"] <= self.max_price_usd)
            & (out["num_brawlers"] >= 1)
            & (out["num_brawlers"] <= 150)
            & (out["avg_brawler_level"] >= 1)
            & (out["avg_brawler_level"] <= 11)
            & (out["total_trophies"] >= 0)
            & (out["total_trophies"] <= self.max_trophies)
        ]

        # Remove impossible progression profiles likely caused by selector mismatches.
        # Accounts with many brawlers almost never have near-zero trophies.
        out = out[
            ~(
                (out["num_brawlers"] >= self.high_brawler_threshold)
                & (out["total_trophies"] < self.min_trophies_for_high_brawlers)
            )
        ]
        after_outlier_rows = len(out)

        # Type cleanup.
        int_cols = [
            "num_brawlers",
            "avg_brawler_level",
            "total_trophies",
            "rare_skins_count",
            "legendary_skins_count",
            "mythic_skins_count",
            "epic_skins_count",
            "rare_skins_count_simple",
        ]
        for col in int_cols:
            if col in out.columns:
                out[col] = out[col].fillna(0).round().astype(int)

        out["price_usd"] = out["price_usd"].round(2)
        out = out.sort_values(["site_source", "price_usd"], ascending=[True, True])
        out = out.reset_index(drop=True)

        report = CleaningReport(
            input_rows=input_rows,
            after_dropna_rows=after_dropna_rows,
            after_dedup_rows=after_dedup_rows,
            after_outlier_rows=after_outlier_rows,
            output_rows=len(out),
        )
        return out, report
