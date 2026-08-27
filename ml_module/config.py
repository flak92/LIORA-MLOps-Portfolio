"""Frozen experiment configuration — the only source of ML constants.

Every parameter below is fixed a priori and never tuned; changing one defines a
different experiment, and the git commit is the record of which one ran.
"""

from __future__ import annotations

from datetime import UTC, datetime

from data_module.config import (  # noqa: F401  (re-exported)
    DB_PATH, MONITORING_DIR, RESEARCH_ARTIFACTS_DIR, TICKERS, artifact_dir,
    parse_tickers, symbol, ticker_parser,
)

SEED = 42

# ---- frozen research window (later data top-ups do not change this experiment)
RESEARCH_START_UTC = "2021-01-01"   # inclusive
RESEARCH_END_UTC = "2026-08-26"     # exclusive


def _utc_ms(day: str) -> int:
    return int(datetime.fromisoformat(day).replace(tzinfo=UTC).timestamp() * 1000)


RESEARCH_START_MS = _utc_ms(RESEARCH_START_UTC)
RESEARCH_END_MS = _utc_ms(RESEARCH_END_UTC)

# ---- hierarchy
LEVELS = ("15m", "1h", "4h")
TF_MS = {"15m": 900_000, "1h": 3_600_000, "4h": 14_400_000}
DECISION_TF = "15m"

# ---- feature contract: 5 families x 3 levels = 15 columns
# each family is named after what it computes, not after the category it belongs
# to, so a column name is readable without the documentation
FAMILIES = (
    "ema20_minus_ema50_over_atr14",
    "centered_rsi14",
    "atr14_over_close",
    "range_position_20",
    "log_volume_zscore_50",
)
TREND_FAMILY = FAMILIES[0]          # the family the strategy hierarchy reads
# the 2-of-3 trend agreement the strategy needs is a rule over these columns,
# not a sixteenth feature: it carries nothing the three trend columns lack
FEATURE_COLUMNS = tuple(f"{fam}_{lvl}" for lvl in LEVELS for fam in FAMILIES)
EMA_FAST = 20
EMA_SLOW = 50
ATR_N = 14
RSI_N = 14
STRUCTURE_N = 20
ACTIVITY_N = 50
WARMUP_4H_BARS = 200                # 4 x EMA_SLOW span on the top level
WARMUP_END_MS = RESEARCH_START_MS + WARMUP_4H_BARS * TF_MS["4h"]

# ---- label contract: triple barrier resolved on the 1m path
K_BARRIER = 2.0                     # +- K * ATR14(last closed 1h bar)
# how an event ended; the values are load-bearing — fill_price compares the
# resolution against the side of the position
EVENT_RESOLUTION_LOWER_BARRIER = -1
EVENT_RESOLUTION_VERTICAL = 0
EVENT_RESOLUTION_UPPER_BARRIER = 1
EVENT_RESOLUTION_AMBIGUOUS = 9
EVENT_RESOLUTION_NAME = {                # the name of each code, used wherever
    EVENT_RESOLUTION_UPPER_BARRIER: "upper_barrier",     # events are counted or
    EVENT_RESOLUTION_LOWER_BARRIER: "lower_barrier",     # reported
    EVENT_RESOLUTION_VERTICAL: "vertical",
    EVENT_RESOLUTION_AMBIGUOUS: "ambiguous",
}
HORIZON_MINUTES = 240               # vertical barrier (240 min = 16 x 15m bars)
HORIZON_MS = HORIZON_MINUTES * 60_000

# ---- folds: WARMUP | TRAIN | PURGE | OOS validation | final holdout
FOLD_BOUNDS_UTC = ("2021-01-01", "2022-01-01", "2023-01-01", "2024-01-01",
                   "2025-01-01", RESEARCH_END_UTC)
FOLD_BOUNDS_MS = tuple(_utc_ms(d) for d in FOLD_BOUNDS_UTC)
VALIDATION_FOLD_IDS = (2, 3, 4)     # F2, F3, F4 — these choose every parameter
FINAL_HOLDOUT_FOLD_ID = 5           # F5 — evaluated, never selected on

# ---- HPO (Optuna TPE, sequential, in-memory)
N_TRIALS = 50
HPO_SPACE = {
    "max_depth": ("int", 2, 6),
    "eta": ("log", 0.01, 0.3),
    "min_child_weight": ("int", 1, 50),
    "subsample": ("float", 0.5, 1.0),
    "colsample_bytree": ("float", 0.5, 1.0),
    "lambda": ("log", 0.1, 10.0),
    "alpha": ("log", 0.01, 1.0),
    "num_boost_round": ("int_step", 100, 800, 50),
}
XGB_FIXED = {
    "objective": "multi:softprob",
    "num_class": 3,
    "tree_method": "hist",
    "nthread": 1,
    "seed": SEED,
}

# ---- strategy (evaluation only)
COST_PER_SIDE = 0.0006              # taker + slippage, per entry and per exit
# how much directional probability edge a signal must carry before it is traded
# (written as the symbol τ in the equations)
ENTRY_EDGE_THRESHOLD_GRID = tuple(round(0.01 * i, 2) for i in range(61))   # 0.00 .. 0.60
MIN_TRADES_PER_VALIDATION_FOLD = 30  # selection guardrail, not an acceptance gate
BARS_PER_YEAR_15M = 96 * 365        # crypto trades 24/7
AGREE_MIN = 2                       # levels whose trend sign must agree with the side
