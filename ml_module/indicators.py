"""Pure numpy indicator kernels — no I/O, no DuckDB, float64 end to end.

Recursive indicators (EMA, Wilder smoothing) run as explicit loops: at ~200k
bars per series the cost is tens of milliseconds and the semantics are exact.
Rolling statistics use sliding_window_view — never cumsum differences, which
cancel catastrophically on long series. Values inside the lookback warm-up are
NaN; the global research warm-up (ml.config.WARMUP_END_MS) starts far later,
and features assert no NaN survives past it.
"""

from __future__ import annotations

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


def ema(x: np.ndarray, n: int) -> np.ndarray:
    alpha = 2.0 / (n + 1.0)
    out = np.empty_like(x)
    out[0] = x[0]
    for i in range(1, x.size):
        out[i] = out[i - 1] + alpha * (x[i] - out[i - 1])
    return out


def wilder_smooth(x: np.ndarray, n: int) -> np.ndarray:
    """Wilder's recursive average: seeded with the SMA of the first n values."""
    out = np.full_like(x, np.nan)
    if x.size < n:
        return out
    out[n - 1] = x[:n].mean()
    for i in range(n, x.size):
        out[i] = out[i - 1] + (x[i] - out[i - 1]) / n
    return out


def rsi(close: np.ndarray, n: int) -> np.ndarray:
    delta = np.diff(close, prepend=close[0])
    gain = wilder_smooth(np.maximum(delta, 0.0), n)
    loss = wilder_smooth(np.maximum(-delta, 0.0), n)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = 100.0 - 100.0 / (1.0 + gain / loss)
    out = np.where((loss == 0.0) & (gain > 0.0), 100.0, out)
    out = np.where((loss == 0.0) & (gain == 0.0), 50.0, out)
    return out


def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int) -> np.ndarray:
    prev_close = np.concatenate(([close[0]], close[:-1]))
    tr = np.maximum(high - low, np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)))
    return wilder_smooth(tr, n)


def rolling_max(x: np.ndarray, n: int) -> np.ndarray:
    out = np.full_like(x, np.nan)
    out[n - 1:] = sliding_window_view(x, n).max(axis=1)
    return out


def rolling_min(x: np.ndarray, n: int) -> np.ndarray:
    out = np.full_like(x, np.nan)
    out[n - 1:] = sliding_window_view(x, n).min(axis=1)
    return out


def range_position(close: np.ndarray, high: np.ndarray, low: np.ndarray, n: int) -> np.ndarray:
    """(close - min(low, n)) / (max(high, n) - min(low, n)); flat range -> 0.5."""
    lo, hi = rolling_min(low, n), rolling_max(high, n)
    span = hi - lo
    with np.errstate(divide="ignore", invalid="ignore"):
        out = (close - lo) / span
    return np.where(span == 0.0, 0.5, out)


def rolling_zscore(x: np.ndarray, n: int) -> np.ndarray:
    """z-score of x against its trailing n-window (sample std); zero-std -> 0."""
    out = np.full_like(x, np.nan)
    w = sliding_window_view(x, n)
    mean = w.mean(axis=1)
    std = w.std(axis=1, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        z = (x[n - 1:] - mean) / std
    out[n - 1:] = np.where(std == 0.0, 0.0, z)
    return out


def asof_index(decision_ts: np.ndarray, timeframe_open_ts: np.ndarray,
               timeframe_duration_ms: int) -> np.ndarray:
    """Index of the last CLOSED bar of a timeframe at each decision_ts.

    A bar [open, open + timeframe) is available from its close time onward, so
    side="right" on close times yields exactly the last closed bar. Causality
    is asserted, not assumed.
    """
    close_ts = timeframe_open_ts + timeframe_duration_ms
    idx = np.searchsorted(close_ts, decision_ts, side="right") - 1
    assert idx.min() >= 0, "decision before the first closed bar of the timeframe"
    assert np.all(close_ts[idx] <= decision_ts), "causality violated in asof_index"
    return idx
