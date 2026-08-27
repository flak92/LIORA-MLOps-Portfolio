"""Split contract and metrics: WARMUP | TRAIN | PURGE | OOS | final OOS.

Pure numpy — no I/O. Training keeps only the rows whose event finished before
the OOS block opened; because event_end_ts is exclusive, that is exactly "no
overlap" and no artificial gap is added. A classical post-test embargo is not
required in forward chaining, since no training observation lies after the OOS
block. Every builder asserts its own contract.
"""

from __future__ import annotations

import numpy as np

from . import config


def split_bounds(split: int) -> tuple[int, int]:
    """OOS bounds of a split: split k tests fold Fk (1-based fold table)."""
    return config.FOLD_BOUNDS_MS[split - 1], config.FOLD_BOUNDS_MS[split]


def train_indices(decision_ts: np.ndarray, event_end_ts: np.ndarray,
                  sample_valid: np.ndarray, oos_start_ms: int) -> np.ndarray:
    """Training rows whose event finished before the OOS block opened.

    event_end_ts is the exclusive end of the event, so `event_end_ts <=
    oos_start` is exactly "no overlap" — no extra gap is needed, and forward
    chaining needs no post-test embargo because no training row lies after the
    OOS block.
    """
    keep = sample_valid & (decision_ts >= config.WARMUP_END_MS) & (event_end_ts <= oos_start_ms)
    idx = np.flatnonzero(keep)
    assert idx.size > 0, "empty training segment"
    assert event_end_ts[idx].max() <= oos_start_ms, "a training event overlaps the OOS block"
    return idx


def oos_indices(decision_ts: np.ndarray, sample_valid: np.ndarray,
                start_ms: int, end_ms: int) -> np.ndarray:
    """Trainable OOS rows — the scoring set for metrics and the HPO objective."""
    keep = sample_valid & (decision_ts >= start_ms) & (decision_ts < end_ms)
    idx = np.flatnonzero(keep)
    assert idx.size > 0, "empty OOS segment"
    return idx


def window_indices(decision_ts: np.ndarray, start_ms: int, end_ms: int) -> np.ndarray:
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
    return float(bar_returns.mean() / sd * np.sqrt(config.BARS_PER_YEAR_15M))


def max_drawdown(equity: np.ndarray) -> float:
    """Largest peak-to-trough fraction of an equity path that starts at E0 = 1.

    The starting capital is part of the definition, so it is part of the
    series: without it a path opening below 1.0 would measure its drawdown
    from its own first dip.
    """
    full = np.concatenate(([1.0], equity))
    peak = np.maximum.accumulate(full)
    return float(np.max((peak - full) / peak))
