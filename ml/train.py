"""Frozen-parameter training: OOF predictions, the locked test report, finalize.

1. With the HPO-frozen parameters, refit the expanding splits and store their
   out-of-fold probabilities (predictions_<T>.parquet) — the only inputs the
   strategy layer may use to choose its threshold.
2. Fit on everything before the locked test fold and evaluate that fold ONCE;
   the classification numbers are frozen in metrics_<T>.json. The model that
   produced them is not persisted — the numbers are.
3. --finalize: fit on the whole research window and persist model_<T>.json
   labelled role=deployment, unbiased_estimate=false.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import tempfile
from pathlib import Path

import duckdb
import numpy as np

from . import config, dataset, model, validation


def write_predictions(ticker: str, rows: list[tuple]) -> Path:
    out = config.ASSETS_DIR / f"Asset_{ticker}" / f"predictions_{ticker}.parquet"
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="") as f:
        w = csv.writer(f)
        for r in rows:
            w.writerow([int(r[0]), int(r[1])] + [repr(float(v)) for v in r[2:]])
        spool = Path(f.name)
    try:
        con = duckdb.connect()
        con.execute(
            f"""COPY (SELECT * FROM read_csv('{spool}', header=false,
                      columns={{'decision_ts': 'BIGINT', 'split': 'TINYINT',
                                'p_short': 'DOUBLE', 'p_neutral': 'DOUBLE',
                                'p_long': 'DOUBLE'}})
                      ORDER BY split, decision_ts)
                TO '{out}.tmp' (FORMAT PARQUET, COMPRESSION zstd)"""
        )
        con.close()
        os.replace(f"{out}.tmp", out)
    finally:
        spool.unlink(missing_ok=True)
    return out


def split_metrics(y_cls, proba, weight) -> dict:
    pred = proba.argmax(axis=1).astype(np.int32)
    return {
        "logloss_weighted": validation.multiclass_logloss(y_cls, proba, weight),
        "balanced_accuracy": validation.balanced_accuracy(y_cls, pred),
        "mcc": validation.matthews_corrcoef(y_cls, pred),
        "n": int(y_cls.size),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="frozen-parameter training and the locked test report")
    ap.add_argument("--tickers", default=",".join(config.TICKERS), help="comma-separated subset")
    ap.add_argument("--finalize", action="store_true", help="fit the deployment model on the full window")
    args = ap.parse_args()

    for t in [x.strip().upper() for x in args.tickers.split(",") if x.strip()]:
        adir = config.ASSETS_DIR / f"Asset_{t}"
        best = dataset.read_json(adir / f"hpo_{t}.json")["best_params"]
        xy = dataset.load_xy(t)
        y_cls = model.to_class(xy["y"])

        if args.finalize:
            keep = np.flatnonzero(xy["label_valid"] & (xy["decision_ts"] >= config.WARMUP_END_MS))
            booster = model.fit(best, xy["x"][keep], xy["y"][keep], xy["weight"][keep])
            payload = {
                "role": "deployment",
                "unbiased_estimate": False,
                "params": best,
                "n_train": int(keep.size),
                "booster": json.loads(booster.save_raw("json").decode()),
            }
            dataset.write_json(adir / f"model_{t}.json", payload)
            print(f"model_{t}.json: deployment fit on {keep.size} rows", flush=True)
            continue

        pred_rows: list[tuple] = []
        per_split, segments = {}, {}

        def run_split(split: int) -> tuple[dict, "np.ndarray"]:
            """Fit before the split's window, predict the FULL window, score the
            label-valid subset only. Returns (metrics, booster's test proba)."""
            oos_start, oos_end = validation.split_bounds(split)
            tr = validation.train_indices(xy["decision_ts"], xy["event_end_ts"],
                                          xy["label_valid"], oos_start)
            wi = validation.window_indices(xy["decision_ts"], oos_start, oos_end)
            oi = validation.oos_indices(xy["decision_ts"], xy["label_valid"], oos_start, oos_end)
            booster = model.fit(best, xy["x"][tr], xy["y"][tr], xy["weight"][tr])
            proba_w = model.predict_proba(booster, xy["x"][wi])
            pos = np.searchsorted(wi, oi)          # oi is a subset of wi
            assert np.array_equal(wi[pos], oi)
            metrics = split_metrics(y_cls[oi], proba_w[pos], xy["weight"][oi])
            pred_rows.extend(
                (xy["decision_ts"][i], split, proba_w[k, 0], proba_w[k, 1], proba_w[k, 2])
                for k, i in enumerate(wi)
            )
            eligible = int((xy["label_valid"] & (xy["decision_ts"] >= config.WARMUP_END_MS)
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

        # locked test fold: fitted on everything before it, evaluated exactly once
        test, booster = run_split(config.TEST_SPLIT)
        te = validation.oos_indices(xy["decision_ts"], xy["label_valid"],
                                    *validation.split_bounds(config.TEST_SPLIT))
        proba_te = model.predict_proba(booster, xy["x"][te])
        test["confusion"] = validation.confusion_matrix(
            y_cls[te], proba_te.argmax(axis=1).astype(np.int32)
        )
        write_predictions(t, pred_rows)

        gain = booster.get_score(importance_type="total_gain")
        payload = {
            "params": best,
            "validation": per_split,
            "test_locked": test,
            "gain_importance": {k: gain.get(k, 0.0) for k in config.FEATURE_COLUMNS},
            "class_counts": {
                "short": int((xy["y"] == -1).sum()),
                "neutral": int((xy["y"] == 0).sum()),
                "long": int((xy["y"] == 1).sum()),
            },
            "mask": {
                "rows": int(xy["y"].size),
                "masked": int((~xy["label_valid"]).sum()),
                "ambiguous": int((xy["exit_reason"] == 9).sum()),
            },
            "segments": {
                **segments,
                "n_warmup_excluded": (config.WARMUP_END_MS - config.RESEARCH_START_MS)
                // config.TF_MS["15m"],
            },
            "uniqueness_weight_mean": float(xy["weight"].mean()),
        }
        dataset.write_json(adir / f"metrics_{t}.json", payload)
        print(f"metrics_{t}.json: test logloss {test['logloss_weighted']:.6f} "
              f"bAcc {test['balanced_accuracy']:.4f} mcc {test['mcc']:.4f}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
