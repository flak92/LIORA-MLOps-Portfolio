"""The feature layer's report: store/status/features_status.json for the dashboard — the catalogue as the register presents
it (the facts of config.py: the hierarchy, the warm-up, every definition with its terms and histories, the nesting) and,
per asset, the row counts of the catalogue's partitions and the serpentine search as it last wrote itself, beside the
module's CONFIGURABLES records — assembled from the register and from what the stages and the turns wrote, and
computing no metric."""

from datetime import UTC, datetime

import duckdb

from . import config, dataset
from .sub_module_serpentine_search import axis_feature_set, config as serpentine_search_config, serpentine_search


def term_block(term: tuple) -> dict:
    """One term of a catalogue definition: the bars its kernel reads, the indicator with its parameter, the range it
    outputs when that range is bounded — the range a normaliser on this term reads — and the popular names its
    operation answers to, read off the register beside the kernel."""
    if len(term) == 1:
        return {"inputs": [term[0]], "indicator": None, "parameter_word": None, "parameter_bars": None,
                "output_range": None, "historical_aliases": []}
    series, indicator, parameter_bars = ("close",) + term if len(term) == 2 else term
    record = config.INDICATORS[indicator]
    return {"inputs": list(record.get("inputs", (series,))), "indicator": indicator,
            "parameter_word": record["parameter_word"], "parameter_bars": parameter_bars,
            "output_range": list(record["output_range"]) if "output_range" in record else None,
            "historical_aliases": list(record.get("historical_aliases", ()))}


def catalogue_block() -> dict:
    """The catalogue as the register presents it — the facts of this module's config.py."""
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
        "tier": definition["tier"],
        "historical_aliases": list(definition.get("historical_aliases", ())),
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


def has_catalogue(ticker: str) -> bool:
    """Whether the asset's partition of the catalogue family stands on every timeframe — the same "no run yet" skip the ML
    status makes."""
    return all(config.catalogue_parquet(ticker, timeframe).exists() for timeframe in config.HIERARCHY_TIMEFRAMES)


def proposal_block(proposal: dict, state_evaluation: dict, active_columns_by_timeframe: dict,
                   timeframes: tuple[str, ...]) -> dict:
    """One proposal as the page reads it: its rank and state evaluation from the search's progress, and everything
    else from that state evaluation's line of the ledger — the columns it moves against the search state the
    serpentine search was run on, the model's skill, then what the strategy would do: each fold's growth and trades,
    the path's growth, Calmar ratio and profit factor, and the threshold it stood at."""
    columns_by_timeframe = state_evaluation["columns_by_timeframe"]
    return {
        "proposal": proposal["proposal"],
        "state_evaluation_index": proposal["state_evaluation_index"],
        "added_columns_by_timeframe": axis_feature_set.columns_added(columns_by_timeframe, active_columns_by_timeframe, timeframes),
        "removed_columns_by_timeframe": axis_feature_set.columns_removed(columns_by_timeframe, active_columns_by_timeframe, timeframes),
        "mean_relative_logloss_skill": round(state_evaluation["mean_relative_logloss_skill"], 6),
        "validation": {fold: {"cagr": round(block["cagr"], 6), "trade_count": block["trade_count"]}
                       for fold, block in sorted(state_evaluation["validation"].items())},
        "validation_path": {key: config.rounded(state_evaluation["validation_path"][key], 6)
                            for key in ("cagr", "calmar", "profit_factor")},
        "entry_edge_threshold": state_evaluation["entry_edge_threshold"],
    }


def serpentine_search_block(ticker: str) -> dict | None:
    """The serpentine search as it last wrote itself, and whether its inputs are still the asset's — a promotion, a
    retuning, a catalogue change, an edited profile or a changed beam width makes a recorded serpentine search describe
    a search state that has gone; None while the asset has no progress file, and false rather than an error while it
    has no profile. The parameters and the contract are read the way a turn reads them, and a progress file is written
    only by a turn that read both."""
    path = serpentine_search_config.serpentine_search_json(ticker)
    if not path.exists():
        return None
    search = dataset.load_json(path)
    cat = dataset.load_json(config.catalogue_json(ticker))
    profile_path = serpentine_search_config.serpentine_search_profile_json(ticker)
    ledger = serpentine_search_config.serpentine_search_state_evaluations_jsonl(ticker)
    # the state evaluations are the ledger's lines, and a proposal is read off the line its index names
    state_evaluations = dataset.load_jsonl(ledger) if ledger.exists() else []
    inputs_current = profile_path.exists() and search["inputs"] == dataset.to_json_safe(
        serpentine_search.build_search_inputs(serpentine_search.load_best_params(ticker),
                                              serpentine_search.load_feature_columns(ticker, cat),
                                              serpentine_search.load_barrier_coordinates(ticker), cat,
                                              dataset.load_json(profile_path)))
    return {
        "state_evaluation_count": len(state_evaluations),
        "selection_hypothesis_count": search["selection_hypothesis_count"],
        "round_count": search["round_count"],
        "search_converged": search["search_converged"],
        "inputs_current": inputs_current,
        # a serpentine search whose inputs have gone describes another experiment, and its proposals are numbers of
        # that one: the page shows none of them, and the snapshot publishes none either
        "proposals": [proposal_block(proposal, state_evaluations[proposal["state_evaluation_index"] - 1],
                                     search["inputs"]["active_columns_by_timeframe"],
                                     serpentine_search_config.timeframes(cat))
                      for proposal in search["proposals"]] if inputs_current else [],
    }


def asset_block(ticker: str) -> dict:
    """One asset's rows: the row count of each partition of its catalogue — the one run-state fact this module has per
    asset, published per timeframe because the partition names it — and its serpentine search as it last wrote itself."""
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{config.DUCKDB_MEMORY_LIMIT}'")
    con.execute("SET threads=1")   # float summation must not be reordered
    counts = {timeframe: con.execute(f"SELECT count(*) FROM read_parquet('{config.catalogue_parquet(ticker, timeframe)}')").fetchone()[0]
              for timeframe in config.HIERARCHY_TIMEFRAMES}
    con.close()
    return {"ticker": ticker, "row_count_by_timeframe": counts, "serpentine_search": serpentine_search_block(ticker)}


def main() -> int:
    args = config.build_ticker_parser("the feature layer's snapshot -> store/status/features_status.json").parse_args()
    tickers = config.parse_tickers(args.tickers)
    assets = [asset_block(ticker) for ticker in tickers if has_catalogue(ticker)]
    payload = {
        "generated_at_utc": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S"),
        "catalogue": catalogue_block(),
        # the module's local view of what an operator may set — the records as config.py holds them
        "configurables": [*config.CONFIGURABLES, *serpentine_search_config.CONFIGURABLES],
        "assets": assets,
    }
    out = config.FEATURES_STATUS_JSON_PATH
    dataset.write_json(out, payload)
    print(f"wrote {out}: the catalogue and {len(assets)} asset(s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
