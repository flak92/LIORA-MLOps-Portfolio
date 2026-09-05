"""The feature layer's report: store_status/features_status.json for the dashboard — the catalogue as the register presents
it (the facts of config.py: the hierarchy, the warm-up, every definition with its terms and histories, the nesting) and,
per asset, the row counts of the catalogue parquets — computing nothing of its own."""

from __future__ import annotations

from datetime import UTC, datetime

import duckdb

from . import config, dataset


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
    """Whether the asset's three parquets exist — the same "no run yet" skip the ML status makes."""
    return all(config.features_parquet(ticker, timeframe).exists() for timeframe in config.HIERARCHY_TIMEFRAMES)


def asset_block(ticker: str) -> dict:
    """One asset's rows: the row count of each catalogue parquet — the one run-state fact this module has per asset,
    published per timeframe because the file names them."""
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{config.DUCKDB_MEMORY_LIMIT}'")
    con.execute("SET threads=1")   # float summation must not be reordered
    counts = {timeframe: con.execute(f"SELECT count(*) FROM read_parquet('{config.features_parquet(ticker, timeframe)}')").fetchone()[0]
              for timeframe in config.HIERARCHY_TIMEFRAMES}
    con.close()
    return {"ticker": ticker, "row_count_by_timeframe": counts}


def main() -> int:
    args = config.build_ticker_parser("the feature layer's snapshot -> store_status/features_status.json").parse_args()
    tickers = config.parse_tickers(args.tickers)
    assets = [asset_block(ticker) for ticker in tickers if has_catalogue(ticker)]
    payload = {
        "generated_at_utc": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S"),
        "catalogue": catalogue_block(),
        "assets": assets,
    }
    out = config.FEATURES_STATUS_JSON_PATH
    dataset.write_json(out, payload)
    print(f"wrote {out}: the catalogue and {len(assets)} asset(s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
