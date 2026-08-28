"""Optuna HPO per asset: TPE(seed), sequential, in-memory study.

Objective = mean uniqueness-weighted multiclass log-loss over the three OOS
validation folds F2-F4 (expanding training, purged before every OOS block).
The populations and their weights do not depend on the hyper-parameters, so
they are built once instead of once per trial.
The final holdout fold is never touched here. <TICKER>_OPTUNAs_XGB_HPOs_best_params.json keeps
the winner and the trial count; the trajectory of 50 trials is a search diary,
not a result.
"""

from __future__ import annotations

import numpy as np
import optuna

from . import config, dataset, model, validation


def objective_factory(xy: dict[str, np.ndarray]):
    y_cls = model.to_class(xy["y"])
    folds = []
    for fold_id in config.VALIDATION_FOLD_IDS:
        oos_start, oos_end = validation.fold_bounds(fold_id)
        folds.append((
            validation.training_set(xy["decision_ts"], xy["entry_ts"], xy["event_end_ts"],
                                    xy["sample_valid"], oos_start),
            validation.scoring_set(xy["decision_ts"], xy["entry_ts"], xy["event_end_ts"],
                                   xy["sample_valid"], oos_start, oos_end),
        ))

    def objective(trial: optuna.Trial) -> float:
        params = model.suggest_params(trial)
        losses = []
        for (training_rows, train_weight), (scoring_rows, scoring_weight) in folds:
            booster = model.fit(params, xy["x"][training_rows], xy["y"][training_rows], train_weight)
            proba = model.predict_proba(booster, xy["x"][scoring_rows])
            losses.append(validation.multiclass_logloss(y_cls[scoring_rows], proba, scoring_weight))
        return float(np.mean(losses))

    return objective


def main() -> int:
    args = config.ticker_parser("Optuna TPE hyper-parameter search per asset").parse_args()
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    for t in config.parse_tickers(args.tickers):
        xy = dataset.load_xy(t)
        study = optuna.create_study(
            direction="minimize", sampler=optuna.samplers.TPESampler(seed=config.SEED)
        )
        study.optimize(objective_factory(xy),
                       n_trials=config.HYPERPARAMETER_SEARCH_TRIAL_COUNT, n_jobs=1)
        payload = {
            "best_params": study.best_trial.params,
            "best_logloss": study.best_value,
            "trial_count": config.HYPERPARAMETER_SEARCH_TRIAL_COUNT,
        }
        out = config.hpo_best_params_json(t)
        dataset.write_json(out, payload)
        print(f"{t} {out.name}: best logloss {study.best_value:.6f} "
              f"(trial {study.best_trial.number})", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
