"""One turn of the serpentine search: read where the search stands, carry it as far as the answers on disk allow,
and leave either the next question or an ended search.

A turn walks the round from its top. Every search state it needs and already has is a line of the ledger; the first
search family whose search states are not all there is the question it asks, written as `<TICKER>_score_request.json`
and answered by another module as `<TICKER>_score_response.json`. It computes no metric of a search state: every
number a gate, a ranking or a proposal reads comes off an answer, and the noise a proposal has to clear is the asset's
noise sigma, a number of the profile measured once off the answers of a calibration search.

The round is the unit of resume, so nothing says which search family a turn stopped at — the walk finds out by asking
the ledger. What the ledger cannot say is which search states a pass asked for once some of them were already written,
so a pass reconstructs its own membership from the provenance each line carries: a search state of this round, this
search axis, this search family and this first move belonged to the pass in flight, and an older line is a cache hit
that did not.
"""

import collections
import json
import math
import statistics

import numpy as np

from .. import config as features_config
from .. import dataset
from . import axis_barrier, axis_feature_set, config

# the two kinds of question: a state evaluation per search state, or a study and its candidate per beam parent. The
# study family has no generator here — its candidate is drawn by a study on the other side and comes back in an answer.
# twice by extraction
KIND_SCORE = "score"
# twice by extraction
KIND_HYPERPARAMETER = "hpo"


# twice by extraction
def theta(row: dict) -> dict:
    """The search state a state evaluation holds, by itself: the columns of the set, the barrier geometry and the
    hyper-parameter point. A state evaluation's line is this and the numbers it earned."""
    return {"columns_by_timeframe": row["columns_by_timeframe"],
            "best_params": row["best_params"],
            **{name: row[name] for name in config.BARRIER_COORDINATE_NAMES}}


# twice by extraction
def search_state_key(search_state: dict) -> str:
    """A search state as the ledger's index keys it — its own canonical text. A search state is written the way the
    artifacts carry it, so a search state read back off disk keys the same as the one that wrote it, with no shape
    to repair first. Every value is a string, a whole number or a multiple of a quarter, so the equality is
    exact and asks for no tolerance."""
    return json.dumps(search_state, sort_keys=True, separators=(",", ":"))


# ---- the one selection: the objective the experiment froze, read per fold and over a whole search state

def fold_objective(row: dict) -> list[float]:
    """What the gate compares fold by fold — each fold's own measure, in the order the selection fixes. The
    fold is the unit of robustness: a move has to be better on all three, not on average."""
    return [row["validation"][f"fold_{fold_id}"][config.SELECTION_FOLD_MEASURE]
            for fold_id in config.VALIDATION_FOLD_IDS]


def search_state_objective(row: dict) -> float:
    """What the ranking maximises over a whole search state: the chained validation path's CAGR, the one objective
    the experiment froze. Its Calmar ratio and its profit factor are reported beside it and belong neither to the
    objective nor to the order that breaks a tie on it, which is the smaller set and then the earlier state
    evaluation."""
    return row["validation_path"]["cagr"]


def is_gate_cleared(row: dict, parent: dict, move: str) -> bool:
    """Whether a child may be kept at all: better than the search state it came from on every validation fold —
    strictly, and no worse for a move that shrinks the search state, which the ranking then puts first for its fewer
    columns.

    The fold measure is the fold's CAGR, so a better fold is a higher final equity, and the chained path, which
    compounds the folds' final equities, is better too: the objective needs no condition of its own. No margin is
    asked of a move, so small true gains can add up move by move; the noise of the whole search is asked once, of
    the proposal.

    The fold measure is a strategy number, so a search state whose threshold fell back to the grid floor — no point
    of the grid cleared the trade floor in every fold — is refused before it is compared: its numbers stand
    at a threshold nothing qualified for."""
    if not row["entry_edge_threshold_constraint_met"]:
        return False
    pairs = zip(fold_objective(row), fold_objective(parent))
    if move == config.SERPENTINE_SEARCH_MOVE_BACKWARD:
        return all(child >= own for child, own in pairs)
    return all(child > own for child, own in pairs)


# ---- the noise a proposal has to clear -----------------------------------------------------------------------

_NODES, _WEIGHTS = np.polynomial.hermite_e.hermegauss(config.PROPOSAL_THRESHOLD_QUADRATURE_NODE_COUNT)
QUADRATURE = [(float(node), float(weight) / math.sqrt(2.0 * math.pi)) for node, weight in zip(_NODES, _WEIGHTS)]
NORMAL = statistics.NormalDist()


def false_exceedance_rate(multiple: float, selection_hypothesis_count: int) -> float:
    """The chance that the best of `selection_hypothesis_count` hypotheses, each scored with noise of its own, beats a
    start that carries noise of its own by `multiple` noise standard deviations: 1 - E_Z[Phi(k + Z)^N], Z standard
    normal — the expectation by Gauss-Hermite quadrature."""
    return 1.0 - sum(weight * NORMAL.cdf(multiple + node) ** selection_hypothesis_count
                     for node, weight in QUADRATURE)


def proposal_threshold_multiple(selection_hypothesis_count: int) -> float:
    """k(N), the multiple of the noise standard deviation at which that chance is the proposal's rate, N the
    selection hypotheses the search tested — by bisection on a fixed bracket in a fixed number of halvings, one
    deterministic function of N."""
    low, high = config.PROPOSAL_THRESHOLD_BISECTION_BRACKET_MULTIPLES
    for _ in range(config.PROPOSAL_THRESHOLD_BISECTION_ITERATION_COUNT):
        middle = 0.5 * (low + high)
        if false_exceedance_rate(middle, selection_hypothesis_count) > config.PROPOSAL_THRESHOLD_FALSE_EXCEEDANCE_RATE:
            low = middle
        else:
            high = middle
    return 0.5 * (low + high)


def _fitted_part(search_state: dict) -> dict:
    """What a search state is fitted on: the whole of it but the exit of a trade, which a backtest reads alone."""
    return {name: value for name, value in search_state.items() if name not in config.TRADE_EXIT_COORDINATE_NAMES}


def path_cagr_noise_standard_deviation(ledgers: list[list[dict]]) -> float | None:
    """The asset's noise sigma: the standard deviation of one evaluation's path CAGR, read off the ledgers of its
    calibration searches. Each line and the parent its `parent_state_evaluation_index` names are one pair when both
    met the threshold constraint and the child was fitted on its own — a move of the trade's exit alone shares its
    parent's fits and so its noise, and would read as none — each pair of search states once over all the ledgers; of
    the pairs' path CAGR differences, the median absolute deviation scaled to a standard deviation, over the
    square root of two, because a difference carries the noise of two evaluations. None, not measurable, with fewer
    than two pairs: the median absolute deviation of none has no value, and of one is zero, which is no noise."""
    differences = {}
    for state_evaluations in ledgers:
        for row in state_evaluations[1:]:
            parent = state_evaluations[row["parent_state_evaluation_index"] - 1]
            if (row["entry_edge_threshold_constraint_met"] and parent["entry_edge_threshold_constraint_met"]
                    and _fitted_part(theta(row)) != _fitted_part(theta(parent))):
                differences.setdefault((search_state_key(theta(parent)), search_state_key(theta(row))),
                                       search_state_objective(row) - search_state_objective(parent))
    values = list(differences.values())
    if len(values) < 2:
        return None
    centre = statistics.median(values)
    return (config.NOISE_MEDIAN_ABSOLUTE_DEVIATION_SCALE * statistics.median([abs(value - centre) for value in values])
            / math.sqrt(2.0))


def ranking_key(state_evaluations: list[dict], index: int, timeframes: tuple[str, ...]) -> tuple:
    """The one order the beam takes: the objective down, then the smaller set, then the earlier state evaluation."""
    row = state_evaluations[index - 1]
    return (-search_state_objective(row), axis_feature_set.column_count(row["columns_by_timeframe"], timeframes),
            index)


def top_beam(children: list[int], state_evaluations: list[dict], timeframes: tuple[str, ...]) -> list[int]:
    """The beam a search family leaves: the best distinct children by the ranking key, at most the width. Two
    parents can reach one search state and one state evaluation serves both, so the indices are made distinct before
    the width is applied — a beam of three is three search states, not one search state three times."""
    ranked = sorted(dict.fromkeys(children), key=lambda index: ranking_key(state_evaluations, index, timeframes))
    return ranked[:config.SERPENTINE_SEARCH_BEAM_WIDTH]


# ---- the search's progress ----------------------------------------------------------------------------

def path_entry(round_number: int, search_axis: str, search_family: str, move: str, beam: list[int]) -> dict:
    """One accepted expansion of the research path: which search axis and search family moved the search, in which
    direction, the state evaluation it landed on and what the beam held after it. The direction is the search
    family's own, not the one the ledger kept for the search state's first provenance; the state evaluation is named
    by its index and nothing of it is copied: its skill and its path are the ledger's line, and a reader reads them
    there."""
    return {"round": round_number, "search_axis": search_axis, "search_family": search_family,
            "state_evaluation_index": beam[0], "beam": list(beam), "move": move}


def proposals_block(state_evaluations: list[dict], champion_state_evaluation_index: int,
                    noise_sigma: float | None, selection_hypothesis_count: int,
                    search_outcome: str | None) -> list[dict]:
    """The search state a hand may promote: the champion alone, and only when it is not the search state the search
    started from and beats it by more than the noise of the whole search — k(N) times the asset's noise sigma, N the
    selection hypotheses the search tested, because the champion is the best of all of them. Its threshold
    constraint and its folds need no test here: every member of the beam cleared the gate against its parent, so the
    champion meets the constraint and stands at or above the start on every fold. A calibration search, whose
    profile has no sigma yet, proposes nothing, and neither does a search with no outcome yet: a proposal published
    mid-search would let the round a hand happened to read it at choose the search state — an optional stop.

    A proposal is its rank and the index of its state evaluation, and nothing else: the columns, the geometry and
    every number are the ledger's line, so each stands in one file and a reader joins it by the index."""
    if search_outcome is None or noise_sigma is None or champion_state_evaluation_index == 1:
        return []
    gain = (search_state_objective(state_evaluations[champion_state_evaluation_index - 1])
            - search_state_objective(state_evaluations[0]))
    if gain > proposal_threshold_multiple(selection_hypothesis_count) * noise_sigma:
        return [{"proposal": 1, "state_evaluation_index": champion_state_evaluation_index}]
    return []


def write_search_progress(ticker: str, search_progress: dict, state_evaluations: list[dict]) -> None:
    """Where the search stood when the round about to run began — the one place this file is written.

    Written at the top of a round, so it exists before the ledger's first line and every line the ledger
    holds has, on disk, the experiment it belongs to; the write that records an ended search is this same
    write one round later. The state evaluations are the ledger beside it, so the progress is a fixed handful of
    keys and the proposals are derived once a round rather than once a state evaluation. The path and the
    proposals name their state evaluations by index and copy none of their numbers, so what the file holds beside
    its inputs is a few hundred bytes however long the search runs."""
    search_progress["proposals"] = proposals_block(
        state_evaluations, search_progress["champion_state_evaluation_index"] or 1,
        search_progress["inputs"]["profile"]["path_cagr_noise_standard_deviation"],
        search_progress["selection_hypothesis_count"], search_progress["search_outcome"])
    dataset.write_json(config.serpentine_search_json(ticker), search_progress)


def build_search_inputs(best_params: dict, active_columns_by_timeframe: dict, active_barriers: dict,
                        cat: dict, profile: dict) -> dict:
    """What a search is conditioned on: the frozen research window, the seed and the warm-up, the parameters and
    the barrier geometry it starts from, the catalogue it draws from, the profile a hand drafted, the selection
    the experiment froze and its round budget — recorded in the search's progress and compared by equality on a
    rerun. The selection is the beam width and the fold measure, and it and the budget belong here because a rerun
    under another of any is another experiment: it starts its own state evaluations instead of resuming these."""
    return {
        "research_window": {"start_utc": features_config.RESEARCH_START_UTC,
                            "end_utc": features_config.RESEARCH_END_UTC},
        "seed": config.SEED,
        "warmup_top_timeframe_bars": cat["warmup_top_timeframe_bars"],
        "best_params": best_params,
        "catalogue_columns_by_timeframe": {timeframe: tuple(cat["columns_by_timeframe"][timeframe])
                                           for timeframe in config.timeframes(cat)},
        "active_columns_by_timeframe": active_columns_by_timeframe,
        "active_barriers": {name: active_barriers[name] for name in config.BARRIER_COORDINATE_NAMES},
        "profile": profile,
        "selection": {"beam_width": config.SERPENTINE_SEARCH_BEAM_WIDTH, "fold_measure": config.SELECTION_FOLD_MEASURE},
        "round_budget": config.SERPENTINE_SEARCH_ROUND_BUDGET,
    }


def start_search_state(profile: dict, active_columns_by_timeframe: dict, active_barriers: dict,
                       best_params: dict, timeframes: tuple[str, ...]) -> dict:
    """The search state a search starts from: the columns the profile names, else the asset's own set, with the
    asset's own barrier geometry and the parameters it holds fixed."""
    columns = profile["start_columns_by_timeframe"] or active_columns_by_timeframe
    return {"columns_by_timeframe": {timeframe: list(columns[timeframe]) for timeframe in timeframes},
            "best_params": best_params,
            **{name: active_barriers[name] for name in config.BARRIER_COORDINATE_NAMES}}


def objective_line(row: dict) -> str:
    """A search state's objective and the folds the gate reads."""
    return (f"cagr {search_state_objective(row):+.4f} "
            f"folds {config.SELECTION_FOLD_MEASURE} {'/'.join(f'{value:+.4f}' for value in fold_objective(row))} "
            f"trades {'/'.join(str(row['validation'][f'fold_{fold_id}']['trade_count']) for fold_id in config.VALIDATION_FOLD_IDS)}")


def progress_line(ticker: str, round_number: int, search_axis: str, search_family: str, label: str,
                  parent: dict, row: dict) -> str:
    return (f"{ticker} round {round_number} {search_axis}/{search_family} {label} "
            f"cagr {search_state_objective(parent):+.4f} -> {search_state_objective(row):+.4f} "
            f"folds {'/'.join(f'{value:+.4f}' for value in fold_objective(row))}")


# ---- what the asset holds today, read without the module that labels ------------------------------------

# twice by extraction
def load_feature_columns(ticker: str, cat: dict) -> dict:
    """The asset's feature set by timeframe: the promoted file's columns, in catalogue order, else the
    default set. The order is the catalogue's and not the file's, because a set is the same set however a hand
    wrote it down."""
    path = config.feature_set_json(ticker)
    if not path.exists():
        return {timeframe: tuple(cat["default_columns_by_timeframe"][timeframe])
                for timeframe in config.timeframes(cat)}
    promoted = dataset.load_json(path)["columns_by_timeframe"]
    return {timeframe: tuple(sorted(promoted[timeframe], key=cat["columns_by_timeframe"][timeframe].index))
            for timeframe in config.timeframes(cat)}


def load_barrier_coordinates(ticker: str) -> dict:
    """The asset's barrier geometry: the promoted file's when it exists, else the geometry the chain stands
    at. Each value passes its own cast, so 2 and 2.0 are one search state however a hand wrote them. The label
    horizon stays the token it travels as — the minute it stands for is the labelling layer's to read."""
    path = config.barriers_json(ticker)
    promoted = dataset.load_json(path) if path.exists() else {}
    return {name: config.BARRIER_COORDINATE_CASTS[name](promoted.get(name, start))
            for name, start in config.START_BY_COORDINATE_DEFAULT.items()}


def load_best_params(ticker: str) -> dict:
    """The asset's hyper-parameter point: the one its ML chain chose last."""
    return dataset.load_json(config.parameters_json(ticker))["hyperparameter_search_result"]["best_params"]


# ---- the question and the answer -------------------------------------------------------------------------

def result_key(kind: str, result: dict) -> str:
    """The search state a result speaks about: a state evaluation carries its own, a study names its parent's."""
    return result["search_state_key"] if kind == KIND_HYPERPARAMETER else search_state_key(theta(result))


def answers_the_question(response: dict | None, kind: str, round_number: int, keys: list[str]) -> bool:
    """Whether an answer on disk is the answer to the question this turn would ask: the same kind, the same
    round and the same search states in the same order. Anything else answers a question no longer asked."""
    return (response is not None and response["kind"] == kind and response["round"] == round_number
            and [result_key(kind, result) for result in response["results"]] == keys)


def write_state_evaluations(ticker: str, state_evaluations: list[dict], index_by_search_state_key: dict[str, int],
                             rows: list[dict]) -> None:
    """The lines one answer adds, appended in one open and held as the ledger will read them back."""
    if not rows:
        return
    dataset.write_jsonl(config.serpentine_search_state_evaluations_jsonl(ticker), rows)
    for row in rows:
        state_evaluations.append(dataset.to_json_safe(row))
        index_by_search_state_key[search_state_key(theta(state_evaluations[-1]))] = len(state_evaluations)


# ---- a search family's pass ----------------------------------------------------------------------------

def candidates_of(beam: list[int], state_evaluations: list[dict], cat: dict, profile: dict,
                  search_axis: str, search_family: str) -> list[dict]:
    """Every move the search family offers from the beam, in the order the beam and the moves generate them, one
    entry per search state: two parents reaching one search state give one candidate, and it keeps the provenance
    of the first move that reached it."""
    offered, seen = [], set()
    for parent in beam:
        parent_search_state = theta(state_evaluations[parent - 1])
        moves = (axis_barrier.moves(parent_search_state, profile, search_family)
                 if search_axis == config.SERPENTINE_SEARCH_AXIS_BARRIER
                 else axis_feature_set.moves(parent_search_state, cat, profile, search_family))
        for move, label, child in moves:
            key = search_state_key(child)
            if key in seen:
                continue
            seen.add(key)
            offered.append({"key": key, "move": move, "label": label, "search_state": child, "parent": parent})
    return offered


def of_this_pass(row: dict, round_number: int, search_axis: str, search_family: str, candidate: dict) -> bool:
    """Whether a line already in the ledger is one this very pass wrote before it was interrupted — the
    round, the search axis, the search family and the first move that reached the search state, all of them. An
    older line with the same search state is a cache hit, and a cache hit was never part of the question."""
    return (row["round"] == round_number and row["search_axis"] == search_axis
            and row["search_family"] == search_family and row["move"] == candidate["move"]
            and row["parent_state_evaluation_index"] == candidate["parent"])


def pass_membership(candidates: list[dict], state_evaluations: list[dict], index_by_search_state_key: dict[str, int],
                    round_number: int, search_axis: str, search_family: str) -> list[dict]:
    """The search states this pass asked for, whether or not some of them are already written: a search state not
    in the ledger, and a search state whose line this pass itself wrote. Reconstructed and not remembered, so the
    turn holds no cursor and the search's progress carries nothing about a pass in flight."""
    members = []
    for candidate in candidates:
        index = index_by_search_state_key.get(candidate["key"])
        if index is None or of_this_pass(state_evaluations[index - 1], round_number, search_axis, search_family,
                                         candidate):
            members.append(candidate)
    return members


def leave_question(ticker: str, kind: str, round_number: int, search_states: list[dict]) -> None:
    """The next question on disk — written over the one it answers — and only then the answer that is spent.
    Nothing is removed before its successor is written: the loop above reads the question's own file to know
    whether to go on, and a gap between the two would read as the end of the work."""
    dataset.write_json(config.score_request_json(ticker),
                       {"kind": kind, "round": round_number, "search_states": list(search_states)})
    config.score_response_json(ticker).unlink(missing_ok=True)


# ---- one turn ---------------------------------------------------------------------------------------------

def turn(ticker: str) -> None:
    profile = dataset.load_json(config.serpentine_search_profile_json(ticker))
    # the asset's noise sigma, or None on the calibration search that measures it
    noise_sigma = profile["path_cagr_noise_standard_deviation"]
    best = load_best_params(ticker)
    cat = dataset.load_json(features_config.catalogue_json(ticker))
    timeframes = config.timeframes(cat)
    columns, barriers = load_feature_columns(ticker, cat), load_barrier_coordinates(ticker)
    inputs = dataset.to_json_safe(build_search_inputs(best, columns, barriers, cat, profile))

    search_progress_path = config.serpentine_search_json(ticker)
    ledger = config.serpentine_search_state_evaluations_jsonl(ticker)
    request, response_path = config.score_request_json(ticker), config.score_response_json(ticker)
    # the recorded search when its inputs are the inputs of this one and the answer on disk was scored under the
    # evaluation contract it recorded, else a fresh progress and a fresh ledger — a state evaluation of another
    # experiment is not a cache hit for this one, and neither is an answer to its question
    search_progress = dataset.load_json(search_progress_path) if search_progress_path.exists() else None
    response = dataset.load_json(response_path) if response_path.exists() else None
    if (search_progress is None or search_progress["inputs"] != inputs
            or response is not None
            and search_progress["evaluation_contract"] not in (None, response["evaluation_contract"])):
        search_progress = {"inputs": inputs, "evaluation_contract": None, "beam": [],
                           "champion_state_evaluation_index": None, "round_count": 0, "beam_changed": None,
                           "search_outcome": None, "path": [], "selection_hypothesis_count_by_search_axis": {},
                           "selection_hypothesis_count": 0}
        ledger.unlink(missing_ok=True)
        request.unlink(missing_ok=True)
        response_path.unlink(missing_ok=True)
        response = None
    # the first answer records the contract every later one is held to; an answer read at the start confirms it
    contract_confirmed = response is not None
    if contract_confirmed and search_progress["evaluation_contract"] is None:
        search_progress["evaluation_contract"] = response["evaluation_contract"]
    state_evaluations = dataset.load_jsonl(ledger) if ledger.exists() else []
    index_by_search_state_key = {search_state_key(theta(row)): index
                                 for index, row in enumerate(state_evaluations, start=1)}
    # the points the studies of earlier rounds drew and never turned into lines: the count the last boundary
    # wrote, less the lines that boundary already counted. A line of the round in flight is not among them — the
    # boundary predates it — and subtracting it would lose a draw for every candidate a stopped round had written
    drawn_by_search_axis = (
        collections.Counter(search_progress["selection_hypothesis_count_by_search_axis"])
        - collections.Counter(row["search_axis"] for row in state_evaluations
                              if row["search_axis"] and row["round"] <= search_progress["round_count"]))
    start = start_search_state(profile, columns, barriers, best, timeframes)
    # a quiet round proves a fixed point only where no search family the profile runs draws its neighbourhood anew
    # each round
    fixed_point_provable = not any((search_axis, search_family) in config.ROUND_DEPENDENT_SEARCH_FAMILIES
                                   for search_axis, search_family in config.ROUND_SCHEDULE
                                   if search_axis in profile["search_axes"])

    while True:
        write_search_progress(ticker, search_progress, state_evaluations)
        if search_progress["search_outcome"] is not None:
            # an ended search stays ended only under the contract it was scored under: a turn that read no answer
            # asks one question naming no search state — the probe — and the answer's contract decides
            if not contract_confirmed:
                leave_question(ticker, KIND_SCORE, search_progress["round_count"], [])
                return
            break
        round_number = search_progress["round_count"] + 1
        # the search state the search starts from is scored like any other, and its line is the round it predates
        if not state_evaluations:
            if not answers_the_question(response, KIND_SCORE, round_number, [search_state_key(start)]):
                leave_question(ticker, KIND_SCORE, round_number, [start])
                return
            write_state_evaluations(ticker, state_evaluations, index_by_search_state_key,
                                     [{**response["results"][0], "search_axis": None, "search_family": None,
                                       "move": None, "round": 0, "parent_state_evaluation_index": None}])
            response = None
            print(f"{ticker} start search state {objective_line(state_evaluations[0])}", flush=True)
        # state evaluation 1 is the search state the search started from — the champion until a search family keeps a
        # move
        beam = search_progress["beam"] or [search_progress["champion_state_evaluation_index"] or 1]
        round_start_beam, round_path, round_drawn = beam, [], collections.Counter()
        for search_axis, search_family in config.ROUND_SCHEDULE:
            if search_axis not in profile["search_axes"]:
                continue
            if search_axis == config.SERPENTINE_SEARCH_AXIS_HPO:
                # the study family asks about lines the ledger already holds — the beam's own — so it is never
                # completed by the ledger and only ever by an answer
                parents = [state_evaluations[index - 1] for index in beam]
                if not answers_the_question(response, KIND_HYPERPARAMETER, round_number,
                                            [search_state_key(theta(row)) for row in parents]):
                    leave_question(ticker, KIND_HYPERPARAMETER, round_number, parents)
                    return
                offered = list(zip(response["results"], beam))
                for result, _ in offered:
                    round_drawn[search_axis] += result["hpo_trial_count"]
                # two parents can be offered one search state — studies over the same columns and geometry can draw
                # the same point — and one line serves both: the first parent to offer it is its provenance
                seen, rows = set(index_by_search_state_key), []
                for result, parent in offered:
                    if result["candidate"] is None:
                        continue
                    key = search_state_key(theta(result["candidate"]))
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append({**result["candidate"], "search_axis": search_axis, "search_family": search_family,
                                 "move": config.SERPENTINE_SEARCH_MOVE_FORWARD, "round": round_number,
                                 "parent_state_evaluation_index": parent})
                write_state_evaluations(ticker, state_evaluations, index_by_search_state_key, rows)
                # a candidate is one of the points its study drew, so a point that became a line is counted once, as
                # the line: the lines this round's studies left — this turn's or a stopped turn's — come off the draws
                round_drawn[search_axis] -= sum(row["search_axis"] == search_axis and row["round"] == round_number
                                                for row in state_evaluations)
                response = None
                reached = [(search_state_key(theta(result["candidate"])), parent, "hpo",
                            config.SERPENTINE_SEARCH_MOVE_FORWARD)
                           for result, parent in offered if result["candidate"] is not None]
            else:
                candidates = candidates_of(beam, state_evaluations, cat, profile, search_axis, search_family)
                members = pass_membership(candidates, state_evaluations, index_by_search_state_key, round_number,
                                          search_axis, search_family)
                if any(candidate["key"] not in index_by_search_state_key for candidate in members):
                    if not answers_the_question(response, KIND_SCORE, round_number,
                                                [candidate["key"] for candidate in members]):
                        leave_question(ticker, KIND_SCORE, round_number,
                                       [candidate["search_state"] for candidate in members])
                        return
                    scored = {result_key(KIND_SCORE, result): result for result in response["results"]}
                    write_state_evaluations(
                        ticker, state_evaluations, index_by_search_state_key,
                        [{**scored[candidate["key"]], "search_axis": search_axis, "search_family": search_family,
                          "move": candidate["move"], "round": round_number,
                          "parent_state_evaluation_index": candidate["parent"]}
                         for candidate in members if candidate["key"] not in index_by_search_state_key])
                    response = None
                reached = [(candidate["key"], candidate["parent"], candidate["label"], candidate["move"])
                           for candidate in candidates]
            # the move the gate reads is the edge this search family just walked, not the one that first wrote the
            # search state: a search state reached before by a move that shrinks it is compared with `>=`, and
            # reaching it again by a move that grows it must be compared with `>`. The ledger keeps the first
            # provenance, which is a different fact and stays where it is.
            children = []
            for key, parent, label, move in reached:
                index, parent_row = index_by_search_state_key[key], state_evaluations[parent - 1]
                print(progress_line(ticker, round_number, search_axis, search_family, label, parent_row,
                                    state_evaluations[index - 1]), flush=True)
                if is_gate_cleared(state_evaluations[index - 1], parent_row, move):
                    children.append(index)
            # the beam the search family leaves is the best of its children **and the parents it came from**: a
            # search family that finds nothing better keeps what it had, and one that improves only the third
            # member does not thereby unseat the first
            previous_beam = beam
            beam = top_beam(children + beam, state_evaluations, timeframes)
            if beam != previous_beam:
                # every edge of one search family walks one direction, so the family's direction is its first edge's
                round_path.append(path_entry(round_number, search_axis, search_family, reached[0][3], beam))
        # the counters, the beam and the champion move together at the round's end
        search_progress["path"].extend(round_path)
        drawn_by_search_axis += round_drawn
        search_progress["selection_hypothesis_count_by_search_axis"] = dict(
            collections.Counter(row["search_axis"] for row in state_evaluations if row["search_axis"])
            + drawn_by_search_axis)
        # N, counted once here and copied by every reader — methodology_features.md gives its one equation
        search_progress["selection_hypothesis_count"] = sum(
            search_progress["selection_hypothesis_count_by_search_axis"].values())
        search_progress["beam"] = list(beam)
        search_progress["champion_state_evaluation_index"] = beam[0]
        search_progress["round_count"] = round_number
        # the proof comes first: a fixed point proven in the budget's last round is a converged search
        search_progress["beam_changed"] = beam != round_start_beam
        search_progress["search_outcome"] = (
            "converged" if not search_progress["beam_changed"] and fixed_point_provable
            else "stopped_by_budget" if round_number >= config.SERPENTINE_SEARCH_ROUND_BUDGET
            else None)

    request.unlink(missing_ok=True)
    response_path.unlink(missing_ok=True)
    champion_row = state_evaluations[search_progress["champion_state_evaluation_index"] - 1]
    print(f"{ticker} {search_progress_path.name}: {search_progress['search_outcome'].replace('_', ' ')} after "
          f"{search_progress['round_count']} rounds, "
          f"{len(state_evaluations)} state evaluations and "
          f"{search_progress['selection_hypothesis_count']} selection hypotheses, "
          f"champion {objective_line(champion_row)} "
          f"({axis_feature_set.column_count(champion_row['columns_by_timeframe'], timeframes)} columns), "
          f"{len(search_progress['proposals'])} proposals", flush=True)
    if noise_sigma is None:
        # a calibration search: what it measured is the noise sigma a hand may draft into the profile, by a decision;
        # a ledger with fewer than two fit-changing pairs measures none
        ledger_noise_sigma = path_cagr_noise_standard_deviation([state_evaluations])
        print(f"{ticker} calibration search: path CAGR noise standard deviation of this ledger "
              f"{'not measurable' if ledger_noise_sigma is None else format(ledger_noise_sigma, '.6f')}", flush=True)


def main() -> int:
    args = features_config.build_ticker_parser(
        "one turn of the serpentine search: carry it as far as the answers on disk allow, then leave the next "
        "question or an ended search"
    ).parse_args()
    for ticker in features_config.parse_tickers(args.tickers):
        turn(ticker)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
