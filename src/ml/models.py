"""Model factory for price prediction."""

from __future__ import annotations

from sklearn.ensemble import RandomForestRegressor


def build_random_forest(random_state: int = 42) -> RandomForestRegressor:
    return RandomForestRegressor(
        n_estimators=300,
        max_depth=18,
        min_samples_split=3,
        min_samples_leaf=1,
        random_state=random_state,
        n_jobs=-1,
    )


def build_xgboost_or_none(random_state: int = 42):
    try:
        from xgboost import XGBRegressor
    except Exception:
        return None

    return XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=random_state,
        objective="reg:squarederror",
        n_jobs=-1,
    )
