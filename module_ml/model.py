"""XGBoost native-API wrapper: class mapping, HPO space, fit and predict.

Pure functions over numpy arrays (xgboost DMatrix is the only container).
Classes {-1, 0, +1} map to {0, 1, 2} in exactly one place. Determinism:
tree_method=hist with nthread=1 and a fixed seed; no early stopping —
num_boost_round is a tuned hyper-parameter. `fit`, `predict_proba` and
`suggest_*` are the libraries' own vocabulary at their boundary.
"""

from __future__ import annotations

import numpy as np
import xgboost as xgb

from . import config

# one Optuna draw per kind of search-space entry (kind, low, high[, step])
SUGGESTERS = {
    "int": lambda trial, name, spec: trial.suggest_int(name, spec[1], spec[2]),
    "int_step": lambda trial, name, spec: trial.suggest_int(name, spec[1], spec[2], step=spec[3]),
    "float": lambda trial, name, spec: trial.suggest_float(name, spec[1], spec[2]),
    "log": lambda trial, name, spec: trial.suggest_float(name, spec[1], spec[2], log=True),
}


def to_class(y: np.ndarray) -> np.ndarray:
    """{-1, 0, +1} -> {0, 1, 2}."""
    return (y.astype(np.int64) + 1).astype(np.int32)


def suggest_params(trial) -> dict:
    """Draw one point of the HPO space from an Optuna trial, in the space's order."""
    return {name: SUGGESTERS[spec[0]](trial, name, spec)
            for name, spec in config.HYPERPARAMETER_SEARCH_SPACE.items()}


def fit(params: dict, x: np.ndarray, y: np.ndarray, weight: np.ndarray) -> xgb.Booster:
    p = dict(params)
    num_boost_round = int(p.pop("num_boost_round"))
    p.update(config.XGBOOST_FIXED_PARAMETERS)
    dtrain = xgb.DMatrix(x, label=to_class(y), weight=weight,
                         feature_names=list(config.FEATURE_COLUMNS))
    return xgb.train(p, dtrain, num_boost_round=num_boost_round)


def predict_proba(booster: xgb.Booster, x: np.ndarray) -> np.ndarray:
    return booster.predict(xgb.DMatrix(x, feature_names=list(config.FEATURE_COLUMNS)))


def gain_importance(booster: xgb.Booster) -> dict[str, float]:
    """Total gain per feature, zero for a feature the trees never split on."""
    score = booster.get_score(importance_type="total_gain")
    return {column: score.get(column, 0.0) for column in config.FEATURE_COLUMNS}
