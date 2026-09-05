"""Frozen experiment configuration of the research layer — the label, fold, search and strategy constants,
re-exporting the research window, the timeframe register and the feature catalogue from module_features/config.py.

Every parameter below is fixed a priori and never tuned; changing one defines a
different experiment, and the git commit is the record of which one ran.
"""

from __future__ import annotations

from module_data.config import (  # re-exported
    BYTES_PER_KIBIBYTE, DUCKDB_MEMORY_LIMIT, MILLISECONDS_PER_MINUTE, MILLISECONDS_PER_SECOND, MODULE_MONITORING_DIR,
    TICKERS, artifact_dir, build_ticker_parser, parse_tickers, research_ohlcv_duckdb, rounded, to_utc_ms,
)
from module_features.config import (  # re-exported
    CATALOGUE_COLUMNS, DECISION_TIMEFRAME, DEFAULT_FEATURE_COLUMNS_BY_TIMEFRAME, FEATURE_CATALOGUE, HIERARCHY_TIMEFRAMES,
    INDICATORS, RESEARCH_END_MS, RESEARCH_END_UTC, RESEARCH_START_MS,
    RESEARCH_START_UTC, TIMEFRAME_DURATION_MS, TIMEFRAME_SLOT, TREND_GATE_FEATURE_DEFINITION, TREND_GATE_TIMEFRAME,
    WARMUP_END_MS, WARMUP_TOP_TIMEFRAME_BARS, catalogue_columns, definition_effective_history_hours,
    definition_warmup_bars, feature_definition_name, feature_id, features_parquet,
)

SEED = 42

# ---- label contract: triple barrier resolved on the 1m path
ATR_BARRIER_MULTIPLIER = 2.0     # barriers at entry_price +- this multiple of the ATR of the last closed barrier-timeframe bar
LABEL_BARRIER_ATR_TIMEFRAME = "1h"      # the timeframe whose last closed bar sets the barrier width — an entry of the hierarchy
ATR_WILDER_SMOOTHING_PERIOD_BARS = 14   # the barrier's width, in bars of that timeframe — a label parameter, not a feature
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
FOLD_BOUNDS_MS = tuple(to_utc_ms(d) for d in FOLD_BOUNDS_UTC)
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

# ---- the feature-set search: selected on the model's validation skill, fold by fold; the final holdout never chooses
FEATURE_SET_PROPOSAL_COUNT = 3
FEATURE_SET_SEARCH_MOVE_FORWARD = "forward"
FEATURE_SET_SEARCH_MOVE_BACKWARD = "backward"

# ---- the asset folder paths: every per-asset file carries the <TICKER>_ prefix, a time series its grid in
# timeframe slots (module_skills/skill_sorting_files_naming_standard.md); built here and nowhere else — the
# feature parquets by module_features/config.py
MODULE_MONITORING_ML_STATUS_JSON_PATH = MODULE_MONITORING_DIR / "ml_status.json"


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


def feature_set_search_json(ticker):
    return artifact_dir(ticker) / f"{ticker}_feature_set_search.json"


def feature_set_json(ticker):
    return artifact_dir(ticker) / f"{ticker}_feature_set.json"


def asset_readme_md(ticker):
    return artifact_dir(ticker) / f"{ticker}_README.md"


# the three files an asset must hold before its research can be read: the search result, the model
# report and the strategy report — the set is_artifact_set_complete() below folds over
ARTIFACT_SET_DESCRIPTORS = (parameters_json, model_evaluation_json, strategy_evaluation_json)


def is_artifact_set_complete(ticker: str) -> bool:
    """Whether the folder holds all three — the one question status.py and the endpoint ask;
    completeness, never freshness."""
    return all(descriptor(ticker).exists() for descriptor in ARTIFACT_SET_DESCRIPTORS)
