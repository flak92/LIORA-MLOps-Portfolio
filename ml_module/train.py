"""Frozen-parameter training: out-of-fold predictions and the final OOS report.

With the parameters chosen by HPO, refit the expanding splits and store their
out-of-fold probabilities (predictions_<T>.parquet) — the only inputs the
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
        config.ASSETS_DIR / f"Asset_{ticker}" / f"predictions_{ticker}.parquet",
        {"decision_ts": "BIGINT", "split": "TINYINT",
         "p_short": "DOUBLE", "p_neutral": "DOUBLE", "p_long": "DOUBLE"},
        ([int(r[0]), int(r[1])] + [repr(float(v)) for v in r[2:]] for r in rows),
        order_by="split, decision_ts",
    )


def split_metrics(y_cls, proba, weight, prior_train) -> dict:
    """Model log-loss against the log-loss of the training class prior.

    skill = 1 - model/prior answers exactly one question: does the model add
    information beyond knowing how often each class occurs? The prior comes
    from the rows the model was fitted on, never from the scored fold.
    """
    pred = proba.argmax(axis=1).astype(np.int32)
    model_ll = validation.multiclass_logloss(y_cls, proba, weight)
    prior_ll = validation.prior_logloss(prior_train, y_cls, weight)
    return {
        "prior_logloss": prior_ll,
        "model_logloss": model_ll,
        "skill": 1.0 - model_ll / prior_ll,
        "mcc": validation.matthews_corrcoef(y_cls, pred),
        "n": int(y_cls.size),
    }


def main() -> int:
    args = config.ticker_parser("frozen-parameter training and the final-OOS report").parse_args()

    for t in config.parse_tickers(args.tickers):
        adir = config.ASSETS_DIR / f"Asset_{t}"
        best = dataset.read_json(adir / f"hpo_{t}.json")["best_params"]
        xy = dataset.load_xy(t)
        y_cls = model.to_class(xy["y"])

        pred_rows: list[tuple] = []
        per_split, segments = {}, {}

        def run_split(split: int) -> tuple[dict, "np.ndarray"]:
            """Fit before the split's window, predict the FULL window, score the
            label-valid subset only. Returns (metrics, booster's test proba)."""
            oos_start, oos_end = validation.split_bounds(split)
            tr = validation.train_indices(xy["decision_ts"], xy["event_end_ts"],
                                          xy["sample_valid"], oos_start)
            wi = validation.window_indices(xy["decision_ts"], oos_start, oos_end)
            oi = validation.oos_indices(xy["decision_ts"], xy["sample_valid"], oos_start, oos_end)
            prior_train = validation.weighted_class_prior(y_cls[tr], xy["weight"][tr])
            assert (prior_train > 0).all(), "a class has zero weighted mass in the training segment"
            booster = model.fit(best, xy["x"][tr], xy["y"][tr], xy["weight"][tr])
            proba_w = model.predict_proba(booster, xy["x"][wi])
            pos = np.searchsorted(wi, oi)          # oi is a subset of wi
            assert np.array_equal(wi[pos], oi)
            metrics = split_metrics(y_cls[oi], proba_w[pos], xy["weight"][oi], prior_train)
            pred_rows.extend(
                (xy["decision_ts"][i], split, proba_w[k, 0], proba_w[k, 1], proba_w[k, 2])
                for k, i in enumerate(wi)
            )
            eligible = int((xy["sample_valid"] & (xy["decision_ts"] >= config.WARMUP_END_MS)
                            & (xy["decision_ts"] < oos_start)).sum())
            segments[f"split_{split}"] = {
                "n_train": int(tr.size),
                "n_purged": eligible - int(tr.size),
                "n_window": int(wi.size),
                "n_scored": int(oi.size),
            }
            return metrics, booster

        for split in config.VALIDATION_SPLITS:
            per_split[f"split_{split}"], _ = run_split(split)

        # final OOS fold: fitted on everything before it, never used for any choice
        test, booster = run_split(config.TEST_SPLIT)
        write_predictions(t, pred_rows)

        trainable = xy["sample_valid"]
        gain = booster.get_score(importance_type="total_gain")
        payload = {
            "params": best,
            "validation": per_split,
            "test": test,
            "gain_importance": {k: gain.get(k, 0.0) for k in config.FEATURE_COLUMNS},
            # classes over the supervised population only: an ambiguous event
            # carries y = 0 in the file and would otherwise be counted as a
            # neutral observation, which is exactly what it is not
            "class_counts": {
                "short": int((trainable & (xy["y"] == -1)).sum()),
                "neutral": int((trainable & (xy["y"] == 0)).sum()),
                "long": int((trainable & (xy["y"] == 1)).sum()),
            },
            "labels": {
                "rows": int(xy["y"].size),
                "ambiguous": int((~xy["label_valid"]).sum()),
                "unobservable": int((~xy["entry_observable"]).sum()),
                "trainable": int(trainable.sum()),
            },
            "segments": {
                **segments,
                "n_warmup_excluded": (config.WARMUP_END_MS - config.RESEARCH_START_MS)
                // config.TF_MS["15m"],
            },
            "uniqueness_weight_mean": float(xy["weight"][trainable].mean()),
        }
        dataset.write_json(adir / f"metrics_{t}.json", payload)
        print(f"metrics_{t}.json: prior {test['prior_logloss']:.6f} "
              f"model {test['model_logloss']:.6f} skill {test['skill']:+.4f} "
              f"mcc {test['mcc']:.4f}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
