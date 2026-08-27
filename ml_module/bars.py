"""Causal 15m/1h/4h bars from the canonical 1m series.

The ONLY writer of the ML layer: builds ohlcv_{15m,1h,4h}_canonical inside the
frozen research window. Every other ML stage opens the database read-only.
No source-specific table lives here: from the canonical database onwards the
research layer knows one market object, not the sources that built it.

Bars are exact UTC-aligned aggregations (O first, H max, L min, C last, V sum;
arg_min/arg_max by timestamp for determinism) — closed bars only, because the
window ends at a UTC midnight. That these aggregations reproduce a provider's
own higher timeframes exactly is a property of the data layer, verified once
and recorded in DATA_README.
"""

from __future__ import annotations

import duckdb

from . import config

BAR_DDL = """
CREATE TABLE IF NOT EXISTS ohlcv_{timeframe}_canonical (
  symbol       VARCHAR NOT NULL,
  timestamp_ms BIGINT  NOT NULL,   -- bar OPEN, UTC epoch ms
  open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, volume DOUBLE,
  n_ffill          INTEGER,        -- forward-filled minutes inside the bar
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
       count(*) FILTER (source = 'ffill')       AS n_ffill,
       count(*) FILTER (zero_volume)            AS zero_volume_bars
FROM ohlcv_1m_canonical
WHERE symbol = ? AND timestamp_ms >= {start_ms} AND timestamp_ms < {end_ms}
GROUP BY symbol, (timestamp_ms // {timeframe_duration_ms})
ORDER BY 2;
"""


def main() -> int:
    args = config.ticker_parser("canonical 1m -> 15m/1h/4h bars").parse_args()
    tickers = config.parse_tickers(args.tickers)

    con = duckdb.connect(str(config.DB_PATH))
    con.execute("SET memory_limit='4GB'")
    con.execute("SET threads=1")   # float summation must not be reordered
    for timeframe, timeframe_duration_ms in config.TIMEFRAME_DURATION_MS.items():
        con.execute(BAR_DDL.format(timeframe=timeframe))
        for t in tickers:
            sym = config.symbol(t)
            con.execute(f"DELETE FROM ohlcv_{timeframe}_canonical WHERE symbol = ?", [sym])
            con.execute(
                BAR_INSERT.format(timeframe=timeframe, timeframe_duration_ms=timeframe_duration_ms,
                                  start_ms=config.RESEARCH_START_MS,
                                  end_ms=config.RESEARCH_END_MS),
                [sym],
            )
            n = con.execute(f"SELECT count(*) FROM ohlcv_{timeframe}_canonical "
                            "WHERE symbol = ?", [sym]).fetchone()[0]
            print(f"{timeframe} {sym}: {n} bars", flush=True)

    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
