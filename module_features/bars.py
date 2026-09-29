"""Exact UTC-aligned aggregations of the canonical 1m series on every timeframe of the register, inside the research
window — the family `bars`, one partition per asset and timeframe, its `schema.json` beside them; the one write of the
feature layer beside the catalogue, DuckDB the engine in memory and the canonical family read as a file."""

from __future__ import annotations

import duckdb

from . import config, dataset

# one partition of the bars family — bar OPEN in UTC epoch ms, OHLCV, the forward-filled minutes and the valid no-trade
# minutes inside the bar — one Parquet file, zstd, in grid order
BAR_COPY = """
COPY (
SELECT (timestamp_ms // {timeframe_duration_ms}) * {timeframe_duration_ms} AS timestamp_ms,
       arg_min(open,  timestamp_ms)             AS open,
       max(high)                                AS high,
       min(low)                                 AS low,
       arg_max(close, timestamp_ms)             AS close,
       sum(volume)                              AS volume,
       CAST(count(*) FILTER (source = 'ffill') AS INTEGER) AS ffill_bars,
       CAST(count(*) FILTER (zero_volume) AS INTEGER)      AS zero_volume_bars
FROM read_parquet('{canonical_parquet}')
WHERE timestamp_ms >= {start_ms} AND timestamp_ms < {end_ms}
GROUP BY (timestamp_ms // {timeframe_duration_ms})
ORDER BY 1
) TO '{path}' (FORMAT PARQUET, COMPRESSION zstd)
"""


def main() -> int:
    args = config.build_ticker_parser("canonical 1m -> the bars family, one partition per timeframe of the register").parse_args()
    tickers = config.parse_tickers(args.tickers)

    for ticker in tickers:
        con = duckdb.connect()
        con.execute(f"SET memory_limit='{config.DUCKDB_MEMORY_LIMIT}'")
        con.execute("SET threads=1")   # float summation must not be reordered
        for timeframe, timeframe_duration_ms in config.TIMEFRAME_DURATION_MS.items():
            path = config.bars_parquet(ticker, timeframe)
            path.parent.mkdir(parents=True, exist_ok=True)
            con.execute(
                BAR_COPY.format(timeframe_duration_ms=timeframe_duration_ms,
                                canonical_parquet=config.ohlcv_1m_canonical_parquet(ticker),
                                start_ms=config.RESEARCH_START_MS, end_ms=config.RESEARCH_END_MS, path=path)
            )
            # every partition of the family carries the same columns, so every timeframe writes the same bytes
            dataset.write_json(config.schema_json("bars"), dataset.load_partition_schema(con, path))
            bar_count = con.execute(f"SELECT count(*) FROM read_parquet('{path}')").fetchone()[0]
            print(f"{timeframe} {ticker}: {bar_count} bars", flush=True)
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
