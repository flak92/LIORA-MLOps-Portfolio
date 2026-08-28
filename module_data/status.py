"""Data-layer quality monitoring: stdout tables + module_monitoring/status.json.

Three full scans (one per venue table, one over the canonical series) feed the
whole report: per-venue availability (coverage, gaps, duplicates, OHLC
violations), canonical source provenance (per-venue shares, forward fills,
zero-volume candles, source switches and the largest move at a switch — the
only place a cross-venue basis jump can enter the series) and the pipeline
flow totals. JSON keys are ordered in flow order; the dashboard renders this
file as-is.
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

CANONICAL_SCAN = """
SELECT symbol,
       count(*)                              AS rows,
       count(*) FILTER (source = 'binance')  AS n_binance,
       count(*) FILTER (source = 'bybit')    AS n_bybit,
       count(*) FILTER (source = 'ffill')    AS ffill_bars,
       count(*) FILTER (zero_volume)         AS zero_volume_bars,
       avg(rel_divergence)                   AS div_mean,
       quantile_cont(rel_divergence, 0.99)   AS div_p99,
       max(rel_divergence)                   AS div_max,
       max(timestamp_ms)                     AS ts_max,
       count(*) FILTER (high < greatest(open, close, low)
                     OR low  > least(open, close, high)) AS ohlc_violations
FROM ohlcv_1m_canonical
GROUP BY symbol
"""

# per-symbol (bounded memory): largest 1m move and longest flat run on the canonical series
CANONICAL_MAX_ABS_RET_1M = """
SELECT max(abs(close / prev - 1)) FROM (
  SELECT close, lag(close) OVER (ORDER BY timestamp_ms) AS prev
  FROM ohlcv_1m_canonical WHERE symbol = ?)
"""

# a basis jump can enter the canonical series only on a minute whose source
# differs from the previous minute — count switches and the largest such move
SOURCE_SWITCHES = """
SELECT count(*) FILTER (chg) AS switches,
       max(CASE WHEN chg THEN abs(close / prev_close - 1) END) AS max_ret_at_switch
FROM (SELECT close,
             lag(close)  OVER (ORDER BY timestamp_ms) AS prev_close,
             source <> lag(source) OVER (ORDER BY timestamp_ms) AS chg
      FROM ohlcv_1m_canonical WHERE symbol = ?)
"""

CANONICAL_LONGEST_FLAT_RUN = """
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
    if not config.STORE_DB_PATH.exists():
        raise SystemExit(f"{config.STORE_DB_PATH} not found — run `make ingest` first")
    con = duckdb.connect(str(config.STORE_DB_PATH), read_only=True)

    con.execute("SET memory_limit='4GB'")
    con.execute("SET threads=1")   # float summation must not be reordered
    venue_rows = {venue: {r[0]: r for r in con.execute(VENUE_SCAN.format(venue=venue)).fetchall()}
                  for venue in config.SOURCE_VENUES}
    canonical_rows = {r[0]: r for r in con.execute(CANONICAL_SCAN).fetchall()}
    canon_extra = {
        symbol: (
            con.execute(CANONICAL_MAX_ABS_RET_1M, [symbol]).fetchone()[0],
            con.execute(CANONICAL_LONGEST_FLAT_RUN, [symbol]).fetchone()[0],
            con.execute(SOURCE_SWITCHES, [symbol]).fetchone(),
        )
        for symbol in canonical_rows
    }
    con.close()

    window_end_ms = max((r[9] for r in canonical_rows.values()), default=None)
    if window_end_ms is not None:
        window_end_ms += config.CANONICAL_GRID_INTERVAL_MS
    expected = ((window_end_ms - config.DATA_WINDOW_START_MS)
                // config.CANONICAL_GRID_INTERVAL_MS) if window_end_ms else 0

    tickers = [t for t in config.TICKERS if config.symbol(t) in canonical_rows]
    zip_counts = {
        venue: {t: sum(1 for _ in config.raw_symbol_dir(t, venue).glob("*_trade.zip")) for t in tickers}
        for venue in config.SOURCE_VENUES
    }

    venues = {}
    for venue in config.SOURCE_VENUES:
        out = []
        for t in tickers:
            symbol = config.symbol(t)
            r = venue_rows[venue].get(symbol)
            rows, distinct_ts = (r[1], r[2]) if r else (0, 0)
            out.append(
                {
                    "symbol": symbol,
                    "zip_count": zip_counts[venue][t],
                    "rows": rows,
                    "coverage_pct": pct(distinct_ts, expected),
                    "gaps": expected - distinct_ts,
                    # measured from the first observation to the END OF THE WINDOW:
                    # a span anchored on the symbol's own last row shrinks together
                    # with a truncated tail and reports zero for a stale feed
                    "gaps_after_first_observation": (
                        (window_end_ms - r[3]) // config.CANONICAL_GRID_INTERVAL_MS - distinct_ts
                    ) if r and window_end_ms else 0,
                    "duplicates": rows - distinct_ts,
                    "ohlc_violations": int(r[5]) if r else 0,
                    "zero_volume_bars": int(r[6]) if r else 0,
                    "flat_bars": int(r[7]) if r else 0,
                    "first_ts": iso(r[3]) if r else None,
                    "last_ts": iso(r[4]) if r else None,
                }
            )
        venues[venue] = out

    canonical, symbols = [], []
    for t in tickers:
        symbol = config.symbol(t)
        r = canonical_rows[symbol]
        rows, ffill_bars = r[1], int(r[4])
        switches, max_ret_switch = canon_extra[symbol][2]
        canonical.append(
            {
                "symbol": symbol,
                "rows": rows,
                "binance_pct": pct(int(r[2]), rows),
                "bybit_pct": pct(int(r[3]), rows),
                "ffill_pct": pct(ffill_bars, rows),
                "ffill_bars": ffill_bars,
                "zero_volume_bars": int(r[5]),
                "source_switches": int(switches),
                "max_abs_ret_at_switch": round(float(max_ret_switch), 6) if max_ret_switch is not None else None,
                "div_mean": round(float(r[6]), 8) if r[6] is not None else None,
                "div_p99": round(float(r[7]), 8) if r[7] is not None else None,
                "div_max": round(float(r[8]), 8) if r[8] is not None else None,
                "ohlc_violations": int(r[10]),
                "max_abs_ret_1m": round(float(canon_extra[symbol][0]), 6) if canon_extra[symbol][0] is not None else None,
                "longest_flat_run_minutes": int(canon_extra[symbol][1]),
            }
        )
        pq = config.canonical_parquet(t)
        pq_rows = 0
        if pq.exists():
            c2 = duckdb.connect()
            pq_rows = c2.execute(f"SELECT count(*) FROM read_parquet('{pq}')").fetchone()[0]
            c2.close()
        symbols.append(
            {
                "symbol": symbol,
                "rows": rows,
                "ffill_bars": ffill_bars,
                "real_data_pct": pct(rows - ffill_bars, rows),
                "rows_parquet": pq_rows,
                "parquet_bytes": pq.stat().st_size if pq.exists() else 0,
            }
        )

    status = {
        "generated_at_utc": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S"),
        "window_start": f"{config.DATA_WINDOW_START_UTC} 00:00",
        "window_end": iso(window_end_ms),
        "duckdb_version": duckdb.__version__,
        "db_bytes": config.STORE_DB_PATH.stat().st_size,
        "flow": {
            "zips_binance": sum(zip_counts["binance"].values()),
            "zips_bybit": sum(zip_counts["bybit"].values()),
            "rows_binance": sum(r[1] for r in venue_rows["binance"].values()),
            "rows_bybit": sum(r[1] for r in venue_rows["bybit"].values()),
            "rows_canonical": sum(s["rows"] for s in symbols),
            "rows_parquet": sum(s["rows_parquet"] for s in symbols),
        },
        "symbols": symbols,
        "venues": venues,
        "canonical_source": canonical,
    }

    config.MODULE_MONITORING_DIR.mkdir(parents=True, exist_ok=True)
    out = config.MODULE_MONITORING_DIR / "status.json"
    out.write_text(json.dumps(status, indent=1) + "\n", encoding="utf-8")

    f = status["flow"]
    print(f"window [{status['window_start']} .. {status['window_end']})  "
          f"db {status['db_bytes'] / 1e6:.1f} MB  duckdb {status['duckdb_version']}")
    print(f"flow: zips {f['zips_binance']}+{f['zips_bybit']} -> rows {f['rows_binance']}+{f['rows_bybit']} "
          f"-> canonical {f['rows_canonical']} -> parquet {f['rows_parquet']}")
    for venue in config.SOURCE_VENUES:
        print(f"[venue {venue}]")
        print(f"{'symbol':9} {'zips':>5} {'rows':>9} {'cover%':>8} {'gaps':>8} {'dups':>4} {'ohlc':>4} {'v0':>6} {'flat':>6}")
        for s in venues[venue]:
            print(f"{s['symbol']:9} {s['zip_count']:>5} {s['rows']:>9} {s['coverage_pct']:>8.3f} "
                  f"{s['gaps']:>8} {s['duplicates']:>4} {s['ohlc_violations']:>4} {s['zero_volume_bars']:>6} {s['flat_bars']:>6}")
    print("[canonical source]")
    print(f"{'symbol':9} {'rows':>9} {'bin%':>7} {'byb%':>6} {'ffill':>6} {'v0':>6} {'switch':>7} "
          f"{'ret@sw':>8} {'ohlc':>4} {'flatrun':>7} {'maxret':>8} {'div_p99':>10} {'div_max':>10}")
    for s in canonical:
        print(f"{s['symbol']:9} {s['rows']:>9} {s['binance_pct']:>7.2f} {s['bybit_pct']:>6.2f} "
              f"{s['ffill_bars']:>6} {s['zero_volume_bars']:>6} {s['source_switches']:>7} "
              f"{s['max_abs_ret_at_switch'] if s['max_abs_ret_at_switch'] is not None else '-':>8} "
              f"{s['ohlc_violations']:>4} {s['longest_flat_run_minutes']:>7} "
              f"{s['max_abs_ret_1m'] if s['max_abs_ret_1m'] is not None else '-':>8} "
              f"{s['div_p99'] if s['div_p99'] is not None else '-':>10} "
              f"{s['div_max'] if s['div_max'] is not None else '-':>10}")
    print(f"wrote {out.relative_to(config.REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
