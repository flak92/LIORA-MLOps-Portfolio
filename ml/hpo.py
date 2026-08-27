"""Optuna HPO per asset: TPE(seed), sequential, in-memory study.

Objective = mean uniqueness-weighted multiclass log-loss over the three OOS
validation splits (expanding training, purge + gap before every OOS block).
The locked test fold is never touched here. The full trial history goes into
hpo_<T>.json so the search itself is auditable.
"""

from __future__ import annotations

import argparse

import duckdb
import numpy as np
import optuna

from . import config, dataset, model, validation


def objective_factory(xy: dict[str, np.ndarray]):
    y_cls = model.to_class(xy["y"])

    def objective(trial: optuna.Trial) -> float:
        params = model.suggest_params(trial)
        losses = []
        for split in config.VALIDATION_SPLITS:
            oos_start, oos_end = validation.split_bounds(split)
            tr = validation.train_indices(xy["decision_ts"], xy["event_end_ts"],
                                          xy["label_valid"], oos_start)
            oo = validation.oos_indices(xy["decision_ts"], xy["label_valid"], oos_start, oos_end)
            booster = model.fit(params, xy["x"][tr], xy["y"][tr], xy["weight"][tr])
            proba = model.predict_proba(booster, xy["x"][oo])
            losses.append(validation.multiclass_logloss(y_cls[oo], proba, xy["weight"][oo]))
        return float(np.mean(losses))

    return objective


def main() -> int:
    ap = argparse.ArgumentParser(description="Optuna TPE hyper-parameter search per asset")
    ap.add_argument("--tickers", default=",".join(config.TICKERS), help="comma-separated subset")
    args = ap.parse_args()
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    for t in [x.strip().upper() for x in args.tickers.split(",") if x.strip()]:
        xy = dataset.load_xy(t)
        study = optuna.create_study(
            direction="minimize", sampler=optuna.samplers.TPESampler(seed=config.SEED)
        )
        study.optimize(objective_factory(xy), n_trials=config.N_TRIALS, n_jobs=1)
        payload = {
            "best_params": study.best_trial.params,
            "best_value": study.best_value,
            "n_trials": config.N_TRIALS,
        }
        out = config.ASSETS_DIR / f"Asset_{t}" / f"hpo_{t}.json"
        dataset.write_json(out, payload)
        print(f"{out.name}: best logloss {study.best_value:.6f} "
              f"(trial {study.best_trial.number})", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
