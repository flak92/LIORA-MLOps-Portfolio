"""Fold contract and metrics: WARMUP | TRAIN | PURGE | OOS | final holdout.

Pure numpy — no I/O. Training keeps only the rows whose event finished before
the OOS block opened; because event_end_ts is exclusive, that is exactly "no
overlap" and no artificial gap is added. A classical embargo after the
evaluated block is not required in forward chaining, since no training
observation lies after the OOS block. Every builder asserts its own contract.

A population and its average-uniqueness weights are one object. Concurrency is
counted inside the population that uses the weights — the purged training rows
of a fold, and separately the scored rows of that fold — so an event the model
never sees, or one that lies in the block being evaluated, cannot change the
weight of a training row. Returning the two together is what makes using a
population with somebody else's weights impossible.
"""

from __future__ import annotations

import numpy as np

from . import config

MILLISECONDS_PER_MINUTE = 60_000


def fold_bounds(fold_id: int) -> tuple[int, int]:
    """OOS bounds of fold Fk, from the 1-based fold table."""
    return config.FOLD_BOUNDS_MS[fold_id - 1], config.FOLD_BOUNDS_MS[fold_id]


def average_uniqueness_weight(entry_ts: np.ndarray, event_end_ts: np.ndarray) -> np.ndarray:
    """Average uniqueness [Lopez de Prado, ch. 4] over exactly the events given.

    The mean, over an event's minutes, of 1 / (events of this population open
    at that minute), exact via prefix sums. Concurrency is counted only among
    the events passed in, so the caller's choice of population *is* the
    definition of the weight.
    """
    n_min = (config.RESEARCH_END_MS - config.RESEARCH_START_MS) // MILLISECONDS_PER_MINUTE
    start = ((entry_ts - config.RESEARCH_START_MS) // MILLISECONDS_PER_MINUTE).astype(np.int64)
    end = ((event_end_ts - config.RESEARCH_START_MS) // MILLISECONDS_PER_MINUTE).astype(np.int64)
    delta = np.zeros(n_min + 1, dtype=np.int64)
    np.add.at(delta, start, 1)
    np.add.at(delta, end, -1)
    concurrent = np.cumsum(delta[:-1])
    inverse = np.zeros(n_min + 1)
    covered = concurrent > 0
    inverse[1:][covered] = 1.0 / concurrent[covered]
    cumulative = np.cumsum(inverse)
    w = (cumulative[end] - cumulative[start]) / (end - start)
    # an event alone in its population averages exactly 1, but the value is the
    # difference of two partial sums over millions of terms, so it can land a
    # few ulps above it. The bound is asserted at the precision the arithmetic
    # delivers; asserting it tighter would fail on correct output.
    assert np.all(w > 0.0) and np.all(w <= 1.0 + 1e-9), "uniqueness weights outside (0, 1]"
    return w


def training_set(decision_ts: np.ndarray, entry_ts: np.ndarray, event_end_ts: np.ndarray,
                 sample_valid: np.ndarray, oos_start_ms: int) -> tuple[np.ndarray, np.ndarray]:
    """Purged training rows and the average uniqueness of that population.

    event_end_ts is the exclusive end of the event, so `event_end_ts <=
    oos_start` is exactly "no overlap" — no extra gap is needed, and forward
    chaining needs no embargo after the evaluated block, because no training row
    lies after the OOS block. The weights are measured after the purge, so a
    dropped event no longer inflates the concurrency of the rows that stay.
    """
    keep = sample_valid & (decision_ts >= config.WARMUP_END_MS) & (event_end_ts <= oos_start_ms)
    idx = np.flatnonzero(keep)
    assert idx.size > 0, "empty training segment"
    assert event_end_ts[idx].max() <= oos_start_ms, "a training event overlaps the OOS block"
    return idx, average_uniqueness_weight(entry_ts[idx], event_end_ts[idx])


def scoring_set(decision_ts: np.ndarray, entry_ts: np.ndarray, event_end_ts: np.ndarray,
                sample_valid: np.ndarray, start_ms: int, end_ms: int) -> tuple[np.ndarray, np.ndarray]:
    """Supervised OOS rows and their average uniqueness — the scoring set.

    The metric is an average over this block, so the redundancy it corrects for
    is the redundancy inside this block: concurrency is counted among the scored
    events alone, never together with the training rows that precede them.
    """
    keep = sample_valid & (decision_ts >= start_ms) & (decision_ts < end_ms)
    idx = np.flatnonzero(keep)
    assert idx.size > 0, "empty OOS segment"
    return idx, average_uniqueness_weight(entry_ts[idx], event_end_ts[idx])


def prediction_window(decision_ts: np.ndarray, start_ms: int, end_ms: int) -> np.ndarray:
    """Every decision row of a window, masked or not — the prediction set.

    Label validity is knowable only after the event resolves, so it may govern
    training and scoring but never which rows receive predictions — and never
    which rows the strategy is allowed to trade.
    """
    keep = (decision_ts >= max(start_ms, config.WARMUP_END_MS)) & (decision_ts < end_ms)
    idx = np.flatnonzero(keep)
    assert idx.size > 0, "empty prediction window"
    return idx


# ---- metrics (weighted where it matters) ----------------------------------

def multiclass_logloss(y_cls: np.ndarray, proba: np.ndarray, weight: np.ndarray) -> float:
    p = np.clip(proba[np.arange(y_cls.size), y_cls], 1e-15, 1.0)
    return float(-(weight * np.log(p)).sum() / weight.sum())


def weighted_class_prior(y_cls: np.ndarray, weight: np.ndarray) -> np.ndarray:
    """Weight-normalised class frequencies — the baseline a model must beat."""
    prior = np.array([weight[y_cls == c].sum() for c in range(3)], dtype=np.float64)
    total = prior.sum()
    assert total > 0.0, "empty or zero-weight segment"
    return prior / total


def prior_logloss(prior: np.ndarray, y_cls: np.ndarray, weight: np.ndarray) -> float:
    """Log-loss of predicting the training prior everywhere.

    Delegates to multiclass_logloss, so the weighting is the same function by
    construction rather than by convention.
    """
    return multiclass_logloss(y_cls, np.broadcast_to(prior, (y_cls.size, 3)), weight)


def matthews_corrcoef(y_cls: np.ndarray, pred_cls: np.ndarray) -> float:
    """Multiclass MCC (Gorodkin) from the 3x3 confusion matrix."""
    cm = np.zeros((3, 3), dtype=np.float64)
    np.add.at(cm, (y_cls, pred_cls), 1.0)
    t, p, c, s = cm.sum(axis=1), cm.sum(axis=0), np.trace(cm), cm.sum()
    num = c * s - t @ p
    den = np.sqrt(s * s - p @ p) * np.sqrt(s * s - t @ t)
    return float(num / den) if den > 0 else 0.0


def sharpe_annualised(bar_returns: np.ndarray) -> float:
    sd = bar_returns.std(ddof=1)
    if sd == 0.0:
        return 0.0
    return float(bar_returns.mean() / sd * np.sqrt(config.ANNUALISATION_PERIOD_15M_BARS))


def max_drawdown(equity: np.ndarray) -> float:
    """Largest peak-to-trough fraction of an equity path that starts at E0 = 1.

    The starting capital is part of the definition, so it is part of the
    series: without it a path opening below 1.0 would measure its drawdown
    from its own first dip.
    """
    full = np.concatenate(([1.0], equity))
    peak = np.maximum.accumulate(full)
    return float(np.max((peak - full) / peak))
