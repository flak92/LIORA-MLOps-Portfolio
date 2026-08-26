"""DATA INGEST quality monitoring: stdout tables + dashboard/status.json.

Three full scans (one per venue table, one over the canonical series) feed the
whole report: per-venue availability (coverage, gaps, duplicates, OHLC
violations), fusion provenance (both / single-venue shares, forward-filled
bars, cross-exchange divergence) and the pipeline flow totals. JSON keys are
ordered in flow order; the dashboard renders this file as-is on two tabs.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import duckdb

from . import config

VENUE_SCAN = """
SELECT symbol,
       count(*)                     AS rows,
       count(DISTINCT timestamp_ms) AS distinct_ts,
       min(timestamp_ms)            AS ts_min,
       max(timestamp_ms)            AS ts_max,
       count(*) FILTER (high < greatest(open, close, low)
                     OR low  > least(open, close, high)) AS ohlc_violations,
       count(*) FILTER (volume = 0) AS zero_volume,
       count(*) FILTER (volume = 0 AND open = high AND high = low
                        AND low = close) AS flat_bars
FROM ohlcv_1m_{venue}
GROUP BY symbol
"""

FUSION_SCAN = """
SELECT symbol,
       count(*)                                            AS rows,
       count(*) FILTER (src_count = 2)                     AS n_both,
       count(*) FILTER (src_count = 1 AND w_binance = 1.0) AS n_binance_only,
       count(*) FILTER (src_count = 1 AND w_binance = 0.0) AS n_bybit_only,
       count(*) FILTER (is_ffill)                          AS ffill_bars,
       count(*) FILTER (close IS NULL)                     AS leading_null,
       avg(rel_divergence)                                 AS div_mean,
       quantile_cont(rel_divergence, 0.99)                 AS div_p99,
       max(rel_divergence)                                 AS div_max,
       max(timestamp_ms)                                   AS ts_max,
       count(*) FILTER (high < greatest(open, close, low)
                     OR low  > least(open, close, high))   AS ohlc_violations,
       count(*) FILTER (volume = 0 AND open = high AND high = low
                        AND low = close)                   AS flat_bars
FROM ohlcv_1m_canonical
GROUP BY symbol
"""

# per-symbol (bounded memory): largest 1m move and longest flat run on the canonical series
CANON_MAX_RET = """
SELECT max(abs(close / prev - 1)) FROM (
  SELECT close, lag(close) OVER (ORDER BY timestamp_ms) AS prev
  FROM ohlcv_1m_canonical WHERE symbol = ?)
"""

CANON_FLAT_RUN = """
WITH f AS (SELECT timestamp_ms, (volume = 0 AND open = high AND high = low
                                 AND low = close) AS flat
           FROM ohlcv_1m_canonical WHERE symbol = ?),
g AS (SELECT *, sum(CASE WHEN flat THEN 0 ELSE 1 END)
                 OVER (ORDER BY timestamp_ms) AS grp FROM f)
SELECT coalesce(max(run), 0) FROM
  (SELECT count(*) FILTER (flat) AS run FROM g GROUP BY grp)
"""


def iso(ms: int | None) -> str | None:
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=UTC).strftime("%Y-%m-%d %H:%M")


def pct(part: int, whole: int) -> float:
    return round(100.0 * part / whole, 3) if whole else 0.0


def main() -> int:
    if not config.DB_PATH.exists():
        raise SystemExit(f"{config.DB_PATH} not found — run `make ingest` first")
    con = duckdb.connect(str(config.DB_PATH), read_only=True)

    con.execute("SET memory_limit='4GB'")
    con.execute("SET threads=2")
    venue_rows = {v: {r[0]: r for r in con.execute(VENUE_SCAN.format(venue=v)).fetchall()} for v in config.VENUES}
    fusion_rows = {r[0]: r for r in con.execute(FUSION_SCAN).fetchall()}
    canon_extra = {
        sym: (
            con.execute(CANON_MAX_RET, [sym]).fetchone()[0],
            con.execute(CANON_FLAT_RUN, [sym]).fetchone()[0],
        )
        for sym in fusion_rows
    }
    con.close()

    window_end_ms = max((r[10] for r in fusion_rows.values()), default=None)
    if window_end_ms is not None:
        window_end_ms += config.GRID_STEP_MS
    expected = (window_end_ms - config.START_MS) // config.GRID_STEP_MS if window_end_ms else 0

    tickers = [t for t in config.TICKERS if config.symbol(t) in fusion_rows]
    zip_counts = {
        v: {t: sum(1 for _ in config.raw_symbol_dir(t, v).glob("*_trade.zip")) for t in tickers}
        for v in config.VENUES
    }

    venues = {}
    for v in config.VENUES:
        out = []
        for t in tickers:
            sym = config.symbol(t)
            r = venue_rows[v].get(sym)
            rows, distinct_ts = (r[1], r[2]) if r else (0, 0)
            out.append(
                {
                    "symbol": sym,
                    "zip_count": zip_counts[v][t],
                    "rows": rows,
                    "coverage_pct": pct(distinct_ts, expected),
                    "gaps": expected - distinct_ts,
                    "duplicates": rows - distinct_ts,
                    "ohlc_violations": int(r[5]) if r else 0,
                    "zero_volume": int(r[6]) if r else 0,
                    "flat_bars": int(r[7]) if r else 0,
                    "first_ts": iso(r[3]) if r else None,
                    "last_ts": iso(r[4]) if r else None,
                }
            )
        venues[v] = out

    fusion, symbols = [], []
    for t in tickers:
        sym = config.symbol(t)
        r = fusion_rows[sym]
        rows, ffill = r[1], int(r[5])
        leading = int(r[6])
        fusion.append(
            {
                "symbol": sym,
                "rows": rows,
                "pct_both": pct(int(r[2]), rows),
                "pct_binance_only": pct(int(r[3]), rows),
                "pct_bybit_only": pct(int(r[4]), rows),
                "ffill_bars": ffill,
                "ffill_pct": pct(ffill, rows),
                "leading_null": leading,
                "div_mean": round(float(r[7]), 8) if r[7] is not None else None,
                "div_p99": round(float(r[8]), 8) if r[8] is not None else None,
                "div_max": round(float(r[9]), 8) if r[9] is not None else None,
                "ohlc_violations": int(r[11]),
                "flat_bars": int(r[12]),
                "max_abs_ret_1m": round(float(canon_extra[sym][0]), 6) if canon_extra[sym][0] is not None else None,
                "longest_flat_run_min": int(canon_extra[sym][1]),
            }
        )
        pq = config.asset_parquet(t)
        pq_rows = 0
        if pq.exists():
            c2 = duckdb.connect()
            pq_rows = c2.execute(f"SELECT count(*) FROM read_parquet('{pq}')").fetchone()[0]
            c2.close()
        symbols.append(
            {
                "symbol": sym,
                "rows": rows,
                "ffill_bars": ffill,
                "data_pct": pct(rows - ffill - leading, rows),
                "parquet_rows": pq_rows,
                "parquet_bytes": pq.stat().st_size if pq.exists() else 0,
            }
        )

    status = {
        "generated_at_utc": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S"),
        "window_start": f"{config.START_UTC} 00:00",
        "window_end": iso(window_end_ms),
        "duckdb_version": duckdb.__version__,
        "db_bytes": config.DB_PATH.stat().st_size,
        "flow": {
            "zips_binance": sum(zip_counts["binance"].values()),
            "zips_bybit": sum(zip_counts["bybit"].values()),
            "rows_binance": sum(r[1] for r in venue_rows["binance"].values()),
            "rows_bybit": sum(r[1] for r in venue_rows["bybit"].values()),
            "rows_canonical": sum(s["rows"] for s in symbols),
            "parquet_rows": sum(s["parquet_rows"] for s in symbols),
        },
        "symbols": symbols,
        "venues": venues,
        "fusion": fusion,
    }

    config.DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    out = config.DASHBOARD_DIR / "status.json"
    out.write_text(json.dumps(status, indent=1) + "\n", encoding="utf-8")

    f = status["flow"]
    print(f"window [{status['window_start']} .. {status['window_end']})  "
          f"db {status['db_bytes'] / 1e6:.1f} MB  duckdb {status['duckdb_version']}")
    print(f"flow: zips {f['zips_binance']}+{f['zips_bybit']} -> rows {f['rows_binance']}+{f['rows_bybit']} "
          f"-> canonical {f['rows_canonical']} -> parquet {f['parquet_rows']}")
    for v in config.VENUES:
        print(f"[venue {v}]")
        print(f"{'symbol':9} {'zips':>5} {'rows':>9} {'cover%':>8} {'gaps':>8} {'dups':>4} {'ohlc':>4} {'v0':>6} {'flat':>6}")
        for s in venues[v]:
            print(f"{s['symbol']:9} {s['zip_count']:>5} {s['rows']:>9} {s['coverage_pct']:>8.3f} "
                  f"{s['gaps']:>8} {s['duplicates']:>4} {s['ohlc_violations']:>4} {s['zero_volume']:>6} {s['flat_bars']:>6}")
    print("[fusion / canonical]")
    print(f"{'symbol':9} {'rows':>9} {'both%':>7} {'bin%':>7} {'byb%':>6} {'ffill':>6} {'lead0':>5} "
          f"{'ohlc':>4} {'flatrun':>7} {'maxret':>8} {'div_p99':>10} {'div_max':>10}")
    for s in fusion:
        print(f"{s['symbol']:9} {s['rows']:>9} {s['pct_both']:>7.2f} {s['pct_binance_only']:>7.2f} "
              f"{s['pct_bybit_only']:>6.2f} {s['ffill_bars']:>6} {s['leading_null']:>5} "
              f"{s['ohlc_violations']:>4} {s['longest_flat_run_min']:>7} "
              f"{s['max_abs_ret_1m'] if s['max_abs_ret_1m'] is not None else '-':>8} "
              f"{s['div_p99'] if s['div_p99'] is not None else '-':>10} "
              f"{s['div_max'] if s['div_max'] is not None else '-':>10}")
    print(f"wrote {out.relative_to(config.REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
