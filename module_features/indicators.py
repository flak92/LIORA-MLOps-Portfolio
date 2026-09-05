"""Pure numpy indicator kernels: recursive indicators as explicit loops, rolling statistics via sliding windows;
values inside a lookback warm-up are NaN. The register at the end names each kernel's invariants once, beside it."""

from __future__ import annotations

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


def ema(x: np.ndarray, span_bars: int) -> np.ndarray:
    alpha = 2.0 / (span_bars + 1.0)
    out = np.empty_like(x)
    out[0] = x[0]
    for i in range(1, x.size):
        out[i] = out[i - 1] + alpha * (x[i] - out[i - 1])
    return out


def wilder_smoothing(x: np.ndarray, smoothing_period_bars: int) -> np.ndarray:
    """Wilder's recursive average: seeded with the SMA of the first period."""
    out = np.full_like(x, np.nan)
    if x.size < smoothing_period_bars:
        return out
    out[smoothing_period_bars - 1] = x[:smoothing_period_bars].mean()
    for i in range(smoothing_period_bars, x.size):
        out[i] = out[i - 1] + (x[i] - out[i - 1]) / smoothing_period_bars
    return out


def rsi(close: np.ndarray, smoothing_period_bars: int) -> np.ndarray:
    """Wilder RSI over np.diff changes; the leading NaN realigns the change grid to the price grid."""
    delta = np.diff(close)
    gain = wilder_smoothing(np.maximum(delta, 0.0), smoothing_period_bars)
    loss = wilder_smoothing(np.maximum(-delta, 0.0), smoothing_period_bars)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = 100.0 - 100.0 / (1.0 + gain / loss)
    out = np.where((loss == 0.0) & (gain > 0.0), 100.0, out)
    out = np.where((loss == 0.0) & (gain == 0.0), 50.0, out)
    return np.concatenate(([np.nan], out))    # delta[i] describes close[i + 1]


def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray,
        smoothing_period_bars: int) -> np.ndarray:
    prev_close = np.concatenate(([close[0]], close[:-1]))
    true_range = np.maximum(high - low,
                            np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)))
    return wilder_smoothing(true_range, smoothing_period_bars)


def sma(x: np.ndarray, lookback_bars: int) -> np.ndarray:
    """Simple moving average over the trailing lookback window."""
    out = np.full_like(x, np.nan)
    out[lookback_bars - 1:] = sliding_window_view(x, lookback_bars).mean(axis=1)
    return out


def rolling_max(x: np.ndarray, lookback_bars: int) -> np.ndarray:
    out = np.full_like(x, np.nan)
    out[lookback_bars - 1:] = sliding_window_view(x, lookback_bars).max(axis=1)
    return out


def rolling_min(x: np.ndarray, lookback_bars: int) -> np.ndarray:
    out = np.full_like(x, np.nan)
    out[lookback_bars - 1:] = sliding_window_view(x, lookback_bars).min(axis=1)
    return out


def range_position(close: np.ndarray, high: np.ndarray, low: np.ndarray,
                   lookback_bars: int) -> np.ndarray:
    """(close - rolling min of low) / (rolling max of high - rolling min of low);
    flat range -> 0.5."""
    lo, hi = rolling_min(low, lookback_bars), rolling_max(high, lookback_bars)
    span = hi - lo
    with np.errstate(divide="ignore", invalid="ignore"):
        out = (close - lo) / span
    return np.where(span == 0.0, 0.5, out)


def rolling_zscore(x: np.ndarray, lookback_bars: int) -> np.ndarray:
    """z-score of x against its trailing lookback window (sample std); zero-std -> 0."""
    out = np.full_like(x, np.nan)
    w = sliding_window_view(x, lookback_bars)
    mean = w.mean(axis=1)
    std = w.std(axis=1, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        z = (x[lookback_bars - 1:] - mean) / std
    out[lookback_bars - 1:] = np.where(std == 0.0, 0.0, z)
    return out


def asof_index(decision_ts: np.ndarray, timeframe_open_ts: np.ndarray,
               timeframe_duration_ms: int) -> np.ndarray:
    """Index of the last closed bar of a timeframe at each decision_ts — causality by construction; the assert says
    such a bar exists."""
    close_ts = timeframe_open_ts + timeframe_duration_ms
    idx = np.searchsorted(close_ts, decision_ts, side="right") - 1
    assert idx.min() >= 0, "decision before the first closed bar of the timeframe"
    return idx


# the indicator register: one record per token beside its kernel — the kernel, the word its one parameter carries
# (AGENTS.md § Canonical vocabulary), the warm-up it needs in multiples of that parameter, and the bar columns it reads
# when its inputs are fixed; an indicator without `inputs` takes any series, close by default. A second parameter,
# when an indicator needs one, extends the record and the name grammar in the same commit.
INDICATORS = {
    "ema": {"kernel": ema, "parameter_word": "SPAN", "warmup_multiple": 4},
    "sma": {"kernel": sma, "parameter_word": "LOOKBACK", "warmup_multiple": 1},
    "rsi": {"kernel": rsi, "parameter_word": "SMOOTHING_PERIOD", "warmup_multiple": 4, "inputs": ("close",)},
    "atr": {"kernel": atr, "parameter_word": "SMOOTHING_PERIOD", "warmup_multiple": 4, "inputs": ("high", "low", "close")},
    "zscore": {"kernel": rolling_zscore, "parameter_word": "LOOKBACK", "warmup_multiple": 1},
    "range_position": {"kernel": range_position, "parameter_word": "LOOKBACK", "warmup_multiple": 1,
                       "inputs": ("close", "high", "low")},
}
