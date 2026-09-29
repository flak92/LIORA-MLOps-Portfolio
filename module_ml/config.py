"""Frozen experiment configuration of the research layer — the label, fold, search and strategy constants,
reading the feature layer's contract per asset from <TICKER>_catalogue.json — never that layer's configuration.

What an operator may set is a record of CONFIGURABLES, fixed a priori and never tuned; changing one defines a
different experiment or run, and the git commit is the record of which one ran.
"""

from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime
from pathlib import Path

# ---- CONFIGURABLES: what an operator may set in this module, one record each, its value written nowhere else — the
# constants below read it, the module's snapshot publishes the records and `make skills-configurables` renders every
# module's into one table. DEFAULT is a starting point of the experiment, SPECTRUM the legal values of one knob and
# WIRING a technical setting of a run; a value derived from them and a constant of the method stand below the block,
# and a register is no configurable
CONFIGURABLES = (
    # twice by extraction
    {"name": "SEED", "value": 42, "class": "DEFAULT", "unit": "seed",
     "meaning": "the one seed of every study and every fit", "tui": False, "experiment_identity": True,
     "requires_rerun": "ml-all, features-serpentine-search", "risk": "another experiment: every study, fit and trade changes"},
    {"name": "FOLD_BOUNDS_UTC", "class": "DEFAULT", "unit": "UTC days, the first inclusive and the last exclusive",
     "value": ("2021-01-01", "2022-01-01", "2023-01-01", "2024-01-01", "2025-01-01", "2026-08-26"),
     "meaning": "the bounds of the five folds — F1 trained on, F2 to F4 validation, F5 the final holdout — the first "
                "and the last the research window", "tui": False, "experiment_identity": True,
     "requires_rerun": "ml-all, features-serpentine-search", "risk": "another experiment: every fold moves"},
    {"name": "LABEL_BARRIER_TRUE_RANGE_TIMEFRAME", "value": "1h", "class": "DEFAULT", "unit": "timeframe token",
     "meaning": "the timeframe whose last closed bar sets the barrier width — an entry of the hierarchy", "tui": False,
     "experiment_identity": True, "requires_rerun": "ml-all, features-serpentine-search",
     "risk": "another label: every fit and trade changes"},
    {"name": "LABEL_BARRIER_TRUE_RANGE_SMOOTHING_PERIOD_BARS", "value": 14, "class": "DEFAULT",
     "unit": "bars of the barrier's timeframe",
     "meaning": "the barrier's width: the recursive mean of the true range over this many bars — a label parameter, "
                "not a feature", "tui": False, "experiment_identity": True,
     "requires_rerun": "ml-all, features-serpentine-search", "risk": "another label: every fit and trade changes"},
    # twice by extraction
    {"name": "START_BY_COORDINATE_DEFAULT", "class": "DEFAULT",
     "unit": "the label's multiplier of the true range, the horizon token, the stop's and the take-profit's multipliers",
     "value": {"label_barrier_true_range_multiplier": 2.0, "label_horizon": "4h",
               "stop_loss_true_range_multiplier": 2.0, "take_profit_true_range_multiplier": 2.0},
     "meaning": "where each barrier coordinate stands until a promotion writes another: the geometry the chain falls "
                "back to and the point the serpentine search and a draft pin an unsearched coordinate at",
     "tui": True, "experiment_identity": True, "requires_rerun": "ml-all, features-serpentine-search",
     "risk": "another label and another trade for every asset without a promotion"},
    {"name": "HYPERPARAMETER_SEARCH_STARTUP_TRIAL_COUNT", "value": 5, "class": "DEFAULT", "unit": "trials",
     "meaning": "the trials TPE draws at random before it models, completed and pruned alike", "tui": False,
     "experiment_identity": True, "requires_rerun": "ml-hpo, ml-train, ml-strategy, ml-status, features-serpentine-search",
     "risk": "at or above the trial count the study is a random search wearing TPE's name"},
    {"name": "HYPERPARAMETER_SEARCH_TRIAL_COUNT", "value": 8, "class": "DEFAULT", "unit": "trials",
     "meaning": "the trials one study draws — the stage's and each beam parent's in the serpentine search",
     "tui": False, "experiment_identity": True,
     "requires_rerun": "ml-hpo, ml-train, ml-strategy, ml-status, features-serpentine-search",
     "risk": "a budget below the method's own: the chosen point is noise"},
    {"name": "HYPERPARAMETER_SEARCH_SPACE", "class": "SPECTRUM",
     "unit": "per parameter the draw's kind and bounds, and a step where it has one",
     "value": {"max_depth": ("int", 2, 6), "eta": ("log", 0.01, 0.3), "min_child_weight": ("int", 1, 50),
               "subsample": ("float", 0.5, 1.0), "colsample_bytree": ("float", 0.5, 1.0),
               "lambda": ("log", 0.1, 10.0), "alpha": ("log", 0.01, 1.0),
               "num_boost_round": ("int_step", 50, 600, 50)},
     "meaning": "the eight hyper-parameters a study draws, in xgboost's own spelling", "tui": False,
     "experiment_identity": True, "requires_rerun": "ml-hpo, ml-train, ml-strategy, ml-status, features-serpentine-search",
     "risk": "another space: the chosen point and everything after it change"},
    {"name": "EXECUTION_COST_RATE_PER_TRADE_SIDE", "value": 0.0006, "class": "DEFAULT", "unit": "share of notional per side",
     "meaning": "taker fee and slippage, charged on the entry and on the exit of every trade", "tui": False,
     "experiment_identity": True, "requires_rerun": "ml-all, features-serpentine-search",
     "risk": "every path, threshold and study objective moves with it"},
    {"name": "ENTRY_EDGE_THRESHOLD_GRID", "class": "SPECTRUM", "unit": "probability edge",
     "value": (
              0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16,
              0.17, 0.18, 0.19, 0.2, 0.21, 0.22, 0.23, 0.24, 0.25, 0.26, 0.27, 0.28, 0.29, 0.3, 0.31, 0.32, 0.33,
              0.34, 0.35, 0.36, 0.37, 0.38, 0.39, 0.4, 0.41, 0.42, 0.43, 0.44, 0.45, 0.46, 0.47, 0.48, 0.49, 0.5,
              0.51, 0.52, 0.53, 0.54, 0.55, 0.56, 0.57, 0.58, 0.59, 0.6),
     "meaning": "the thresholds of probability edge a signal must carry before it is traded — τ in the equations",
     "tui": False, "experiment_identity": True, "requires_rerun": "ml-all, features-serpentine-search",
     "risk": "the threshold is chosen from other points: every trade can move"},
    {"name": "MINIMUM_TRADES_PER_VALIDATION_FOLD", "value": 30, "class": "DEFAULT", "unit": "trades per validation fold",
     "meaning": "the trade floor a threshold must clear on every validation fold — a selection guardrail, not an "
                "acceptance gate", "tui": False, "experiment_identity": True,
     "requires_rerun": "ml-all, features-serpentine-search", "risk": "a threshold chosen on too few trades to mean anything"},
    {"name": "MINIMUM_AGREEING_TREND_TIMEFRAMES", "value": 2, "class": "DEFAULT", "unit": "timeframes",
     "meaning": "the timeframes whose trend sign must agree with the side before an entry is taken", "tui": False,
     "experiment_identity": True, "requires_rerun": "ml-hpo, ml-train, ml-strategy, ml-status, features-serpentine-search",
     "risk": "another strategy: every trade changes"},
    # twice by extraction
    {"name": "DUCKDB_MEMORY_LIMIT", "value": "4GB", "class": "WIRING", "unit": "DuckDB memory size",
     "meaning": "the ceiling of every DuckDB connection of the module, beside threads=1", "tui": False,
     "experiment_identity": False, "requires_rerun": "none",
     "risk": "a stage stops on memory where its container holds less"},
)
# every record's value by its name — what a constant below reads
VALUE_BY_CONFIGURABLE = {record["name"]: record["value"] for record in CONFIGURABLES}

# twice by extraction
MILLISECONDS_PER_SECOND = 1000
# twice by extraction
MILLISECONDS_PER_MINUTE = 60_000
# twice by extraction
BYTES_PER_KIBIBYTE = 1024
# twice by extraction
DUCKDB_MEMORY_LIMIT = VALUE_BY_CONFIGURABLE["DUCKDB_MEMORY_LIMIT"]
# twice by extraction
STORE_ASSETS_ARTIFACTS_DIR = Path(os.environ["STORE_ASSETS_ARTIFACTS_DIR"])
# twice by extraction
STORE_STATUS_DIR = Path(os.environ["STORE_STATUS_DIR"])

# this module's alone: the trials store, where hpo.py leaves every point it drew
# twice by extraction
STORE_TRIALS_DIR = Path(os.environ["STORE_TRIALS_DIR"])


# twice by extraction
def to_utc_ms(day: str) -> int:
    """A UTC calendar day, `YYYY-MM-DD`, as the epoch milliseconds of its midnight."""
    return int(datetime.fromisoformat(day).replace(tzinfo=UTC).timestamp() * MILLISECONDS_PER_SECOND)


# twice by extraction
def artifact_dir(ticker: str) -> Path:
    """The asset's folder of non-tabular files — the segment `ticker=<TICKER>/` a partition carries, at the root of the
    store; inside it one file per artifact, named for it."""
    return STORE_ASSETS_ARTIFACTS_DIR / f"ticker={ticker}"


# twice by extraction
def partition_dir(family: str, ticker: str, timeframe: str | None = None, store: Path = STORE_ASSETS_ARTIFACTS_DIR) -> Path:
    """One partition of a table family: `<store>/<family>/ticker=<TICKER>/[timeframe=<timeframe>/]` — Hive's
    `key=value`, the value the ticker in capitals and the compact token; the store the artifacts store unless the
    family lives in another."""
    partition = store / family / f"ticker={ticker}"
    return partition if timeframe is None else partition / f"timeframe={timeframe}"


# twice by extraction
def ohlcv_1m_canonical_parquet(ticker: str) -> Path:
    """The canonical series of the asset — the family `ohlcv_1m_canonical`, one Parquet file per partition, written by ingest alone."""
    return partition_dir("ohlcv_1m_canonical", ticker) / "ohlcv_1m_canonical.parquet"


# twice by extraction
def bars_parquet(ticker: str, timeframe: str) -> Path:
    """One timeframe's bars of the asset — the family `bars`, partitioned by asset and timeframe, written by bars alone."""
    return partition_dir("bars", ticker, timeframe) / "bars.parquet"


# twice by extraction
def schema_json(family: str, store: Path = STORE_ASSETS_ARTIFACTS_DIR) -> Path:
    """A family's schema as data, beside its partitions: the columns of the union of the partitions, written by the family's
    one writer; the store the artifacts store unless the family lives in another."""
    return store / family / "schema.json"


# twice by extraction
def build_ticker_parser(description: str) -> argparse.ArgumentParser:
    """The one CLI every stage shares: --tickers, required — the launcher names the basket, a stage never does."""
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--tickers", required=True, help="comma-separated tickers, e.g. BTC or BTC,ETH")
    return ap


# twice by extraction
def parse_tickers(tickers_csv: str) -> list[str]:
    """The --tickers value as a basket: split on commas, trimmed, upper case, an empty item dropped."""
    return [ticker.strip().upper() for ticker in tickers_csv.split(",") if ticker.strip()]


# twice by extraction
def rounded(value, ndigits: int):
    """round() that tolerates None: the NULL a scan reports when no row qualifies, the None a fold without trades reports."""
    return None if value is None else round(float(value), ndigits)


# twice by extraction
SEED = VALUE_BY_CONFIGURABLE["SEED"]

# ---- the frozen research window: here it bounds the labels and the folds — the first and the last bound of the folds;
# a later top-up of the data moves neither
# twice by extraction
RESEARCH_START_UTC = VALUE_BY_CONFIGURABLE["FOLD_BOUNDS_UTC"][0]    # inclusive
# twice by extraction
RESEARCH_END_UTC = VALUE_BY_CONFIGURABLE["FOLD_BOUNDS_UTC"][-1]     # exclusive
# twice by extraction
RESEARCH_START_MS = to_utc_ms(RESEARCH_START_UTC)
# twice by extraction
RESEARCH_END_MS = to_utc_ms(RESEARCH_END_UTC)

# ---- label contract: triple barrier resolved on the 1m path
# where each barrier coordinate stands until a promotion writes another: the geometry the chain falls back to
# in dataset.load_barriers(), and the point the serpentine search pins an unsearched coordinate at
# twice by extraction
START_BY_COORDINATE_DEFAULT = VALUE_BY_CONFIGURABLE["START_BY_COORDINATE_DEFAULT"]
LABEL_BARRIER_TRUE_RANGE_TIMEFRAME = VALUE_BY_CONFIGURABLE["LABEL_BARRIER_TRUE_RANGE_TIMEFRAME"]
LABEL_BARRIER_TRUE_RANGE_SMOOTHING_PERIOD_BARS = VALUE_BY_CONFIGURABLE["LABEL_BARRIER_TRUE_RANGE_SMOOTHING_PERIOD_BARS"]
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
# the vertical barrier, a duration token of the timeframe grammar: the serpentine search moves it a
# token at a time, and one place turns a token into minutes — dataset.barriers_from()
HORIZON_TOKEN_MINUTES = {"1h": 60, "2h": 120, "4h": 240, "8h": 480, "12h": 720, "1d": 1440}

# ---- folds: WARMUP | TRAIN | PURGE | OOS validation | final holdout
FOLD_BOUNDS_UTC = VALUE_BY_CONFIGURABLE["FOLD_BOUNDS_UTC"]
FOLD_BOUNDS_MS = tuple(to_utc_ms(d) for d in FOLD_BOUNDS_UTC)
# F2, F3, F4 — the data-driven selection of the hyper-parameters, the threshold and, once a set is promoted, the feature set
# twice by extraction
VALIDATION_FOLD_IDS = (2, 3, 4)
FINAL_HOLDOUT_FOLD_ID = 5           # F5 — evaluated, never selected on

# ---- HPO (Optuna TPE, sequential, in-memory)
# activation values, not calibration — held until the method is calibrated; the 16-core machine and a recomputed
# feature layer are a new experiment. They are the smallest counts at which every part of the method runs: TPE draws at
# random until it has HYPERPARAMETER_SEARCH_STARTUP_TRIAL_COUNT trials to fit on — completed and pruned alike, in this
# Optuna — and models from the next one, so trials 6 to 8 of every study are the sampler's own, and a trial count at or
# below the startup count would be a random search wearing its name. The startup count is written here rather than left
# to the library: a number that decides how the experiment searches is the experiment's, and a default that moves with a
# version bump is not a frozen method
HYPERPARAMETER_SEARCH_STARTUP_TRIAL_COUNT = VALUE_BY_CONFIGURABLE["HYPERPARAMETER_SEARCH_STARTUP_TRIAL_COUNT"]
HYPERPARAMETER_SEARCH_TRIAL_COUNT = VALUE_BY_CONFIGURABLE["HYPERPARAMETER_SEARCH_TRIAL_COUNT"]
HYPERPARAMETER_SEARCH_SPACE = VALUE_BY_CONFIGURABLE["HYPERPARAMETER_SEARCH_SPACE"]
XGBOOST_FIXED_PARAMETERS = {
    "objective": "multi:softprob",
    "num_class": 3,
    "tree_method": "hist",
    "nthread": 1,
    "seed": SEED,
}

# ---- strategy (evaluation only)
EXECUTION_COST_RATE_PER_TRADE_SIDE = VALUE_BY_CONFIGURABLE["EXECUTION_COST_RATE_PER_TRADE_SIDE"]
ENTRY_EDGE_THRESHOLD_GRID = VALUE_BY_CONFIGURABLE["ENTRY_EDGE_THRESHOLD_GRID"]   # 0.00 .. 0.60
MINIMUM_TRADES_PER_VALIDATION_FOLD = VALUE_BY_CONFIGURABLE["MINIMUM_TRADES_PER_VALIDATION_FOLD"]
MINUTES_PER_YEAR = 365 * 1440                   # crypto trades 24/7: the year of a path measured in minutes and of the bars it is sampled at
MINIMUM_AGREEING_TREND_TIMEFRAMES = VALUE_BY_CONFIGURABLE["MINIMUM_AGREEING_TREND_TIMEFRAMES"]

# ---- a state of the serpentine search as this module scores it: the values a state is made of and the measure the
# gate inside a study reads, each of which the feature layer's copy must equal; the final holdout never chooses
# what the gate compares fold by fold: the growth a fold earned per unit of the drawdown it took. The fold
# is the unit of robustness and the validation path is the unit of the goal — the model's own skill is
# measured and reported beside both, and selected on by nothing
# twice by extraction
SELECTION_FOLD_MEASURE = "calmar"
# the barrier geometry a promotion writes, in the order a state keys it, and what each value is however a
# hand wrote it in a grid: a multiplier is a float, a horizon a token of HORIZON_TOKEN_MINUTES
# twice by extraction
BARRIER_COORDINATE_CASTS = {"label_barrier_true_range_multiplier": float, "label_horizon": str,
                            "take_profit_true_range_multiplier": float, "stop_loss_true_range_multiplier": float}
# twice by extraction
BARRIER_COORDINATE_NAMES = tuple(BARRIER_COORDINATE_CASTS)
# the coordinates a move of which changes only where a position leaves: neither a fit nor a prediction depends on
# them, so two states differing only here are one fit identity and share one set of fits
# twice by extraction
TRADE_EXIT_COORDINATE_NAMES = ("take_profit_true_range_multiplier", "stop_loss_true_range_multiplier")
# what a state of a request must build again before it can be scored: the trade's own exit alone, or the model's
# matrix and its three fits, Y walked again before them where the label's own geometry moved — score.fit_identity()
# decides which, and nothing asks which coordinate moved
REBUILD_BACKTEST = "backtest"
REBUILD_FITS = "fits"

# ---- the feature layer's contract, per asset: <TICKER>_catalogue.json, written by module_features.catalogue and read once
# per stage by dataset.load_catalogue — carried as `cat` (xy["catalogue"]) into every helper below; a helper reads the
# dict and builds a path, and never reads a file
TREND_GATE_FEATURE_DEFINITION = "exponential_smoothing20_minus_exponential_smoothing50_over_true_range_recursive_mean14"   # the definition the strategy reads on every timeframe, by name, set or no set


# twice by extraction
def catalogue_json(ticker: str):
    """The asset's copy of the feature layer's contract — what the ML layer reads instead of the feature configuration."""
    return artifact_dir(ticker) / f"{ticker}_catalogue.json"


# twice by extraction
def timeframes(cat: dict) -> tuple[str, ...]:
    """The hierarchy as the contract lists it, finest first."""
    return tuple(entry["timeframe"] for entry in cat["timeframes"])


def timeframe_entry(cat: dict, timeframe: str) -> dict:
    """One timeframe of the contract: its token, its slot and its duration."""
    return next(entry for entry in cat["timeframes"] if entry["timeframe"] == timeframe)


def trend_gate_timeframe(cat: dict) -> str:
    """The top timeframe of the hierarchy — the one that vetoes a side."""
    return timeframes(cat)[-1]


# twice by extraction
def feature_id(definition_name: str, timeframe: str) -> str:
    """The column of X and the key of an importance: the definition aligned to the decision grid on one timeframe."""
    return f"{definition_name}_{timeframe}"


def catalogue_feature_ids(cat: dict) -> tuple[str, ...]:
    """Every feature id the catalogue offers, timeframe-major and catalogue-order within."""
    return tuple(feature_id(name, timeframe) for timeframe in timeframes(cat) for name in cat["columns_by_timeframe"][timeframe])


# ---- the asset's files: the non-tabular ones carry the <TICKER>_ prefix in the asset's folder `ticker=<TICKER>/`; the
# families this module writes — `labels` and `oos_predictions`, partitioned by asset and by the decision timeframe, in the
# artifacts store; `hpo_trials` and `score_trials`, partitioned by asset, in the trials store — are built here and nowhere
# else, the catalogue's partitions named by the contract itself
ML_STATUS_JSON_PATH = STORE_STATUS_DIR / "ml_status.json"   # the snapshot this module writes; the dashboard reads it there


def catalogue_parquet(cat: dict, timeframe: str) -> Path:
    """One timeframe's partition of the catalogue family, where the contract says it is — a path under the artifacts store."""
    return STORE_ASSETS_ARTIFACTS_DIR / cat["parquet_by_timeframe"][timeframe]


def labels_parquet(ticker: str, timeframe: str) -> Path:
    """Y of the asset on its decision grid — the family `labels`, partitioned by asset and by the decision timeframe, written
    by labels alone."""
    return partition_dir("labels", ticker, timeframe) / "labels.parquet"


def oos_predictions_parquet(ticker: str, timeframe: str) -> Path:
    """The out-of-sample class probabilities of the asset on its decision grid — the family `oos_predictions`, partitioned by
    asset and by the decision timeframe, written by train alone."""
    return partition_dir("oos_predictions", ticker, timeframe) / "oos_predictions.parquet"


# twice by extraction
def parameters_json(ticker):
    return artifact_dir(ticker) / f"{ticker}_parameters.json"


def model_evaluation_json(ticker):
    return artifact_dir(ticker) / f"{ticker}_model_evaluation.json"


def strategy_evaluation_json(ticker):
    return artifact_dir(ticker) / f"{ticker}_strategy_evaluation.json"


def hpo_trials_jsonl(ticker: str) -> Path:
    """Every point every hyper-parameter study of the chain drew, one JSON object a line, appended and never rewritten —
    the asset's partition of the `hpo_trials` family, written by `ml-hpo` alone, the same technique the serpentine
    search's ledger uses. The parameters file keeps the one point that was chosen; this keeps the ones that were not,
    which is what makes the choice readable. It carries no run id, no timestamp and no host name, so two studies over
    an empty store leave the same file to the byte."""
    return partition_dir("hpo_trials", ticker, store=STORE_TRIALS_DIR) / "hpo_trials.jsonl"


def score_trials_jsonl(ticker: str) -> Path:
    """Every point a study of the serpentine search drew for the asset — its partition of the `score_trials` family, the
    same row as `hpo_trials`, written by `ml-score` alone."""
    return partition_dir("score_trials", ticker, store=STORE_TRIALS_DIR) / "score_trials.jsonl"


# twice by extraction
def score_request_json(ticker):
    """The states to score, written by whoever drives the serpentine search and read by this module: the kind of scoring
    asked for, the round it runs in, and the states themselves. This module reads it and writes nothing back
    into it."""
    return artifact_dir(ticker) / f"{ticker}_score_request.json"


# twice by extraction
def score_response_json(ticker):
    """What the states of one request are worth, in the order the request named them. Written once the whole
    request has been answered, so a stop leaves no half answer behind."""
    return artifact_dir(ticker) / f"{ticker}_score_response.json"


# twice by extraction
def feature_set_json(ticker):
    return artifact_dir(ticker) / f"{ticker}_feature_set.json"


# twice by extraction
def barriers_json(ticker):
    """The asset's promoted barrier geometry — absent, the frozen constants above are the asset's."""
    return artifact_dir(ticker) / f"{ticker}_barriers.json"


def asset_readme_md(ticker):
    return artifact_dir(ticker) / f"{ticker}_README.md"


# the three files an asset must hold before its research can be read: the search result, the model
# report and the strategy report — the set is_artifact_set_complete() below folds over
ARTIFACT_SET_DESCRIPTORS = (parameters_json, model_evaluation_json, strategy_evaluation_json)


def is_artifact_set_complete(ticker: str) -> bool:
    """Whether the folder holds all three — the one question status.py asks; completeness, never freshness."""
    return all(descriptor(ticker).exists() for descriptor in ARTIFACT_SET_DESCRIPTORS)
