"""The ML reports: module_monitoring/ml_status.json for the dashboard, and each asset's byte-reproducible
<TICKER>_README.md — assembled from the three per-asset result files, computing nothing of their own."""

from __future__ import annotations

from datetime import UTC, datetime


from . import config, dataset, feature_set_search

EQUITY_CURVE_DOWNSAMPLE_INTERVAL_DAYS = 7          # daily equity grid -> weekly points for the sparkline


def sample_block(metrics: dict) -> dict:
    labels = metrics["labels"]
    return {
        "decision_count": labels["decision_count"],
        "ambiguous_event_count": labels["ambiguous_event_count"],
        "unobservable_entry_count": labels["unobservable_entry_count"],
        "trainable_row_count": labels["trainable_row_count"],
        "trainable_row_pct": round(100.0 * labels["trainable_row_count"] / labels["decision_count"], 4),
        "warmup_excluded_decision_count": metrics["segments"]["warmup_excluded_decision_count"],
        "class_counts": dict(metrics["class_counts"]),
    }


def hyperparameter_search_result_block(hyperparameter_search_result: dict) -> dict:
    return {
        "trial_count": hyperparameter_search_result["trial_count"],
        "best_logloss": round(hyperparameter_search_result["best_logloss"], 6),
        "best_params": dict(sorted(hyperparameter_search_result["best_params"].items())),
    }


def _classification_block(metrics_block: dict) -> dict:
    return {
        "prior_logloss": round(metrics_block["prior_logloss"], 6),
        "model_logloss": round(metrics_block["model_logloss"], 6),
        "relative_logloss_skill": round(metrics_block["relative_logloss_skill"], 6),
        "scored_row_count": metrics_block["scored_row_count"],
    }


def classification_block(metrics: dict) -> tuple[dict, dict]:
    """(validation per fold, final holdout)."""
    validation = {k: _classification_block(v) for k, v in sorted(metrics["validation"].items())}
    return validation, _classification_block(metrics["final_holdout"])


def equity_curve_block(curve: dict, final_equity: float) -> dict:
    """Weekly-sampled equity for the sparkline; the settled final value is appended when the stride misses it."""
    values = [round(v, 4) for v in curve["equity"][::EQUITY_CURVE_DOWNSAMPLE_INTERVAL_DAYS]]
    end = round(final_equity, 4)
    if values[-1] != end:
        values.append(end)
    return {"equity": values}


def _pnl_block(block: dict) -> dict:
    return {
        "sharpe": round(block["sharpe"], 3),
        "max_drawdown": round(block["max_drawdown"], 4),
        "trade_count": block["trade_count"],
        "hit_rate": config.rounded(block["hit_rate"], 4),
        "average_trade_return": config.rounded(block["average_trade_return"], 6),
        "exposure": round(block["exposure"], 4),
        "final_equity": round(block["final_equity"], 4),
        "exit_counts": dict(block["exit_counts"]),
    }


def strategy_block(strategy: dict) -> dict:
    final_holdout = strategy["final_holdout"]
    return {
        "entry_edge_threshold": strategy["entry_edge_threshold"],
        "entry_edge_threshold_constraint_met":
            strategy["entry_edge_threshold_constraint_met"],
        "selection_score_mean_sharpe": config.rounded(strategy["selection_score_mean_sharpe"], 3),
        "execution_cost_rate_per_trade_side": strategy["execution_cost_rate_per_trade_side"],
        "validation": {k: _pnl_block(v) for k, v in sorted(strategy["validation"].items())},
        "final_holdout": _pnl_block(final_holdout),
        "equity_curve": equity_curve_block(final_holdout["equity_curve"],
                                   final_holdout["final_equity"]),
    }


def term_block(term: tuple) -> dict:
    """One term of a catalogue definition: the bars its kernel reads, the indicator with its parameter, and the range
    it outputs when that range is bounded — the range a normaliser on this term reads."""
    if len(term) == 1:
        return {"inputs": [term[0]], "indicator": None, "parameter_word": None, "parameter_bars": None,
                "output_range": None}
    series, indicator, parameter_bars = ("close",) + term if len(term) == 2 else term
    record = config.INDICATORS[indicator]
    return {"inputs": list(record.get("inputs", (series,))), "indicator": indicator,
            "parameter_word": record["parameter_word"], "parameter_bars": parameter_bars,
            "output_range": list(record["output_range"]) if "output_range" in record else None}


def catalogue_block() -> dict:
    """The catalogue as the register presents it — the facts of module_features/config.py, published here
    because that module measures no run state."""
    timeframes = []
    for lower, timeframe in zip((None,) + config.HIERARCHY_TIMEFRAMES, config.HIERARCHY_TIMEFRAMES):
        duration_ms = config.TIMEFRAME_DURATION_MS[timeframe]
        timeframes.append({
            "timeframe": timeframe, "duration_ms": duration_ms,
            "bars_per_day": config.MILLISECONDS_PER_DAY // duration_ms,
            "ratio_to_lower": None if lower is None else duration_ms // config.TIMEFRAME_DURATION_MS[lower],
            "slot": config.TIMEFRAME_SLOT[timeframe],
        })
    definitions = [{
        "feature_definition": config.feature_definition_name(definition),
        "terms": [term_block(term) for term in definition["terms"]],
        "operators": list(definition.get("operators", ())),
        "normaliser": definition.get("normaliser"),
        "range": definition["range"],
        "timeframes": list(definition["timeframes"]),
        "effective_history_hours_by_timeframe": {timeframe: config.definition_effective_history_hours(definition, timeframe)
                                                 for timeframe in definition["timeframes"]},
        "warmup_bars": config.definition_warmup_bars(definition),
        "definition_in_default_set": definition["definition_in_default_set"],
    } for definition in config.FEATURE_CATALOGUE]
    nesting = [{
        "lower": lower, "upper": upper,
        "lower_longest_effective_history_hours": max(
            config.definition_effective_history_hours(definition, lower)
            for definition in config.FEATURE_CATALOGUE if lower in definition["timeframes"]),
        "upper_shortest_effective_history_hours": min(
            config.definition_effective_history_hours(definition, upper)
            for definition in config.FEATURE_CATALOGUE if upper in definition["timeframes"]),
    } for lower, upper in zip(config.HIERARCHY_TIMEFRAMES, config.HIERARCHY_TIMEFRAMES[1:])]
    warmup_end = datetime.fromtimestamp(config.WARMUP_END_MS / config.MILLISECONDS_PER_SECOND, tz=UTC)
    return {
        "decision_timeframe": config.DECISION_TIMEFRAME,
        "timeframes": timeframes,
        "warmup": {"top_timeframe_bars": config.WARMUP_TOP_TIMEFRAME_BARS, "end_utc": warmup_end.strftime("%Y-%m-%d %H:%M")},
        "definitions": definitions,
        "nesting": nesting,
    }


def proposal_block(proposal: dict) -> dict:
    """One proposal as the page reads it: the model's skill it was chosen on, then what the strategy would do."""
    return {
        "proposal": proposal["proposal"],
        "trial": proposal["trial"],
        "added_columns_by_timeframe": proposal["added_columns_by_timeframe"],
        "removed_columns_by_timeframe": proposal["removed_columns_by_timeframe"],
        "mean_relative_logloss_skill": round(proposal["mean_relative_logloss_skill"], 6),
        "validation": {fold: {"relative_logloss_skill": round(block["relative_logloss_skill"], 6),
                              "sharpe": round(block["sharpe"], 3), "trade_count": block["trade_count"]}
                       for fold, block in sorted(proposal["validation"].items())},
        "entry_edge_threshold": proposal["entry_edge_threshold"],
        "entry_edge_threshold_constraint_met": proposal["entry_edge_threshold_constraint_met"],
        "selection_score_mean_sharpe": config.rounded(proposal["selection_score_mean_sharpe"], 3),
    }


def feature_set_block(ticker: str) -> dict:
    """Where the asset's feature set came from — the promoted file when it exists, else the default set of the
    catalogue — and the columns it holds by timeframe."""
    return {"source": "promoted" if config.feature_set_json(ticker).exists() else "default",
            "columns_by_timeframe": dataset.load_feature_columns(ticker)}


def feature_set_search_block(ticker: str, best_params: dict, active_columns_by_timeframe: dict) -> dict | None:
    """The feature-set search as it last wrote itself, and whether its inputs are still the asset's — a promotion,
    a retuning or a catalogue change makes a recorded search describe a state that has gone; None while the asset
    has no search file."""
    path = config.feature_set_search_json(ticker)
    if not path.exists():
        return None
    search = dataset.load_json(path)
    return {
        "trial_count": len(search["trials"]),
        "pass_count": search["pass_count"],
        "search_converged": search["search_converged"],
        "inputs_current": search["inputs"] == dataset.to_json_safe(
            feature_set_search.build_search_inputs(best_params, active_columns_by_timeframe)),
        "proposals": [proposal_block(proposal) for proposal in search["proposals"]],
    }


def artifacts_block(ticker: str) -> dict:
    """A fact of the folder, not of the experiment: it goes to the payload, never to the timestamp-free README."""
    modified = config.model_evaluation_json(ticker).stat().st_mtime
    return {"model_evaluation_modified_utc": datetime.fromtimestamp(modified, tz=UTC).strftime("%Y-%m-%d %H:%M:%S")}


# the rounding of each importance as the page shows it: gain is a sum of gains, the SHAP value a margin
IMPORTANCE_ROUNDING_DIGITS = {"gain_importance": 1, "mean_abs_shap_importance": 6}


def validation_importance_block(validation_importance: dict) -> dict:
    """The two importances of every validation booster, per column, rounded — the page takes their means."""
    return {fold: {measure: {column: round(value, IMPORTANCE_ROUNDING_DIGITS[measure])
                             for column, value in sorted(block[measure].items())}
                   for measure in IMPORTANCE_ROUNDING_DIGITS}
            for fold, block in sorted(validation_importance.items())}


def asset_report(ticker: str, hyperparameter_search_result: dict, metrics: dict, strategy: dict) -> dict:
    validation, final_holdout = classification_block(metrics)
    feature_set = feature_set_block(ticker)
    return {
        "ticker": ticker,
        "sample": sample_block(metrics),
        "hyperparameter_search_result": hyperparameter_search_result_block(hyperparameter_search_result),
        "validation": validation,
        "final_holdout": final_holdout,
        "feature_columns": list(metrics["feature_columns"]),
        "feature_set": feature_set,
        "validation_importance": validation_importance_block(metrics["validation_importance"]),
        "feature_set_search": feature_set_search_block(ticker, hyperparameter_search_result["best_params"],
                                                       feature_set["columns_by_timeframe"]),
        "strategy": strategy_block(strategy),
        "artifacts": artifacts_block(ticker),
    }


# the asset folder manifest in LC_COLLATE=C listing order: (path descriptor, what it holds)
FILE_MANIFEST = (
    (config.asset_readme_md, "this file"),
    (config.feature_set_json, "the promoted feature set: its columns per timeframe, a hand's choice — absent, the default set is the asset's"),
    (config.feature_set_search_json, "the feature-set search: every trial, the champion, the proposals"),
    # one row per timeframe of the hierarchy: the slot standard sorts them finest first, as LC_COLLATE=C does
    *((lambda ticker, timeframe=timeframe: config.features_parquet(ticker, timeframe),
       f"the catalogue on {timeframe} — every definition offered on it, on the decision grid")
      for timeframe in config.HIERARCHY_TIMEFRAMES),
    (config.label_events_parquet, "Y — triple-barrier outcome and the event prices"),
    (config.model_evaluation_json, "classification metrics per fold"),
    (config.oos_predictions_parquet, "out-of-sample class probabilities, full windows"),
    (config.parameters_json, "the one parameters file: what the search chose"),
    (config.strategy_evaluation_json, "threshold, PnL and the equity curve"),
)


def load_file_size_text(path):
    if not path.exists():
        return "—"
    n = path.stat().st_size
    return f"{n:,} B" if n < config.BYTES_PER_KIBIBYTE else f"{n / config.BYTES_PER_KIBIBYTE:,.0f} KB"


def markdown_table_row(cells):
    return "| " + " | ".join(str(c) for c in cells) + " |"


def markdown_table(headers, rows):
    return "\n".join([markdown_table_row(headers), markdown_table_row(["---"] * len(headers))] + [markdown_table_row(r) for r in rows])


def asset_readme(ticker: str, hyperparameter_search_result: dict, metrics: dict, strategy: dict) -> str:
    """What this folder holds and what came out of it — no timestamp, by design."""
    labels, counts = metrics["labels"], metrics["class_counts"]
    supervised = counts["short"] + counts["neutral"] + counts["long"]
    folds = [f"fold_{i}" for i in config.VALIDATION_FOLD_IDS]
    holdout = f"fold_{config.FINAL_HOLDOUT_FOLD_ID}"
    best_params = hyperparameter_search_result["best_params"]

    files = []
    for descriptor, note in FILE_MANIFEST:
        path = descriptor(ticker)
        # this file's own size would be self-referential: writing it changes it
        size = "—" if descriptor is config.asset_readme_md else load_file_size_text(path)
        files.append([f"`{path.name}`", note, size])

    cls_rows = [[f"F{k.split('_')[1]}", f"{metrics['validation'][k]['prior_logloss']:.6f}",
                 f"{metrics['validation'][k]['model_logloss']:.6f}",
                 f"{100 * metrics['validation'][k]['relative_logloss_skill']:+.2f}%",
                 f"{metrics['validation'][k]['scored_row_count']:,}"]
                for k in folds]
    final_holdout_metrics = metrics["final_holdout"]
    cls_rows.append([f"**F{config.FINAL_HOLDOUT_FOLD_ID} — final holdout**",
                     f"{final_holdout_metrics['prior_logloss']:.6f}", f"{final_holdout_metrics['model_logloss']:.6f}",
                     f"{100 * final_holdout_metrics['relative_logloss_skill']:+.2f}%",
                     f"{final_holdout_metrics['scored_row_count']:,}"])

    segments = metrics["segments"]
    geo_rows = [[f"F{k.split('_')[1]}", f"{segments[k]['training_row_count']:,}",
                 f"{segments[k]['purged_event_count']:,}", f"{segments[k]['window_row_count']:,}",
                 f"{segments[k]['scored_row_count']:,}"]
                for k in folds + [holdout]]

    def pnl_row(label, block):
        return [label, f"{block['sharpe']:+.3f}", f"{100 * block['max_drawdown']:.1f}%",
                f"{block['trade_count']:,}",
                f"{100 * block['hit_rate']:.1f}%" if block["hit_rate"] is not None else "—",
                f"{100 * block['exposure']:.2f}%", f"{block['final_equity']:.4f}"]

    feature_set = feature_set_block(ticker)
    feature_set_rows = [[timeframe, ", ".join(f"`{column}`" for column in feature_set["columns_by_timeframe"][timeframe])
                         or "—"] for timeframe in config.HIERARCHY_TIMEFRAMES]
    feature_set_source = ("The default set of the catalogue — no promoted file" if feature_set["source"] == "default"
                          else f"A promoted set — `{config.feature_set_json(ticker).name}`, a hand's choice; "
                               f"the commit history is the record")
    feature_set_reproduce_note = ("" if feature_set["source"] == "default" else
                                  f"`{config.feature_set_json(ticker).name}` must lie beside this file as well — every fit "
                                  f"reads the promoted set from it; absent, the chain reads the default set and the folder "
                                  f"it rebuilds is another one.\n\n")

    pnl_rows = [pnl_row(f"F{k.split('_')[1]}", strategy["validation"][k]) for k in folds]
    final_holdout_strategy = strategy["final_holdout"]
    pnl_rows.append(pnl_row(f"**F{config.FINAL_HOLDOUT_FOLD_ID} — final holdout**", final_holdout_strategy))
    exits = ", ".join(f"{name} {final_holdout_strategy['exit_counts'][name]}"
                     for name in config.EVENT_RESOLUTION_NAMES.values())
    fallback_note = ("" if strategy["entry_edge_threshold_constraint_met"]
                     else f" — **fallback**, no threshold reaches "
                          f"{config.MINIMUM_TRADES_PER_VALIDATION_FOLD} trades in every validation fold")

    reproduce = " ".join(
        [f"python -m module_features.{stage} --tickers {ticker} &&" for stage in ("bars", "catalogue")]
        + [f"python -m module_ml.{stage} --tickers {ticker} &&" for stage in ("labels", "hpo", "train", "strategy")]
    ) + f" python -m module_ml.status --tickers {ticker}"

    return f"""# {ticker} — research artifacts

Research window {config.RESEARCH_START_UTC} → {config.RESEARCH_END_UTC}, seed {config.SEED}. One directory per ticker, one file per distinct artifact responsibility; `{config.parameters_json(ticker).name}` next to this file is the one parameters file: its `hyperparameter_search_result` section is what the search chose, written when the search runs — the a-priori configuration is `module_ml/config.py` at the commit that ran it, not a copy in the folder.

## Files

{markdown_table(["file", "holds", "size"], files)}

Each of the three catalogue parquets carries {config.LABEL_HORIZON_MS // config.TIMEFRAME_DURATION_MS[config.DECISION_TIMEFRAME]} rows more than `{config.label_events_parquet(ticker).name}`: the tail decisions whose full {config.LABEL_HORIZON_MINUTES}-minute horizon does not fit inside the research window have features but no label. `{config.oos_predictions_parquet(ticker).name}` holds the four out-of-sample prediction windows end to end; the metrics score only the supervised, horizon-fitting subset of each.

## Feature set

{feature_set_source}. The asset's feature set by timeframe — the set every fit reads; the feature id is the column with the timeframe appended:

{markdown_table(["timeframe", "columns"], feature_set_rows)}

## Labels

{labels['decision_count']:,} decisions, of which **{labels['trainable_row_count']:,} supervised** ({100 * labels['trainable_row_count'] / labels['decision_count']:.3f}%) — {labels['ambiguous_event_count']:,} events resolve ambiguously and {labels['unobservable_entry_count']:,} entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short {counts['short']:,}, neutral {counts['neutral']:,}, long {counts['long']:,} ({supervised:,} total).

## Model

Search: {hyperparameter_search_result['trial_count']} Optuna trials, best log-loss {hyperparameter_search_result['best_logloss']:.6f}. Winner: depth {best_params['max_depth']}, eta {best_params['eta']:.4f}, {best_params['num_boost_round']} rounds, subsample {best_params['subsample']:.3f}, colsample {best_params['colsample_bytree']:.3f}, min_child_weight {best_params['min_child_weight']}, lambda {best_params['lambda']:.4f}, alpha {best_params['alpha']:.4f}.

{markdown_table(["fold", "prior log-loss", "model log-loss", "rel. skill", "scored"], cls_rows)}

## Fold geometry

{markdown_table(["fold", "trained on", "purged", "window", "scored"], geo_rows)}

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated. Average-uniqueness weights are measured on each of these populations separately, after the purge.

## Strategy

Entry edge threshold **{strategy['entry_edge_threshold']}**{fallback_note}. Cost {100 * strategy['execution_cost_rate_per_trade_side']:.2f}% per side; the hierarchy gate requires the side to match the 4h trend sign with at least {config.MINIMUM_AGREEING_TREND_TIMEFRAMES} of {len(config.HIERARCHY_TIMEFRAMES)} timeframes agreeing.

{markdown_table(["fold", "Sharpe", "maxDD", "trades", "hit rate", "exposure", "final equity"], pnl_rows)}

Final-holdout exits: {exits}.

## Reproducing the ML artifacts in this folder

    {reproduce}

The OHLCV lives in `{config.research_ohlcv_duckdb(ticker).name}` beside this file — the market object the whole chain reads, resident in the folder and outside the manifest above, because its size moves with every top-up and this file is promised byte-reproducible.

{feature_set_reproduce_note}F{config.FINAL_HOLDOUT_FOLD_ID} never participates in feature definition, hyper-parameter selection, entry-edge-threshold selection or strategy-rule selection — folds {', '.join('F' + str(i) for i in config.VALIDATION_FOLD_IDS)} carry the data-driven selection of the hyper-parameters, the entry edge threshold and, once a set is promoted, the feature set. The method is in `module_ml/skills/methodology_ml.md`, the field names in `module_skills/glossary.md`.
"""


def main() -> int:
    args = config.build_ticker_parser("aggregate ML artifacts -> module_monitoring/ml_status.json").parse_args()
    # the payload folds over the whole basket whatever --tickers says; --tickers scopes the READMEs
    readme_tickers = set(config.parse_tickers(args.tickers))

    assets = []
    for ticker in config.TICKERS:
        if not config.is_artifact_set_complete(ticker):
            continue
        hyperparameter_search_result = dataset.load_json(config.parameters_json(ticker))["hyperparameter_search_result"]
        metrics = dataset.load_json(config.model_evaluation_json(ticker))
        strategy = dataset.load_json(config.strategy_evaluation_json(ticker))
        assets.append(asset_report(ticker, hyperparameter_search_result, metrics, strategy))
        if ticker in readme_tickers:
            config.asset_readme_md(ticker).write_text(asset_readme(ticker, hyperparameter_search_result, metrics, strategy),
                                                 encoding="utf-8")
    if not assets:
        raise SystemExit("no complete artifact set found — run `make ml-all` first")

    payload = {
        "generated_at_utc": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S"),
        "research_window": {"start_utc": config.RESEARCH_START_UTC,
                            "end_utc": config.RESEARCH_END_UTC,
                            "seed": config.SEED},
        # the one structural number the page needs to label the final fold
        "final_holdout_fold_id": config.FINAL_HOLDOUT_FOLD_ID,
        "minimum_agreeing_trend_timeframes": config.MINIMUM_AGREEING_TREND_TIMEFRAMES,
        "trend_gate_feature": config.feature_id(config.TREND_GATE_FEATURE_DEFINITION, config.TREND_GATE_TIMEFRAME),
        # the facts of module_features/config.py, published here because that module measures no run state
        "catalogue": catalogue_block(),
        "assets": assets,
    }
    out = config.MODULE_MONITORING_ML_STATUS_JSON_PATH
    dataset.write_json(out, payload)

    for asset in assets:
        print(f"{asset['ticker']:5} "
              f"skill={asset['final_holdout']['relative_logloss_skill']:+.4f} "
              f"threshold={asset['strategy']['entry_edge_threshold']} "
              f"sharpe={asset['strategy']['final_holdout']['sharpe']} "
              f"trades={asset['strategy']['final_holdout']['trade_count']}")
    print(f"wrote {out} ({out.stat().st_size / config.BYTES_PER_KIBIBYTE:.1f} KB) "
          f"+ <TICKER>_README.md in {len(readme_tickers & {asset['ticker'] for asset in assets})} asset folders")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
