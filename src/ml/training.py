"""Training orchestration for account price prediction models."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold, cross_validate
from sklearn.compose import TransformedTargetRegressor

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

    candidates: list[tuple[str, object]] = [
        (
            "random_forest",
            TransformedTargetRegressor(
                regressor=build_random_forest(random_state),
                func=np.log1p,
                inverse_func=np.expm1,
                check_inverse=False,
            ),
        )
    ]
    xgb = build_xgboost_or_none(random_state)
    if xgb is not None:
        candidates.append(
            (
                "xgboost",
                TransformedTargetRegressor(
                    regressor=xgb,
                    func=np.log1p,
                    inverse_func=np.expm1,
                    check_inverse=False,
                ),
            )
        )

    results: list[TrainResult] = []
    n_splits = min(5, len(data))
    if n_splits < 3:
        raise ValueError("Need at least 3 rows to perform cross-validation")
    cv = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)

    for name, model in candidates:
        cv_scores = cross_validate(
            model,
            x,
            y,
            cv=cv,
            scoring={
                "mae": "neg_mean_absolute_error",
                "rmse": "neg_root_mean_squared_error",
                "r2": "r2",
            },
            n_jobs=None,
        )

        mae_mean = float((-cv_scores["test_mae"]).mean())
        rmse_mean = float((-cv_scores["test_rmse"]).mean())
        r2_mean = float(cv_scores["test_r2"].mean())

        model.fit(x, y)
        preds = model.predict(x)
        train_metrics = regression_metrics(y, preds)

        metrics = {
            "mae": mae_mean,
            "rmse": rmse_mean,
            "r2": r2_mean,
            "cv_mae_mean": mae_mean,
            "cv_mae_std": float((-cv_scores["test_mae"]).std()),
            "cv_rmse_mean": rmse_mean,
            "cv_rmse_std": float((-cv_scores["test_rmse"]).std()),
            "cv_r2_mean": r2_mean,
            "cv_r2_std": float(cv_scores["test_r2"].std()),
            "train_mae": train_metrics["mae"],
            "train_rmse": train_metrics["rmse"],
            "train_r2": train_metrics["r2"],
        }
        results.append(TrainResult(name=name, model=model, metrics=metrics))

    best = max(results, key=lambda r: r.metrics["cv_r2_mean"])

    split_info = {
        "rows": int(len(x)),
        "cv_folds": int(n_splits),
        "feature_count": int(len(feature_cols)),
        "target": target_col,
    }
    return best, results, split_info
