"""ML research monitoring: aggregate per-asset artifacts into ml_status.json.

Observation only. Envelope consistency (one data_sha256, one config_sha256
across every artifact) is asserted, per-artifact SHA-256 file hashes are
recorded, and the dashboard renders the snapshot on the ML Research tab.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime

from . import artifacts, config

LN3 = 1.0986122886681098   # uniform 3-class baseline log-loss


def sha256_file(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="aggregate ML artifacts -> dashboard/ml_status.json")
    ap.add_argument("--tickers", default=",".join(config.TICKERS), help="comma-separated subset")
    args = ap.parse_args()

    assets, envelopes = [], set()
    for t in [x.strip().upper() for x in args.tickers.split(",") if x.strip()]:
        adir = config.ASSETS_DIR / f"Asset_{t}"
        needed = {k: adir / f"{k}_{t}.json" for k in ("hpo", "metrics", "strategy")}
        if not all(p.exists() for p in needed.values()):
            continue
        hpo = artifacts.read_json(needed["hpo"])
        metrics = artifacts.read_json(needed["metrics"])
        strategy = artifacts.read_json(needed["strategy"])
        for doc in (hpo, metrics, strategy):
            envelopes.add((doc["data_sha256"], doc["config_sha256"]))
        test_m, test_s = metrics["test_locked"], strategy["test_locked"]
        assets.append(
            {
                "ticker": t,
                "rows": metrics["mask"]["rows"],
                "masked_pct": round(100.0 * metrics["mask"]["masked"] / metrics["mask"]["rows"], 3),
                "ambiguous": metrics["mask"]["ambiguous"],
                "class_counts": metrics["class_counts"],
                "uniqueness_weight_mean": round(metrics["uniqueness_weight_mean"], 4),
                "segments": metrics["segments"],
                "best_params": {k: hpo["best_params"][k] for k in ("max_depth", "eta", "num_boost_round")},
                "hpo_best_logloss": round(hpo["best_value"], 6),
                "validation_logloss": {k: round(v["logloss_weighted"], 6)
                                       for k, v in metrics["validation"].items()},
                "test": {
                    "logloss": round(test_m["logloss_weighted"], 6),
                    "balanced_accuracy": round(test_m["balanced_accuracy"], 4),
                    "mcc": round(test_m["mcc"], 4),
                },
                "strategy": {
                    "tau": strategy["tau"],
                    "tau_constraint_met": strategy["tau_constraint_met"],
                    "sharpe": round(test_s["sharpe"], 3),
                    "max_drawdown": round(test_s["max_drawdown"], 4),
                    "n_trades": test_s["n_trades"],
                    "hit_rate": round(test_s["hit_rate"], 4),
                    "exposure": round(test_s["exposure"], 4),
                    "gate_share": round(test_s["gate_share"], 4),
                },
                "top_gain": dict(sorted(metrics["gain_importance"].items(),
                                        key=lambda kv: -kv[1])[:5]),
                "warnings": {
                    "test_logloss_above_uniform": test_m["logloss_weighted"] >= LN3,
                    "too_few_trades": test_s["n_trades"] < config.MIN_TRADES_PER_SPLIT,
                },
                "artifact_sha256": {k: sha256_file(p) for k, p in needed.items()},
            }
        )

    assert len(envelopes) <= 1, f"inconsistent artifact envelopes: {envelopes}"
    data_sha, config_sha = (next(iter(envelopes)) if envelopes else (None, None))
    payload = {
        "generated_at_utc": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S"),
        "research_window": [config.RESEARCH_START_UTC, config.RESEARCH_END_UTC],
        "data_sha256": data_sha,
        "config_sha256": config_sha,
        "assets": assets,
    }
    out = config.ASSETS_DIR.parent / "dashboard" / "ml_status.json"
    out.write_text(json.dumps(artifacts.canon(payload), sort_keys=True, indent=1) + "\n",
                   encoding="utf-8")
    for a in assets:
        print(f"{a['ticker']:5} test_logloss={a['test']['logloss']:.4f} "
              f"bAcc={a['test']['balanced_accuracy']:.3f} mcc={a['test']['mcc']:.3f} "
              f"tau={a['strategy']['tau']} sharpe={a['strategy']['sharpe']} "
              f"trades={a['strategy']['n_trades']}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
