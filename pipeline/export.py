"""Export per-asset Parquet files from the canonical fused series.

One file per asset: assets/Asset_<TICKER>/1m_<TICKER>_data.parquet with pure
timestamp_ms, open, high, low, close, volume columns — a continuous canonical
series with no gaps, so downstream indicator / ML code needs no gap handling.
Provenance (src_count, is_ffill, divergence, weights) stays in the database and
in the monitoring layer. Writes are atomic: COPY to a temp file, verify the
read-back row count, then os.replace.
"""

from __future__ import annotations

import argparse
import os

import duckdb

from . import config


def main() -> int:
    ap = argparse.ArgumentParser(description="ohlcv_1m_canonical -> assets/Asset_<T>/1m_<T>_data.parquet")
    ap.add_argument("--tickers", default=",".join(config.TICKERS), help="comma-separated subset")
    args = ap.parse_args()
    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]

    con = duckdb.connect(str(config.DB_PATH), read_only=True)
    for t in tickers:
        sym = config.symbol(t)
        out = config.asset_parquet(t)
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".parquet.tmp")
        con.execute(
            f"""COPY (SELECT timestamp_ms, open, high, low, close, volume
                      FROM ohlcv_1m_canonical WHERE symbol = '{sym}' ORDER BY timestamp_ms)
                TO '{tmp}' (FORMAT PARQUET, COMPRESSION zstd)"""
        )
        db_rows = con.execute("SELECT count(*) FROM ohlcv_1m_canonical WHERE symbol = ?", [sym]).fetchone()[0]
        file_rows = con.execute(f"SELECT count(*) FROM read_parquet('{tmp}')").fetchone()[0]
        if file_rows != db_rows:
            raise SystemExit(f"{out.name}: read-back {file_rows} rows != canonical {db_rows}")
        os.replace(tmp, out)
        print(f"{out.relative_to(config.REPO_ROOT)}: {file_rows} rows", flush=True)
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
