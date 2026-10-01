"""Optuna TPE per asset, sequential and seeded, over the frozen search space. The objective is the CAGR of
the chained validation path at the threshold the one selection rule would pick — the quantity the serpentine
search selects on, so the parameters are tuned on it. The final holdout is never touched here.

The stage is a function of X, Y, the frozen constants and the point a hand promoted: that point, when there is one,
is its study's first trial and every other is drawn, so the parameters file it writes is a function of the raw store,
the files a hand drafted and this code, never of what it wrote last.

Inside the serpentine search the study is also the hpo axis: one candidate per beam member, drawn on that
member's own X and Y by `score.hpo_results()`, and pruned by one explicit gate. It cannot answer worse than the
member it ran on, because a candidate has to beat it — the guarantee is the gate's, not a point the study was
handed.

That gate is the serpentine search's gate read one fold at a time: after each fold, the thresholds at
which **every** fold so far clears the trade floor and beats the parent's CAGR. The set only shrinks as
folds are added, and the child the serpentine search would keep needs one threshold inside it over all three, so a
trial whose set has gone empty cannot produce one and stops. Nothing admissible is discarded by it.

Optuna's own median pruner is not a gate here: it compares a trial's best value over all its steps with the median
of other trials at one step, and with folds as calendar years that comparison is not of like with like.

Every point the search drew is left in the asset's partition of the `hpo_trials` family — `score.py` leaves a
study's points in `score_trials`, the same row, one writer each — where the parameters file keeps only the one
it chose. The ledger is JSON Lines appended a line at a time — the technique the serpentine search's own ledger
uses, written by `dataset.write_jsonl` and by nothing else — and the family's `schema.json` is written from the
one constant the row is built from."""

from pathlib import Path

import numpy as np
import optuna

from . import config, dataset, model, strategy, train, validation


def log_trials(study: optuna.Study, origin: str, round_number: int | None, ledger: Path) -> None:
    """Every point a study drew, one line each, appended to the ledger it is given — the writer's family's partition of
    the asset — and never rewritten, the family's `schema.json` beside its partitions.

    A study's place in the ledger is read off the ledger: every study opens with its own HPO trial 1, so the
    lines carrying that index are the studies before this one. One read per study and no state kept outside
    the file, which is why two fanned-out processes need nothing from each other — they write different
    assets' partitions.

    Nothing here is written differently by a second run: no run id, no timestamp, no host name. Two studies
    over an empty store therefore leave the same bytes, and the ledger stops being a note about the search
    and becomes a thing the search can be proved against. The ledger only grows; a hand clears it."""
    study_index = 1 + sum(row["hpo_trial_index"] == 1 for row in dataset.load_jsonl(ledger)) if ledger.exists() else 1
    for trial in study.trials:
        dataset.write_jsonl(ledger, trial_row(trial, origin, round_number, study_index))
    # a partition's file is named for its family, so the family's schema lands beside the partitions — the same bytes
    # from every asset and every study
    dataset.write_json(config.schema_json(ledger.stem, config.STORE_TRIALS_DIR),
                       [{"column": column, "type": kind} for column, kind in TRIAL_COLUMNS.items()])


# the key the chosen point's value is published under, and the name one trial's value carries in the
# ledger — each named for what it measures
OBJECTIVE_KEY = "best_cagr_validation_path"
TRIAL_METRIC_KEY = "cagr_validation_path"

# the DuckDB type a drawn parameter takes, by the kind of its draw in HYPERPARAMETER_SEARCH_SPACE
HYPERPARAMETER_TYPE_BY_DRAW_KIND = {"int": "BIGINT", "int_step": "BIGINT", "float": "DOUBLE", "log": "DOUBLE"}
# the columns of a trial row, in the writer's order, each with the DuckDB type its values take — the one constant the
# row is built from and the `schema.json` of both ledger families is written from; `params` a struct of the search
# space, its field names quoted because xgboost's `lambda` is a word of the SQL
TRIAL_COLUMNS = {
    "origin": "VARCHAR", "round": "BIGINT", "study_index": "BIGINT", "hpo_trial_index": "BIGINT",
    "hpo_trial_outcome": "VARCHAR",
    "params": "STRUCT(" + ", ".join(f'"{name}" {HYPERPARAMETER_TYPE_BY_DRAW_KIND[draw[0]]}'
                                    for name, draw in config.HYPERPARAMETER_SEARCH_SPACE.items()) + ")",
    "floor_clearing_threshold_count_by_fold": "BIGINT[]", "admissible_threshold_count_by_fold": "BIGINT[]",
    "admissible": "BOOLEAN", "pruned_at_fold": "BIGINT", TRIAL_METRIC_KEY: "DOUBLE",
}


def admissible_thresholds(sweeps: dict[int, dict], parent_validation_by_fold: dict[int, dict] | None,
                          fold_ids: tuple[int, ...]) -> list[float]:
    """The thresholds at which every fold evaluated so far clears the trade floor and — when there is a
    parent to beat — beats it there on the measure the selection names. One list, shrinking as folds are added.

    This is the serpentine search's gate read one fold at a time. That gate keeps a child only where a
    **single** threshold makes every validation fold better than the parent, so its threshold must lie in
    this set over all three folds; a trial whose set has gone empty cannot produce one however the remaining
    folds land, because adding a fold can only remove thresholds. Nothing admissible is discarded: the gate
    stops a trial exactly when the trial can no longer produce a child the serpentine search would keep, at
    the first fold that settles it."""
    return [threshold for threshold in config.ENTRY_EDGE_THRESHOLD_GRID
            if all(sweeps[fold_id][threshold]["trade_count"] >= config.MINIMUM_TRADES_PER_VALIDATION_FOLD
                   and (parent_validation_by_fold is None
                        or sweeps[fold_id][threshold][config.SELECTION_FOLD_MEASURE]
                        > parent_validation_by_fold[fold_id][config.SELECTION_FOLD_MEASURE])
                   for fold_id in fold_ids)]


def sweep_selection(sweeps: dict[int, dict]) -> tuple[float, float]:
    """The threshold the one selection rule would pick over these folds, and the chained path's growth rate
    there — the trial's own value. Ties keep the smaller threshold, as the rule takes them.

    The rule reads the trade floor and nothing else, never the parent: a trial's value is what it is worth,
    not what it is worth against something. A trial with no threshold clearing the floor in every fold never
    reaches here — the fold loop stops it — because the grid floor it would otherwise be scored at is a
    fallback for a *report*, a number to show when nothing qualified: handed to a sampler, it would let a trial
    that never qualified compete on the numbers of a threshold nothing qualified for."""
    cleared = admissible_thresholds(sweeps, None, config.VALIDATION_FOLD_IDS)
    value, negated = max((strategy.validation_path_cagr(
        {fold_id: sweeps[fold_id][threshold]["final_equity"] for fold_id in config.VALIDATION_FOLD_IDS}),
        -threshold) for threshold in cleared)
    return -negated, value


def build_objective(xy: dict[str, np.ndarray], bars_1m: dict[str, np.ndarray],
                    parent_validation_by_fold: dict[int, dict] | None = None):
    """The objective one trial is scored by, and the gates that stop it early when it cannot win.

    One sweep of the threshold grid per fold, kept for the trial's life: the gates read off it the thresholds
    that clear the trade floor and, against a parent, beat it on every fold so far, and the trial's own value
    is read off the same three sweeps. Nothing is
    replayed, because nothing has to be — a sweep is a deterministic function of the fold's predictions."""
    y_cls = model.to_class(xy["y"])

    def objective(trial: optuna.Trial) -> float:
        params = model.suggest_params(trial)
        prediction_records, sweeps = [], {}
        floor_count_by_fold, admissible_count_by_fold = [], []
        for fold_id in config.VALIDATION_FOLD_IDS:
            _, _, rows, _ = train.fold_evaluation(xy, y_cls, params, fold_id)
            prediction_records.extend(rows)
            simulation_inputs = strategy.build_simulation_inputs(
                xy, bars_1m, train.to_oos_predictions(prediction_records))
            sweeps[fold_id] = strategy.results_by_threshold(
                simulation_inputs, strategy.signals_for_fold(simulation_inputs, fold_id),
                *validation.fold_bounds(fold_id))
            evaluated = config.VALIDATION_FOLD_IDS[:len(sweeps)]
            # two counts, two questions. The floor is the trial's own admissibility — a strategy at all —
            # and is asked in both modes. Admissibility against a parent is the serpentine search's gate's question
            # and exists only where there is a parent; one key holding both would answer a different question
            # depending on who ran the study, which is the kind of key a register cannot define
            floor = admissible_thresholds(sweeps, None, evaluated)
            floor_count_by_fold.append(len(floor))
            trial.set_user_attr("floor_clearing_threshold_count_by_fold", list(floor_count_by_fold))
            admissible = None
            if parent_validation_by_fold is not None:
                admissible = admissible_thresholds(sweeps, parent_validation_by_fold, evaluated)
                admissible_count_by_fold.append(len(admissible))
                trial.set_user_attr("admissible_threshold_count_by_fold", list(admissible_count_by_fold))
            if not floor or (admissible is not None and not admissible):
                raise optuna.TrialPruned()
        threshold, value = sweep_selection(sweeps)
        # whether the threshold the rule chose for this trial is one at which every fold beats the parent —
        # the serpentine search's gate's own question about this trial's own tau, answered where the sweeps already
        # are so the loop need not refit to ask it. Not "the set is non-empty": a non-empty set the chosen threshold
        # does not belong to is a child the gate still refuses
        trial.set_user_attr("admissible", None if admissible is None else threshold in admissible)
        return value

    return objective


def trial_row(trial: optuna.trial.FrozenTrial, origin: str, round_number: int | None,
              study_index: int) -> dict:
    """One trial as one line: where it was drawn and in which round, its place in the study and the study's
    in the ledger, the point the sampler drew, and what the trial left — the columns of `TRIAL_COLUMNS`, no other.

    Every key stands on every line, `null` where it does not apply, so the file reads as one table and not
    as two, and a reader counting lines does not have to know which is which first.

    The outcome is read from `trial.state`, Optuna's own word for how the trial ended, and never inferred from
    `trial.value`; a pruned trial's line carries no value."""
    pruned = trial.state == optuna.trial.TrialState.PRUNED
    floor_counts = trial.user_attrs["floor_clearing_threshold_count_by_fold"]
    admissible_counts = trial.user_attrs.get("admissible_threshold_count_by_fold")
    admissible = trial.user_attrs["admissible"] if not pruned else None
    values = {"origin": origin, "round": round_number, "study_index": study_index,
              "hpo_trial_index": trial.number + 1, "hpo_trial_outcome": "pruned" if pruned else "complete",
              "params": trial.params,
              "floor_clearing_threshold_count_by_fold": floor_counts,
              "admissible_threshold_count_by_fold": admissible_counts,
              "admissible": admissible,
              "pruned_at_fold": config.VALIDATION_FOLD_IDS[len(floor_counts) - 1] if pruned else None,
              TRIAL_METRIC_KEY: None if pruned else trial.value}
    return {column: values[column] for column in TRIAL_COLUMNS}


def search_hyperparameters(xy: dict, bars_1m: dict[str, np.ndarray], seed: int,
                           parent_validation_by_fold: dict[int, dict] | None = None,
                           first_point: dict | None = None) -> optuna.Study:
    """The asset's TPE search over the frozen space, sequential and seeded — the study itself, so a caller
    reads the point it chose, that point's value and every point it drew from one object. The chain seeds it with
    `SEED`; a study of the serpentine search with `SEED` plus its round, so a parent that stays in the beam draws
    new points in the next round rather than the same ones again.

    The chain's study takes the point a hand promoted as its first trial: on the promoted search state's own X and
    Y, with the same fits and the same threshold rule, it scores the proposal's path CAGR, so the point the stage
    keeps is worth at least that. A study of the serpentine search takes none: the parent's own parameters can never be
    offered — at its own threshold every fold equals the parent's, and no other threshold beats the parent on every
    fold, or the parent would stand there — so a trial spent on them is a fit that cannot become a candidate. Its
    guarantee lives in the gate: a candidate must beat the parent, so a study that finds nothing better offers
    nothing."""
    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=seed,
                                           n_startup_trials=config.HYPERPARAMETER_SEARCH_STARTUP_TRIAL_COUNT),
    )
    if first_point is not None:
        study.enqueue_trial(first_point)
    study.optimize(build_objective(xy, bars_1m, parent_validation_by_fold),
                   n_trials=config.HYPERPARAMETER_SEARCH_TRIAL_COUNT, n_jobs=1)
    return study


def admissible_point(study) -> dict | None:
    """The study's best admissible point, or nothing.

    The point is the best **admissible** one, not the best. A study's best trial by value may be one whose
    chosen threshold does not beat the parent on every fold; the serpentine search's gate refuses such a child, while
    a point further down the list may be one the gate keeps. The trials are read by value, descending, and the
    first admissible one is offered: better than the parent's CAGR on every fold, it beats the parent's path
    too and is not the parent's own point. When none is, nothing is — which is an answer."""
    completed = study.get_trials(deepcopy=False, states=(optuna.trial.TrialState.COMPLETE,))
    admissible = sorted((trial for trial in completed if trial.user_attrs["admissible"]),
                        key=lambda trial: (-trial.value, trial.number))
    return admissible[0].params if admissible else None


def main() -> int:
    args = config.build_ticker_parser("Optuna TPE hyper-parameter search per asset").parse_args()
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    for ticker in config.parse_tickers(args.tickers):
        xy = dataset.load_xy(ticker)
        bars_1m = strategy.load_bars_1m(ticker)
        # the stage has no parent to beat, and its one point to start from is the one a hand promoted — a drafted
        # file, so <TICKER>_parameters.json is never a function of its own last value
        point = config.hyperparameter_point_json(ticker)
        study = search_hyperparameters(xy, bars_1m, config.SEED,
                                       first_point=dataset.load_json(point)["best_params"] if point.exists() else None)
        if not study.get_trials(deepcopy=False, states=(optuna.trial.TrialState.COMPLETE,)):
            raise SystemExit(f"{ticker}: no admissible strategy on every validation fold at any threshold — "
                             f"every one of the {config.HYPERPARAMETER_SEARCH_TRIAL_COUNT} trials was pruned")
        payload = {
            "hyperparameter_search_result": {
                "best_params": study.best_trial.params,
                OBJECTIVE_KEY: study.best_value,
                "hpo_trial_count": config.HYPERPARAMETER_SEARCH_TRIAL_COUNT,
            },
        }
        out = config.parameters_json(ticker)
        dataset.write_json(out, payload)
        log_trials(study, "hpo", None, config.hpo_trials_jsonl(ticker))
        print(f"{ticker} {out.name}: {OBJECTIVE_KEY} {study.best_value:.6f} "
              f"(HPO trial {study.best_trial.number + 1})", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
