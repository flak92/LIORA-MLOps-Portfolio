"""Frozen experiment configuration of the research layer — the label, fold, search and strategy constants,
reading the feature layer's contract per asset from <TICKER>_catalogue.json — never that layer's configuration.

Every parameter below is fixed a priori and never tuned; changing one defines a
different experiment, and the git commit is the record of which one ran.
"""

from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime
from pathlib import Path

# twice by extraction — identical in module_data/config.py, module_features/config.py, module_ml/config.py
# (module_skills/glossary.md § Twice by extraction): the units, the ceiling, the two stores this module touches and their
# descriptors, and the one CLI every stage shares; a change to one copy is a change to every copy, by hand
MILLISECONDS_PER_SECOND = 1000
MILLISECONDS_PER_MINUTE = 60_000
BYTES_PER_KIBIBYTE = 1024
DUCKDB_MEMORY_LIMIT = "4GB"
STORE_ASSETS_ARTIFACTS_DIR = Path(os.environ["STORE_ASSETS_ARTIFACTS_DIR"])
STORE_STATUS_DIR = Path(os.environ["STORE_STATUS_DIR"])


def to_utc_ms(day: str) -> int:
    """A UTC calendar day, `YYYY-MM-DD`, as the epoch milliseconds of its midnight."""
    return int(datetime.fromisoformat(day).replace(tzinfo=UTC).timestamp() * MILLISECONDS_PER_SECOND)


def artifact_dir(ticker: str) -> Path:
    """One directory per ticker; inside it one file per artifact, named for it."""
    return STORE_ASSETS_ARTIFACTS_DIR / ticker


def research_ohlcv_duckdb(ticker: str) -> Path:
    """The asset's own database — the market object's one home, resident in the asset folder."""
    return artifact_dir(ticker) / f"{ticker}_research_ohlcv.duckdb"


def build_ticker_parser(description: str) -> argparse.ArgumentParser:
    """The one CLI every stage shares: --tickers, required — the launcher names the basket, a stage never does."""
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--tickers", required=True, help="comma-separated tickers, e.g. BTC or BTC,ETH")
    return ap


def parse_tickers(tickers_csv: str) -> list[str]:
    return [ticker.strip().upper() for ticker in tickers_csv.split(",") if ticker.strip()]


def rounded(x, ndigits: int):
    """round() that tolerates None: the NULL a scan reports when no row qualifies, the None a fold without trades reports."""
    return None if x is None else round(float(x), ndigits)


SEED = 42

# ---- the frozen research window — twice by extraction: identical in module_features/config.py, where it bounds the bars
# and the catalogue, and here, where it bounds the labels and the folds; a later top-up of the data moves neither
RESEARCH_START_UTC = "2021-01-01"   # inclusive
RESEARCH_END_UTC = "2026-08-26"     # exclusive
RESEARCH_START_MS = to_utc_ms(RESEARCH_START_UTC)
RESEARCH_END_MS = to_utc_ms(RESEARCH_END_UTC)

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
# F2, F3, F4 — the data-driven selection of the hyper-parameters, the threshold and, once a set is promoted, the feature set
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

# ---- the feature layer's contract, per asset: <TICKER>_catalogue.json, written by module_features.catalogue and read once
# per stage by dataset.load_catalogue — carried as `cat` (xy["catalogue"]) into every helper below; a helper reads the
# dict and builds a path, and never reads a file
TREND_GATE_FEATURE_DEFINITION = "ema20_minus_ema50_over_atr14"   # the definition the strategy reads on every timeframe, by name, set or no set


def catalogue_json(ticker):
    return artifact_dir(ticker) / f"{ticker}_catalogue.json"


def timeframes(cat: dict) -> tuple[str, ...]:
    """The hierarchy as the contract lists it, finest first."""
    return tuple(entry["timeframe"] for entry in cat["timeframes"])


def timeframe_entry(cat: dict, timeframe: str) -> dict:
    """One timeframe of the contract: its token, its file-name slot and its duration."""
    return next(entry for entry in cat["timeframes"] if entry["timeframe"] == timeframe)


def decision_slot(cat: dict) -> str:
    return timeframe_entry(cat, cat["decision_timeframe"])["slot"]


def trend_gate_timeframe(cat: dict) -> str:
    """The top timeframe of the hierarchy — the one that vetoes a side."""
    return timeframes(cat)[-1]


# twice by extraction — identical in module_features/config.py: the grammar of module_features/skills/skill_feature_taxonomy.md
def feature_id(definition_name: str, timeframe: str) -> str:
    """The column of X and the key of an importance: the definition aligned to the decision grid on one timeframe."""
    return f"{definition_name}_{timeframe}"


def catalogue_feature_ids(cat: dict) -> tuple[str, ...]:
    """Every feature id the catalogue offers, timeframe-major and catalogue-order within."""
    return tuple(feature_id(name, timeframe) for timeframe in timeframes(cat) for name in cat["columns_by_timeframe"][timeframe])


# ---- the asset folder paths: every per-asset file carries the <TICKER>_ prefix, a time series its grid in
# timeframe slots (module_skills/skill_sorting_files_naming_standard.md), the decision slot read off the contract;
# built here and nowhere else — the feature parquets named by the contract itself
ML_STATUS_JSON_PATH = STORE_STATUS_DIR / "ml_status.json"


def features_parquet(ticker, cat, timeframe):
    return artifact_dir(ticker) / cat["parquet_by_timeframe"][timeframe]


def label_events_parquet(ticker, cat):
    return artifact_dir(ticker) / f"{ticker}_label_events_{decision_slot(cat)}.parquet"


def oos_predictions_parquet(ticker, cat):
    return artifact_dir(ticker) / f"{ticker}_oos_predictions_{decision_slot(cat)}.parquet"


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
