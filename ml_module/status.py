"""Aggregate the per-asset artifacts into monitoring_module/ml_status.json.

Observation only, and the single place where the dashboard payload is
assembled: the blocks below follow the experiment flow (sample -> search ->
validation -> final holdout -> attribution -> strategy). The file is
written with sorted keys, so reading order lives in the dashboard and in
ML_README, never in key names. The experiment is described once, globally, by
its research window and seed — library versions are in requirements.lock and
model parameters in hpo_<T>.json.
"""

from __future__ import annotations

from datetime import UTC, datetime

from . import config, dataset

ARTIFACT_KINDS = ("hyperparameter_search", "model_evaluation", "strategy_evaluation")
EQUITY_STRIDE = 7          # daily equity grid -> weekly points for the sparkline


def _r(x, n):
    """round() that tolerates the nulls to_json_safe() writes for non-finite floats."""
    return None if x is None else round(x, n)


def sample_block(metrics: dict) -> dict:
    labels = metrics["labels"]
    return {
        "rows": labels["rows"],
        "ambiguous": labels["ambiguous"],
        "unobservable": labels["unobservable"],
        "trainable": labels["trainable"],
        "trainable_pct": round(100.0 * labels["trainable"] / labels["rows"], 4),
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
        "relative_logloss_skill": round(v["relative_logloss_skill"], 6),
        "mcc": round(v["mcc"], 4),
        "n": v["n"],
    }


def classification_block(metrics: dict) -> tuple[dict, dict]:
    """(validation per fold, final holdout)."""
    validation = {k: _cls(v) for k, v in sorted(metrics["validation"].items())}
    return validation, _cls(metrics["final_holdout"])


def thin_curve(curve: dict, final_equity: float, stride: int = EQUITY_STRIDE) -> dict:
    """The sparkline needs the shape, not the calendar: thinned values only.

    The end of the curve is the measured result, not whatever the thinning
    happened to land on — daily sampling then a stride of seven can stop days
    before the fold does. The settled value is appended when it differs.
    """
    values = [round(v, 4) for v in curve["equity"][::stride]]
    end = round(final_equity, 4)
    if values[-1] != end:
        values.append(end)
    return {"equity": values, "equity_final": end}


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
    final_holdout = strategy["final_holdout"]
    return {
        "entry_edge_threshold": strategy["entry_edge_threshold"],
        "entry_edge_threshold_constraint_met":
            strategy["entry_edge_threshold_constraint_met"],
        "selection_score_mean_sharpe": _r(strategy["selection_score_mean_sharpe"], 3),
        "costs_per_side": strategy["costs_per_side"],
        "validation": {k: _pnl(v) for k, v in sorted(strategy["validation"].items())},
        "final_holdout": _pnl(final_holdout),
        "equity_curve": thin_curve(final_holdout["equity_curve"],
                                   final_holdout["final_equity"]),
    }


def asset_report(ticker: str, hpo: dict, metrics: dict, strategy: dict) -> dict:
    validation, final_holdout = classification_block(metrics)
    gain = {k: round(v, 1) for k, v in sorted(metrics["gain_importance"].items())}
    assert len(gain) == len(config.FEATURE_COLUMNS), "gain importance misses the feature contract"
    return {
        "ticker": ticker,
        "sample": sample_block(metrics),
        "hpo": hpo_block(hpo),
        "validation": validation,
        "final_holdout": final_holdout,
        "gain_importance": gain,
        "strategy": strategy_block(strategy),
    }


def main() -> int:
    args = config.ticker_parser("aggregate ML artifacts -> monitoring_module/ml_status.json").parse_args()

    assets = []
    for t in config.parse_tickers(args.tickers):
        adir = config.artifact_dir(t)
        paths = {k: adir / f"{k}.json" for k in ARTIFACT_KINDS}
        if not all(p.exists() for p in paths.values()):
            continue
        loaded = {k: dataset.read_json(p) for k, p in paths.items()}
        assets.append(asset_report(t, loaded["hyperparameter_search"],
                                   loaded["model_evaluation"],
                                   loaded["strategy_evaluation"]))
    assert assets, "no complete artifact set found — run the ML chain first"

    payload = {
        "generated_at_utc": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S"),
        "research_window": [config.RESEARCH_START_UTC, config.RESEARCH_END_UTC],
        "seed": config.SEED,
        # the one structural number the page needs to label the final fold
        "final_holdout_fold_id": config.FINAL_HOLDOUT_FOLD_ID,
        "gate_min_agree": config.AGREE_MIN,
        "assets": assets,
    }
    out = config.MONITORING_DIR / "ml_status.json"
    dataset.write_json(out, payload)

    for a in assets:
        print(f"{a['ticker']:5} "
              f"skill={a['final_holdout']['relative_logloss_skill']:+.4f} "
              f"mcc={a['final_holdout']['mcc']:.3f} "
              f"threshold={a['strategy']['entry_edge_threshold']} "
              f"sharpe={a['strategy']['final_holdout']['sharpe']} "
              f"trades={a['strategy']['final_holdout']['n_trades']}")
    print(f"wrote {out} ({out.stat().st_size / 1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
