"""XGBoost native-API wrapper: class mapping, HPO space, fit and predict.

Pure functions over numpy arrays (xgboost DMatrix is the only container).
Classes {-1, 0, +1} map to {0, 1, 2} in exactly one place. Determinism:
tree_method=hist with nthread=1 and a fixed seed; no early stopping —
num_boost_round is a tuned hyper-parameter.
"""

from __future__ import annotations

import numpy as np
import xgboost as xgb

from . import config


def to_class(y: np.ndarray) -> np.ndarray:
    """{-1, 0, +1} -> {0, 1, 2}."""
    return (y.astype(np.int64) + 1).astype(np.int32)


def suggest_params(trial) -> dict:
    """Draw one point of the HPO space from an Optuna trial."""
    out = {}
    for name, spec in config.HYPERPARAMETER_SEARCH_SPACE.items():
        kind = spec[0]
        if kind == "int":
            out[name] = trial.suggest_int(name, spec[1], spec[2])
        elif kind == "int_step":
            out[name] = trial.suggest_int(name, spec[1], spec[2], step=spec[3])
        elif kind == "float":
            out[name] = trial.suggest_float(name, spec[1], spec[2])
        elif kind == "log":
            out[name] = trial.suggest_float(name, spec[1], spec[2], log=True)
        else:
            raise ValueError(f"unknown space kind {kind}")
    return out


def fit(params: dict, x: np.ndarray, y: np.ndarray, weight: np.ndarray) -> xgb.Booster:
    p = dict(params)
    num_boost_round = int(p.pop("num_boost_round"))
    p.update(config.XGBOOST_FIXED_PARAMETERS)
    dtrain = xgb.DMatrix(x, label=to_class(y), weight=weight,
                         feature_names=list(config.FEATURE_COLUMNS))
    return xgb.train(p, dtrain, num_boost_round=num_boost_round)


def predict_proba(booster: xgb.Booster, x: np.ndarray) -> np.ndarray:
    return booster.predict(xgb.DMatrix(x, feature_names=list(config.FEATURE_COLUMNS)))
