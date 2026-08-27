"""Frozen experiment configuration — the only source of ML constants.

Every parameter below is fixed a priori and never tuned; changing one defines a
different experiment, and the git commit is the record of which one ran.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pipeline.config import ASSETS_DIR, DB_PATH, TICKERS, symbol  # noqa: F401  (re-exported)

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
FAMILIES = ("trend", "momentum", "volatility", "structure", "activity")
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
HORIZON_BARS = 16                   # vertical barrier: 16 x 15m = 240 minutes
HORIZON_MS = HORIZON_BARS * TF_MS["15m"]

# ---- split: WARMUP | TRAIN | PURGE+GAP | OOS validation | locked TEST
FOLD_BOUNDS_UTC = ("2021-01-01", "2022-01-01", "2023-01-01", "2024-01-01",
                   "2025-01-01", RESEARCH_END_UTC)
FOLD_BOUNDS_MS = tuple(_utc_ms(d) for d in FOLD_BOUNDS_UTC)
VALIDATION_SPLITS = (2, 3, 4)       # OOS = F2, F3, F4 (expanding training)
TEST_SPLIT = 5                      # locked F5, read once

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
TAU_GRID = tuple(round(0.01 * i, 2) for i in range(61))   # 0.00 .. 0.60
TAU_MIN_TRADES = 30                  # a tau must produce this many trades in every validation fold
BARS_PER_YEAR_15M = 96 * 365        # crypto trades 24/7
AGREE_MIN = 2                       # levels whose trend sign must agree with the side
