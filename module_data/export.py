"""Export per-asset Parquet files from the canonical series.

One file per asset: store_Assets_artifacts/<TICKER>/canonical_ss-01-hh-dd-MM.parquet with pure
timestamp_ms, open, high, low, close, volume columns — a continuous canonical
series with no gaps. Provenance (source, zero_volume, validity, divergence)
stays in the database and in the monitoring layer.

Writes are fail-closed: the data is COPY'd to a temp file and a set of
invariants is asserted on the temp file BEFORE os.replace — a failing
invariant leaves the previously published Parquet untouched:
  - row count equals the full minute grid of the window,
  - timestamps are distinct and on the 60000 ms grid,
  - no NULL and no non-finite OHLCV values,
  - OHLC ordering invariants hold on every row.
"""

from __future__ import annotations

import os

import duckdb

from . import config

INVARIANTS = """
SELECT count(*)                                                        AS rows,
       count(DISTINCT timestamp_ms)                                    AS distinct_ts,
       count(*) FILTER (timestamp_ms % 60000 <> 0)                     AS off_grid,
       count(*) FILTER (open IS NULL OR high IS NULL OR low IS NULL
                        OR close IS NULL OR volume IS NULL)            AS nulls,
       count(*) FILTER (NOT (isfinite(open) AND isfinite(high) AND isfinite(low)
                             AND isfinite(close) AND isfinite(volume))) AS non_finite,
       count(*) FILTER (high < greatest(open, close, low)
                     OR low  > least(open, close, high))               AS ohlc_broken
FROM read_parquet('{path}')
"""


def main() -> int:
    ap = config.ticker_parser("ohlcv_1m_canonical -> store_Assets_artifacts/<T>/canonical_ss-01-hh-dd-MM.parquet")
    args = ap.parse_args()
    tickers = config.parse_tickers(args.tickers)

    con = duckdb.connect(str(config.STORE_DB_PATH), read_only=True)
    grid_rows = con.execute(
        f"""SELECT (max(timestamp_ms) + {config.CANONICAL_GRID_INTERVAL_MS} - {config.DATA_WINDOW_START_MS})
                   // {config.CANONICAL_GRID_INTERVAL_MS} FROM ohlcv_1m_canonical"""
    ).fetchone()[0]
    for t in tickers:
        symbol = config.symbol(t)
        out = config.canonical_parquet(t)
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".parquet.tmp")
        con.execute(
            f"""COPY (SELECT timestamp_ms, open, high, low, close, volume
                      FROM ohlcv_1m_canonical WHERE symbol = '{symbol}' ORDER BY timestamp_ms)
                TO '{tmp}' (FORMAT PARQUET, COMPRESSION zstd)"""
        )
        inv = con.execute(INVARIANTS.format(path=tmp)).fetchone()
        rows, distinct_ts, off_grid, nulls, non_finite, ohlc_broken = inv
        assert rows == grid_rows, f"{out.name}: {rows} rows != grid {grid_rows}"
        assert distinct_ts == rows, f"{out.name}: duplicate timestamps"
        assert off_grid == 0, f"{out.name}: {off_grid} off-grid timestamps"
        assert nulls == 0 and non_finite == 0, f"{out.name}: NULL/non-finite OHLCV"
        assert ohlc_broken == 0, f"{out.name}: {ohlc_broken} OHLC-broken rows"
        os.replace(tmp, out)
        print(f"{out.relative_to(config.REPO_ROOT)}: {rows} rows (invariants ok)", flush=True)
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
