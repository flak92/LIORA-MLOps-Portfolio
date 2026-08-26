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

from . import artifacts, config, dataset, model, validation


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

    con = duckdb.connect(str(config.DB_PATH), read_only=True)
    data_sha, config_sha = dataset.run_ids(con)
    con.close()

    for t in [x.strip().upper() for x in args.tickers.split(",") if x.strip()]:
        adir = config.ASSETS_DIR / f"Asset_{t}"
        best = artifacts.read_json(adir / f"hpo_{t}.json")["best_params"]
        xy = dataset.load_xy(t)
        y_cls = model.to_class(xy["y"])

        if args.finalize:
            keep = np.flatnonzero(xy["mask_ok"] & (xy["decision_ts"] >= config.WARMUP_END_MS))
            booster = model.fit(best, xy["x"][keep], xy["y"][keep], xy["weight"][keep])
            payload = artifacts.envelope(data_sha, config_sha, config.SEED, dataset.versions())
            payload.update(
                {
                    "role": "deployment",
                    "unbiased_estimate": False,
                    "params": best,
                    "n_train": int(keep.size),
                    "booster": json.loads(booster.save_raw("json").decode()),
                }
            )
            artifacts.write_json(adir / f"model_{t}.json", payload)
            print(f"model_{t}.json: deployment fit on {keep.size} rows", flush=True)
            continue

        pred_rows: list[tuple] = []
        per_split = {}
        for split in config.VALIDATION_SPLITS:
            oos_start, oos_end = validation.split_bounds(split)
            tr = validation.train_indices(xy["decision_ts"], xy["event_end_ts"],
                                          xy["mask_ok"], oos_start)
            oo = validation.oos_indices(xy["decision_ts"], xy["mask_ok"], oos_start, oos_end)
            booster = model.fit(best, xy["x"][tr], xy["y"][tr], xy["weight"][tr])
            proba = model.predict_proba(booster, xy["x"][oo])
            per_split[f"split_{split}"] = split_metrics(y_cls[oo], proba, xy["weight"][oo])
            pred_rows += [
                (xy["decision_ts"][i], split, proba[k, 0], proba[k, 1], proba[k, 2])
                for k, i in enumerate(oo)
            ]

        # locked test fold: fitted on everything before it, evaluated exactly once
        test_start, test_end = validation.split_bounds(config.TEST_SPLIT)
        tr = validation.train_indices(xy["decision_ts"], xy["event_end_ts"],
                                      xy["mask_ok"], test_start)
        te = validation.oos_indices(xy["decision_ts"], xy["mask_ok"], test_start, test_end)
        booster = model.fit(best, xy["x"][tr], xy["y"][tr], xy["weight"][tr])
        proba_te = model.predict_proba(booster, xy["x"][te])
        test = split_metrics(y_cls[te], proba_te, xy["weight"][te])
        test["confusion"] = validation.confusion_matrix(
            y_cls[te], proba_te.argmax(axis=1).astype(np.int32)
        )
        pred_rows += [
            (xy["decision_ts"][i], config.TEST_SPLIT, proba_te[k, 0], proba_te[k, 1], proba_te[k, 2])
            for k, i in enumerate(te)
        ]
        write_predictions(t, pred_rows)

        gain = booster.get_score(importance_type="total_gain")
        payload = artifacts.envelope(data_sha, config_sha, config.SEED, dataset.versions())
        payload.update(
            {
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
                    "masked": int((~xy["mask_ok"]).sum()),
                    "ambiguous": int((xy["exit_reason"] == 9).sum()),
                },
                "segments": {
                    "train_final": int(tr.size),
                    "test_locked": int(te.size),
                },
                "uniqueness_weight_mean": float(xy["weight"].mean()),
            }
        )
        artifacts.write_json(adir / f"metrics_{t}.json", payload)
        print(f"metrics_{t}.json: test logloss {test['logloss_weighted']:.6f} "
              f"bAcc {test['balanced_accuracy']:.4f} mcc {test['mcc']:.4f}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
