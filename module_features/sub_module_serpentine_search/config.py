"""What a hand may set for the serpentine search, what the search is made of, and where its files lie — the only
place this sub-module builds a path.

It reads the feature layer's own configuration for what the layer already knows: where an asset's artifacts are,
how a ticker reaches a stage, and the window the experiment froze. What it does not read is the other module: the
values a state is made of and the files the evaluation contract names are registered copies, because the state
this sub-module moves is the state that module scores, and a copy that drifts makes every cache lookup miss.
"""

from __future__ import annotations

from .. import config as features_config

# ---- CONFIGURABLES: what an operator may set in the serpentine search, one record each, its value written nowhere
# else — the constants below and the features terminal's copies read it, the module's snapshot publishes the records.
# DEFAULT is a starting point of the experiment, SPECTRUM the legal values of one knob, WIRING a technical contract
CONFIGURABLES = (
    {"name": "SERPENTINE_SEARCH_BEAM_WIDTH", "value": 3, "class": "DEFAULT", "unit": "states",
     "meaning": "the branches a family keeps; 1 is one champion moved one move at a time", "tui": False,
     "experiment_identity": True, "requires_rerun": "features-serpentine-search",
     "risk": "another experiment: the recorded serpentine search starts again"},
    # twice by extraction
    {"name": "GRID_BY_COORDINATE_DEFAULT", "class": "SPECTRUM", "unit": "grid points per barrier coordinate",
     "value": {"label_barrier_true_range_multiplier": [1.75, 2.0, 2.25],
               "label_horizon": ["2h", "4h", "8h", "12h", "1d"],
               "stop_loss_true_range_multiplier": [1.5, 2.0, 2.5],
               "take_profit_true_range_multiplier": [1.5, 2.0, 2.5]},
     "meaning": "what each barrier coordinate may be searched over — the preset a draft of the profile offers; "
                "multipliers are multiples of a quarter, exact in binary, a horizon a duration token",
     "tui": True, "experiment_identity": True, "requires_rerun": "features-serpentine-search",
     "risk": "a profile drafted from another grid describes another experiment"},
    # twice by extraction
    {"name": "PROMOTE_TARGET", "value": "features-serpentine-search-promote", "class": "WIRING",
     "unit": "make target", "meaning": "the module's target that runs the promotion, the one the features terminal "
                                        "opens its own screen for", "tui": True, "experiment_identity": False,
     "requires_rerun": "none", "risk": "the terminal's option and its screen part ways"},
)
# every record's value by its name — what a constant below reads
VALUE_BY_CONFIGURABLE = {record["name"]: record["value"] for record in CONFIGURABLES}

SERPENTINE_SEARCH_BEAM_WIDTH = VALUE_BY_CONFIGURABLE["SERPENTINE_SEARCH_BEAM_WIDTH"]

# ---- what the search is made of ---------------------------------------------------------------------------
SERPENTINE_SEARCH_MOVE_FORWARD = "forward"     # a move that grows the state
SERPENTINE_SEARCH_MOVE_BACKWARD = "backward"   # a move that shrinks it — kept when no worse on a calibration run only
SERPENTINE_SEARCH_LOOP_BARRIER = "barrier"
SERPENTINE_SEARCH_LOOP_FEATURE_SET = "feature_set"
SERPENTINE_SEARCH_LOOP_HPO = "hpo"
# one round, family by family, in the order it runs them. The hyper-parameter family is last, so the turn that
# reads its answer ends the round and no later turn has to recover a study; moving it is a new decision.
ROUND_SCHEDULE = ((SERPENTINE_SEARCH_LOOP_BARRIER, "trade"),
                  (SERPENTINE_SEARCH_LOOP_BARRIER, "label"),
                  (SERPENTINE_SEARCH_LOOP_FEATURE_SET, SERPENTINE_SEARCH_MOVE_FORWARD),
                  (SERPENTINE_SEARCH_LOOP_FEATURE_SET, SERPENTINE_SEARCH_MOVE_BACKWARD),
                  (SERPENTINE_SEARCH_LOOP_HPO, "study"))
# twice by extraction
SERPENTINE_SEARCH_ROUND_LOOPS = tuple(dict.fromkeys(loop for loop, _ in ROUND_SCHEDULE))

# twice by extraction
SELECTION_FOLD_MEASURE = "cagr"   # the measure the fold gate reads; the study's own gate reads the copy in ML

# ---- the noise a proposal has to clear: the asset's noise sigma — the standard deviation of one evaluation's path
# CAGR, a number of the profile — times k(N), the multiple at which the best of N states, each scored with noise of its
# own, beats a start that carries its own by chance at the rate below; k(N) by Gauss-Hermite quadrature and bisection,
# a fixed node count, bracket and number of halvings, so one N gives one k on every machine
PROPOSAL_THRESHOLD_FALSE_EXCEEDANCE_RATE = 0.05
PROPOSAL_THRESHOLD_QUADRATURE_NODE_COUNT = 160
PROPOSAL_THRESHOLD_BISECTION_BRACKET_MULTIPLES = (0.0, 12.0)
PROPOSAL_THRESHOLD_BISECTION_ITERATION_COUNT = 64
# the median absolute deviation of a normal sample times this is its standard deviation
NOISE_MEDIAN_ABSOLUTE_DEVIATION_SCALE = 1.4826

# ---- the values a state is made of, which the module that scores it owns ------------------------------------
# twice by extraction
SEED = 42
# twice by extraction
VALIDATION_FOLD_IDS = (2, 3, 4)
# twice by extraction
BARRIER_COORDINATE_CASTS = {"label_barrier_true_range_multiplier": float, "label_horizon": str,
                            "take_profit_true_range_multiplier": float, "stop_loss_true_range_multiplier": float}
# twice by extraction
BARRIER_COORDINATE_NAMES = tuple(BARRIER_COORDINATE_CASTS)
# twice by extraction
START_BY_COORDINATE_DEFAULT = {
    "label_barrier_true_range_multiplier": 2.0,
    "label_horizon": "4h",
    "stop_loss_true_range_multiplier": 2.0,
    "take_profit_true_range_multiplier": 2.0,
}
# twice by extraction
TRADE_EXIT_COORDINATE_NAMES = ("take_profit_true_range_multiplier", "stop_loss_true_range_multiplier")


# twice by extraction
def timeframes(cat: dict) -> tuple[str, ...]:
    """The hierarchy as the contract lists it, finest first."""
    return tuple(entry["timeframe"] for entry in cat["timeframes"])


# ---- the search's own files ---------------------------------------------------------------------------------
# twice by extraction
def serpentine_search_json(ticker):
    """Where the search stands: what it was conditioned on, its beam, its champion, the path it took and the
    states it proposes. Written before the request beside it, so a stop never leaves an answer without a state."""
    return features_config.artifact_dir(ticker) / f"{ticker}_serpentine_search.json"


# twice by extraction
def serpentine_search_trials_jsonl(ticker):
    """Every scored state, one JSON object a line, appended and never rewritten. A line's number, counted from
    one, is the trial's index — what the champion, the beam, a parent and a proposal carry — so a reader joins a
    trial's columns, geometry and numbers here and the state file holds none of them."""
    return features_config.artifact_dir(ticker) / f"{ticker}_serpentine_search_trials.jsonl"


# twice by extraction
def serpentine_search_profile_json(ticker):
    """What a hand asks the search to look at: the columns admitted, the state to start from, the grid of each
    coordinate, the loops of a round and the asset's noise sigma its proposal clears. Drafted, never derived."""
    return features_config.artifact_dir(ticker) / f"{ticker}_serpentine_search_profile.json"


# ---- the files of the evaluation contract, named by both sides ------------------------------------------------
# twice by extraction
def score_request_json(ticker):
    return features_config.artifact_dir(ticker) / f"{ticker}_score_request.json"


# twice by extraction
def score_response_json(ticker):
    return features_config.artifact_dir(ticker) / f"{ticker}_score_response.json"


# ---- the artifacts of the chain this search reads and the promotion writes -------------------------------------
# twice by extraction
def parameters_json(ticker):
    return features_config.artifact_dir(ticker) / f"{ticker}_parameters.json"


# twice by extraction
def feature_set_json(ticker):
    return features_config.artifact_dir(ticker) / f"{ticker}_feature_set.json"


# twice by extraction
def barriers_json(ticker):
    """The asset's promoted barrier geometry — absent, the frozen constants of the module that labels are."""
    return features_config.artifact_dir(ticker) / f"{ticker}_barriers.json"
