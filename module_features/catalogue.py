"""The feature catalogue on the decision grid: every feature definition evaluated on every timeframe it is offered on,
each value from the last closed bar of its timeframe; the family `catalogue`, one partition per asset and timeframe, from
the research warm-up onward, and the asset's copy of the contract the ML layer reads."""

from pathlib import Path

import duckdb
import numpy as np

from . import config, dataset, indicators

def load_timeframe(con: duckdb.DuckDBPyConnection, ticker: str, timeframe: str) -> dict[str, np.ndarray]:
    """The asset's bars of one timeframe, as the bars stage wrote them, in grid order."""
    return con.execute(
        f"""SELECT timestamp_ms, open, high, low, close, volume
            FROM read_parquet('{config.bars_parquet(ticker, timeframe)}') ORDER BY timestamp_ms"""
    ).fetchnumpy()


def series_values(bars: dict[str, np.ndarray], series: str) -> np.ndarray:
    """A series of the register runs its kernel over the bars; any other series is a bar column."""
    record = indicators.SERIES_KERNELS.get(series)
    return record["kernel"](bars) if record else bars[series]


def term_values(bars: dict[str, np.ndarray], term: tuple) -> np.ndarray:
    """A bare series is its column; an indicator runs its kernel on its fixed inputs, else on the term's series."""
    if len(term) == 1:
        return series_values(bars, term[0])
    series, indicator, parameter_bars = ("close",) + term if len(term) == 2 else term
    record = indicators.INDICATORS[indicator]
    inputs = [bars[name] for name in record.get("inputs", ())] or [series_values(bars, series)]
    return record["kernel"](*inputs, parameter_bars)


def difference(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """`minus`: the left term less the right."""
    return left - right


def ratio(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    """`over`: a ratio, 0 where the denominator is 0."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(denominator == 0.0, 0.0, numerator / denominator)


def centered(value: np.ndarray, low: float, high: float) -> np.ndarray:
    """`centered`: a bounded term mapped to [-1, 1] from the output range of its own indicator."""
    return (value - (low + high) / 2) / ((high - low) / 2)


# the two registers of the composition grammar, each beside its kernels, in the shape of INDICATORS
OPERATORS = {"minus": {"kernel": difference}, "over": {"kernel": ratio}}
NORMALISERS = {"centered": {"kernel": centered}}


def feature_definition_values(bars: dict[str, np.ndarray], definition: dict) -> np.ndarray:
    """The definition on one timeframe's own bars: the terms folded left to right by the operators, then normalised
    over the output range of the one bounded indicator the normalised definition is written on."""
    value = term_values(bars, definition["terms"][0])
    for operator, term in zip(definition.get("operators", ()), definition["terms"][1:]):
        value = OPERATORS[operator]["kernel"](value, term_values(bars, term))
    normaliser = definition.get("normaliser")
    if not normaliser:
        return value
    low, high = indicators.INDICATORS[config.term_indicator(definition["terms"][0])]["output_range"]
    return NORMALISERS[normaliser]["kernel"](value, low, high)


def timeframe_catalogue(bars: dict[str, np.ndarray], timeframe: str) -> dict[str, np.ndarray]:
    """Every definition offered on the timeframe, by its name, on that timeframe's own bars."""
    return {config.feature_definition_name(definition): feature_definition_values(bars, definition)
            for definition in config.FEATURE_CATALOGUE if timeframe in definition["timeframes"]}


def build_catalogue(con: duckdb.DuckDBPyConnection, ticker: str) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Return (decision_ts, every catalogued column by feature id); the stacked matrix is built only to assert
    finiteness across all of them — a term that needs more warm-up than the experiment grants stops here."""
    bars_by_timeframe = {timeframe: load_timeframe(con, ticker, timeframe) for timeframe in config.HIERARCHY_TIMEFRAMES}
    catalogue = {timeframe: timeframe_catalogue(bars_by_timeframe[timeframe], timeframe)
                 for timeframe in config.HIERARCHY_TIMEFRAMES}

    grid_decision_ts = bars_by_timeframe[config.DECISION_TIMEFRAME]["timestamp_ms"].astype(np.int64)
    decision_ts = grid_decision_ts[grid_decision_ts >= config.WARMUP_END_MS]

    catalogue_values: dict[str, np.ndarray] = {}
    for timeframe in config.HIERARCHY_TIMEFRAMES:
        closed_bar_rows = indicators.asof_index(decision_ts,
                                                bars_by_timeframe[timeframe]["timestamp_ms"].astype(np.int64),
                                                config.TIMEFRAME_DURATION_MS[timeframe])
        for name in config.catalogue_columns(timeframe):
            catalogue_values[config.feature_id(name, timeframe)] = catalogue[timeframe][name][closed_bar_rows]

    catalogue_matrix = np.column_stack([catalogue_values[c] for c in config.CATALOGUE_COLUMNS])
    assert np.isfinite(catalogue_matrix).all(), "NaN/inf in the catalogue after the research warm-up"
    return decision_ts, catalogue_values


def write_catalogue(ticker: str, decision_ts: np.ndarray, catalogue_values: dict[str, np.ndarray]) -> list[Path]:
    """One partition of the catalogue family per timeframe — the columns the catalogue offers on it, on the decision
    grid; the partition carries the timeframe, so the columns do not — the family's schema from the register, the same
    bytes from every asset, and the asset's copy of the contract the ML layer reads."""
    written = []
    for timeframe in config.HIERARCHY_TIMEFRAMES:
        names = config.catalogue_columns(timeframe)
        written.append(dataset.write_parquet(
            config.catalogue_parquet(ticker, timeframe),
            {"decision_ts": "BIGINT", **{name: "DOUBLE" for name in names}},
            ([int(decision_ts[i])] + [repr(float(catalogue_values[config.feature_id(name, timeframe)][i]))
                                      for name in names]
             for i in range(decision_ts.size)),
            order_by="decision_ts",
        ))
    dataset.write_json(config.schema_json("catalogue"), config.catalogue_schema())
    contract = config.catalogue_json(ticker)
    dataset.write_json(contract, config.catalogue_contract(ticker))
    written.append(contract)
    return written


def main() -> int:
    args = config.build_ticker_parser("the feature catalogue on the decision grid per asset").parse_args()
    for ticker in config.parse_tickers(args.tickers):
        con = duckdb.connect()
        con.execute(f"SET memory_limit='{config.DUCKDB_MEMORY_LIMIT}'")
        con.execute("SET threads=1")   # float summation must not be reordered
        decision_ts, catalogue_values = build_catalogue(con, ticker)
        con.close()
        *parquets, contract = write_catalogue(ticker, decision_ts, catalogue_values)
        print(f"{ticker} {', '.join(w.parent.name for w in parquets)}: {decision_ts.size} rows x "
              f"{'/'.join(str(len(config.catalogue_columns(t))) for t in config.HIERARCHY_TIMEFRAMES)} columns, + {contract.name}",
              flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
