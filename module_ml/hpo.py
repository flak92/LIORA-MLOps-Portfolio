"""Optuna HPO per asset: TPE(seed), sequential, in-memory study.

Objective = mean uniqueness-weighted multiclass log-loss over the three OOS
validation folds F2-F4 (expanding training, purged before every OOS block).
The populations and their weights do not depend on the hyper-parameters, so
they are built once instead of once per trial.
The final holdout fold is never touched here. <TICKER>_parameters.json keeps
the winner and the trial count; the trajectory of 50 trials is a search diary,
not a result.
"""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import optuna

from . import config, dataset, model, validation


def build_objective(xy: dict[str, np.ndarray]):
    y_cls = model.to_class(xy["y"])
    folds = []
    for fold_id in config.VALIDATION_FOLD_IDS:
        oos_start, oos_end = validation.fold_bounds(fold_id)
        folds.append((
            validation.training_set(xy["entry_ts"], xy["event_end_ts"],
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


def experiment_configuration(ticker: str) -> dict:
    """The a-priori experiment configuration section of the parameters file.

    Read from the current module_ml/config.py when the search runs, not
    recovered from the artifacts — it describes the experiment's a-priori
    settings and is not artifact provenance: it proves nothing about any
    particular file. Everything the run *chose* — the winning
    hyper-parameters, the entry edge threshold — lives in the result files,
    never here.
    """
    return {
        "ticker": ticker,
        "research_window": {
            "start_utc": config.RESEARCH_START_UTC,
            "end_utc": config.RESEARCH_END_UTC,
            "seed": config.SEED,
        },
        "folds": {
            "bounds_utc": list(config.FOLD_BOUNDS_UTC),
            "validation_fold_ids": list(config.VALIDATION_FOLD_IDS),
            "final_holdout_fold_id": config.FINAL_HOLDOUT_FOLD_ID,
            "warmup_4h_bars": config.WARMUP_4H_BARS,
            "first_decision_utc": datetime.fromtimestamp(
                config.WARMUP_END_MS / 1000, tz=UTC).strftime("%Y-%m-%d %H:%M"),
            "purge_rule": "event_end_ts <= oos_start",
            "embargo": "none — forward chaining places no training row after the OOS block",
        },
        "features": {
            "hierarchy_timeframes": list(config.HIERARCHY_TIMEFRAMES),
            "decision_timeframe": config.DECISION_TIMEFRAME,
            "families": list(config.FEATURE_FAMILIES),
            "columns": list(config.FEATURE_COLUMNS),
            "ema_fast_span_bars": config.EMA_FAST_SPAN_BARS,
            "ema_slow_span_bars": config.EMA_SLOW_SPAN_BARS,
            "atr_wilder_smoothing_period_bars": config.ATR_WILDER_SMOOTHING_PERIOD_BARS,
            "rsi_wilder_smoothing_period_bars": config.RSI_WILDER_SMOOTHING_PERIOD_BARS,
            "range_position_lookback_bars": config.RANGE_POSITION_LOOKBACK_BARS,
            "log_volume_zscore_lookback_bars": config.LOG_VOLUME_ZSCORE_LOOKBACK_BARS,
        },
        "labels": {
            "atr_barrier_multiplier": config.ATR_BARRIER_MULTIPLIER,
            "label_horizon_minutes": config.LABEL_HORIZON_MINUTES,
            "sigma": "ATR14 of the last closed canonical 1h bar",
            "touch_requires": "volume > 0",
            "event_resolution_codes": {
                name: code for code, name in config.EVENT_RESOLUTION_NAMES.items()},
            "supervised_population": "sample_valid = entry_observable & label_valid",
        },
        "hyperparameter_search": {
            "sampler": "optuna.samplers.TPESampler",
            "sampler_seed": config.SEED,
            "trial_count": config.HYPERPARAMETER_SEARCH_TRIAL_COUNT,
            "parallelism": "sequential (n_jobs=1) — TPE is reproducible only in order",
            "objective": "mean uniqueness-weighted multiclass log-loss over folds "
                         + ", ".join(f"F{i}" for i in config.VALIDATION_FOLD_IDS),
            "space": {k: list(v) for k, v in config.HYPERPARAMETER_SEARCH_SPACE.items()},
            "xgboost_fixed_parameters": dict(config.XGBOOST_FIXED_PARAMETERS),
        },
        "strategy": {
            "execution_cost_rate_per_trade_side": config.EXECUTION_COST_RATE_PER_TRADE_SIDE,
            "entry_edge_threshold_grid": {
                "minimum": config.ENTRY_EDGE_THRESHOLD_GRID[0],
                "maximum": config.ENTRY_EDGE_THRESHOLD_GRID[-1],
                "step": round(config.ENTRY_EDGE_THRESHOLD_GRID[1]
                              - config.ENTRY_EDGE_THRESHOLD_GRID[0], 4),
                "count": len(config.ENTRY_EDGE_THRESHOLD_GRID),
            },
            "minimum_trades_per_validation_fold": config.MINIMUM_TRADES_PER_VALIDATION_FOLD,
            "trend_gate_timeframe": config.TREND_GATE_TIMEFRAME,
            "minimum_agreeing_trend_timeframes": config.MINIMUM_AGREEING_TREND_TIMEFRAMES,
            "annualisation_period_15m_bars": config.ANNUALISATION_PERIOD_15M_BARS,
        },
    }


def main() -> int:
    args = config.ticker_parser("Optuna TPE hyper-parameter search per asset").parse_args()
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    for t in config.parse_tickers(args.tickers):
        xy = dataset.load_xy(t)
        study = optuna.create_study(
            direction="minimize", sampler=optuna.samplers.TPESampler(seed=config.SEED)
        )
        study.optimize(build_objective(xy),
                       n_trials=config.HYPERPARAMETER_SEARCH_TRIAL_COUNT, n_jobs=1)
        payload = {
            "experiment_configuration": experiment_configuration(t),
            "OPTUNAs_XGB_HPOs_best_params": {
                "best_params": study.best_trial.params,
                "best_logloss": study.best_value,
                "trial_count": config.HYPERPARAMETER_SEARCH_TRIAL_COUNT,
            },
        }
        out = config.parameters_json(t)
        dataset.write_json(out, payload)
        print(f"{t} {out.name}: best logloss {study.best_value:.6f} "
              f"(trial {study.best_trial.number})", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
