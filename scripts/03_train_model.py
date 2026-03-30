"""Train ML models and persist the best model artifact."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ml.training import train_and_select_best
from src.preprocessing.features import build_features, model_columns


def main() -> int:
    processed_path = ROOT / "data" / "processed" / "training_data.csv"
    if not processed_path.exists():
        print(f"[ERROR] Missing file: {processed_path}")
        print("[INFO] Run: python scripts/02_process_data.py")
        return 1

    df = pd.read_csv(processed_path)
    if df.empty:
        print("[ERROR] training_data.csv is empty")
        return 1

    featured = build_features(df)
    feature_cols = model_columns(featured)

    best, all_results, split_info = train_and_select_best(
        data=featured,
        feature_cols=feature_cols,
        target_col="price_usd",
    )

    models_dir = ROOT / "data" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    model_path = models_dir / "best_model.pkl"
    feature_path = models_dir / "feature_columns.json"
    config_path = models_dir / "model_config.json"

    joblib.dump(best.model, model_path)
    feature_path.write_text(json.dumps(feature_cols, indent=2), encoding="utf-8")

    payload = {
        "best_model": best.name,
        "best_metrics": best.metrics,
        "all_results": [{"name": r.name, "metrics": r.metrics} for r in all_results],
        "split_info": split_info,
    }
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"[OK] Best model: {best.name}")
    print(f"[OK] Metrics: {best.metrics}")
    print(f"[OK] Saved model: {model_path}")
    print(f"[OK] Saved features: {feature_path}")
    print(f"[OK] Saved config: {config_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
