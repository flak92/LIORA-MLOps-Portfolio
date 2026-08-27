"""Causal 15m/1h/4h bars from the canonical 1m series.

The ONLY writer of the ML layer: builds ohlcv_{15m,1h,4h}_canonical (market
observation, feeding X) and ohlcv_1h_binance (execution venue, feeding the
label barriers) inside the frozen research window. Every other ML stage opens
the database read-only.

Bars are exact UTC-aligned aggregations (O first, H max, L min, C last, V sum;
arg_min/arg_max by timestamp for determinism) — closed bars only, because the
window ends at a UTC midnight. `--verify` aggregates the raw Binance table
alone for one month of BTCUSDT and compares it against native fapi 1h klines.
"""

from __future__ import annotations

import argparse
import json
import urllib.request

import duckdb
import numpy as np

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

META_DDL = "CREATE TABLE IF NOT EXISTS _ml_meta (key VARCHAR PRIMARY KEY, value VARCHAR NOT NULL);"


def verify_native_1h(con: duckdb.DuckDBPyConnection, month: str = "2021-02") -> dict:
    """Aggregate raw Binance 1m to 1h for one month of BTCUSDT and diff vs fapi klines."""
    start = int(np.datetime64(f"{month}-01T00:00").astype("datetime64[ms]").astype(np.int64))
    end = start + 28 * 86_400_000
    agg = con.execute(
        f"""SELECT (timestamp_ms // 3600000) * 3600000 AS ts,
                   arg_min(open, timestamp_ms) AS o, max(high) AS h, min(low) AS l,
                   arg_max(close, timestamp_ms) AS c, sum(volume) AS v
            FROM ohlcv_1m_binance
            WHERE symbol = 'BTCUSDT' AND timestamp_ms >= {start} AND timestamp_ms < {end}
            GROUP BY 1 ORDER BY 1"""
    ).fetchall()
    native = []
    cur = start
    while cur < end:
        url = ("https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=1h"
               f"&startTime={cur}&endTime={min(cur + 500 * 3600000, end) - 1}&limit=500")
        req = urllib.request.Request(url, headers={"User-Agent": config.symbol('BTC')})
        with urllib.request.urlopen(req, timeout=30) as r:
            batch = json.loads(r.read().decode())
        native.extend(batch)
        cur += 500 * 3600000
    native_map = {int(k[0]): k for k in native}
    ohlc_mismatch = vol_max_rel = 0
    for ts, o, h, l, c, v in agg:
        k = native_map[ts]
        if (float(k[1]), float(k[2]), float(k[3]), float(k[4])) != (o, h, l, c):
            ohlc_mismatch += 1
        nv = float(k[5])
        vol_max_rel = max(vol_max_rel, abs(v - nv) / nv if nv else abs(v - nv))
    return {"month": month, "bars": len(agg), "ohlc_mismatch": ohlc_mismatch,
            "volume_max_rel_diff": vol_max_rel}


def main() -> int:
    ap = argparse.ArgumentParser(description="canonical 1m -> 15m/1h/4h bars")
    ap.add_argument("--tickers", default=",".join(config.TICKERS), help="comma-separated subset")
    ap.add_argument("--verify", action="store_true", help="compare aggregated 1h vs native fapi klines")
    args = ap.parse_args()
    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]

    con = duckdb.connect(str(config.DB_PATH))
    con.execute("SET memory_limit='4GB'")
    con.execute("SET threads=2")
    con.execute(META_DDL)
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

    con.execute("INSERT OR REPLACE INTO _ml_meta VALUES ('research_start', ?)", [config.RESEARCH_START_UTC])
    con.execute("INSERT OR REPLACE INTO _ml_meta VALUES ('research_end', ?)", [config.RESEARCH_END_UTC])

    if args.verify:
        result = verify_native_1h(con)
        print(f"native-1h verification: {result}", flush=True)
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
