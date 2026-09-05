"""Stepwise feature-set search on the validation folds under the asset's frozen hyper-parameters: a forward step that
adds the one column clearing the acceptance margin, a backward step that drops the least important column at no worse
score, until a pass accepts nothing. Every candidate is scored by the strategy's own threshold selection on F2–F4; the
ledger of every scored trial is the state, written after each, so an interrupted run resumes without a refit and a
finished run rewrites the same bytes. Promotes nothing: the proposals are read by a hand and copied by
feature_set_promote."""

from __future__ import annotations

import math
from statistics import NormalDist

import numpy as np

from . import config, dataset, model, strategy, train, validation

STANDARD_NORMAL = NormalDist()


def columns_added(columns_by_timeframe: dict, active: dict) -> dict:
    return {timeframe: [name for name in columns_by_timeframe[timeframe] if name not in active[timeframe]]
            for timeframe in config.HIERARCHY_TIMEFRAMES}


def columns_removed(columns_by_timeframe: dict, active: dict) -> dict:
    return columns_added(active, columns_by_timeframe)


def with_column(columns_by_timeframe: dict, timeframe: str, name: str) -> dict:
    """The set with one definition added on one timeframe, kept in catalogue order."""
    kept = set(columns_by_timeframe[timeframe]) | {name}
    return {**columns_by_timeframe,
            timeframe: tuple(column for column in config.catalogue_columns(timeframe) if column in kept)}


def without_column(columns_by_timeframe: dict, timeframe: str, name: str) -> dict:
    return {**columns_by_timeframe,
            timeframe: tuple(column for column in columns_by_timeframe[timeframe] if column != name)}


def return_moments(returns_15m: np.ndarray) -> tuple[int, float, float]:
    """Count, skewness and kurtosis (not excess) of the bar returns — what the deflated Sharpe ratio needs."""
    centred = returns_15m - returns_15m.mean()
    m2 = float((centred ** 2).mean())
    skewness = float((centred ** 3).mean() / m2 ** 1.5) if m2 > 0.0 else math.nan
    kurtosis = float((centred ** 4).mean() / m2 ** 2) if m2 > 0.0 else math.nan
    return int(returns_15m.size), skewness, kurtosis


def trial_result(xy: dict, y_cls: np.ndarray, best: dict, close_1m: np.ndarray,
                 columns_by_timeframe: dict) -> tuple[dict, dict, dict]:
    """Score one set: three boosters, their windows predicted, the strategy's threshold selection on the validation
    folds. Returns (the ledger row without its pass and move, the candidate xy, the boosters by fold)."""
    x, feature_columns = dataset.build_x(xy["catalogue_values"], columns_by_timeframe)
    xy_candidate = {**xy, "x": x, "feature_columns": feature_columns}
    prediction_records, boosters, metrics_by_fold = [], {}, {}
    for fold_id in config.VALIDATION_FOLD_IDS:
        metrics_by_fold[fold_id], _, rows, boosters[fold_id] = train.fold_evaluation(xy_candidate, y_cls, best, fold_id)
        prediction_records.extend(rows)
    # the predictions as strategy.load_oos_predictions returns them: fold-major, by decision, the probabilities widened
    # to float64 exactly as the parquet round trip widens them
    oos_predictions = {
        "decision_ts": np.array([row[0] for row in prediction_records], dtype=np.int64),
        "oos_fold_id": np.array([row[1] for row in prediction_records], dtype=np.int8),
        "p_short": np.array([row[2] for row in prediction_records], dtype=np.float64),
        "p_neutral": np.array([row[3] for row in prediction_records], dtype=np.float64),
        "p_long": np.array([row[4] for row in prediction_records], dtype=np.float64),
    }
    selection = strategy.entry_edge_threshold_selection(strategy.build_simulation_inputs(xy_candidate, close_1m, oos_predictions))
    by_fold = selection["validation_by_fold"]
    return_count, return_skewness, return_kurtosis = return_moments(
        np.concatenate([by_fold[fold_id]["returns_15m"] for fold_id in config.VALIDATION_FOLD_IDS]))
    row = {
        "columns_by_timeframe": columns_by_timeframe,
        "selection_score_mean_sharpe": selection["selection_score_mean_sharpe"],
        "entry_edge_threshold": selection["entry_edge_threshold"],
        "entry_edge_threshold_constraint_met": selection["entry_edge_threshold_constraint_met"],
        "validation": {f"fold_{fold_id}": {"sharpe": by_fold[fold_id]["sharpe"], "trade_count": by_fold[fold_id]["trade_count"]}
                       for fold_id in config.VALIDATION_FOLD_IDS},
        "return_count": return_count,
        "return_skewness": return_skewness,
        "return_kurtosis": return_kurtosis,
    }
    return row, {"xy": xy_candidate, "metrics_by_fold": metrics_by_fold}, boosters


def mean_permutation_logloss_delta_importance(fit: dict, y_cls: np.ndarray, boosters: dict) -> dict[str, float]:
    """The champion's permutation importance, averaged over the validation folds — the backward step reads it."""
    xy_candidate = fit["xy"]
    deltas_by_fold = []
    for fold_id in config.VALIDATION_FOLD_IDS:
        oos_start, oos_end = validation.fold_bounds(fold_id)
        scoring_rows, scoring_weight = validation.scoring_set(
            xy_candidate["decision_ts"], xy_candidate["entry_ts"], xy_candidate["event_end_ts"],
            xy_candidate["sample_valid"], oos_start, oos_end)
        deltas_by_fold.append(train.permutation_logloss_delta_importance(
            boosters[fold_id], xy_candidate["x"][scoring_rows], y_cls[scoring_rows], scoring_weight,
            fit["metrics_by_fold"][fold_id]["model_logloss"], xy_candidate["feature_columns"]))
    return {column: float(np.mean([deltas[column] for deltas in deltas_by_fold]))
            for column in xy_candidate["feature_columns"]}


def deflated_sharpe_ratio_block(trials: list[dict], trial: dict) -> dict | None:
    """Bailey and López de Prado's deflated Sharpe ratio of one trial against every trial that cleared the trade
    floor: the probability that its Sharpe exceeds the maximum expected from that many trials, per 15m bar. None
    below two trials, where the variance of the scores is undefined."""
    scores = [row["selection_score_mean_sharpe"] for row in trials if row["entry_edge_threshold_constraint_met"]]
    trial_count = len(scores)
    if trial_count < 2:
        return None
    variance_15m = float(np.var(scores, ddof=1)) / config.ANNUALISATION_PERIOD_15M_BARS
    gamma = config.EULER_MASCHERONI_CONSTANT
    expected_maximum_sharpe_15m = math.sqrt(variance_15m) * (
        (1.0 - gamma) * STANDARD_NORMAL.inv_cdf(1.0 - 1.0 / trial_count)
        + gamma * STANDARD_NORMAL.inv_cdf(1.0 - 1.0 / (trial_count * math.e)))
    sharpe_15m = trial["selection_score_mean_sharpe"] / math.sqrt(config.ANNUALISATION_PERIOD_15M_BARS)
    return_count, skewness, kurtosis = trial["return_count"], trial["return_skewness"], trial["return_kurtosis"]
    denominator_squared = 1.0 - skewness * sharpe_15m + (kurtosis - 1.0) / 4.0 * sharpe_15m ** 2
    statistic = ((sharpe_15m - expected_maximum_sharpe_15m) * math.sqrt(return_count - 1) / math.sqrt(denominator_squared)
                 if denominator_squared > 0.0 else math.nan)
    return {
        "probability": STANDARD_NORMAL.cdf(statistic) if math.isfinite(statistic) else math.nan,
        "sharpe_15m": sharpe_15m,
        "expected_maximum_sharpe_15m": expected_maximum_sharpe_15m,
    }


def proposals_block(trials: list[dict], active: dict) -> list[dict]:
    """The best trials that cleared the trade floor and differ from the active set, by score, ties to the earlier."""
    active = as_tuples(active)
    candidates = sorted(
        ((index, row) for index, row in enumerate(trials, start=1)
         if row["entry_edge_threshold_constraint_met"] and row["columns_by_timeframe"] != active),
        key=lambda item: (-item[1]["selection_score_mean_sharpe"], item[0]))
    return [{
        "proposal": rank,
        "trial": index,
        "columns_by_timeframe": row["columns_by_timeframe"],
        "added_columns_by_timeframe": columns_added(row["columns_by_timeframe"], active),
        "removed_columns_by_timeframe": columns_removed(row["columns_by_timeframe"], active),
        "entry_edge_threshold": row["entry_edge_threshold"],
        "selection_score_mean_sharpe": row["selection_score_mean_sharpe"],
        "validation": row["validation"],
        "deflated_sharpe_ratio": deflated_sharpe_ratio_block(trials, row),
    } for rank, (index, row) in enumerate(candidates[:config.FEATURE_SET_PROPOSAL_COUNT], start=1)]


def write_state(ticker: str, state: dict) -> None:
    state["proposals"] = proposals_block(state["trials"], state["inputs"]["active_columns_by_timeframe"])
    dataset.write_json(config.feature_set_search_json(ticker), state)


def as_tuples(columns_by_timeframe: dict) -> dict:
    return {timeframe: tuple(columns_by_timeframe[timeframe]) for timeframe in config.HIERARCHY_TIMEFRAMES}


def ledger_key(columns_by_timeframe: dict) -> tuple:
    """A set as the ledger indexes it: timeframe-major, independent of how a dict was built or read back."""
    return tuple((timeframe, tuple(columns_by_timeframe[timeframe])) for timeframe in config.HIERARCHY_TIMEFRAMES)


def trade_counts(row: dict) -> str:
    return "/".join(str(row["validation"][f"fold_{fold_id}"]["trade_count"]) for fold_id in config.VALIDATION_FOLD_IDS)


def main() -> int:
    args = config.build_ticker_parser(
        "stepwise feature-set search on the validation folds under the frozen hyper-parameters; resumes"
    ).parse_args()

    for ticker in config.parse_tickers(args.tickers):
        if not config.is_artifact_set_complete(ticker):
            print(f"{ticker}: no complete artifact set — run `make ml-all` first", flush=True)
            continue
        best = dataset.load_json(config.parameters_json(ticker))["hyperparameter_search_result"]["best_params"]
        xy = dataset.load_xy(ticker)
        y_cls = model.to_class(xy["y"])
        close_1m = strategy.load_close_1m(ticker)
        active = dataset.load_feature_columns(ticker)
        inputs = dataset.to_json_safe({
            "research_window": {"start_utc": config.RESEARCH_START_UTC, "end_utc": config.RESEARCH_END_UTC, "seed": config.SEED},
            "best_params": best,
            "catalogue_columns_by_timeframe": {timeframe: config.catalogue_columns(timeframe)
                                               for timeframe in config.HIERARCHY_TIMEFRAMES},
            "active_columns_by_timeframe": active,
        })

        # the state: the recorded run when its inputs are the inputs of this one, else a fresh ledger
        path = config.feature_set_search_json(ticker)
        state = dataset.load_json(path) if path.exists() else None
        if state is None or state["inputs"] != inputs:
            state = {"inputs": inputs, "trials": [], "champion_trial": None, "pass_count": 0, "search_converged": False}
        trials = state["trials"]
        ledger = {}
        for index, row in enumerate(trials, start=1):
            row["columns_by_timeframe"] = as_tuples(row["columns_by_timeframe"])
            ledger[ledger_key(row["columns_by_timeframe"])] = index
        if state["search_converged"]:
            print(f"{ticker}: the search converged after {state['pass_count']} passes and {len(trials)} trials — "
                  f"{len(state['proposals'])} proposals in {path.name}", flush=True)
            continue

        fits: dict[int, tuple] = {}   # the boosters of the trials scored in this process, by trial index

        def score(columns_by_timeframe: dict, move: str | None) -> int:
            """The trial index of a set: the ledger's when it was scored before, else a new trial scored now."""
            key = ledger_key(columns_by_timeframe)
            if key in ledger:
                return ledger[key]
            row, fit, boosters = trial_result(xy, y_cls, best, close_1m, columns_by_timeframe)
            trials.append({**row, "pass": state["pass_count"] + 1 if move else 0, "move": move})
            ledger[key] = len(trials)
            fits[len(trials)] = (fit, boosters)
            write_state(ticker, state)
            return len(trials)

        def champion_importance(index: int) -> dict[str, float]:
            """The champion's permutation importance from the boosters in memory, else from one refit."""
            if index not in fits:
                columns_by_timeframe = trials[index - 1]["columns_by_timeframe"]
                _, fit, boosters = trial_result(xy, y_cls, best, close_1m, columns_by_timeframe)
                fits[index] = (fit, boosters)
            fit, boosters = fits[index]
            return mean_permutation_logloss_delta_importance(fit, y_cls, boosters)

        if not trials:
            index = score(active, None)
            print(f"{ticker} active set score {trials[index - 1]['selection_score_mean_sharpe']:.2f} "
                  f"trades {trade_counts(trials[index - 1])}", flush=True)
        # trial 1 is the active set by construction — the champion until a pass accepts a move
        champion = state["champion_trial"] or 1
        state["champion_trial"] = champion

        while not state["search_converged"]:
            pass_number = state["pass_count"] + 1
            champion_row = trials[champion - 1]
            accepted = False

            # forward: every admissible one-column addition, the highest score clearing the margin
            best_index = None
            for timeframe in config.HIERARCHY_TIMEFRAMES:
                if len(champion_row["columns_by_timeframe"][timeframe]) >= config.FEATURE_SET_MAXIMUM_COLUMNS_PER_TIMEFRAME:
                    continue
                for name in config.catalogue_columns(timeframe):
                    if name in champion_row["columns_by_timeframe"][timeframe]:
                        continue
                    index = score(with_column(champion_row["columns_by_timeframe"], timeframe, name),
                                  config.FEATURE_SET_SEARCH_MOVE_FORWARD)
                    row = trials[index - 1]
                    print(f"{ticker} pass {pass_number} forward +{config.feature_id(name, timeframe)} "
                          f"score {champion_row['selection_score_mean_sharpe']:.2f} -> {row['selection_score_mean_sharpe']:.2f} "
                          f"trades {trade_counts(row)}", flush=True)
                    clears = (row["selection_score_mean_sharpe"]
                              >= champion_row["selection_score_mean_sharpe"] + config.FEATURE_SET_FORWARD_ACCEPTANCE_MINIMUM_SHARPE_DELTA)
                    if clears and (best_index is None
                                   or row["selection_score_mean_sharpe"] > trials[best_index - 1]["selection_score_mean_sharpe"]):
                        best_index = index
            if best_index is not None:
                champion, accepted = best_index, True
                champion_row = trials[champion - 1]

            # backward: drop the least important column at no worse score, never the last on its timeframe
            importance = champion_importance(champion)
            droppable = [(timeframe, name) for timeframe in config.HIERARCHY_TIMEFRAMES
                         for name in champion_row["columns_by_timeframe"][timeframe]
                         if len(champion_row["columns_by_timeframe"][timeframe]) > config.FEATURE_SET_MINIMUM_COLUMNS_PER_TIMEFRAME]
            if droppable:
                timeframe, name = min(droppable, key=lambda item: importance[config.feature_id(item[1], item[0])])
                index = score(without_column(champion_row["columns_by_timeframe"], timeframe, name),
                              config.FEATURE_SET_SEARCH_MOVE_BACKWARD)
                row = trials[index - 1]
                print(f"{ticker} pass {pass_number} backward -{config.feature_id(name, timeframe)} "
                      f"score {champion_row['selection_score_mean_sharpe']:.2f} -> {row['selection_score_mean_sharpe']:.2f} "
                      f"trades {trade_counts(row)}", flush=True)
                if row["selection_score_mean_sharpe"] >= champion_row["selection_score_mean_sharpe"]:
                    champion, accepted = index, True

            state["champion_trial"] = champion
            state["pass_count"] = pass_number
            state["search_converged"] = not accepted
            write_state(ticker, state)

        print(f"{ticker} {path.name}: converged after {state['pass_count']} passes and {len(trials)} trials, "
              f"champion score {trials[champion - 1]['selection_score_mean_sharpe']:.2f}, "
              f"{len(state['proposals'])} proposals", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
