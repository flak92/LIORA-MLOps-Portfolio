"""The evaluation of one state — what a state is worth, and nothing about which state to try next.

X and Y for a state, the material a score is computed from, and the row a scored state carries: what a request
of the serpentine search asks, answered in its response file. They read a state and answer with numbers; they
hold no beam, no round, no ledger and no order of families, and they decide nothing.
"""

from __future__ import annotations

import json

import numpy as np

from . import config, dataset, hpo, labels, model, strategy, train

# the two kinds of scoring a request may ask for: a row per state, or a study and its candidate per beam parent
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


def build_asset(ticker: str) -> dict:
    """The asset's material, loaded once for a whole request: the catalogue and its feature grids, the labels
    and the set the asset holds today, and the 1m path a backtest walks. It is what a state is scored against,
    and it says nothing about which states those are."""
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


def fit_identity(state: dict) -> str:
    """What two states must share for one set of fits to serve both: the whole state but where a position
    leaves. States of one request that share it are fitted once and backtested each."""
    return state_key({name: value for name, value in state.items()
                      if name not in config.TRADE_EXIT_COORDINATE_NAMES})


def score_results(asset: dict, states: list[dict]) -> list[dict]:
    """A trial row per state, in the order the request named them. The first state of a fit identity pays for
    its fits and the rest inherit them, so a request that moves only the trade's exit costs one set of fits."""
    fitted: dict[str, dict] = {}
    results = []
    for state in states:
        identity = fit_identity(state)
        inherited = fitted.get(identity)
        material = state_material(asset, state,
                                  config.REBUILD_BACKTEST if inherited else config.REBUILD_FITS, inherited)
        if inherited is None:
            fitted[identity] = material
        results.append(trial_result(asset, state, material))
    return results


def hpo_results(ticker: str, asset: dict, parents: list[dict], round_number: int) -> list[dict]:
    """A study per beam parent, in the order the request named them, and the candidate the study offers. The
    gate of each study reads its own parent's numbers: every validation fold it stands at, and the growth rate
    of the path it chained. A parent whose study offers nothing answers with null, which is an answer.

    The points of every study go to the asset's partition of the `score_trials` family once the last study has ended, in
    the order of the parents, and the response is written after them: a stop inside a study leaves nothing
    behind, and a stop between them leaves a ledger a replay will write again."""
    studies, results = [], []
    for parent in parents:
        state = theta(parent)
        champion_by_fold = {fold_id: parent["validation"][f"fold_{fold_id}"]
                            for fold_id in config.VALIDATION_FOLD_IDS}
        study = hpo.search_hyperparameters(xy_for_state(asset, state), asset["bars_1m"], champion_by_fold)
        studies.append(study)
        params = hpo.admissible_point(study, parent["validation_path"]["cagr"], state["best_params"])
        candidate = None
        if params is not None:
            offered = {**state, "best_params": params}
            candidate = trial_result(asset, offered,
                                     state_material(asset, offered, config.REBUILD_FITS, None))
        results.append({"state_key": state_key(state), "trial_count_drawn": len(study.trials),
                        "candidate": candidate})
    for study in studies:
        hpo.log_trials(study, "serpentine_search", round_number, config.score_trials_jsonl(ticker))
    return results


def main() -> int:
    args = config.build_ticker_parser(
        "score the states one request names: a trial row per state, or a study and its candidate per beam parent"
    ).parse_args()

    for ticker in config.parse_tickers(args.tickers):
        request = dataset.load_json(config.score_request_json(ticker))
        # a request says what to score and nothing about what to do with the answer: a key it does not carry
        # is an error, and the response is written only once every state of the request has one
        kind, round_number, states = request["kind"], request["round"], request["states"]
        asset = build_asset(ticker)
        if kind == KIND_SCORE:
            results = score_results(asset, states)
        elif kind == KIND_HYPERPARAMETER:
            results = hpo_results(ticker, asset, states, round_number)
        else:
            raise ValueError(f"{ticker}: {kind!r} is no kind of scoring this stage answers")
        dataset.write_json(config.score_response_json(ticker),
                           {"kind": kind, "round": round_number, "results": results})
        print(f"{ticker} {kind} round {round_number}: {len(results)} scored", flush=True)
    return 0


def xy_for_state(asset: dict, state: dict) -> dict:
    """X and Y for one state: the asset's own Y when the label's geometry is still the asset's — only X is
    stacked again — else Y walked down the 1m path in process and the feature grids joined to the decisions
    the new horizon admits."""
    barriers = dataset.barriers_from({name: state[name] for name in config.BARRIER_COORDINATE_NAMES})
    if all(asset["xy"]["barriers"][name] == barriers[name] for name in config.BARRIER_COORDINATE_NAMES):
        x, feature_columns = dataset.build_x(asset["xy"]["catalogue_values"],
                                             state["columns_by_timeframe"], asset["timeframes"])
        return {**asset["xy"], "x": x, "feature_columns": feature_columns, "barriers": barriers}
    label_events = labels.label_events(asset["label_inputs"], asset["catalogue"], barriers)
    return dataset.build_xy(asset["catalogue"], asset["timeframes"], asset["catalogue_values"],
                            asset["decision_grids"], label_events, state["columns_by_timeframe"], barriers)


def state_material(asset: dict, state: dict, rebuild: str, inherited: dict | None) -> dict:
    """What a state is scored from — X and Y, the three boosters' out-of-fold predictions and their skill.

    A move of the trade's own exit inherits all of it: neither a fit nor a prediction depends on where a
    position leaves, so only the geometry the backtest reads is replaced. Anything else is three fits, and Y
    before them when the label's own geometry moved."""
    barriers = dataset.barriers_from({name: state[name] for name in config.BARRIER_COORDINATE_NAMES})
    if rebuild == config.REBUILD_BACKTEST:
        return {**inherited, "xy": {**inherited["xy"], "barriers": barriers}}
    xy = xy_for_state(asset, state)
    y_cls = model.to_class(xy["y"])
    prediction_records, skill_by_fold = [], {}
    for fold_id in config.VALIDATION_FOLD_IDS:
        metrics, _, rows, _ = train.fold_evaluation(xy, y_cls, state["best_params"], fold_id)
        skill_by_fold[fold_id] = metrics["relative_logloss_skill"]
        prediction_records.extend(rows)
    return {"xy": xy, "skill_by_fold": skill_by_fold,
            "oos_predictions": train.to_oos_predictions(prediction_records)}


def trial_result(asset: dict, state: dict, material: dict) -> dict:
    """Score one state: the strategy's threshold selection on the boosters' predictions, the folds it chose
    at, and the path those folds chain into. The row carries the whole state, so the gate, the ranking, the
    beam and the cache never ask which coordinate moved."""
    selection = strategy.entry_edge_threshold_selection(
        strategy.build_simulation_inputs(material["xy"], asset["bars_1m"], material["oos_predictions"]))
    by_fold, skill_by_fold = selection["validation_by_fold"], material["skill_by_fold"]
    return {
        "columns_by_timeframe": state["columns_by_timeframe"],
        "best_params": state["best_params"],
        **{name: state[name] for name in config.BARRIER_COORDINATE_NAMES},
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
