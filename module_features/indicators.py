"""Pure numpy kernels: recursive operations as explicit loops, rolling statistics via sliding windows; a kernel's
values before its lookback or its smoothing period has filled are NaN. The two registers at the end name each
kernel's invariants once, beside it — the series that are not bar columns, and the indicators that take one integer
parameter. Every token is the word of its operation: the name of a kernel is the name of what it computes."""

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


def exponential_smoothing(x: np.ndarray, span_bars: int) -> np.ndarray:
    alpha = 2.0 / (span_bars + 1.0)
    out = np.empty_like(x)
    out[0] = x[0]
    for i in range(1, x.size):
        out[i] = out[i - 1] + alpha * (x[i] - out[i - 1])
    return out


# twice by extraction
def recursive_mean(x: np.ndarray, smoothing_period_bars: int) -> np.ndarray:
    """The recursive mean: seeded with the mean of the first period."""
    out = np.full_like(x, np.nan)
    if x.size < smoothing_period_bars:
        return out
    out[smoothing_period_bars - 1] = x[:smoothing_period_bars].mean()
    for i in range(smoothing_period_bars, x.size):
        out[i] = out[i - 1] + (x[i] - out[i - 1]) / smoothing_period_bars
    return out


def recursive_mean_gain_share(close: np.ndarray, smoothing_period_bars: int) -> np.ndarray:
    """The share the recursively averaged gains hold of the averaged gains and losses, 0 to 100; the leading NaN
    realigns the change grid to the price grid. A zero loss with a positive gain gives 100, a zero gain and loss 50."""
    delta = np.diff(close)
    gain = recursive_mean(np.maximum(delta, 0.0), smoothing_period_bars)
    loss = recursive_mean(np.maximum(-delta, 0.0), smoothing_period_bars)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = 100.0 - 100.0 / (1.0 + gain / loss)
    out = np.where((loss == 0.0) & (gain > 0.0), 100.0, out)
    out = np.where((loss == 0.0) & (gain == 0.0), 50.0, out)
    return np.concatenate(([np.nan], out))    # delta[i] describes close[i + 1]


# twice by extraction
def true_range(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    """The bar's range against the previous close; the first bar has no previous close, so it is its own."""
    prev_close = np.concatenate(([close[0]], close[:-1]))
    return np.maximum(high - low,
                      np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)))


def rolling_mean(x: np.ndarray, lookback_bars: int) -> np.ndarray:
    """The mean over the trailing lookback window."""
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


def rolling_range_position(close: np.ndarray, high: np.ndarray, low: np.ndarray,
                           lookback_bars: int) -> np.ndarray:
    """(close - rolling min of low) / (rolling max of high - rolling min of low);
    flat range -> 0.5."""
    rolling_low, rolling_high = rolling_min(low, lookback_bars), rolling_max(high, lookback_bars)
    value_range = rolling_high - rolling_low
    with np.errstate(divide="ignore", invalid="ignore"):
        out = (close - rolling_low) / value_range
    return np.where(value_range == 0.0, 0.5, out)


def rolling_standard_score(x: np.ndarray, lookback_bars: int) -> np.ndarray:
    """(x - mean) / standard deviation of the trailing lookback window (sample); zero deviation -> 0."""
    out = np.full_like(x, np.nan)
    lookback_window = sliding_window_view(x, lookback_bars)
    mean = lookback_window.mean(axis=1)
    std = lookback_window.std(axis=1, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        z = (x[lookback_bars - 1:] - mean) / std
    out[lookback_bars - 1:] = np.where(std == 0.0, 0.0, z)
    return out


def rolling_standard_deviation(x: np.ndarray, lookback_bars: int) -> np.ndarray:
    """The sample standard deviation of the trailing lookback window."""
    out = np.full_like(x, np.nan)
    out[lookback_bars - 1:] = sliding_window_view(x, lookback_bars).std(axis=1, ddof=1)
    return out


def relative_change(close: np.ndarray, lookback_bars: int) -> np.ndarray:
    """The change over the lookback, as a share of where it started; a zero start gives 0."""
    out = np.full_like(close, np.nan)
    started_at = close[:-lookback_bars]
    with np.errstate(divide="ignore", invalid="ignore"):
        change = close[lookback_bars:] / started_at - 1.0
    out[lookback_bars:] = np.where(started_at == 0.0, 0.0, change)
    return out


def _directional_movement(high: np.ndarray, low: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The upward and downward movement on the change grid: the larger of the two moves, and only when it rises."""
    upward_move, downward_move = np.diff(high), -np.diff(low)
    return (np.where((upward_move > downward_move) & (upward_move > 0.0), upward_move, 0.0),
            np.where((downward_move > upward_move) & (downward_move > 0.0), downward_move, 0.0))


def recursive_mean_upward_movement_share(high: np.ndarray, low: np.ndarray,
                                         smoothing_period_bars: int) -> np.ndarray:
    """The share the recursively averaged upward movement holds of both movements, 0 to 100; no movement gives 50.
    The leading NaN realigns the change grid to the price grid."""
    upward, downward = _directional_movement(high, low)
    smoothed_upward = recursive_mean(upward, smoothing_period_bars)
    smoothed_downward = recursive_mean(downward, smoothing_period_bars)
    both = smoothed_upward + smoothed_downward
    with np.errstate(divide="ignore", invalid="ignore"):
        out = 100.0 * smoothed_upward / both
    return np.concatenate(([np.nan], np.where(both == 0.0, 50.0, out)))


def recursive_mean_directional_movement_imbalance(high: np.ndarray, low: np.ndarray,
                                                  smoothing_period_bars: int) -> np.ndarray:
    """The recursively averaged imbalance between the two movements, without its sign, 0 to 100; no movement gives 0.
    The second recursion starts where the first has a value, because a mean seeded over a warm-up is NaN for good.
    The leading NaN realigns the change grid to the price grid."""
    upward, downward = _directional_movement(high, low)
    smoothed_upward = recursive_mean(upward, smoothing_period_bars)
    smoothed_downward = recursive_mean(downward, smoothing_period_bars)
    both = smoothed_upward + smoothed_downward
    with np.errstate(divide="ignore", invalid="ignore"):
        imbalance = 100.0 * np.abs(smoothed_upward - smoothed_downward) / both
    imbalance = np.where(both == 0.0, 0.0, imbalance)
    out = np.full_like(imbalance, np.nan)
    settled = np.flatnonzero(np.isfinite(imbalance))
    if settled.size:
        out[settled[0]:] = recursive_mean(imbalance[settled[0]:], smoothing_period_bars)
    return np.concatenate(([np.nan], out))


def rolling_volume_weighted_mean(close: np.ndarray, volume: np.ndarray, lookback_bars: int) -> np.ndarray:
    """The mean of the window weighted by volume; a window of no volume falls back to the unweighted mean of the
    same window, where equal weights say what volume no longer can."""
    out = np.full_like(close, np.nan)
    close_window = sliding_window_view(close, lookback_bars)
    volume_window = sliding_window_view(volume, lookback_bars)
    traded = volume_window.sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        weighted = (close_window * volume_window).sum(axis=1) / traded
    out[lookback_bars - 1:] = np.where(traded == 0.0, close_window.mean(axis=1), weighted)
    return out


def rolling_volume_weighted_close_location(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                                           volume: np.ndarray, lookback_bars: int) -> np.ndarray:
    """Where the close sits in its bar, from -1 at the low to 1 at the high, weighted by the volume of the window;
    a bar of no range sits at 0, and a window of no volume gives 0."""
    value_range = high - low
    with np.errstate(divide="ignore", invalid="ignore"):
        location = ((close - low) - (high - close)) / value_range
    flow = np.where(value_range == 0.0, 0.0, location) * volume
    out = np.full_like(close, np.nan)
    traded = sliding_window_view(volume, lookback_bars).sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        weighted = sliding_window_view(flow, lookback_bars).sum(axis=1) / traded
    out[lookback_bars - 1:] = np.where(traded == 0.0, 0.0, weighted)
    return out


def rolling_money_flow_gain_share(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                                  volume: np.ndarray, lookback_bars: int) -> np.ndarray:
    """The share the window's rising money flow holds of all its flow, 0 to 100; no flow gives 50. Money flow is the
    typical price times the volume, and it rises or falls with the typical price. The leading NaN realigns the change
    grid to the price grid."""
    typical_price = (high + low + close) / 3.0
    flow = typical_price * volume
    change = np.diff(typical_price)
    gained = sliding_window_view(np.where(change > 0.0, flow[1:], 0.0), lookback_bars).sum(axis=1)
    lost = sliding_window_view(np.where(change < 0.0, flow[1:], 0.0), lookback_bars).sum(axis=1)
    both = gained + lost
    out = np.full(change.shape, np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        share = 100.0 * gained / both
    out[lookback_bars - 1:] = np.where(both == 0.0, 50.0, share)
    return np.concatenate(([np.nan], out))


# twice by extraction
def asof_index(decision_ts: np.ndarray, timeframe_open_ms: np.ndarray,
               timeframe_duration_ms: int) -> np.ndarray:
    """Index of the last closed bar of a timeframe at each decision_ts — causality by construction; the assert says
    such a bar exists."""
    timeframe_close_ms = timeframe_open_ms + timeframe_duration_ms
    last_closed_bar_rows = np.searchsorted(timeframe_close_ms, decision_ts, side="right") - 1
    assert last_closed_bar_rows.min() >= 0, "decision before the first closed bar of the timeframe"
    return last_closed_bar_rows


# the series register: one record per series that is not a bar column, its kernel reading the bars it needs. A series
# takes no parameter, so a record carries its kernel and nothing else; an indicator of the register below averages,
# standardises or positions it when a term names both.
SERIES_KERNELS = {
    "logarithmic_volume": {"kernel": lambda bars: np.log1p(bars["volume"])},
    "true_range": {"kernel": lambda bars: true_range(bars["high"], bars["low"], bars["close"])},
    "cumulative_signed_volume": {"kernel": lambda bars: np.concatenate(
        ([0.0], np.cumsum(np.sign(np.diff(bars["close"])) * bars["volume"][1:])))},
}

# the indicator register: one record per token beside its kernel — the kernel, the word its one parameter carries
# (AGENTS.md § Canonical vocabulary), the warm-up it needs in multiples of that parameter — and, for a window over
# changes, `warmup_offset_bars`, the one bar before the window its first change is taken off —, the bar columns it
# reads when its inputs are fixed, and the range it outputs when that range is bounded; an indicator without `inputs` takes
# any series, close by default, and one without `output_range` is unbounded, so no normaliser can be written on it.
# A second parameter, when an indicator needs one, extends the record and the name grammar in the same commit.
# `historical_aliases` carries the popular names the operation answers to: provenance, never a key or a column.
INDICATORS = {
    "exponential_smoothing": {"kernel": exponential_smoothing, "parameter_word": "SPAN", "warmup_multiple": 4,
        "historical_aliases": ("EMA",)},
    "rolling_mean": {"kernel": rolling_mean, "parameter_word": "LOOKBACK", "warmup_multiple": 1,
        "historical_aliases": ("SMA",)},
    "recursive_mean": {"kernel": recursive_mean, "parameter_word": "SMOOTHING_PERIOD", "warmup_multiple": 4,
        "historical_aliases": ("Wilder smoothing",)},
    "recursive_mean_gain_share": {"kernel": recursive_mean_gain_share, "parameter_word": "SMOOTHING_PERIOD",
                                  "warmup_multiple": 4, "inputs": ("close",), "output_range": (0.0, 100.0),
        "historical_aliases": ("RSI",)},
    "rolling_standard_score": {"kernel": rolling_standard_score, "parameter_word": "LOOKBACK", "warmup_multiple": 1,
        "historical_aliases": ("Bollinger %B", "rolling z-score")},
    "rolling_range_position": {"kernel": rolling_range_position, "parameter_word": "LOOKBACK", "warmup_multiple": 1,
                               "inputs": ("close", "high", "low"), "output_range": (0.0, 1.0),
        "historical_aliases": ("Stochastic %K", "Williams %R")},
    "rolling_standard_deviation": {"kernel": rolling_standard_deviation, "parameter_word": "LOOKBACK",
                                   "warmup_multiple": 1,
        "historical_aliases": ("Bollinger width",)},
    "relative_change": {"kernel": relative_change, "parameter_word": "LOOKBACK", "warmup_multiple": 1,
                        "warmup_offset_bars": 1, "inputs": ("close",),
        "historical_aliases": ("ROC", "momentum")},
    "recursive_mean_upward_movement_share": {"kernel": recursive_mean_upward_movement_share,
                                             "parameter_word": "SMOOTHING_PERIOD", "warmup_multiple": 4,
                                             "inputs": ("high", "low"), "output_range": (0.0, 100.0),
        "historical_aliases": ("DMI", "+DI", "-DI")},
    # two recursions in a row, so the warm-up is twice a single recursion's
    "recursive_mean_directional_movement_imbalance": {"kernel": recursive_mean_directional_movement_imbalance,
                                                      "parameter_word": "SMOOTHING_PERIOD", "warmup_multiple": 8,
                                                      "inputs": ("high", "low"), "output_range": (0.0, 100.0),
        "historical_aliases": ("ADX",)},
    "rolling_volume_weighted_mean": {"kernel": rolling_volume_weighted_mean, "parameter_word": "LOOKBACK",
                                     "warmup_multiple": 1, "inputs": ("close", "volume"),
        "historical_aliases": ("VWAP",)},
    "rolling_volume_weighted_close_location": {"kernel": rolling_volume_weighted_close_location,
                                               "parameter_word": "LOOKBACK", "warmup_multiple": 1,
                                               "inputs": ("high", "low", "close", "volume"),
                                               "output_range": (-1.0, 1.0),
        "historical_aliases": ("CMF",)},
    "rolling_money_flow_gain_share": {"kernel": rolling_money_flow_gain_share, "parameter_word": "LOOKBACK",
                                      "warmup_multiple": 1, "warmup_offset_bars": 1,
                                      "inputs": ("high", "low", "close", "volume"),
                                      "output_range": (0.0, 100.0),
        "historical_aliases": ("MFI",)},
}
