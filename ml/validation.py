"""Split contract and metrics: WARMUP | TRAIN | PURGE+GAP | OOS | locked TEST.

Pure numpy — no I/O. Training keeps only rows whose event truly finishes
before the pre-test cutoff (purge on the real event_end_ts, plus a
conservative 16-bar gap). Classical post-test embargo is not required in
forward chaining because no training observation lies after the OOS block.
Every builder asserts its own contract.
"""

from __future__ import annotations

import numpy as np

from . import config

GAP_MS = config.PRETEST_GAP_BARS * config.TF_MS["15m"]


def split_bounds(split: int) -> tuple[int, int]:
    """OOS bounds of a split: split k tests fold Fk (1-based fold table)."""
    return config.FOLD_BOUNDS_MS[split - 1], config.FOLD_BOUNDS_MS[split]


def train_indices(decision_ts: np.ndarray, event_end_ts: np.ndarray,
                  mask_ok: np.ndarray, oos_start_ms: int) -> np.ndarray:
    cutoff = oos_start_ms - GAP_MS
    keep = mask_ok & (decision_ts >= config.WARMUP_END_MS) & (event_end_ts < cutoff)
    idx = np.flatnonzero(keep)
    assert idx.size > 0, "empty training segment"
    assert decision_ts[idx].max() < oos_start_ms
    assert event_end_ts[idx].max() < cutoff, "an event leaks past the pre-test cutoff"
    return idx


def oos_indices(decision_ts: np.ndarray, mask_ok: np.ndarray,
                start_ms: int, end_ms: int) -> np.ndarray:
    keep = mask_ok & (decision_ts >= start_ms) & (decision_ts < end_ms)
    idx = np.flatnonzero(keep)
    assert idx.size > 0, "empty OOS segment"
    assert decision_ts[idx].min() >= max(start_ms, config.WARMUP_END_MS)
    return idx


# ---- metrics (weighted where it matters) ----------------------------------

def multiclass_logloss(y_cls: np.ndarray, proba: np.ndarray, weight: np.ndarray) -> float:
    p = np.clip(proba[np.arange(y_cls.size), y_cls], 1e-15, 1.0)
    return float(-(weight * np.log(p)).sum() / weight.sum())


def balanced_accuracy(y_cls: np.ndarray, pred_cls: np.ndarray) -> float:
    recalls = []
    for c in range(3):
        m = y_cls == c
        if m.any():
            recalls.append((pred_cls[m] == c).mean())
    return float(np.mean(recalls))


def matthews_corrcoef(y_cls: np.ndarray, pred_cls: np.ndarray) -> float:
    """Multiclass MCC (Gorodkin) from the 3x3 confusion matrix."""
    cm = np.zeros((3, 3), dtype=np.float64)
    np.add.at(cm, (y_cls, pred_cls), 1.0)
    t, p, c, s = cm.sum(axis=1), cm.sum(axis=0), np.trace(cm), cm.sum()
    num = c * s - t @ p
    den = np.sqrt(s * s - p @ p) * np.sqrt(s * s - t @ t)
    return float(num / den) if den > 0 else 0.0


def confusion_matrix(y_cls: np.ndarray, pred_cls: np.ndarray) -> list[list[int]]:
    cm = np.zeros((3, 3), dtype=np.int64)
    np.add.at(cm, (y_cls, pred_cls), 1)
    return cm.tolist()


def sharpe_annualised(bar_returns: np.ndarray) -> float:
    sd = bar_returns.std(ddof=1)
    if sd == 0.0:
        return 0.0
    return float(bar_returns.mean() / sd * np.sqrt(config.BARS_PER_YEAR_15M))


def max_drawdown(equity: np.ndarray) -> float:
    peak = np.maximum.accumulate(equity)
    return float(np.max((peak - equity) / peak)) if equity.size else 0.0
