"""One turn of the serpentine search: read where the search stands, carry it as far as the answers on disk allow,
and leave either the next question or a finished search.

A turn walks the round from its top. Every state it needs and already has is a line of the ledger; the first family
whose states are not all there is the question it asks, written as `<TICKER>_score_request.json` and answered by
another module as `<TICKER>_score_response.json`. It computes no metric of a state: every number a gate, a ranking
or a proposal reads comes off an answer, and the noise a proposal has to clear is the asset's noise sigma, a number of
the profile measured once off the answers of a calibration run.

The round is the unit of resume, so nothing says which family a turn stopped at — the walk finds out by asking the
ledger. What the ledger cannot say is which states a pass asked for once some of them were already written, so a
pass reconstructs its own membership from the provenance each line carries: a state of this round, this loop, this
family and this first move belonged to the pass in flight, and an older line is a cache hit that did not.
"""

from __future__ import annotations

import collections
import json
import math
import statistics

import numpy as np

from .. import config as features_config
from .. import dataset
from . import config, coordinate_barrier, coordinate_feature_set

# the two kinds of question: a row per state, or a study and its candidate per beam parent. The hyper-parameter
# family has no generator here — its candidate is drawn by a study on the other side and comes back in an answer.
# twice by extraction
KIND_SCORE = "score"
# twice by extraction
KIND_HYPERPARAMETER = "hpo"


# twice by extraction
def theta(row: dict) -> dict:
    """The state a trial holds, by itself: the columns of the set, the barrier geometry and the
    hyper-parameter point. A trial's row is this and the numbers it earned."""
    return {"columns_by_timeframe": row["columns_by_timeframe"],
            "best_params": row["best_params"],
            **{name: row[name] for name in config.BARRIER_COORDINATE_NAMES}}


# twice by extraction
def state_key(state: dict) -> str:
    """A state as the scored-trial index keys it — its own canonical text. A state is written the way the
    artifacts carry it, so a state read back off disk keys the same as the one that wrote it, with no shape
    to repair first. Every value is a string, a whole number or a multiple of a quarter, so the equality is
    exact and asks for no tolerance."""
    return json.dumps(state, sort_keys=True, separators=(",", ":"))


# ---- the one selection: the objective the experiment froze, read per fold and over a whole state -------

def fold_objective(row: dict) -> list[float]:
    """What the gate compares fold by fold — each fold's own measure, in the order the selection fixes. The
    fold is the unit of robustness: a move has to be better on all three, not on average."""
    return [row["validation"][f"fold_{fold_id}"][config.SELECTION_FOLD_MEASURE]
            for fold_id in config.VALIDATION_FOLD_IDS]


def state_objective(row: dict) -> tuple:
    """What the ranking maximises over a whole state, most significant first: the chained validation path's
    CAGR, then its Calmar ratio, then its profit factor. A path that never lost has no profit factor and is
    the best there is, so it sorts first."""
    path = row["validation_path"]
    profit_factor = math.inf if path["profit_factor"] is None else path["profit_factor"]
    return (path["cagr"], path["calmar"], profit_factor)


def is_gate_cleared(row: dict, parent: dict, move: str) -> bool:
    """Whether a child may be kept at all: better than the state it came from on every validation fold — strictly,
    and no worse for a move that shrinks the state, which the ranking then puts first for its fewer columns.

    The fold measure is the fold's CAGR, so a better fold is a higher final equity, and the chained path, which
    compounds the folds' final equities, is better too: the objective needs no condition of its own. No margin is
    asked of a move, so small true gains can add up move by move; the noise of the whole search is asked once, of
    the proposal.

    The fold measure is a strategy number, so a state whose threshold fell back to the grid floor — no point
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


def false_exceedance_rate(multiple: float, candidate_count: int) -> float:
    """The chance that the best of `candidate_count` states, each scored with noise of its own, beats a start that
    carries noise of its own by `multiple` noise standard deviations: 1 - E_Z[Phi(k + Z)^N], Z standard normal —
    the expectation by Gauss-Hermite quadrature."""
    return 1.0 - sum(weight * NORMAL.cdf(multiple + node) ** candidate_count for node, weight in QUADRATURE)


def proposal_threshold_multiple(candidate_count: int) -> float:
    """k(N), the multiple of the noise standard deviation at which that chance is the proposal's rate, N every
    state the search scored — by bisection on a fixed bracket in a fixed number of halvings, one deterministic
    function of N."""
    low, high = config.PROPOSAL_THRESHOLD_BISECTION_BRACKET_MULTIPLES
    for _ in range(config.PROPOSAL_THRESHOLD_BISECTION_ITERATION_COUNT):
        middle = 0.5 * (low + high)
        if false_exceedance_rate(middle, candidate_count) > config.PROPOSAL_THRESHOLD_FALSE_EXCEEDANCE_RATE:
            low = middle
        else:
            high = middle
    return 0.5 * (low + high)


def _fitted_part(state: dict) -> dict:
    """What a state is fitted on: the whole of it but the exit of a trade, which a backtest reads alone."""
    return {name: value for name, value in state.items() if name not in config.TRADE_EXIT_COORDINATE_NAMES}


def path_cagr_noise_standard_deviation(ledgers: list[list[dict]]) -> float:
    """The asset's noise sigma: the standard deviation of one evaluation's path CAGR, read off the ledgers of its
    calibration searches. Each line and the parent its `parent_trial_index` names are one pair when both met the
    threshold constraint and the child was fitted on its own — a move of the trade's exit alone shares its
    parent's fits and so its noise, and would read as none — each pair of states once over all the ledgers; of
    the pairs' path CAGR differences, the median absolute deviation scaled to a standard deviation, over the
    square root of two, because a difference carries the noise of two evaluations."""
    differences = {}
    for trials in ledgers:
        for row in trials[1:]:
            parent = trials[row["parent_trial_index"] - 1]
            if (row["entry_edge_threshold_constraint_met"] and parent["entry_edge_threshold_constraint_met"]
                    and _fitted_part(theta(row)) != _fitted_part(theta(parent))):
                differences.setdefault((state_key(theta(parent)), state_key(theta(row))),
                                       state_objective(row)[0] - state_objective(parent)[0])
    values = list(differences.values())
    centre = statistics.median(values)
    return (config.NOISE_MEDIAN_ABSOLUTE_DEVIATION_SCALE * statistics.median([abs(value - centre) for value in values])
            / math.sqrt(2.0))


def ranking_key(trials: list[dict], index: int, timeframes: tuple[str, ...]) -> tuple:
    """The one order the beam takes: the objective down, then the smaller set, then the earlier trial."""
    row = trials[index - 1]
    return (*(-value for value in state_objective(row)),
            coordinate_feature_set.column_count(row["columns_by_timeframe"], timeframes), index)


def top_beam(children: list[int], trials: list[dict], timeframes: tuple[str, ...]) -> list[int]:
    """The beam a family leaves: the best distinct children by the ranking key, at most the width. Two
    parents can reach one state and one trial serves both, so the indices are made distinct before the width
    is applied — a beam of three is three states, not one state three times."""
    ranked = sorted(dict.fromkeys(children), key=lambda index: ranking_key(trials, index, timeframes))
    return ranked[:config.SERPENTINE_SEARCH_BEAM_WIDTH]


# ---- the state file ------------------------------------------------------------------------------------

def path_entry(round_number: int, loop: str, family: str, move: str, beam: list[int]) -> dict:
    """One accepted expansion of the research path: which loop and family moved the search, in which direction,
    the trial it landed on and what the beam held after it. The direction is the family's own, not the one the
    ledger kept for the state's first provenance; the trial is named by its index and nothing of it is copied:
    its skill and its path are the ledger's line, and a reader reads them there."""
    return {"round": round_number, "loop": loop, "family": family,
            "trial_index": beam[0], "beam": list(beam), "move": move}


def proposals_block(trials: list[dict], champion_trial_index: int,
                    noise_sigma: float | None, trial_count: int) -> list[dict]:
    """The state a hand may promote: the champion alone, and only when it is not the state the search started
    from and beats it by more than the noise of the whole search — k(N) times the asset's noise sigma, N every
    state the search scored, because the champion is the best of all of them. Its threshold constraint and its
    folds need no test here: every member of the beam cleared the gate against its parent, so the champion meets
    the constraint and stands at or above the start on every fold. A calibration run, whose profile has no sigma
    yet, proposes nothing.

    A proposal is its rank and the index of its trial, and nothing else: the columns, the geometry and every
    number are the ledger's line, so each stands in one file and a reader joins it by the index."""
    if noise_sigma is None or champion_trial_index == 1:
        return []
    gain = state_objective(trials[champion_trial_index - 1])[0] - state_objective(trials[0])[0]
    if gain > proposal_threshold_multiple(trial_count) * noise_sigma:
        return [{"proposal": 1, "trial_index": champion_trial_index}]
    return []


def write_round_state(ticker: str, state_file: dict, trials: list[dict]) -> None:
    """Where the search stood when the round about to run began — the one place this file is written.

    Written at the top of a round, so it exists before the ledger's first line and every line the ledger
    holds has, on disk, the experiment it belongs to; the write that records a finished search is this same
    write one round later. The trials are the ledger beside it, so the state is a fixed handful of keys and
    the proposals are derived once a round rather than once a trial. The path and the proposals name their
    trials by index and copy none of their numbers, so what the file holds beside its inputs is a few hundred
    bytes however long the search runs."""
    state_file["proposals"] = proposals_block(trials, state_file["champion_trial_index"] or 1,
                                              state_file["inputs"]["profile"]["path_cagr_noise_standard_deviation"],
                                              sum(state_file["trial_count_by_loop"].values()))
    dataset.write_json(config.serpentine_search_json(ticker), state_file)


def build_search_inputs(best_params: dict, active_columns_by_timeframe: dict, active_barriers: dict,
                        cat: dict, profile: dict) -> dict:
    """What a search is conditioned on: the frozen window with its warm-up, the parameters and the barrier
    geometry it starts from, the catalogue it draws from, the profile a hand drafted and the selection the
    experiment froze — recorded in the state file and compared by equality on a rerun. The selection is the
    beam width and the fold measure, and it belongs here because a rerun under another of either is another
    experiment: it starts its own trials instead of resuming these."""
    return {
        "research_window": {"start_utc": features_config.RESEARCH_START_UTC,
                            "end_utc": features_config.RESEARCH_END_UTC,
                            "seed": config.SEED, "warmup_top_timeframe_bars": cat["warmup_top_timeframe_bars"]},
        "best_params": best_params,
        "catalogue_columns_by_timeframe": {timeframe: tuple(cat["columns_by_timeframe"][timeframe])
                                           for timeframe in config.timeframes(cat)},
        "active_columns_by_timeframe": active_columns_by_timeframe,
        "active_barriers": {name: active_barriers[name] for name in config.BARRIER_COORDINATE_NAMES},
        "profile": profile,
        "selection": {"beam_width": config.SERPENTINE_SEARCH_BEAM_WIDTH, "fold_measure": config.SELECTION_FOLD_MEASURE},
    }


def start_state(profile: dict, active_columns_by_timeframe: dict, active_barriers: dict,
                best_params: dict, timeframes: tuple[str, ...]) -> dict:
    """The state a search starts from: the columns the profile names, else the asset's own set, with the
    asset's own barrier geometry and the parameters it holds fixed."""
    columns = profile["start_columns_by_timeframe"] or active_columns_by_timeframe
    return {"columns_by_timeframe": {timeframe: list(columns[timeframe]) for timeframe in timeframes},
            "best_params": best_params,
            **{name: active_barriers[name] for name in config.BARRIER_COORDINATE_NAMES}}


def objective_line(row: dict) -> str:
    """A state's objective and the folds the gate reads."""
    return (f"cagr {state_objective(row)[0]:+.4f} "
            f"folds {config.SELECTION_FOLD_MEASURE} {'/'.join(f'{value:+.4f}' for value in fold_objective(row))} "
            f"trades {'/'.join(str(row['validation'][f'fold_{fold_id}']['trade_count']) for fold_id in config.VALIDATION_FOLD_IDS)}")


def progress_line(ticker: str, round_number: int, loop: str, family: str, label: str,
                  parent: dict, row: dict) -> str:
    return (f"{ticker} round {round_number} {loop}/{family} {label} "
            f"cagr {state_objective(parent)[0]:+.4f} -> {state_objective(row)[0]:+.4f} "
            f"folds {'/'.join(f'{value:+.4f}' for value in fold_objective(row))}")


# ---- what the asset holds today, read without the module that labels ------------------------------------

# twice by extraction
def load_feature_columns(ticker: str, cat: dict) -> dict:
    """The asset's feature set by timeframe: the promoted file's columns, in catalogue order, else the
    default set. The order is the catalogue's and not the file's, because a set is one state however a hand
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
    at. Each value passes its own cast, so 2 and 2.0 are one state however a hand wrote them. The horizon
    stays the token it travels as — the minute it stands for is the labelling layer's to read."""
    path = config.barriers_json(ticker)
    promoted = dataset.load_json(path) if path.exists() else {}
    return {name: config.BARRIER_COORDINATE_CASTS[name](promoted.get(name, start))
            for name, start in config.START_BY_COORDINATE_DEFAULT.items()}


def load_best_params(ticker: str) -> dict:
    """The asset's hyper-parameter point: the one its ML chain chose last."""
    return dataset.load_json(config.parameters_json(ticker))["hyperparameter_search_result"]["best_params"]


# ---- the question and the answer -------------------------------------------------------------------------

def result_key(kind: str, result: dict) -> str:
    """The state a result speaks about: a scored state carries its own, a study names its parent's."""
    return result["state_key"] if kind == KIND_HYPERPARAMETER else state_key(theta(result))


def answers_the_question(response: dict | None, kind: str, round_number: int, keys: list[str]) -> bool:
    """Whether an answer on disk is the answer to the question this turn would ask: the same kind, the same
    round and the same states in the same order. Anything else answers a question no longer asked."""
    return (response is not None and response.get("kind") == kind and response.get("round") == round_number
            and [result_key(kind, result) for result in response["results"]] == keys)


def append_trials(ticker: str, trials: list[dict], index_by_state: dict[str, int], rows: list[dict]) -> None:
    """The lines one answer adds, appended in one open and held as the ledger will read them back."""
    if not rows:
        return
    dataset.append_jsonl(config.serpentine_search_trials_jsonl(ticker), rows)
    for row in rows:
        trials.append(dataset.to_json_safe(row))
        index_by_state[state_key(theta(trials[-1]))] = len(trials)


# ---- a family pass ----------------------------------------------------------------------------------------

def candidates_of(beam: list[int], trials: list[dict], cat: dict, profile: dict,
                  loop: str, family: str) -> list[dict]:
    """Every move the family offers from the beam, in the order the beam and the moves generate them, one
    entry per state: two parents reaching one state give one candidate, and it keeps the provenance of the
    first move that reached it."""
    offered, seen = [], set()
    for parent in beam:
        parent_state = theta(trials[parent - 1])
        moves = (coordinate_barrier.moves(parent_state, profile, family)
                 if loop == config.SERPENTINE_SEARCH_LOOP_BARRIER
                 else coordinate_feature_set.moves(parent_state, cat, profile, family))
        for move, label, child in moves:
            key = state_key(child)
            if key in seen:
                continue
            seen.add(key)
            offered.append({"key": key, "move": move, "label": label, "state": child, "parent": parent})
    return offered


def of_this_pass(row: dict, round_number: int, loop: str, family: str, candidate: dict) -> bool:
    """Whether a line already in the ledger is one this very pass wrote before it was interrupted — the
    round, the loop, the family and the first move that reached the state, all of them. An older line with
    the same state is a cache hit, and a cache hit was never part of the question."""
    return (row["round"] == round_number and row["loop"] == loop and row["family"] == family
            and row["move"] == candidate["move"] and row["parent_trial_index"] == candidate["parent"])


def pass_membership(candidates: list[dict], trials: list[dict], index_by_state: dict[str, int],
                    round_number: int, loop: str, family: str) -> list[dict]:
    """The states this pass asked for, whether or not some of them are already written: a state not in the
    ledger, and a state whose line this pass itself wrote. Reconstructed and not remembered, so the turn
    holds no cursor and the state file carries nothing about a pass in flight."""
    members = []
    for candidate in candidates:
        index = index_by_state.get(candidate["key"])
        if index is None or of_this_pass(trials[index - 1], round_number, loop, family, candidate):
            members.append(candidate)
    return members


def leave_question(ticker: str, kind: str, round_number: int, states: list[dict]) -> None:
    """The next question on disk — written over the one it answers — and only then the answer that is spent.
    Nothing is removed before its successor is written: the loop above reads the question's own file to know
    whether to go on, and a gap between the two would read as the end of the work."""
    dataset.write_json(config.score_request_json(ticker),
                       {"kind": kind, "round": round_number, "states": list(states)})
    config.score_response_json(ticker).unlink(missing_ok=True)


# ---- one turn ---------------------------------------------------------------------------------------------

def turn(ticker: str) -> None:
    profile = dataset.load_json(config.serpentine_search_profile_json(ticker))
    # the asset's noise sigma, or None on the calibration run that measures it
    noise_sigma = profile["path_cagr_noise_standard_deviation"]
    best = load_best_params(ticker)
    cat = dataset.load_json(features_config.catalogue_json(ticker))
    timeframes = config.timeframes(cat)
    columns, barriers = load_feature_columns(ticker, cat), load_barrier_coordinates(ticker)
    inputs = dataset.to_json_safe(build_search_inputs(best, columns, barriers, cat, profile))

    state_path = config.serpentine_search_json(ticker)
    ledger = config.serpentine_search_trials_jsonl(ticker)
    request, response_path = config.score_request_json(ticker), config.score_response_json(ticker)
    # the recorded run when its inputs are the inputs of this one, else a fresh state and a fresh ledger — a
    # trial of another experiment is not a cache hit for this one, and neither is an answer to its question
    state_file = dataset.load_json(state_path) if state_path.exists() else None
    if state_file is None or state_file["inputs"] != inputs:
        state_file = {"inputs": inputs, "beam": [], "champion_trial_index": None, "round_count": 0,
                      "search_converged": False, "path": [], "trial_count_by_loop": {}}
        ledger.unlink(missing_ok=True)
        request.unlink(missing_ok=True)
        response_path.unlink(missing_ok=True)
    trials = dataset.load_jsonl(ledger) if ledger.exists() else []
    index_by_state = {state_key(theta(row)): index for index, row in enumerate(trials, start=1)}
    # the points the studies of earlier rounds drew and never turned into lines: the count the last boundary
    # wrote, less the lines that boundary already counted. A line of the round in flight is not among them — the
    # boundary predates it — and subtracting it would lose a draw for every candidate a stopped round had written
    drawn_by_loop = (collections.Counter(state_file["trial_count_by_loop"])
                     - collections.Counter(row["loop"] for row in trials
                                           if row["loop"] and row["round"] <= state_file["round_count"]))
    start = start_state(profile, columns, barriers, best, timeframes)
    response = dataset.load_json(response_path) if response_path.exists() else None

    while True:
        write_round_state(ticker, state_file, trials)
        if state_file["search_converged"]:
            break
        round_number = state_file["round_count"] + 1
        # the state the search starts from is scored like any other, and its line is the round it predates
        if not trials:
            if not answers_the_question(response, KIND_SCORE, round_number, [state_key(start)]):
                leave_question(ticker, KIND_SCORE, round_number, [start])
                return
            append_trials(ticker, trials, index_by_state,
                          [{**response["results"][0], "loop": None, "family": None, "move": None,
                            "round": 0, "parent_trial_index": None}])
            response = None
            print(f"{ticker} start state {objective_line(trials[0])}", flush=True)
        # trial 1 is the state the search started from — the champion until a family keeps a move
        beam = state_file["beam"] or [state_file["champion_trial_index"] or 1]
        round_accepted, round_path, round_drawn = False, [], collections.Counter()
        for loop, family in config.ROUND_SCHEDULE:
            if loop not in profile["loops"]:
                continue
            if loop == config.SERPENTINE_SEARCH_LOOP_HPO:
                # the hyper-parameter family asks about lines the ledger already holds — the beam's own — so it
                # is never finished by the ledger and only ever by an answer
                parents = [trials[index - 1] for index in beam]
                if not answers_the_question(response, KIND_HYPERPARAMETER, round_number,
                                            [state_key(theta(row)) for row in parents]):
                    leave_question(ticker, KIND_HYPERPARAMETER, round_number, parents)
                    return
                offered = list(zip(response["results"], beam))
                for result, _ in offered:
                    round_drawn[loop] += result["trial_count_drawn"]
                # two parents can be offered one state — studies over the same columns and geometry can draw the
                # same point — and one line serves both: the first parent to offer it is its provenance
                seen, rows = set(index_by_state), []
                for result, parent in offered:
                    if result["candidate"] is None:
                        continue
                    key = state_key(theta(result["candidate"]))
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append({**result["candidate"], "loop": loop, "family": family,
                                 "move": config.SERPENTINE_SEARCH_MOVE_FORWARD, "round": round_number,
                                 "parent_trial_index": parent})
                append_trials(ticker, trials, index_by_state, rows)
                # a candidate is one of the points its study drew, so a point that became a line is counted once, as
                # the line: the lines this round's studies left — this turn's or a stopped turn's — come off the draws
                round_drawn[loop] -= sum(row["loop"] == loop and row["round"] == round_number for row in trials)
                response = None
                reached = [(state_key(theta(result["candidate"])), parent, "hpo",
                            config.SERPENTINE_SEARCH_MOVE_FORWARD)
                           for result, parent in offered if result["candidate"] is not None]
            else:
                candidates = candidates_of(beam, trials, cat, profile, loop, family)
                members =pass_membership(candidates, trials, index_by_state, round_number, loop, family)
                if any(candidate["key"] not in index_by_state for candidate in members):
                    if not answers_the_question(response, KIND_SCORE, round_number,
                                                [candidate["key"] for candidate in members]):
                        leave_question(ticker, KIND_SCORE, round_number,
                                       [candidate["state"] for candidate in members])
                        return
                    scored = {result_key(KIND_SCORE, result): result for result in response["results"]}
                    append_trials(ticker, trials, index_by_state,
                                  [{**scored[candidate["key"]], "loop": loop, "family": family,
                                    "move": candidate["move"], "round": round_number,
                                    "parent_trial_index": candidate["parent"]}
                                   for candidate in members if candidate["key"] not in index_by_state])
                    response = None
                reached = [(candidate["key"], candidate["parent"], candidate["label"], candidate["move"])
                           for candidate in candidates]
            # the move the gate reads is the edge this family just walked, not the one that first wrote the
            # state: a state reached before by a move that shrinks it is compared with `>=`, and reaching it again
            # by a move that grows it must be compared with `>`. The ledger keeps the first provenance, which is a
            # different fact and stays where it is.
            children = []
            for key, parent, label, move in reached:
                index, parent_row = index_by_state[key], trials[parent - 1]
                print(progress_line(ticker, round_number, loop, family, label, parent_row,
                                    trials[index - 1]), flush=True)
                if is_gate_cleared(trials[index - 1], parent_row, move):
                    children.append(index)
            # the beam the family leaves is the best of its children **and the parents it came from**: a family
            # that finds nothing better keeps what it had, and one that improves only the third member does not
            # thereby unseat the first
            previous_beam = beam
            beam = top_beam(children + beam, trials, timeframes)
            if beam != previous_beam:
                round_accepted = True
                # every edge of one family walks one direction, so the family's direction is its first edge's
                round_path.append(path_entry(round_number, loop, family, reached[0][3], beam))
        # the counters, the beam and the champion move together at the round's end
        state_file["path"].extend(round_path)
        drawn_by_loop += round_drawn
        state_file["trial_count_by_loop"] = dict(
            collections.Counter(row["loop"] for row in trials if row["loop"]) + drawn_by_loop)
        state_file["beam"] = list(beam)
        state_file["champion_trial_index"] = beam[0]
        state_file["round_count"] = round_number
        state_file["search_converged"] = not round_accepted

    request.unlink(missing_ok=True)
    response_path.unlink(missing_ok=True)
    champion_row = trials[state_file["champion_trial_index"] - 1]
    print(f"{ticker} {state_path.name}: converged after {state_file['round_count']} rounds and {len(trials)} "
          f"trials, champion {objective_line(champion_row)} "
          f"({coordinate_feature_set.column_count(champion_row['columns_by_timeframe'], timeframes)} columns), "
          f"{len(state_file['proposals'])} proposals", flush=True)
    if noise_sigma is None:
        # a calibration run: what it measured is the noise sigma a hand may draft into the profile, by a decision
        print(f"{ticker} calibration run: path CAGR noise standard deviation of this ledger "
              f"{path_cagr_noise_standard_deviation([trials]):.6f}", flush=True)


def main() -> int:
    args = features_config.build_ticker_parser(
        "one turn of the serpentine search: carry it as far as the answers on disk allow, then leave the next "
        "question or a finished search"
    ).parse_args()
    for ticker in features_config.parse_tickers(args.tickers):
        turn(ticker)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
