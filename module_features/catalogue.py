"""The feature catalogue on the decision grid: every feature definition evaluated on every timeframe it is offered on,
each value from the last closed bar of its timeframe; one parquet per timeframe, from the research warm-up onward."""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np

from . import config, dataset, indicators

# one kernel per indicator token of the register; the series kernels cover the one series that is not a bar column
SERIES_KERNELS = {"log_volume": lambda bars: np.log1p(bars["volume"])}
INDICATOR_KERNELS = {"ema": indicators.ema, "sma": indicators.sma, "rsi": indicators.rsi, "atr": indicators.atr,
                     "zscore": indicators.rolling_zscore, "range_position": indicators.range_position}


def load_timeframe(con: duckdb.DuckDBPyConnection, timeframe: str) -> dict[str, np.ndarray]:
    return con.execute(
        f"""SELECT timestamp_ms, open, high, low, close, volume
            FROM ohlcv_{timeframe}_canonical ORDER BY timestamp_ms"""
    ).fetchnumpy()


def series_values(bars: dict[str, np.ndarray], series: str) -> np.ndarray:
    return SERIES_KERNELS[series](bars) if series in SERIES_KERNELS else bars[series]


def term_values(bars: dict[str, np.ndarray], term: tuple) -> np.ndarray:
    """A bare series is its column; an indicator runs its kernel on its fixed inputs, else on the term's series."""
    if len(term) == 1:
        return series_values(bars, term[0])
    series, indicator, parameter_bars = ("close",) + term if len(term) == 2 else term
    inputs = [bars[name] for name in config.INDICATOR_FIXED_INPUTS.get(indicator, ())] or [series_values(bars, series)]
    return INDICATOR_KERNELS[indicator](*inputs, parameter_bars)


def ratio(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    """`over`: a ratio, 0 where the denominator is 0."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(denominator == 0.0, 0.0, numerator / denominator)


OPERATOR_KERNELS = {"minus": lambda left, right: left - right, "over": ratio}
NORMALISER_KERNELS = {"centered": lambda value: (value - 50.0) / 50.0}   # a bounded oscillator mapped to [-1, 1]


def feature_definition_values(bars: dict[str, np.ndarray], definition: dict) -> np.ndarray:
    """The definition on one timeframe's own bars: the terms folded left to right by the operators, then normalised."""
    value = term_values(bars, definition["terms"][0])
    for operator, term in zip(definition.get("operators", ()), definition["terms"][1:]):
        value = OPERATOR_KERNELS[operator](value, term_values(bars, term))
    normaliser = definition.get("normaliser")
    return NORMALISER_KERNELS[normaliser](value) if normaliser else value


def timeframe_catalogue(bars: dict[str, np.ndarray], timeframe: str) -> dict[str, np.ndarray]:
    """Every definition offered on the timeframe, by its name, on that timeframe's own bars."""
    return {config.feature_definition_name(definition): feature_definition_values(bars, definition)
            for definition in config.FEATURE_CATALOGUE if timeframe in definition["timeframes"]}


def build_catalogue(con: duckdb.DuckDBPyConnection) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Return (decision_ts, every catalogued column by feature id, config.CATALOGUE_COLUMNS); the stacked matrix is
    built only to assert finiteness across all of them — a term that needs more warm-up than the experiment grants
    stops here."""
    timeframes = {timeframe: load_timeframe(con, timeframe) for timeframe in config.HIERARCHY_TIMEFRAMES}
    catalogue = {timeframe: timeframe_catalogue(timeframes[timeframe], timeframe)
                 for timeframe in config.HIERARCHY_TIMEFRAMES}

    ts_15m = timeframes[config.DECISION_TIMEFRAME]["timestamp_ms"].astype(np.int64)
    decision_ts = ts_15m[ts_15m >= config.WARMUP_END_MS]

    cols: dict[str, np.ndarray] = {}
    for timeframe in config.HIERARCHY_TIMEFRAMES:
        idx = indicators.asof_index(decision_ts,
                                    timeframes[timeframe]["timestamp_ms"].astype(np.int64),
                                    config.TIMEFRAME_DURATION_MS[timeframe])
        for name in config.catalogue_columns(timeframe):
            cols[config.feature_id(name, timeframe)] = catalogue[timeframe][name][idx]

    x = np.column_stack([cols[c] for c in config.CATALOGUE_COLUMNS])
    assert np.isfinite(x).all(), "NaN/inf in the catalogue after the research warm-up"
    return decision_ts, cols


def write_catalogue(ticker: str, decision_ts: np.ndarray, cols: dict[str, np.ndarray]) -> list[Path]:
    """One parquet per timeframe: the columns the catalogue offers on it, on the decision grid. The filename carries
    the timeframe, so the columns do not."""
    written = []
    for timeframe in config.HIERARCHY_TIMEFRAMES:
        names = config.catalogue_columns(timeframe)
        written.append(dataset.write_parquet(
            config.features_parquet(ticker, timeframe),
            {"decision_ts": "BIGINT", **{name: "DOUBLE" for name in names}},
            ([int(decision_ts[i])] + [repr(float(cols[config.feature_id(name, timeframe)][i])) for name in names]
             for i in range(decision_ts.size)),
            order_by="decision_ts",
        ))
    return written


def main() -> int:
    args = config.build_ticker_parser("the feature catalogue on the decision grid per asset").parse_args()
    for ticker in config.parse_tickers(args.tickers):
        con = duckdb.connect(str(config.research_ohlcv_duckdb(ticker)), read_only=True)
        con.execute(f"SET memory_limit='{config.DUCKDB_MEMORY_LIMIT}'")
        con.execute("SET threads=1")   # float summation must not be reordered
        decision_ts, cols = build_catalogue(con)
        con.close()
        written = write_catalogue(ticker, decision_ts, cols)
        print(f"{ticker} {', '.join(w.name for w in written)}: {decision_ts.size} rows x "
              f"{'/'.join(str(len(config.catalogue_columns(t))) for t in config.HIERARCHY_TIMEFRAMES)} columns",
              flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
