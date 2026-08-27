"""Causal 15m/1h/4h bars from the canonical 1m series.

The ONLY writer of the ML layer: builds ohlcv_{15m,1h,4h}_canonical (market
observation, feeding X) and ohlcv_1h_binance (execution venue, feeding the
label barriers) inside the frozen research window. Every other ML stage opens
the database read-only.

Bars are exact UTC-aligned aggregations (O first, H max, L min, C last, V sum;
arg_min/arg_max by timestamp for determinism) — closed bars only, because the
window ends at a UTC midnight. A one-off diff of one month of aggregated 1h
bars against native fapi klines gave 0 OHLC mismatches (see ML_README).
"""

from __future__ import annotations

import duckdb

from . import config

BAR_DDL = """
CREATE TABLE IF NOT EXISTS ohlcv_{tf}_canonical (
  symbol       VARCHAR NOT NULL,
  timestamp_ms BIGINT  NOT NULL,   -- bar OPEN, UTC epoch ms
  open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, volume DOUBLE,
  n_ffill          INTEGER,        -- forward-filled minutes inside the bar
  zero_volume_bars INTEGER         -- valid no-trade minutes inside the bar
);
"""

BAR_INSERT = """
INSERT INTO ohlcv_{tf}_canonical
SELECT symbol,
       (timestamp_ms // {tf_ms}) * {tf_ms}      AS timestamp_ms,
       arg_min(open,  timestamp_ms)             AS open,
       max(high)                                AS high,
       min(low)                                 AS low,
       arg_max(close, timestamp_ms)             AS close,
       sum(volume)                              AS volume,
       count(*) FILTER (source = 'ffill')       AS n_ffill,
       count(*) FILTER (zero_volume)            AS zero_volume_bars
FROM ohlcv_1m_canonical
WHERE symbol = ? AND timestamp_ms >= {start_ms} AND timestamp_ms < {end_ms}
GROUP BY symbol, (timestamp_ms // {tf_ms})
ORDER BY 2;
"""

# sigma for the labels comes from the execution venue, not from the canonical
# blend: Y and PnL must describe the same instrument.
VENUE_1H_DDL = """
CREATE TABLE IF NOT EXISTS ohlcv_1h_binance (
  symbol       VARCHAR NOT NULL,
  timestamp_ms BIGINT  NOT NULL,
  open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, volume DOUBLE
);
"""

VENUE_1H_INSERT = """
INSERT INTO ohlcv_1h_binance
SELECT symbol,
       (timestamp_ms // 3600000) * 3600000 AS timestamp_ms,
       arg_min(open,  timestamp_ms)        AS open,
       max(high)                           AS high,
       min(low)                            AS low,
       arg_max(close, timestamp_ms)        AS close,
       sum(volume)                         AS volume
FROM ohlcv_1m_binance
WHERE symbol = ? AND timestamp_ms >= {start_ms} AND timestamp_ms < {end_ms}
GROUP BY symbol, (timestamp_ms // 3600000)
ORDER BY 2;
"""

def main() -> int:
    args = config.ticker_parser("canonical 1m -> 15m/1h/4h bars").parse_args()
    tickers = config.parse_tickers(args.tickers)

    con = duckdb.connect(str(config.DB_PATH))
    con.execute("SET memory_limit='4GB'")
    con.execute("SET threads=2")
    for tf, tf_ms in config.TF_MS.items():
        con.execute(BAR_DDL.format(tf=tf))
        for t in tickers:
            sym = config.symbol(t)
            con.execute(f"DELETE FROM ohlcv_{tf}_canonical WHERE symbol = ?", [sym])
            con.execute(
                BAR_INSERT.format(tf=tf, tf_ms=tf_ms,
                                  start_ms=config.RESEARCH_START_MS,
                                  end_ms=config.RESEARCH_END_MS),
                [sym],
            )
            n = con.execute(f"SELECT count(*) FROM ohlcv_{tf}_canonical WHERE symbol = ?", [sym]).fetchone()[0]
            print(f"{tf} {sym}: {n} bars", flush=True)

    con.execute(VENUE_1H_DDL)
    for t in tickers:
        sym = config.symbol(t)
        con.execute("DELETE FROM ohlcv_1h_binance WHERE symbol = ?", [sym])
        con.execute(
            VENUE_1H_INSERT.format(start_ms=config.RESEARCH_START_MS, end_ms=config.RESEARCH_END_MS),
            [sym],
        )
        n = con.execute("SELECT count(*) FROM ohlcv_1h_binance WHERE symbol = ?", [sym]).fetchone()[0]
        print(f"1h binance {sym}: {n} bars", flush=True)

    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
