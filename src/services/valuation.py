"""Model valuation helpers for account value prediction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from src.ml.training import train_and_select_best
from src.preprocessing.features import build_features
from src.preprocessing.features import model_columns


def train_artifacts_if_missing(root: Path) -> None:
    processed_path = root / "data" / "processed" / "training_data.csv"
    if not processed_path.exists():
        raise FileNotFoundError("Missing training_data.csv; cannot auto-train model artifacts.")

    df = pd.read_csv(processed_path)
    if df.empty:
        raise FileNotFoundError("training_data.csv is empty; cannot auto-train model artifacts.")

    featured = build_features(df)
    feature_cols = model_columns(featured)
    best, _all_results, _split_info = train_and_select_best(
        data=featured,
        feature_cols=feature_cols,
        target_col="price_usd",
    )

    models_dir = root / "data" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    model_path = models_dir / "best_model.pkl"
    columns_path = models_dir / "feature_columns.json"
    joblib.dump(best.model, model_path)
    columns_path.write_text(json.dumps(feature_cols, indent=2), encoding="utf-8")


def load_model_artifacts(root: Path) -> tuple[Any, list[str]]:
    model_path = root / "data" / "models" / "best_model.pkl"
    columns_path = root / "data" / "models" / "feature_columns.json"

    if not model_path.exists() or not columns_path.exists():
        train_artifacts_if_missing(root)

    if not model_path.exists() or not columns_path.exists():
        raise FileNotFoundError("Model artifacts not found after auto-train fallback.")

    model = joblib.load(model_path)
    feature_columns = json.loads(columns_path.read_text(encoding="utf-8"))
    return model, feature_columns


def build_row_from_player_data(player_data: dict) -> dict:
    brawlers = player_data.get("brawlers", [])
    num_brawlers = max(1, len(brawlers))

    power_values = [int(b.get("power", 1) or 1) for b in brawlers]
    avg_power = round(sum(power_values) / len(power_values)) if power_values else 1

    # API does not provide skins directly; progression score works as a stable proxy.
    progression_points = 0
    for b in brawlers:
        progression_points += len(b.get("starPowers", []))
        progression_points += len(b.get("gadgets", []))
        progression_points += len(b.get("gears", []))
        if int(b.get("power", 1) or 1) >= 10:
            progression_points += 1
        if int(b.get("power", 1) or 1) >= 11:
            progression_points += 1

    # Keep this un-capped to preserve separation between high-end accounts.
    rare_skins_count = progression_points

    return {
        "num_brawlers": num_brawlers,
        "avg_brawler_level": max(1, min(avg_power, 11)),
        "total_trophies": int(player_data.get("trophies", 0) or 0),
        "rare_skins_count": int(max(0, rare_skins_count)),
        "site_source": "API",
        "currency": "USD",
    }


def predict_account_value(model: Any, feature_columns: list[str], row: dict) -> float:
    df = pd.DataFrame([row])
    featured = build_features(df)

    for col in feature_columns:
        if col not in featured.columns:
            featured[col] = 0

    x = featured[feature_columns]
    prediction = float(model.predict(x)[0])
    return max(1.0, round(prediction, 2))
