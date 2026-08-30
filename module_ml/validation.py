"""Fold contract WARMUP | TRAIN | PURGE | OOS | final holdout, and the metrics. Pure numpy; a population and its
average-uniqueness weights are returned together, so a population is never used with somebody else's weights."""

from __future__ import annotations

import numpy as np

from . import config


def fold_bounds(fold_id: int) -> tuple[int, int]:
    """OOS bounds of fold Fk, from the 1-based fold table."""
    return config.FOLD_BOUNDS_MS[fold_id - 1], config.FOLD_BOUNDS_MS[fold_id]


def average_uniqueness_weight(entry_ts: np.ndarray, event_end_ts: np.ndarray) -> np.ndarray:
    """Average uniqueness [Lopez de Prado, ch. 4] over exactly the events given: the mean over an event's minutes of
    1 / (events of this population open at that minute), exact via prefix sums."""
    research_minute_count = (config.RESEARCH_END_MS - config.RESEARCH_START_MS) // config.MILLISECONDS_PER_MINUTE
    start = ((entry_ts - config.RESEARCH_START_MS) // config.MILLISECONDS_PER_MINUTE).astype(np.int64)
    end = ((event_end_ts - config.RESEARCH_START_MS) // config.MILLISECONDS_PER_MINUTE).astype(np.int64)
    delta = np.zeros(research_minute_count + 1, dtype=np.int64)
    np.add.at(delta, start, 1)
    np.add.at(delta, end, -1)
    concurrent = np.cumsum(delta[:-1])
    inverse = np.zeros(research_minute_count + 1)
    covered = concurrent > 0
    inverse[1:][covered] = 1.0 / concurrent[covered]
    cumulative = np.cumsum(inverse)
    return (cumulative[end] - cumulative[start]) / (end - start)


def training_set(entry_ts: np.ndarray, event_end_ts: np.ndarray,
                 sample_valid: np.ndarray, oos_start_ms: int) -> tuple[np.ndarray, np.ndarray]:
    """Purged training rows — event_end_ts <= oos_start is exactly no overlap, the end being exclusive — and their
    weights, measured after the purge."""
    keep = sample_valid & (event_end_ts <= oos_start_ms)
    idx = np.flatnonzero(keep)
    return idx, average_uniqueness_weight(entry_ts[idx], event_end_ts[idx])


def scoring_set(decision_ts: np.ndarray, entry_ts: np.ndarray, event_end_ts: np.ndarray,
                sample_valid: np.ndarray, start_ms: int, end_ms: int) -> tuple[np.ndarray, np.ndarray]:
    """Supervised OOS rows whose maximum horizon fits the block — decidable at t_0 — and their weights, with
    concurrency counted among the scored events alone."""
    keep = (sample_valid & (decision_ts >= start_ms)
            & (entry_ts + config.LABEL_HORIZON_MS <= end_ms))
    idx = np.flatnonzero(keep)
    return idx, average_uniqueness_weight(entry_ts[idx], event_end_ts[idx])


def prediction_window(decision_ts: np.ndarray, start_ms: int, end_ms: int) -> np.ndarray:
    """Every decision row of a window: label validity never decides which rows receive predictions."""
    return np.flatnonzero((decision_ts >= start_ms) & (decision_ts < end_ms))


# ---- metrics (weighted where it matters) ----------------------------------

def multiclass_logloss(y_cls: np.ndarray, proba: np.ndarray, weight: np.ndarray) -> float:
    p = np.clip(proba[np.arange(y_cls.size), y_cls], 1e-15, 1.0)
    return float(-(weight * np.log(p)).sum() / weight.sum())


def weighted_class_prior(y_cls: np.ndarray, weight: np.ndarray) -> np.ndarray:
    """Weight-normalised class frequencies — the baseline a model must beat."""
    prior = np.array([weight[y_cls == c].sum() for c in range(3)], dtype=np.float64)
    return prior / prior.sum()


def prior_logloss(prior: np.ndarray, y_cls: np.ndarray, weight: np.ndarray) -> float:
    """Log-loss of predicting the training prior everywhere, weighted by the same function."""
    return multiclass_logloss(y_cls, np.broadcast_to(prior, (y_cls.size, 3)), weight)


def sharpe_annualised(bar_returns: np.ndarray) -> float:
    sd = bar_returns.std(ddof=1)
    if sd == 0.0:
        return 0.0
    return float(bar_returns.mean() / sd * np.sqrt(config.ANNUALISATION_PERIOD_15M_BARS))


def max_drawdown(equity: np.ndarray) -> float:
    """Largest peak-to-trough fraction of an equity path that starts at E0 = 1, the starting capital included."""
    full = np.concatenate(([1.0], equity))
    peak = np.maximum.accumulate(full)
    return float(np.max((peak - full) / peak))
