"""Training orchestration for account price prediction models."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.model_selection import train_test_split

from src.ml.evaluation import regression_metrics
from src.ml.models import build_random_forest, build_xgboost_or_none


@dataclass
class TrainResult:
    name: str
    model: object
    metrics: dict


def train_and_select_best(
    data: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "price_usd",
    random_state: int = 42,
) -> tuple[TrainResult, list[TrainResult], dict]:
    x = data[feature_cols]
    y = data[target_col]

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=random_state
    )

    candidates: list[tuple[str, object]] = [("random_forest", build_random_forest(random_state))]
    xgb = build_xgboost_or_none(random_state)
    if xgb is not None:
        candidates.append(("xgboost", xgb))

    results: list[TrainResult] = []

    for name, model in candidates:
        model.fit(x_train, y_train)
        preds = model.predict(x_test)
        metrics = regression_metrics(y_test, preds)
        results.append(TrainResult(name=name, model=model, metrics=metrics))

    best = max(results, key=lambda r: r.metrics["r2"])

    split_info = {
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "feature_count": int(len(feature_cols)),
        "target": target_col,
    }
    return best, results, split_info
