"""The evaluation of one search state — what a search state is worth, and nothing about which search state to try
next.

X and Y for a search state, the material a score is computed from, and the state evaluation a search state earns:
what a request of the serpentine search asks, answered in its response file. They read a search state and answer with
numbers; they hold no beam, no round, no ledger and no order of search families, and they decide nothing.
"""

import json

import numpy as np

from . import config, dataset, hpo, labels, model, strategy, train

# the two kinds of scoring a request may ask for: a state evaluation per search state, or a study and its candidate
# per beam parent
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


def build_asset(ticker: str) -> dict:
    """The asset's material, loaded once for a whole request: the catalogue and its feature grids, the labels
    and the set the asset holds today, and the 1m path a backtest walks. It is what a search state is scored against,
    and it says nothing about which search states those are."""
    cat = dataset.load_catalogue(ticker)
    timeframes = config.timeframes(cat)
    catalogue_values, decision_grids = dataset.load_feature_material(ticker, cat, timeframes)
    xy = dataset.build_xy(cat, timeframes, catalogue_values, decision_grids,
                          dataset.load_label_events(ticker, cat),
                          dataset.load_feature_columns(ticker, cat), dataset.load_barriers(ticker))
    return {"xy": xy, "catalogue": cat, "timeframes": timeframes,
            "catalogue_values": catalogue_values, "decision_grids": decision_grids,
            "label_inputs": labels.load_label_inputs(ticker, cat),
            "bars_1m": strategy.load_bars_1m(ticker)}


def fit_identity(search_state: dict) -> str:
    """What two search states must share for one set of fits to serve both: the whole search state but where a
    position leaves. Search states of one request that share it are fitted once and backtested each."""
    return search_state_key({name: value for name, value in search_state.items()
                             if name not in config.TRADE_EXIT_COORDINATE_NAMES})


def score_results(asset: dict, search_states: list[dict]) -> list[dict]:
    """A state evaluation per search state, in the order the request named them. The first search state of a fit
    identity pays for its fits and the rest inherit them, so a request that moves only the trade's exit costs one set
    of fits."""
    fitted: dict[str, dict] = {}
    results = []
    for search_state in search_states:
        identity = fit_identity(search_state)
        inherited = fitted.get(identity)
        material = search_state_material(asset, search_state, inherited)
        if inherited is None:
            fitted[identity] = material
        results.append(state_evaluation(asset, search_state, material))
    return results


def hpo_results(ticker: str, asset: dict, parents: list[dict], round_number: int) -> list[dict]:
    """A study per beam parent, in the order the request named them, and the candidate the study offers. The
    gate of each study reads its own parent's numbers: the growth rate of every validation fold it stands at. A
    parent whose study offers nothing answers with null, which is an answer; `hpo_trial_count` is every point the
    study drew, completed and pruned alike.

    The points of every study go to the asset's partition of the `score_trials` family once the last study has ended, in
    the order of the parents, and the response is written after them: a stop inside a study leaves nothing
    behind, and a stop between them leaves a ledger a replay will write again."""
    studies, results = [], []
    for parent in parents:
        search_state = theta(parent)
        parent_validation_by_fold = {fold_id: parent["validation"][f"fold_{fold_id}"]
                                     for fold_id in config.VALIDATION_FOLD_IDS}
        study = hpo.search_hyperparameters(xy_for_search_state(asset, search_state), asset["bars_1m"],
                                           config.SEED + round_number, parent_validation_by_fold)
        studies.append(study)
        params = hpo.admissible_point(study)
        candidate = None
        if params is not None:
            offered = {**search_state, "best_params": params}
            candidate = state_evaluation(asset, offered,
                                         search_state_material(asset, offered, None))
        results.append({"search_state_key": search_state_key(search_state), "hpo_trial_count": len(study.trials),
                        "candidate": candidate})
    for study in studies:
        hpo.log_trials(study, "serpentine_search", round_number, config.score_trials_jsonl(ticker))
    return results


def evaluation_contract() -> dict:
    """What every answer is scored under: the records of this module that name the experiment's identity, by name —
    so a search can tell whether its ledger was scored under the records the next answer is."""
    return {record["name"]: record["value"] for record in config.CONFIGURABLES if record["experiment_identity"]}


def main() -> int:
    args = config.build_ticker_parser(
        "score the search states one request names: a state evaluation per search state, or a study and its "
        "candidate per beam parent"
    ).parse_args()

    for ticker in config.parse_tickers(args.tickers):
        request = dataset.load_json(config.score_request_json(ticker))
        # a request says what to score and nothing about what to do with the answer: a key it does not carry
        # is an error, and the response is written only once every search state of the request has one
        kind, round_number, search_states = request["kind"], request["round"], request["search_states"]
        if kind == KIND_SCORE:
            # a question naming no search state asks for the evaluation contract alone, and builds no material
            results = score_results(build_asset(ticker), search_states) if search_states else []
        elif kind == KIND_HYPERPARAMETER:
            results = hpo_results(ticker, build_asset(ticker), search_states, round_number)
        else:
            raise SystemExit(f"{ticker}: {kind!r} is no kind of scoring this stage answers")
        dataset.write_json(config.score_response_json(ticker),
                           {"kind": kind, "round": round_number, "results": results,
                            "evaluation_contract": evaluation_contract()})
        print(f"{ticker} {kind} round {round_number}: {len(results)} scored", flush=True)
    return 0


def xy_for_search_state(asset: dict, search_state: dict) -> dict:
    """X and Y for one search state: the asset's own Y when the label's geometry is still the asset's — only X is
    stacked again — else Y walked down the 1m path in process and the feature grids joined to the decisions
    the new label horizon admits."""
    barriers = dataset.barriers_from({name: search_state[name] for name in config.BARRIER_COORDINATE_NAMES})
    if all(asset["xy"]["barriers"][name] == barriers[name] for name in config.BARRIER_COORDINATE_NAMES
           if name not in config.TRADE_EXIT_COORDINATE_NAMES):
        x, feature_columns = dataset.build_x(asset["xy"]["catalogue_values"],
                                             search_state["columns_by_timeframe"], asset["timeframes"])
        return {**asset["xy"], "x": x, "feature_columns": feature_columns, "barriers": barriers}
    label_events = labels.label_events(asset["label_inputs"], asset["catalogue"], barriers)
    return dataset.build_xy(asset["catalogue"], asset["timeframes"], asset["catalogue_values"],
                            asset["decision_grids"], label_events, search_state["columns_by_timeframe"], barriers)


def search_state_material(asset: dict, search_state: dict, inherited: dict | None) -> dict:
    """What a search state is scored from — X and Y, the three boosters' out-of-fold predictions and their skill.

    A search state of the fit identity of an earlier one inherits all of it: neither a fit nor a prediction depends on
    where a position leaves, so only the geometry the backtest reads is replaced. Anything else is three fits, and Y
    before them when the label's own geometry moved."""
    barriers = dataset.barriers_from({name: search_state[name] for name in config.BARRIER_COORDINATE_NAMES})
    if inherited is not None:
        return {**inherited, "xy": {**inherited["xy"], "barriers": barriers}}
    xy = xy_for_search_state(asset, search_state)
    y_cls = model.to_class(xy["y"])
    prediction_records, skill_by_fold = [], {}
    for fold_id in config.VALIDATION_FOLD_IDS:
        metrics, _, rows, _ = train.fold_evaluation(xy, y_cls, search_state["best_params"], fold_id)
        skill_by_fold[fold_id] = metrics["relative_logloss_skill"]
        prediction_records.extend(rows)
    return {"xy": xy, "skill_by_fold": skill_by_fold,
            "oos_predictions": train.to_oos_predictions(prediction_records)}


def state_evaluation(asset: dict, search_state: dict, material: dict) -> dict:
    """Score one search state: the strategy's threshold selection on the boosters' predictions, the folds it chose
    at, and the path those folds chain into. The evaluation carries the whole search state, so the gate, the ranking,
    the beam and the cache never ask which coordinate moved."""
    selection = strategy.entry_edge_threshold_selection(
        strategy.build_simulation_inputs(material["xy"], asset["bars_1m"], material["oos_predictions"]))
    by_fold, skill_by_fold = selection["validation_by_fold"], material["skill_by_fold"]
    return {
        "columns_by_timeframe": search_state["columns_by_timeframe"],
        "best_params": search_state["best_params"],
        **{name: search_state[name] for name in config.BARRIER_COORDINATE_NAMES},
        "validation": {f"fold_{fold_id}": {
            "relative_logloss_skill": skill_by_fold[fold_id],
            "sharpe": by_fold[fold_id]["sharpe"],
            "cagr": by_fold[fold_id]["cagr"],
            "max_drawdown": by_fold[fold_id]["max_drawdown"],
            "calmar": by_fold[fold_id]["calmar"],
            "profit_factor": by_fold[fold_id]["profit_factor"],
            "trade_count": by_fold[fold_id]["trade_count"]}
            for fold_id in config.VALIDATION_FOLD_IDS},
        "mean_relative_logloss_skill": float(np.mean([skill_by_fold[fold_id] for fold_id in config.VALIDATION_FOLD_IDS])),
        "validation_path": selection["validation_path"],
        "entry_edge_threshold": selection["entry_edge_threshold"],
        "entry_edge_threshold_constraint_met": selection["entry_edge_threshold_constraint_met"],
        **{name: selection[name] for name in strategy.SELECTION_EXPOSURE_KEYS},
        strategy.SELECTION_SCORE_KEY: selection[strategy.SELECTION_SCORE_KEY],
    }


if __name__ == "__main__":
    raise SystemExit(main())
