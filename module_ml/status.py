"""Report on the ML layer: the global payload and each asset folder.

Observation only, and the single place the reports are assembled. Three
outputs, none of which computes a result of its own:

    module_monitoring/ml_status.json        the dashboard payload, all assets
    <TICKER>_parameters.json                the one parameters file (written by hpo)
    <TICKER>_README.md                      what the folder holds and what came out

The payload blocks follow the experiment flow (sample -> search -> validation
-> final holdout -> attribution -> strategy) and are written with sorted keys,
so reading order lives in the dashboard and in methodology_ml.md, never in key names.
The two per-asset files carry no timestamp: rerunning an unchanged experiment
must reproduce them byte for byte, and the moment of generation is recorded
once, globally, in ml_status.json.
"""

from __future__ import annotations

from datetime import UTC, datetime
from . import config, dataset

EQUITY_CURVE_DOWNSAMPLE_INTERVAL_DAYS = 7          # daily equity grid -> weekly points for the sparkline


def _rounded(x, ndigits):
    """round() that tolerates the nulls to_json_safe() writes for non-finite floats."""
    return None if x is None else round(x, ndigits)


def sample_block(metrics: dict) -> dict:
    labels = metrics["labels"]
    return {
        "rows": labels["rows"],
        "ambiguous": labels["ambiguous"],
        "unobservable": labels["unobservable"],
        "trainable": labels["trainable"],
        "trainable_pct": round(100.0 * labels["trainable"] / labels["rows"], 4),
        "warmup_excluded_decision_count": metrics["segments"]["warmup_excluded_decision_count"],
        "class_counts": dict(metrics["class_counts"]),
    }


def hpo_block(hpo: dict) -> dict:
    return {
        "trial_count": hpo["trial_count"],
        "best_logloss": round(hpo["best_logloss"], 6),
        "best_params": dict(sorted(hpo["best_params"].items())),
    }


def _classification_block(v: dict) -> dict:
    return {
        "prior_logloss": round(v["prior_logloss"], 6),
        "model_logloss": round(v["model_logloss"], 6),
        "relative_logloss_skill": round(v["relative_logloss_skill"], 6),
        "scored_row_count": v["scored_row_count"],
    }


def classification_block(metrics: dict) -> tuple[dict, dict]:
    """(validation per fold, final holdout)."""
    validation = {k: _classification_block(v) for k, v in sorted(metrics["validation"].items())}
    return validation, _classification_block(metrics["final_holdout"])


def thin_curve(curve: dict, final_equity: float) -> dict:
    """The sparkline needs the shape, not the calendar: thinned values only.

    The end of the curve is the measured result, not whatever the thinning
    happened to land on — daily sampling then a stride of seven can stop days
    before the fold does. The settled value is appended when it differs.
    """
    values = [round(v, 4) for v in curve["equity"][::EQUITY_CURVE_DOWNSAMPLE_INTERVAL_DAYS]]
    end = round(final_equity, 4)
    if values[-1] != end:
        values.append(end)
    return {"equity": values, "final_equity": end}


def _pnl_block(block: dict) -> dict:
    return {
        "sharpe": _rounded(block["sharpe"], 3),
        "max_drawdown": _rounded(block["max_drawdown"], 4),
        "trade_count": block["trade_count"],
        "hit_rate": _rounded(block["hit_rate"], 4),
        "average_trade_return": _rounded(block["average_trade_return"], 6),
        "exposure": _rounded(block["exposure"], 4),
        "final_equity": _rounded(block["final_equity"], 4),
        "exit_counts": dict(block["exit_counts"]),
    }


def strategy_block(strategy: dict) -> dict:
    final_holdout = strategy["final_holdout"]
    return {
        "entry_edge_threshold": strategy["entry_edge_threshold"],
        "entry_edge_threshold_constraint_met":
            strategy["entry_edge_threshold_constraint_met"],
        "selection_score_mean_sharpe": _rounded(strategy["selection_score_mean_sharpe"], 3),
        "execution_cost_rate_per_trade_side": strategy["execution_cost_rate_per_trade_side"],
        "validation": {k: _pnl_block(v) for k, v in sorted(strategy["validation"].items())},
        "final_holdout": _pnl_block(final_holdout),
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
        "hyperparameter_search": hpo_block(hpo),
        "validation": validation,
        "final_holdout": final_holdout,
        "gain_importance": gain,
        "strategy": strategy_block(strategy),
    }


# the asset folder manifest, in listing order: (path descriptor, what it holds)
FILE_MANIFEST = (
    (config.canonical_ohlcv_parquet, "the published canonical 1m series"),
    (config.parameters_json, "the one parameters file: a-priori configuration + the Optuna→XGB winner"),
    (lambda ticker: config.features_parquet(ticker, "15m"), "X — the five 15m family columns on the decision grid"),
    (lambda ticker: config.features_parquet(ticker, "1h"), "X — the five 1h family columns on the decision grid"),
    (lambda ticker: config.features_parquet(ticker, "4h"), "X — the five 4h family columns on the decision grid"),
    (config.label_events_parquet, "Y — triple-barrier outcome and the event prices"),
    (config.model_evaluation_json, "classification metrics per fold"),
    (config.oos_predictions_parquet, "out-of-fold class probabilities, full windows"),
    (config.asset_readme_md, "this file"),
    (config.strategy_evaluation_json, "threshold, PnL and the equity curve"),
)


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
    labels, counts = metrics["labels"], metrics["class_counts"]
    supervised = counts["short"] + counts["neutral"] + counts["long"]
    folds = [f"fold_{i}" for i in config.VALIDATION_FOLD_IDS]
    holdout = f"fold_{config.FINAL_HOLDOUT_FOLD_ID}"
    p = hpo["best_params"]

    files = []
    for descriptor, note in FILE_MANIFEST:
        path = descriptor(ticker)
        # this file's own size would be self-referential: writing it changes it
        size = "—" if descriptor is config.asset_readme_md else _size(path)
        files.append([f"`{path.name}`", note, size])

    cls_rows = [[f"F{k.split('_')[1]}", f"{metrics['validation'][k]['prior_logloss']:.6f}",
                 f"{metrics['validation'][k]['model_logloss']:.6f}",
                 f"{100 * metrics['validation'][k]['relative_logloss_skill']:+.2f}%",
                 f"{metrics['validation'][k]['scored_row_count']:,}"]
                for k in folds]
    fh = metrics["final_holdout"]
    cls_rows.append([f"**F{config.FINAL_HOLDOUT_FOLD_ID} — final holdout**",
                     f"{fh['prior_logloss']:.6f}", f"{fh['model_logloss']:.6f}",
                     f"{100 * fh['relative_logloss_skill']:+.2f}%",
                     f"{fh['scored_row_count']:,}"])

    seg = metrics["segments"]
    geo_rows = [[f"F{k.split('_')[1]}", f"{seg[k]['training_row_count']:,}",
                 f"{seg[k]['purged_event_count']:,}", f"{seg[k]['window_row_count']:,}",
                 f"{seg[k]['scored_row_count']:,}"]
                for k in folds + [holdout]]

    def pnl_row(label, block):
        return [label, f"{block['sharpe']:+.3f}", f"{100 * block['max_drawdown']:.1f}%",
                f"{block['trade_count']:,}",
                f"{100 * block['hit_rate']:.1f}%" if block["hit_rate"] is not None else "—",
                f"{100 * block['exposure']:.2f}%", f"{block['final_equity']:.4f}"]

    pnl_rows = [pnl_row(f"F{k.split('_')[1]}", strategy["validation"][k]) for k in folds]
    sh = strategy["final_holdout"]
    pnl_rows.append(pnl_row(f"**F{config.FINAL_HOLDOUT_FOLD_ID} — final holdout**", sh))
    exits = ", ".join(f"{name} {sh['exit_counts'][name]}"
                     for name in config.EVENT_RESOLUTION_NAME.values())
    fallback_note = ("" if strategy["entry_edge_threshold_constraint_met"]
                     else f" — **fallback**, no threshold reaches "
                          f"{config.MINIMUM_TRADES_PER_VALIDATION_FOLD} trades in every validation fold")

    reproduce = " ".join(
        f"python -m module_ml.{stage} --tickers {ticker} &&"
        for stage in ("features", "labels", "hpo", "train", "strategy")
    ) + f" python -m module_ml.status --tickers {ticker}"

    return f"""# {ticker} — research artifacts

Research window {config.RESEARCH_START_UTC} → {config.RESEARCH_END_UTC}, seed {config.SEED}. One directory per ticker, one file per distinct artifact responsibility; `{config.parameters_json(ticker).name}` next to this file is the one parameters file: the a-priori experiment configuration plus the winning point of the Optuna→XGB search, written when the search runs — it is not artifact provenance.

## Files

{_table(["file", "holds", "size"], files)}

Each of the three feature parquets carries {config.LABEL_HORIZON_MS // config.TIMEFRAME_DURATION_MS[config.DECISION_TIMEFRAME]} rows more than `{config.label_events_parquet(ticker).name}`: the tail decisions whose full {config.LABEL_HORIZON_MINUTES}-minute horizon does not fit inside the research window have features but no label. `{config.oos_predictions_parquet(ticker).name}` holds the four out-of-sample prediction windows end to end; the metrics score only the supervised, horizon-fitting subset of each.

## Labels

{labels['rows']:,} decisions, of which **{labels['trainable']:,} supervised** ({100 * labels['trainable'] / labels['rows']:.3f}%) — {labels['ambiguous']:,} events resolve ambiguously and {labels['unobservable']:,} entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short {counts['short']:,}, neutral {counts['neutral']:,}, long {counts['long']:,} ({supervised:,} total).

## Model

Search: {hpo['trial_count']} Optuna trials, best log-loss {hpo['best_logloss']:.6f}. Winner: depth {p['max_depth']}, eta {p['eta']:.4f}, {p['num_boost_round']} rounds, subsample {p['subsample']:.3f}, colsample {p['colsample_bytree']:.3f}, min_child_weight {p['min_child_weight']}, lambda {p['lambda']:.4f}, alpha {p['alpha']:.4f}.

{_table(["fold", "prior log-loss", "model log-loss", "rel. skill", "scored"], cls_rows)}

## Fold geometry

{_table(["fold", "trained on", "purged", "window", "scored"], geo_rows)}

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated. Average-uniqueness weights are measured on each of these populations separately, after the purge.

## Strategy

Entry edge threshold **{strategy['entry_edge_threshold']}**{fallback_note}. Cost {100 * strategy['execution_cost_rate_per_trade_side']:.2f}% per side; the hierarchy gate requires the side to match the 4h trend sign with at least {config.MINIMUM_AGREEING_TREND_TIMEFRAMES} of 3 timeframes agreeing.

{_table(["fold", "Sharpe", "maxDD", "trades", "hit rate", "exposure", "final equity"], pnl_rows)}

Final-holdout exits: {exits}.

## Reproducing the ML artifacts in this folder

    {reproduce}

`{config.canonical_ohlcv_parquet(ticker).name}` is not produced by that chain and not read by it: it is the published per-asset representation of the canonical series (`make export`); the ML stages read the same canonical market object from the DuckDB tables.

F{config.FINAL_HOLDOUT_FOLD_ID} never participates in feature definition, hyper-parameter selection, entry-edge-threshold selection or strategy-rule selection — folds {', '.join('F' + str(i) for i in config.VALIDATION_FOLD_IDS)} carry the data-driven selection of the hyper-parameters and the entry edge threshold. The method is in `module_skills/methodology_ml.md`, the field names in `module_skills/glossary.md`.
"""


def main() -> int:
    args = config.ticker_parser("aggregate ML artifacts -> module_monitoring/ml_status.json").parse_args()

    assets = []
    for t in config.parse_tickers(args.tickers):
        paths = {"parameters": config.parameters_json(t),
                 "model_evaluation": config.model_evaluation_json(t),
                 "strategy_evaluation": config.strategy_evaluation_json(t)}
        if not all(p.exists() for p in paths.values()):
            continue
        loaded = {k: dataset.read_json(p) for k, p in paths.items()}
        hpo = loaded["parameters"]["OPTUNAs_XGB_HPOs_best_params"]
        metrics = loaded["model_evaluation"]
        strategy = loaded["strategy_evaluation"]
        assets.append(asset_report(t, hpo, metrics, strategy))
        config.asset_readme_md(t).write_text(asset_readme(t, hpo, metrics, strategy),
                                             encoding="utf-8")
    assert assets, "no complete artifact set found — run the ML chain first"

    payload = {
        "generated_at_utc": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S"),
        "research_window": {"start_utc": config.RESEARCH_START_UTC,
                            "end_utc": config.RESEARCH_END_UTC},
        "seed": config.SEED,
        # the one structural number the page needs to label the final fold
        "final_holdout_fold_id": config.FINAL_HOLDOUT_FOLD_ID,
        "minimum_agreeing_trend_timeframes": config.MINIMUM_AGREEING_TREND_TIMEFRAMES,
        "assets": assets,
    }
    out = config.MODULE_MONITORING_DIR / "ml_status.json"
    dataset.write_json(out, payload)

    for a in assets:
        print(f"{a['ticker']:5} "
              f"skill={a['final_holdout']['relative_logloss_skill']:+.4f} "
              f"threshold={a['strategy']['entry_edge_threshold']} "
              f"sharpe={a['strategy']['final_holdout']['sharpe']} "
              f"trades={a['strategy']['final_holdout']['trade_count']}")
    print(f"wrote {out} ({out.stat().st_size / 1024:.1f} KB) "
          f"+ <TICKER>_README.md in {len(assets)} asset folders")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
