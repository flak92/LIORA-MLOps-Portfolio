"""Exact UTC-aligned aggregations of the canonical 1m series on every timeframe of the register, inside the research
window, in each asset's own database — the one writer of the feature layer; every stage downstream opens the database
read-only."""

from __future__ import annotations

import duckdb

from . import config

BAR_DDL = """
CREATE TABLE IF NOT EXISTS ohlcv_{timeframe}_canonical (
  timestamp_ms BIGINT  NOT NULL,   -- bar OPEN, UTC epoch ms
  open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, volume DOUBLE,
  ffill_bars          INTEGER,        -- forward-filled minutes inside the bar
  zero_volume_bars INTEGER         -- valid no-trade minutes inside the bar
);
"""

BAR_INSERT = """
INSERT INTO ohlcv_{timeframe}_canonical
SELECT (timestamp_ms // {timeframe_duration_ms}) * {timeframe_duration_ms} AS timestamp_ms,
       arg_min(open,  timestamp_ms)             AS open,
       max(high)                                AS high,
       min(low)                                 AS low,
       arg_max(close, timestamp_ms)             AS close,
       sum(volume)                              AS volume,
       count(*) FILTER (source = 'ffill')       AS ffill_bars,
       count(*) FILTER (zero_volume)            AS zero_volume_bars
FROM ohlcv_1m_canonical
WHERE timestamp_ms >= {start_ms} AND timestamp_ms < {end_ms}
GROUP BY (timestamp_ms // {timeframe_duration_ms})
ORDER BY 1;
"""


def main() -> int:
    args = config.build_ticker_parser("canonical 1m -> every timeframe of the register").parse_args()
    tickers = config.parse_tickers(args.tickers)

    for ticker in tickers:
        con = duckdb.connect(str(config.research_ohlcv_duckdb(ticker)))
        con.execute(f"SET memory_limit='{config.DUCKDB_MEMORY_LIMIT}'")
        con.execute("SET threads=1")   # float summation must not be reordered
        for timeframe, timeframe_duration_ms in config.TIMEFRAME_DURATION_MS.items():
            con.execute(BAR_DDL.format(timeframe=timeframe))
            con.execute(f"DELETE FROM ohlcv_{timeframe}_canonical")
            con.execute(
                BAR_INSERT.format(timeframe=timeframe, timeframe_duration_ms=timeframe_duration_ms,
                                  start_ms=config.RESEARCH_START_MS,
                                  end_ms=config.RESEARCH_END_MS)
            )
            bar_count = con.execute(f"SELECT count(*) FROM ohlcv_{timeframe}_canonical").fetchone()[0]
            print(f"{timeframe} {ticker}: {bar_count} bars", flush=True)
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
