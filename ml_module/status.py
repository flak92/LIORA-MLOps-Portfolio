"""Aggregate the per-asset artifacts into monitoring_module/ml_status.json.

Observation only, and the single place where the dashboard payload is
assembled: the blocks below follow the experiment flow (sample -> search ->
validation -> final OOS -> attribution -> strategy). The file is
written with sorted keys, so reading order lives in the dashboard and in
ML_README, never in key names. The experiment is described once, globally, by
its research window and seed — library versions are in requirements.lock and
model parameters in hpo_<T>.json.
"""

from __future__ import annotations

from datetime import UTC, datetime

from . import config, dataset

ARTIFACT_KINDS = ("hpo", "metrics", "strategy")
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


def _cls(v: dict) -> dict:
    return {
        "prior_logloss": round(v["prior_logloss"], 6),
        "model_logloss": round(v["model_logloss"], 6),
        "skill": round(v["skill"], 6),
        "mcc": round(v["mcc"], 4),
        "n": v["n"],
    }


def classification_block(metrics: dict) -> tuple[dict, dict]:
    """(validation per split, final OOS)."""
    validation = {k: _cls(v) for k, v in sorted(metrics["validation"].items())}
    return validation, _cls(metrics["test"])


def thin_curve(curve: dict, stride: int = EQUITY_STRIDE) -> dict:
    """The sparkline needs the shape, not the calendar: thinned values only."""
    equity = curve["equity"]
    return {
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
        "final_equity": _r(block["final_equity"], 4),
        "exit_counts": dict(block["exit_counts"]),
    }


def strategy_block(strategy: dict) -> dict:
    test = strategy["test"]
    return {
        "tau": strategy["tau"],
        "tau_constraint_met": strategy["tau_constraint_met"],
        "selection_score_mean_sharpe": _r(strategy["selection_score_mean_sharpe"], 3),
        "costs_per_side": strategy["costs_per_side"],
        "validation": {k: _pnl(v) for k, v in sorted(strategy["validation"].items())},
        "test": _pnl(test),
        "equity_curve": thin_curve(test["equity_curve"]),
    }


def asset_report(ticker: str, hpo: dict, metrics: dict, strategy: dict) -> dict:
    validation, test = classification_block(metrics)
    gain = {k: round(v, 1) for k, v in sorted(metrics["gain_importance"].items())}
    assert len(gain) == len(config.FEATURE_COLUMNS), "gain importance misses the feature contract"
    return {
        "ticker": ticker,
        "sample": sample_block(metrics),
        "hpo": hpo_block(hpo),
        "validation": validation,
        "test": test,
        "gain_importance": gain,
        "strategy": strategy_block(strategy),
    }


def main() -> int:
    args = config.ticker_parser("aggregate ML artifacts -> monitoring_module/ml_status.json").parse_args()

    assets = []
    for t in config.parse_tickers(args.tickers):
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
        # the one structural number the page needs to label the final fold
        "test_fold": config.TEST_SPLIT,
        "gate_min_agree": config.AGREE_MIN,
        "assets": assets,
    }
    out = config.MONITORING_DIR / "ml_status.json"
    dataset.write_json(out, payload)

    for a in assets:
        print(f"{a['ticker']:5} skill={a['test']['skill']:+.4f} "
              f"mcc={a['test']['mcc']:.3f} tau={a['strategy']['tau']} "
              f"sharpe={a['strategy']['test']['sharpe']} "
              f"trades={a['strategy']['test']['n_trades']}")
    print(f"wrote {out} ({out.stat().st_size / 1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
