"""Aggregate the per-asset artifacts into dashboard/ml_status.json.

Observation only, and the single place where the dashboard payload is
assembled: the blocks below follow the experiment flow (sample -> segments ->
search -> validation -> locked test -> attribution -> strategy). The file is
written with sorted keys, so reading order lives in the dashboard and in
ML_README, never in key names. The experiment is described once, globally, by
its research window and seed — library versions are in requirements.lock and
model parameters in hpo_<T>.json.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime

from . import config, dataset

ARTIFACT_KINDS = ("hpo", "metrics", "strategy")
LN3 = 1.0986122886681098   # uniform 3-class baseline (replaced by the training prior in a later commit)
EQUITY_STRIDE = 7          # daily equity grid -> weekly points for the sparkline


def _r(x, n):
    """round() that tolerates the nulls canon() writes for non-finite floats."""
    return None if x is None else round(x, n)


def sample_block(metrics: dict) -> dict:
    mask = metrics["mask"]
    return {
        "rows": mask["rows"],
        "masked": mask["masked"],
        "ambiguous": mask["ambiguous"],
        "masked_pct": round(100.0 * mask["masked"] / mask["rows"], 4),
        "n_warmup_excluded": metrics["segments"]["n_warmup_excluded"],
        "uniqueness_weight_mean": round(metrics["uniqueness_weight_mean"], 4),
        "class_counts": dict(metrics["class_counts"]),
    }


def hpo_block(hpo: dict) -> dict:
    return {
        "n_trials": hpo["n_trials"],
        "best_logloss": round(hpo["best_value"], 6),
        "best_params": dict(sorted(hpo["best_params"].items())),
    }


def classification_block(metrics: dict) -> tuple[dict, dict]:
    """(validation per split, locked test) — confusion rows are true classes."""
    validation = {
        k: {
            "logloss": round(v["logloss_weighted"], 6),
            "balanced_accuracy": round(v["balanced_accuracy"], 4),
            "mcc": round(v["mcc"], 4),
            "n": v["n"],
        }
        for k, v in sorted(metrics["validation"].items())
    }
    t = metrics["test_locked"]
    confusion = t["confusion"]
    assert sum(sum(row) for row in confusion) == t["n"], "confusion does not sum to scored rows"
    test = {
        "n": t["n"],
        "logloss": round(t["logloss_weighted"], 6),
        "balanced_accuracy": round(t["balanced_accuracy"], 4),
        "mcc": round(t["mcc"], 4),
        "confusion": confusion,
    }
    return validation, test


def thin_curve(curve: dict, stride: int = EQUITY_STRIDE) -> dict:
    """Drop the timestamp array: the grid is regular, so origin + step rebuild it."""
    ts, equity = curve["timestamp_ms"], curve["equity"]
    steps = {ts[i + 1] - ts[i] for i in range(len(ts) - 1)}
    assert len(steps) == 1, f"irregular equity grid: {sorted(steps)[:3]}"
    return {
        "t0_ms": ts[0],
        "step_ms": steps.pop() * stride,
        "stride": stride,
        "n_source": len(equity),
        "equity": [round(v, 4) for v in equity[::stride]],
        "equity_final": round(equity[-1], 4),
    }


def _pnl(block: dict) -> dict:
    return {
        "sharpe": _r(block["sharpe"], 3),
        "max_drawdown": _r(block["max_drawdown"], 4),
        "n_trades": block["n_trades"],
        "hit_rate": _r(block["hit_rate"], 4),
        "avg_trade_ret": _r(block["avg_trade_ret"], 6),
        "exposure": _r(block["exposure"], 4),
        "turnover": _r(block["turnover"], 6),
        "gate_share": _r(block["gate_share"], 4),
        "exit_counts": dict(block["exit_counts"]),
    }


def strategy_block(strategy: dict) -> dict:
    test = strategy["test_locked"]
    return {
        "tau": strategy["tau"],
        "tau_constraint_met": strategy["tau_constraint_met"],
        "selection_score_mean_sharpe": _r(strategy["selection_score_mean_sharpe"], 3),
        "costs_per_side": strategy["costs_per_side"],
        "validation": {k: _pnl(v) for k, v in sorted(strategy["validation"].items())},
        "test": _pnl(test),
        "equity_curve": thin_curve(test["equity_curve"]),
    }


def warnings_block(test: dict, strategy: dict) -> dict:
    """Protocol conditions only — never an unfavourable result."""
    return {
        "test_logloss_above_uniform": test["logloss"] >= LN3,
        "too_few_trades": strategy["test"]["n_trades"] < config.MIN_TRADES_PER_SPLIT,
        "tau_fallback": not strategy["tau_constraint_met"],
    }


def asset_report(ticker: str, hpo: dict, metrics: dict, strategy: dict) -> dict:
    validation, test = classification_block(metrics)
    strat = strategy_block(strategy)
    gain = {k: round(v, 1) for k, v in sorted(metrics["gain_importance"].items())}
    assert len(gain) == len(config.FEATURE_COLUMNS), "gain importance misses the feature contract"
    segments = {k: v for k, v in sorted(metrics["segments"].items()) if k.startswith("split_")}
    expected = {f"split_{s}" for s in (*config.VALIDATION_SPLITS, config.TEST_SPLIT)}
    assert set(segments) == expected, f"segments {sorted(segments)} != {sorted(expected)}"
    return {
        "ticker": ticker,
        "sample": sample_block(metrics),
        "segments": segments,
        "hpo": hpo_block(hpo),
        "validation": validation,
        "test": test,
        "gain_importance": gain,
        "strategy": strat,
        "warnings": warnings_block(test, strat),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="aggregate ML artifacts -> dashboard/ml_status.json")
    ap.add_argument("--tickers", default=",".join(config.TICKERS), help="comma-separated subset")
    args = ap.parse_args()

    assets = []
    for t in [x.strip().upper() for x in args.tickers.split(",") if x.strip()]:
        adir = config.ASSETS_DIR / f"Asset_{t}"
        paths = {k: adir / f"{k}_{t}.json" for k in ARTIFACT_KINDS}
        if not all(p.exists() for p in paths.values()):
            continue
        loaded = {k: dataset.read_json(p) for k, p in paths.items()}
        assets.append(asset_report(t, loaded["hpo"], loaded["metrics"], loaded["strategy"]))
    assert assets, "no complete artifact set found — run the ML chain first"

    payload = {
        "generated_at_utc": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S"),
        "research_window": [config.RESEARCH_START_UTC, config.RESEARCH_END_UTC],
        "seed": config.SEED,
        "baseline_logloss_uniform": round(LN3, 6),
        # structural parameters the page needs to label folds without hardcoding them
        "folds": {
            "bounds_utc": list(config.FOLD_BOUNDS_UTC),
            "validation": list(config.VALIDATION_SPLITS),
            "test": config.TEST_SPLIT,
        },
        "gate_min_agree": config.AGREE_MIN,
        "assets": assets,
    }
    out = config.ASSETS_DIR.parent / "dashboard" / "ml_status.json"
    dataset.write_json(out, payload)

    for a in assets:
        print(f"{a['ticker']:5} test_logloss={a['test']['logloss']:.4f} "
              f"mcc={a['test']['mcc']:.3f} tau={a['strategy']['tau']} "
              f"sharpe={a['strategy']['test']['sharpe']} "
              f"trades={a['strategy']['test']['n_trades']}")
    print(f"wrote {out} ({out.stat().st_size / 1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
