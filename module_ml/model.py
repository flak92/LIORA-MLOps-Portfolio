"""XGBoost native-API wrapper: class mapping, HPO space, fit, predict and the two importances the booster gives.

Pure functions over numpy arrays (xgboost DMatrix is the only container).
Classes {-1, 0, +1} map to {0, 1, 2} in exactly one place. Determinism:
tree_method=hist with nthread=1 and a fixed seed; no early stopping —
num_boost_round is a tuned hyper-parameter. `fit`, `predict_proba`, `pred_contribs` and
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


def fit(params: dict, x: np.ndarray, y: np.ndarray, weight: np.ndarray, feature_columns: tuple[str, ...]) -> xgb.Booster:
    xgboost_params = dict(params)
    num_boost_round = int(xgboost_params.pop("num_boost_round"))
    xgboost_params.update(config.XGBOOST_FIXED_PARAMETERS)
    dtrain = xgb.DMatrix(x, label=to_class(y), weight=weight, feature_names=list(feature_columns))
    return xgb.train(xgboost_params, dtrain, num_boost_round=num_boost_round)


def predict_proba(booster: xgb.Booster, x: np.ndarray, feature_columns: tuple[str, ...]) -> np.ndarray:
    return booster.predict(xgb.DMatrix(x, feature_names=list(feature_columns)))


def gain_importance(booster: xgb.Booster, feature_columns: tuple[str, ...]) -> dict[str, float]:
    """Total gain per feature, zero for a feature the trees never split on."""
    score = booster.get_score(importance_type="total_gain")
    return {column: score.get(column, 0.0) for column in feature_columns}


def mean_abs_shap_importance(booster: xgb.Booster, x: np.ndarray, feature_columns: tuple[str, ...]) -> dict[str, float]:
    """Mean absolute SHAP value per feature over the rows and the classes — xgboost's `pred_contribs`, in margin
    space, the bias column dropped; unweighted, because it is a property of the fitted function, not of a population."""
    contributions = booster.predict(xgb.DMatrix(x, feature_names=list(feature_columns)), pred_contribs=True)
    mean_abs = np.abs(contributions[:, :, :-1]).mean(axis=(0, 1))
    return {column: float(value) for column, value in zip(feature_columns, mean_abs)}
