"""Feature engineering utilities for account price prediction."""

from __future__ import annotations

import numpy as np
import pandas as pd


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create model-ready feature dataframe from cleaned input."""
    out = df.copy()

    # Safe denominators to avoid inf values.
    brawlers = out["num_brawlers"].replace(0, np.nan)
    trophies = out["total_trophies"].replace(0, np.nan)

    out["trophies_per_brawler"] = out["total_trophies"] / brawlers
    out["skin_density"] = out["rare_skins_count"] / brawlers

    out["trophies_per_brawler"] = out["trophies_per_brawler"].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    out["skin_density"] = out["skin_density"].replace([np.inf, -np.inf], np.nan).fillna(0.0)

    # One-hot encode site source for model signal.
    out = pd.get_dummies(out, columns=["site_source"], prefix="site", drop_first=False)

    return out


def model_columns(df: pd.DataFrame) -> list[str]:
    """Return columns used as model features."""
    base_cols = [
        "num_brawlers",
        "avg_brawler_level",
        "total_trophies",
        "rare_skins_count",
        "trophies_per_brawler",
        "skin_density",
    ]

    one_hot_cols = [col for col in df.columns if col.startswith("site_")]
    return [c for c in base_cols if c in df.columns] + sorted(one_hot_cols)
