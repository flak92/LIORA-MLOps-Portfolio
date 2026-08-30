"""Exact UTC-aligned 15m/1h/4h aggregations of the canonical 1m series inside the research window, in each asset's
own database — the one writer of the ML layer; every other ML stage opens the database read-only."""

from __future__ import annotations

import duckdb

from . import config

BAR_DDL = """
CREATE TABLE IF NOT EXISTS ohlcv_{timeframe}_canonical (
  symbol       VARCHAR NOT NULL,
  timestamp_ms BIGINT  NOT NULL,   -- bar OPEN, UTC epoch ms
  open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, volume DOUBLE,
  ffill_bars          INTEGER,        -- forward-filled minutes inside the bar
  zero_volume_bars INTEGER         -- valid no-trade minutes inside the bar
);
"""

BAR_INSERT = """
INSERT INTO ohlcv_{timeframe}_canonical
SELECT symbol,
       (timestamp_ms // {timeframe_duration_ms}) * {timeframe_duration_ms}      AS timestamp_ms,
       arg_min(open,  timestamp_ms)             AS open,
       max(high)                                AS high,
       min(low)                                 AS low,
       arg_max(close, timestamp_ms)             AS close,
       sum(volume)                              AS volume,
       count(*) FILTER (source = 'ffill')       AS ffill_bars,
       count(*) FILTER (zero_volume)            AS zero_volume_bars
FROM ohlcv_1m_canonical
WHERE symbol = ? AND timestamp_ms >= {start_ms} AND timestamp_ms < {end_ms}
GROUP BY symbol, (timestamp_ms // {timeframe_duration_ms})
ORDER BY 2;
"""


def main() -> int:
    args = config.build_ticker_parser("canonical 1m -> 15m/1h/4h bars").parse_args()
    tickers = config.parse_tickers(args.tickers)

    for ticker in tickers:
        symbol = config.symbol(ticker)
        con = duckdb.connect(str(config.research_ohlcv_duckdb(ticker)))
        con.execute(f"SET memory_limit='{config.DUCKDB_MEMORY_LIMIT}'")
        con.execute("SET threads=1")   # float summation must not be reordered
        for timeframe, timeframe_duration_ms in config.TIMEFRAME_DURATION_MS.items():
            con.execute(BAR_DDL.format(timeframe=timeframe))
            con.execute(f"DELETE FROM ohlcv_{timeframe}_canonical WHERE symbol = ?", [symbol])
            con.execute(
                BAR_INSERT.format(timeframe=timeframe, timeframe_duration_ms=timeframe_duration_ms,
                                  start_ms=config.RESEARCH_START_MS,
                                  end_ms=config.RESEARCH_END_MS),
                [symbol],
            )
            bar_count = con.execute(f"SELECT count(*) FROM ohlcv_{timeframe}_canonical "
                                    "WHERE symbol = ?", [symbol]).fetchone()[0]
            print(f"{timeframe} {symbol}: {bar_count} bars", flush=True)
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
