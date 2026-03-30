"""Predict account price from manually provided account attributes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.preprocessing.features import build_features


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Predict Brawl Stars account price")
    parser.add_argument("--num_brawlers", type=int, required=True)
    parser.add_argument("--avg_level", type=int, required=True)
    parser.add_argument("--total_trophies", type=int, required=True)
    parser.add_argument("--rare_skins", type=int, required=True)
    parser.add_argument("--site_source", type=str, default="SkyCoach")
    parser.add_argument("--currency", type=str, default="USD")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    model_path = ROOT / "data" / "models" / "best_model.pkl"
    feature_path = ROOT / "data" / "models" / "feature_columns.json"

    if not model_path.exists() or not feature_path.exists():
        print("[ERROR] Missing model artifacts. Run: python scripts/03_train_model.py")
        return 1

    model = joblib.load(model_path)
    feature_columns = json.loads(feature_path.read_text(encoding="utf-8"))

    row = {
        "num_brawlers": args.num_brawlers,
        "avg_brawler_level": args.avg_level,
        "total_trophies": args.total_trophies,
        "rare_skins_count": args.rare_skins,
        "site_source": args.site_source,
        "currency": args.currency,
    }

    df = pd.DataFrame([row])
    featured = build_features(df)

    # Add missing one-hot columns expected by training.
    for col in feature_columns:
        if col not in featured.columns:
            featured[col] = 0

    # Keep only model columns in exact order.
    x = featured[feature_columns]
    prediction = float(model.predict(x)[0])

    print("[OK] Prediction completed")
    print(f"[RESULT] Estimated price (USD): {prediction:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
