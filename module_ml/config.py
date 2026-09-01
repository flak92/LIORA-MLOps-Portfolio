"""Frozen experiment configuration — the only source of ML constants.

Every parameter below is fixed a priori and never tuned; changing one defines a
different experiment, and the git commit is the record of which one ran.
"""

from __future__ import annotations

from datetime import UTC, datetime

from module_data.config import (  # re-exported
    BYTES_PER_KIBIBYTE, DUCKDB_MEMORY_LIMIT, MILLISECONDS_PER_MINUTE, MILLISECONDS_PER_SECOND, MODULE_MONITORING_DIR,
    TICKERS, artifact_dir, build_ticker_parser, parse_tickers, research_ohlcv_duckdb, rounded,
)

SEED = 42

# ---- frozen research window (later data top-ups do not change this experiment)
# The start repeats module_data's DATA_WINDOW_START_UTC on purpose rather than importing it: the
# download window may be widened without moving an experiment already run against this one.
RESEARCH_START_UTC = "2021-01-01"   # inclusive
RESEARCH_END_UTC = "2026-08-26"     # exclusive


def _utc_ms(day: str) -> int:
    return int(datetime.fromisoformat(day).replace(tzinfo=UTC).timestamp() * MILLISECONDS_PER_SECOND)


RESEARCH_START_MS = _utc_ms(RESEARCH_START_UTC)
RESEARCH_END_MS = _utc_ms(RESEARCH_END_UTC)

# ---- hierarchy
HIERARCHY_TIMEFRAMES = ("15m", "1h", "4h")
TIMEFRAME_DURATION_MS = {"15m": 900_000, "1h": 3_600_000, "4h": 14_400_000}
DECISION_TIMEFRAME = "15m"

# ---- feature contract: 5 families x 3 timeframes = 15 columns
# each family is named after what it computes, not after the category it belongs
# to, so a column name is readable without the documentation
FEATURE_FAMILIES = (
    "ema20_minus_ema50_over_atr14",
    "centered_rsi14",
    "atr14_over_close",
    "range_position_20",
    "log_volume_zscore_50",
)
TREND_FAMILY = FEATURE_FAMILIES[0]  # the family the strategy hierarchy reads
TREND_GATE_TIMEFRAME = HIERARCHY_TIMEFRAMES[-1]   # the top timeframe that vetoes a side
# cross-timeframe trend agreement is a strategy rule over these columns, not a sixteenth feature
FEATURE_COLUMNS = tuple(f"{family}_{timeframe}"
                        for timeframe in HIERARCHY_TIMEFRAMES for family in FEATURE_FAMILIES)
EMA_FAST_SPAN_BARS = 20
EMA_SLOW_SPAN_BARS = 50
ATR_WILDER_SMOOTHING_PERIOD_BARS = 14
RSI_WILDER_SMOOTHING_PERIOD_BARS = 14
RANGE_POSITION_LOOKBACK_BARS = 20
LOG_VOLUME_ZSCORE_LOOKBACK_BARS = 50
WARMUP_4H_BARS = 200                # 4 x EMA_SLOW_SPAN_BARS on the top timeframe
WARMUP_END_MS = RESEARCH_START_MS + WARMUP_4H_BARS * TIMEFRAME_DURATION_MS[HIERARCHY_TIMEFRAMES[-1]]

# ---- label contract: triple barrier resolved on the 1m path
ATR_BARRIER_MULTIPLIER = 2.0     # barriers at entry_price +- this multiple of ATR14(last closed 1h bar)
# how an event ended; the values are load-bearing — fill_price compares the
# resolution against the side of the position
EVENT_RESOLUTION_LOWER_BARRIER = -1
EVENT_RESOLUTION_VERTICAL = 0
EVENT_RESOLUTION_UPPER_BARRIER = 1
EVENT_RESOLUTION_AMBIGUOUS = 9
EVENT_RESOLUTION_NAMES = {               # the name of each code, used wherever
    EVENT_RESOLUTION_UPPER_BARRIER: "upper_barrier",     # events are counted or
    EVENT_RESOLUTION_LOWER_BARRIER: "lower_barrier",     # reported
    EVENT_RESOLUTION_VERTICAL: "vertical",
    EVENT_RESOLUTION_AMBIGUOUS: "ambiguous",
}
LABEL_HORIZON_MINUTES = 240               # vertical barrier (240 min = 16 x 15m bars)
LABEL_HORIZON_MS = LABEL_HORIZON_MINUTES * MILLISECONDS_PER_MINUTE

# ---- folds: WARMUP | TRAIN | PURGE | OOS validation | final holdout
FOLD_BOUNDS_UTC = ("2021-01-01", "2022-01-01", "2023-01-01", "2024-01-01",
                   "2025-01-01", RESEARCH_END_UTC)
FOLD_BOUNDS_MS = tuple(_utc_ms(d) for d in FOLD_BOUNDS_UTC)
# F2, F3, F4 — the data-driven selection of hyper-parameters and the threshold
VALIDATION_FOLD_IDS = (2, 3, 4)
FINAL_HOLDOUT_FOLD_ID = 5           # F5 — evaluated, never selected on

# ---- HPO (Optuna TPE, sequential, in-memory)
HYPERPARAMETER_SEARCH_TRIAL_COUNT = 50
HYPERPARAMETER_SEARCH_SPACE = {
    "max_depth": ("int", 2, 6),
    "eta": ("log", 0.01, 0.3),
    "min_child_weight": ("int", 1, 50),
    "subsample": ("float", 0.5, 1.0),
    "colsample_bytree": ("float", 0.5, 1.0),
    "lambda": ("log", 0.1, 10.0),
    "alpha": ("log", 0.01, 1.0),
    "num_boost_round": ("int_step", 100, 800, 50),
}
XGBOOST_FIXED_PARAMETERS = {
    "objective": "multi:softprob",
    "num_class": 3,
    "tree_method": "hist",
    "nthread": 1,
    "seed": SEED,
}

# ---- strategy (evaluation only)
EXECUTION_COST_RATE_PER_TRADE_SIDE = 0.0006              # taker + slippage, per entry and per exit
# how much directional probability edge a signal must carry before it is traded
# (written as the symbol τ in the equations)
ENTRY_EDGE_THRESHOLD_GRID = tuple(round(0.01 * i, 2) for i in range(61))   # 0.00 .. 0.60
MINIMUM_TRADES_PER_VALIDATION_FOLD = 30  # selection guardrail, not an acceptance gate
ANNUALISATION_PERIOD_15M_BARS = 96 * 365        # crypto trades 24/7
# timeframes whose trend sign must agree with the side before an entry is taken
MINIMUM_AGREEING_TREND_TIMEFRAMES = 2

# ---- the asset folder paths: every per-asset file carries the <TICKER>_ prefix, a time series its grid in
# timeframe slots (module_skills/skill_sorting_files_naming_standard.md); built here and nowhere else
TIMEFRAME_SLOT = {"15m": "ss-15-hh-dd-MM", "1h": "ss-mm-01-dd-MM", "4h": "ss-mm-04-dd-MM"}
MODULE_MONITORING_ML_STATUS_JSON_PATH = MODULE_MONITORING_DIR / "ml_status.json"


def features_parquet(ticker, timeframe):
    return artifact_dir(ticker) / f"{ticker}_features_{TIMEFRAME_SLOT[timeframe]}.parquet"


def label_events_parquet(ticker):
    return artifact_dir(ticker) / f"{ticker}_label_events_{TIMEFRAME_SLOT[DECISION_TIMEFRAME]}.parquet"


def oos_predictions_parquet(ticker):
    return artifact_dir(ticker) / f"{ticker}_oos_predictions_{TIMEFRAME_SLOT[DECISION_TIMEFRAME]}.parquet"


def parameters_json(ticker):
    return artifact_dir(ticker) / f"{ticker}_parameters.json"


def model_evaluation_json(ticker):
    return artifact_dir(ticker) / f"{ticker}_model_evaluation.json"


def strategy_evaluation_json(ticker):
    return artifact_dir(ticker) / f"{ticker}_strategy_evaluation.json"


def asset_readme_md(ticker):
    return artifact_dir(ticker) / f"{ticker}_README.md"


# the three files an asset must hold before its research can be read: the search result, the model
# report and the strategy report — the set is_artifact_set_complete() below folds over
ARTIFACT_SET_DESCRIPTORS = (parameters_json, model_evaluation_json, strategy_evaluation_json)


def is_artifact_set_complete(ticker: str) -> bool:
    """Whether the folder holds all three — the one question status.py and the endpoint ask;
    completeness, never freshness."""
    return all(descriptor(ticker).exists() for descriptor in ARTIFACT_SET_DESCRIPTORS)
