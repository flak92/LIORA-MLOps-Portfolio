"""Frozen-parameter training: out-of-fold predictions and the final-holdout report.

With the parameters chosen by HPO, refit the expanding folds and store their
out-of-fold probabilities (<TICKER>_oos_predictions_ss-15-hh-dd-MM.parquet) — the only inputs the
strategy layer may use to choose its threshold — then fit on everything before
the final fold and evaluate that fold. The numbers are persisted; the model is
not, because nothing in this repo performs inference yet.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from . import config, dataset, model, validation


def write_predictions(ticker: str, rows: list[tuple]) -> Path:
    return dataset.write_parquet(
        config.oos_predictions_parquet(ticker),
        {"decision_ts": "BIGINT", "oos_fold_id": "TINYINT",
         "p_short": "DOUBLE", "p_neutral": "DOUBLE", "p_long": "DOUBLE"},
        ([int(r[0]), int(r[1])] + [repr(float(v)) for v in r[2:]] for r in rows),
        order_by="oos_fold_id, decision_ts",
    )


def fold_metrics(y_cls, proba, weight, prior_train) -> dict:
    """Model log-loss against the log-loss of the training class prior.

    relative_logloss_skill = 1 - model/prior answers exactly one question: does the model add
    information beyond knowing how often each class occurs? The prior comes
    from the rows the model was fitted on, never from the scored fold.
    """
    model_logloss = validation.multiclass_logloss(y_cls, proba, weight)
    prior_logloss = validation.prior_logloss(prior_train, y_cls, weight)
    return {
        "prior_logloss": prior_logloss,
        "model_logloss": model_logloss,
        "relative_logloss_skill": 1.0 - model_logloss / prior_logloss,
        "scored_row_count": int(y_cls.size),
    }


def fold_evaluation(xy: dict, y_cls: np.ndarray, best: dict, fold_id: int) -> tuple[dict, dict, list[tuple], "object"]:
    """Fit before the fold's window, predict the FULL window, score the supervised
    subset only. Returns (metrics, segment, prediction_rows, booster)."""
    oos_start, oos_end = validation.fold_bounds(fold_id)
    training_rows, train_weight = validation.training_set(
        xy["entry_ts"], xy["event_end_ts"], xy["sample_valid"], oos_start)
    window_rows = validation.prediction_window(xy["decision_ts"], oos_start, oos_end)
    scoring_rows, scoring_weight = validation.scoring_set(
        xy["decision_ts"], xy["entry_ts"], xy["event_end_ts"],
        xy["sample_valid"], oos_start, oos_end)
    prior_train = validation.weighted_class_prior(y_cls[training_rows], train_weight)
    assert (prior_train > 0).all(), "a class has zero weighted mass in the training segment"
    booster = model.fit(best, xy["x"][training_rows], xy["y"][training_rows], train_weight)
    window_proba = model.predict_proba(booster, xy["x"][window_rows])
    pos = np.searchsorted(window_rows, scoring_rows)   # scoring_rows ⊂ window_rows
    assert np.array_equal(window_rows[pos], scoring_rows)
    metrics = fold_metrics(y_cls[scoring_rows], window_proba[pos], scoring_weight, prior_train)
    prediction_rows = [
        (xy["decision_ts"][i], fold_id, window_proba[k, 0], window_proba[k, 1], window_proba[k, 2])
        for k, i in enumerate(window_rows)
    ]
    eligible = int((xy["sample_valid"] & (xy["decision_ts"] < oos_start)).sum())
    segment = {
        "training_row_count": int(training_rows.size),
        "purged_event_count": eligible - int(training_rows.size),
        "window_row_count": int(window_rows.size),
        "scored_row_count": int(scoring_rows.size),
    }
    return metrics, segment, prediction_rows, booster


def main() -> int:
    args = config.ticker_parser("frozen-parameter training and the final-holdout report").parse_args()

    for t in config.parse_tickers(args.tickers):
        best = dataset.load_json(config.parameters_json(t))["OPTUNAs_XGB_HPOs_best_params"]["best_params"]
        xy = dataset.load_xy(t)
        y_cls = model.to_class(xy["y"])

        pred_rows, per_fold, segments = [], {}, {}
        for fold_id in config.VALIDATION_FOLD_IDS:
            per_fold[f"fold_{fold_id}"], segments[f"fold_{fold_id}"], rows, _ = fold_evaluation(xy, y_cls, best, fold_id)
            pred_rows.extend(rows)

        # the final holdout: fitted on everything before it, never used for a choice
        final_holdout, segments[f"fold_{config.FINAL_HOLDOUT_FOLD_ID}"], rows, booster = fold_evaluation(
            xy, y_cls, best, config.FINAL_HOLDOUT_FOLD_ID)
        pred_rows.extend(rows)
        write_predictions(t, pred_rows)

        trainable = xy["sample_valid"]
        # attribution of the final-holdout booster (fitted on F1-F4) — the one fit
        # that saw the most history; the validation boosters are not kept
        gain = model.gain_importance(booster)
        payload = {
            "validation": per_fold,
            "final_holdout": final_holdout,
            "gain_importance": gain,
            # classes over the supervised population only: an ambiguous event
            # carries y = 0 in the file and would otherwise be counted as a
            # neutral observation, which is exactly what it is not
            "class_counts": {
                "short": int((trainable & (xy["y"] == -1)).sum()),
                "neutral": int((trainable & (xy["y"] == 0)).sum()),
                "long": int((trainable & (xy["y"] == 1)).sum()),
            },
            "labels": {
                "decision_count": int(xy["y"].size),
                "ambiguous_event_count": int((~xy["label_valid"]).sum()),
                "unobservable_entry_count": int((~xy["entry_observable"]).sum()),
                "trainable_row_count": int(trainable.sum()),
            },
            "segments": {
                **segments,
                "warmup_excluded_decision_count": (config.WARMUP_END_MS - config.RESEARCH_START_MS)
                // config.TIMEFRAME_DURATION_MS[config.DECISION_TIMEFRAME],
            },
        }
        dataset.write_json(config.model_evaluation_json(t), payload)
        print(f"{t} model_evaluation: prior {final_holdout['prior_logloss']:.6f} "
              f"model {final_holdout['model_logloss']:.6f} "
              f"skill {final_holdout['relative_logloss_skill']:+.4f}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
