"""Report on the ML layer: the global payload and each asset folder.

Observation only, and the single place the reports are assembled. Three
outputs, none of which computes a result of its own:

    monitoring_module/ml_status.json   the dashboard payload, all assets
    <asset>/calibration.json           the settings that produced this asset
    <asset>/README.md                  what the folder holds and what came out

The payload blocks follow the experiment flow (sample -> search -> validation
-> final holdout -> attribution -> strategy) and are written with sorted keys,
so reading order lives in the dashboard and in ML_README, never in key names.
The two per-asset files carry no timestamp: rerunning an unchanged experiment
must reproduce them byte for byte, and the moment of generation is recorded
once, globally, in ml_status.json.
"""

from __future__ import annotations

from datetime import UTC, datetime
from importlib.metadata import version

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


FILE_NOTES = {
    "canonical_1m.parquet": "the published canonical 1m series",
    "features.parquet": "X — 15 causal columns on the decision grid",
    "label_events.parquet": "Y — triple-barrier outcome and the event prices",
    "oos_predictions.parquet": "out-of-fold class probabilities",
    "hyperparameter_search.json": "the winning point of the search",
    "model_evaluation.json": "classification metrics per fold",
    "strategy_evaluation.json": "threshold, PnL and the equity curve",
    "calibration.json": "the settings all of the above were computed under",
    "README.md": "this file",
}


def _size(path):
    if not path.exists():
        return "—"
    n = path.stat().st_size
    return f"{n:,} B" if n < 1024 else f"{n / 1024:,.0f} KB"


def _row(cells):
    return "| " + " | ".join(str(c) for c in cells) + " |"


def _table(headers, rows):
    return "\n".join([_row(headers), _row(["---"] * len(headers))] + [_row(r) for r in rows])


def asset_readme(ticker: str, hpo: dict, metrics: dict, strategy: dict) -> str:
    """What this folder holds and what came out of it — no timestamp, by design."""
    adir = config.artifact_dir(ticker)
    labels, counts = metrics["labels"], metrics["class_counts"]
    supervised = counts["short"] + counts["neutral"] + counts["long"]
    folds = [f"fold_{i}" for i in config.VALIDATION_FOLD_IDS]
    holdout = f"fold_{config.FINAL_HOLDOUT_FOLD_ID}"
    p = hpo["best_params"]

    files = []
    for name, note in FILE_NOTES.items():
        # this file's own size would be self-referential: writing it changes it
        size = "—" if name == "README.md" else _size(adir / name)
        files.append([f"`{name}`", note, size])

    cls_rows = [[f"F{k.split('_')[1]}", f"{metrics['validation'][k]['prior_logloss']:.6f}",
                 f"{metrics['validation'][k]['model_logloss']:.6f}",
                 f"{100 * metrics['validation'][k]['relative_logloss_skill']:+.2f}%",
                 f"{metrics['validation'][k]['mcc']:.4f}", f"{metrics['validation'][k]['n']:,}"]
                for k in folds]
    fh = metrics["final_holdout"]
    cls_rows.append([f"**F{config.FINAL_HOLDOUT_FOLD_ID} — final holdout**",
                     f"{fh['prior_logloss']:.6f}", f"{fh['model_logloss']:.6f}",
                     f"{100 * fh['relative_logloss_skill']:+.2f}%",
                     f"{fh['mcc']:.4f}", f"{fh['n']:,}"])

    seg = metrics["segments"]
    geo_rows = [[f"F{k.split('_')[1]}", f"{seg[k]['n_train']:,}", f"{seg[k]['n_purged']:,}",
                 f"{seg[k]['n_window']:,}", f"{seg[k]['n_scored']:,}"]
                for k in folds + [holdout]]

    def pnl_row(label, b):
        return [label, f"{b['sharpe']:+.3f}", f"{100 * b['max_drawdown']:.1f}%",
                f"{b['n_trades']:,}", f"{100 * b['hit_rate']:.1f}%",
                f"{100 * b['exposure']:.2f}%", f"{b['final_equity']:.4f}"]

    pnl_rows = [pnl_row(f"F{k.split('_')[1]}", strategy["validation"][k]) for k in folds]
    sh = strategy["final_holdout"]
    pnl_rows.append(pnl_row(f"**F{config.FINAL_HOLDOUT_FOLD_ID} — final holdout**", sh))
    exits = ", ".join(f"{k} {v}" for k, v in sorted(sh["exit_counts"].items()))
    met = ("" if strategy["entry_edge_threshold_constraint_met"]
           else f" — **fallback**, no threshold reaches "
                f"{config.MIN_TRADES_PER_VALIDATION_FOLD} trades in every validation fold")

    reproduce = " ".join(
        f"python -m ml_module.{stage} --tickers {ticker} &&"
        for stage in ("features", "labels", "hpo", "train", "strategy")
    ) + f" python -m ml_module.status --tickers {ticker}"

    return f"""# {ticker} — research artifacts

Research window {config.RESEARCH_START_UTC} → {config.RESEARCH_END_UTC}, seed {config.SEED}. One directory per ticker, one file per stage; `calibration.json` next to this file records the settings every number below was computed under.

## Files

{_table(["file", "holds", "size"], files)}

`features.parquet` carries {config.HORIZON_BARS} rows more than `label_events.parquet`: the tail decisions whose full {config.HORIZON_MS // 60_000}-minute horizon does not fit inside the research window have features but no label. `oos_predictions.parquet` holds the four scored windows end to end.

## Labels

{labels['rows']:,} decisions, of which **{labels['trainable']:,} supervised** ({100 * labels['trainable'] / labels['rows']:.3f}%) — {labels['ambiguous']:,} events resolve ambiguously and {labels['unobservable']:,} entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short {counts['short']:,}, neutral {counts['neutral']:,}, long {counts['long']:,} ({supervised:,} total). Mean uniqueness weight {metrics['uniqueness_weight_mean']:.4f}.

## Model

Search: {hpo['n_trials']} Optuna trials, best objective {hpo['best_value']:.6f}. Winner: depth {p['max_depth']}, eta {p['eta']:.4f}, {p['num_boost_round']} rounds, subsample {p['subsample']:.3f}, colsample {p['colsample_bytree']:.3f}, min_child_weight {p['min_child_weight']}, lambda {p['lambda']:.4f}, alpha {p['alpha']:.4f}.

{_table(["fold", "prior log-loss", "model log-loss", "rel. skill", "MCC", "scored"], cls_rows)}

## Fold geometry

{_table(["fold", "trained on", "purged", "window", "scored"], geo_rows)}

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated.

## Strategy

Entry edge threshold **{strategy['entry_edge_threshold']}**{met}. Cost {100 * strategy['costs_per_side']:.2f}% per side; the hierarchy gate requires the side to match the 4h trend sign with at least {config.AGREE_MIN} of 3 levels agreeing.

{_table(["fold", "Sharpe", "maxDD", "trades", "hit rate", "exposure", "final equity"], pnl_rows)}

Final-holdout exits: {exits}.

## Reproducing this folder

    {reproduce}

F{config.FINAL_HOLDOUT_FOLD_ID} never participates in feature definition, hyper-parameter selection, threshold selection or strategy-rule selection — folds {', '.join('F' + str(i) for i in config.VALIDATION_FOLD_IDS)} carry every research decision. The method is in `Skills_For_The_Project/ML_README.md`, the field names in `Skills_For_The_Project/glossary.md`.
"""


PINNED = ("duckdb", "numpy", "optuna", "xgboost-cpu")


def calibration(ticker: str, hpo: dict, strategy: dict) -> dict:
    """Every setting that took part in producing this asset's artifacts.

    Not a provenance envelope: it proves nothing and gates nothing. It answers
    the one question the folder cannot otherwise answer — under which settings
    were these numbers computed — so the artifacts can be reproduced without
    reading the source.
    """
    booster = {k: v for k, v in hpo["best_params"].items() if k != "num_boost_round"}
    booster.update(config.XGB_FIXED)          # fixed wins on collision, as in model.fit
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
            "levels": list(config.LEVELS),
            "decision_timeframe": config.DECISION_TF,
            "families": list(config.FAMILIES),
            "columns": list(config.FEATURE_COLUMNS),
            "ema_fast": config.EMA_FAST, "ema_slow": config.EMA_SLOW,
            "atr_n": config.ATR_N, "rsi_n": config.RSI_N,
            "range_position_n": config.STRUCTURE_N, "volume_zscore_n": config.ACTIVITY_N,
        },
        "labels": {
            "k_barrier": config.K_BARRIER,
            "horizon_bars": config.HORIZON_BARS,
            "horizon_minutes": config.HORIZON_MS // 60_000,
            "sigma": "ATR14 of the last closed canonical 1h bar",
            "touch_requires": "volume > 0",
            "event_resolution_codes": {
                "lower_barrier": config.EVENT_RESOLUTION_LOWER_BARRIER,
                "vertical": config.EVENT_RESOLUTION_VERTICAL,
                "upper_barrier": config.EVENT_RESOLUTION_UPPER_BARRIER,
                "ambiguous": config.EVENT_RESOLUTION_AMBIGUOUS,
            },
            "supervised_population": "sample_valid = entry_observable & label_valid",
        },
        "hyperparameter_search": {
            "sampler": "optuna.samplers.TPESampler",
            "sampler_seed": config.SEED,
            "n_trials": config.N_TRIALS,
            "parallelism": "sequential (n_jobs=1) — TPE is reproducible only in order",
            "objective": "mean uniqueness-weighted multiclass log-loss over folds "
                         + ", ".join(f"F{i}" for i in config.VALIDATION_FOLD_IDS),
            "space": {k: list(v) for k, v in config.HPO_SPACE.items()},
            "xgb_fixed": dict(config.XGB_FIXED),
            "best_params": dict(sorted(hpo["best_params"].items())),
            "best_value": hpo["best_value"],
        },
        # what actually trained: model.fit pops num_boost_round and lets the
        # fixed parameters overwrite the searched ones, so neither dict alone
        # describes the booster
        "effective_booster_params": dict(sorted(booster.items())),
        "num_boost_round": hpo["best_params"]["num_boost_round"],
        "strategy": {
            "cost_per_side": config.COST_PER_SIDE,
            "entry_edge_threshold_grid": {
                "min": config.ENTRY_EDGE_THRESHOLD_GRID[0],
                "max": config.ENTRY_EDGE_THRESHOLD_GRID[-1],
                "step": round(config.ENTRY_EDGE_THRESHOLD_GRID[1]
                              - config.ENTRY_EDGE_THRESHOLD_GRID[0], 4),
                "n": len(config.ENTRY_EDGE_THRESHOLD_GRID),
            },
            "min_trades_per_validation_fold": config.MIN_TRADES_PER_VALIDATION_FOLD,
            "hierarchy_min_agree": config.AGREE_MIN,
            "bars_per_year_15m": config.BARS_PER_YEAR_15M,
            "selected_entry_edge_threshold": strategy["entry_edge_threshold"],
            "constraint_met": strategy["entry_edge_threshold_constraint_met"],
        },
        "runtime": {
            "libraries": {name: version(name) for name in PINNED},
            "thread_caps": {"xgboost_nthread": config.XGB_FIXED["nthread"],
                            "omp_num_threads": 1},
        },
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
        hpo = loaded["hyperparameter_search"]
        metrics = loaded["model_evaluation"]
        strategy = loaded["strategy_evaluation"]
        assets.append(asset_report(t, hpo, metrics, strategy))
        dataset.write_json(adir / "calibration.json", calibration(t, hpo, strategy))
        (adir / "README.md").write_text(asset_readme(t, hpo, metrics, strategy),
                                        encoding="utf-8")
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
    print(f"wrote {out} ({out.stat().st_size / 1024:.1f} KB) "
          f"+ calibration.json and README.md in {len(assets)} asset folders")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
