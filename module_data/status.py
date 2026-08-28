"""Data-layer quality monitoring: stdout tables + module_monitoring/status.json.

Three basket-wide scans (one per venue table, one over the canonical series)
plus three bounded per-symbol passes (largest 1m move, longest flat run, source
switches) feed the report: per-venue availability (coverage, gaps, duplicates,
OHLC violations), canonical source provenance (per-venue shares, forward fills,
zero-volume candles, source switches and the largest move at a switch — the
only place a cross-venue basis jump can enter the series) and the pipeline
flow totals. JSON keys are ordered in flow order; the dashboard renders this
file as-is. Every SQL alias is the key it becomes, and the report reads the
scan rows by column name, never by position.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import duckdb

from . import config
from .lean import LEAN_DAY_ZIP_GLOB

VENUE_SCAN = """
SELECT symbol,
       count(*)                     AS row_count,
       count(DISTINCT timestamp_ms) AS distinct_timestamp_count,
       min(timestamp_ms)            AS first_timestamp_ms,
       max(timestamp_ms)            AS last_timestamp_ms,
       count(*) FILTER (high < greatest(open, close, low)
                     OR low  > least(open, close, high)) AS ohlc_violation_count,
       count(*) FILTER (volume = 0) AS zero_volume_bars,
       count(*) FILTER (volume = 0 AND open = high AND high = low
                        AND low = close) AS flat_bars
FROM ohlcv_1m_{venue}
GROUP BY symbol
"""

CANONICAL_SCAN = """
SELECT symbol,
       count(*)                              AS row_count,
       count(*) FILTER (source = 'binance')  AS binance_row_count,
       count(*) FILTER (source = 'bybit')    AS bybit_row_count,
       count(*) FILTER (source = 'ffill')    AS ffill_bars,
       count(*) FILTER (zero_volume)         AS zero_volume_bars,
       avg(rel_divergence)                   AS relative_divergence_mean,
       quantile_cont(rel_divergence, 0.99)   AS relative_divergence_p99,
       max(rel_divergence)                   AS relative_divergence_max,
       max(timestamp_ms)                     AS last_timestamp_ms,
       count(*) FILTER (high < greatest(open, close, low)
                     OR low  > least(open, close, high)) AS ohlc_violation_count
FROM ohlcv_1m_canonical
GROUP BY symbol
"""

# per-symbol (bounded memory): largest 1m move on the canonical series
CANONICAL_MAX_ABS_RETURN_1M_SCAN = """
SELECT max(abs(close / previous_close - 1)) AS max_abs_return_1m FROM (
  SELECT close, lag(close) OVER (ORDER BY timestamp_ms) AS previous_close
  FROM ohlcv_1m_canonical WHERE symbol = ?)
"""

# a basis jump can enter the canonical series only on a minute whose source
# differs from the previous minute — count switches and the largest such move
SOURCE_SWITCH_SCAN = """
SELECT count(*) FILTER (source_changed) AS source_switch_count,
       max(CASE WHEN source_changed THEN abs(close / previous_close - 1) END) AS max_abs_return_at_switch
FROM (SELECT close,
             lag(close)  OVER (ORDER BY timestamp_ms) AS previous_close,
             source <> lag(source) OVER (ORDER BY timestamp_ms) AS source_changed
      FROM ohlcv_1m_canonical WHERE symbol = ?)
"""

CANONICAL_LONGEST_FLAT_RUN_SCAN = """
WITH flat_minutes AS (SELECT timestamp_ms, (volume = 0 AND open = high AND high = low
                                            AND low = close) AS flat
                      FROM ohlcv_1m_canonical WHERE symbol = ?),
run_groups AS (SELECT *, sum(CASE WHEN flat THEN 0 ELSE 1 END)
                        OVER (ORDER BY timestamp_ms) AS run_group FROM flat_minutes)
SELECT coalesce(max(flat_run_minutes), 0) AS longest_flat_run_minutes FROM
  (SELECT count(*) FILTER (flat) AS flat_run_minutes FROM run_groups GROUP BY run_group)
"""


def load_rows_by_symbol(con: duckdb.DuckDBPyConnection, statement: str) -> dict[str, dict]:
    """One dict per symbol (the first column), keyed by the scan's column names."""
    cursor = con.execute(statement)
    names = [column[0] for column in cursor.description]
    return {row[0]: dict(zip(names, row)) for row in cursor.fetchall()}


def load_row(con: duckdb.DuckDBPyConnection, statement: str, params: list) -> dict:
    cursor = con.execute(statement, params)
    names = [column[0] for column in cursor.description]
    return dict(zip(names, cursor.fetchone()))


def to_utc_minute(ms: int | None) -> str | None:
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=UTC).strftime("%Y-%m-%d %H:%M")


def share_pct(part: int, whole: int) -> float:
    return round(100.0 * part / whole, 3) if whole else 0.0


def _rounded(x, ndigits):
    """round() that tolerates the NULL a scan reports when no row qualifies."""
    return None if x is None else round(float(x), ndigits)


def main() -> int:
    if not config.STORE_DB_PATH.exists():
        raise SystemExit(f"{config.STORE_DB_PATH} not found — run `make data-ingest` first")
    con = duckdb.connect(str(config.STORE_DB_PATH), read_only=True)

    con.execute("SET memory_limit='4GB'")
    con.execute("SET threads=1")   # float summation must not be reordered
    venue_rows = {venue: load_rows_by_symbol(con, VENUE_SCAN.format(venue=venue))
                  for venue in config.SOURCE_VENUES}
    canonical_rows = load_rows_by_symbol(con, CANONICAL_SCAN)
    for symbol, row in canonical_rows.items():
        row.update(load_row(con, CANONICAL_MAX_ABS_RETURN_1M_SCAN, [symbol]))
        row.update(load_row(con, CANONICAL_LONGEST_FLAT_RUN_SCAN, [symbol]))
        row.update(load_row(con, SOURCE_SWITCH_SCAN, [symbol]))
    con.close()

    window_end_ms = max((r["last_timestamp_ms"] for r in canonical_rows.values()), default=None)
    if window_end_ms is not None:
        window_end_ms += config.CANONICAL_GRID_INTERVAL_MS
    expected = ((window_end_ms - config.DATA_WINDOW_START_MS)
                // config.CANONICAL_GRID_INTERVAL_MS) if window_end_ms else 0

    tickers = [t for t in config.TICKERS if config.symbol(t) in canonical_rows]
    zip_counts = {
        venue: {t: sum(1 for _ in config.raw_symbol_dir(t, venue).glob(LEAN_DAY_ZIP_GLOB)) for t in tickers}
        for venue in config.SOURCE_VENUES
    }

    venues = {}
    for venue in config.SOURCE_VENUES:
        out = []
        for t in tickers:
            symbol = config.symbol(t)
            r = venue_rows[venue].get(symbol)
            row_count, distinct = (r["row_count"], r["distinct_timestamp_count"]) if r else (0, 0)
            out.append(
                {
                    "symbol": symbol,
                    "zip_count": zip_counts[venue][t],
                    "row_count": row_count,
                    "coverage_pct": share_pct(distinct, expected),
                    "gap_count": expected - distinct,
                    # measured from the first observation to the END OF THE WINDOW:
                    # a span anchored on the symbol's own last row shrinks together
                    # with a truncated tail and reports zero for a stale feed
                    "gap_count_after_first_observation": (
                        (window_end_ms - r["first_timestamp_ms"]) // config.CANONICAL_GRID_INTERVAL_MS - distinct
                    ) if r and window_end_ms else 0,
                    "duplicate_count": row_count - distinct,
                    "ohlc_violation_count": int(r["ohlc_violation_count"]) if r else 0,
                    "zero_volume_bars": int(r["zero_volume_bars"]) if r else 0,
                    "flat_bars": int(r["flat_bars"]) if r else 0,
                    "first_observation_utc": to_utc_minute(r["first_timestamp_ms"]) if r else None,
                    "last_observation_utc": to_utc_minute(r["last_timestamp_ms"]) if r else None,
                }
            )
        venues[venue] = out

    canonical, symbols = [], []
    for t in tickers:
        symbol = config.symbol(t)
        r = canonical_rows[symbol]
        row_count, ffill_bars = r["row_count"], int(r["ffill_bars"])
        canonical.append(
            {
                "symbol": symbol,
                "row_count": row_count,
                "binance_pct": share_pct(int(r["binance_row_count"]), row_count),
                "bybit_pct": share_pct(int(r["bybit_row_count"]), row_count),
                "ffill_pct": share_pct(ffill_bars, row_count),
                "ffill_bars": ffill_bars,
                "zero_volume_bars": int(r["zero_volume_bars"]),
                "source_switch_count": int(r["source_switch_count"]),
                "max_abs_return_at_switch": _rounded(r["max_abs_return_at_switch"], 6),
                "relative_divergence_mean": _rounded(r["relative_divergence_mean"], 8),
                "relative_divergence_p99": _rounded(r["relative_divergence_p99"], 8),
                "relative_divergence_max": _rounded(r["relative_divergence_max"], 8),
                "ohlc_violation_count": int(r["ohlc_violation_count"]),
                "max_abs_return_1m": _rounded(r["max_abs_return_1m"], 6),
                "longest_flat_run_minutes": int(r["longest_flat_run_minutes"]),
            }
        )

        symbols.append(
            {
                "symbol": symbol,
                "row_count": row_count,
                "ffill_bars": ffill_bars,
                "real_data_pct": share_pct(row_count - ffill_bars, row_count),
            }
        )

    status = {
        "generated_at_utc": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S"),
        "window_start_utc": f"{config.DATA_WINDOW_START_UTC} 00:00",
        "window_end_utc": to_utc_minute(window_end_ms),
        "duckdb_version": duckdb.__version__,
        "db_bytes": config.STORE_DB_PATH.stat().st_size,
        "flow": {
            "binance_zip_count": sum(zip_counts["binance"].values()),
            "bybit_zip_count": sum(zip_counts["bybit"].values()),
            "binance_row_count": sum(r["row_count"] for r in venue_rows["binance"].values()),
            "bybit_row_count": sum(r["row_count"] for r in venue_rows["bybit"].values()),
            "canonical_row_count": sum(s["row_count"] for s in symbols),
        },
        "symbols": symbols,
        "venues": venues,
        "canonical_source": canonical,
    }

    config.MODULE_MONITORING_DIR.mkdir(parents=True, exist_ok=True)
    out = config.MODULE_MONITORING_STATUS_JSON_PATH
    out.write_text(json.dumps(status, indent=1) + "\n", encoding="utf-8")

    f = status["flow"]
    print(f"window [{status['window_start_utc']} .. {status['window_end_utc']})  "
          f"db {status['db_bytes'] / 1e6:.1f} MB  duckdb {status['duckdb_version']}")
    print(f"flow: zips {f['binance_zip_count']}+{f['bybit_zip_count']} -> rows {f['binance_row_count']}+{f['bybit_row_count']} "
          f"-> canonical {f['canonical_row_count']}")
    for venue in config.SOURCE_VENUES:
        print(f"[venue {venue}]")
        print(f"{'symbol':9} {'zips':>5} {'rows':>9} {'cover%':>8} {'gaps':>8} {'dups':>4} {'ohlc':>4} {'v0':>6} {'flat':>6}")
        for s in venues[venue]:
            print(f"{s['symbol']:9} {s['zip_count']:>5} {s['row_count']:>9} {s['coverage_pct']:>8.3f} "
                  f"{s['gap_count']:>8} {s['duplicate_count']:>4} {s['ohlc_violation_count']:>4} {s['zero_volume_bars']:>6} {s['flat_bars']:>6}")
    print("[canonical source]")
    print(f"{'symbol':9} {'rows':>9} {'bin%':>7} {'byb%':>6} {'ffill':>6} {'v0':>6} {'switch':>7} "
          f"{'ret@sw':>8} {'ohlc':>4} {'flatrun':>7} {'maxret':>8} {'rdiv_p99':>10} {'rdiv_max':>10}")
    for s in canonical:
        print(f"{s['symbol']:9} {s['row_count']:>9} {s['binance_pct']:>7.2f} {s['bybit_pct']:>6.2f} "
              f"{s['ffill_bars']:>6} {s['zero_volume_bars']:>6} {s['source_switch_count']:>7} "
              f"{s['max_abs_return_at_switch'] if s['max_abs_return_at_switch'] is not None else '-':>8} "
              f"{s['ohlc_violation_count']:>4} {s['longest_flat_run_minutes']:>7} "
              f"{s['max_abs_return_1m'] if s['max_abs_return_1m'] is not None else '-':>8} "
              f"{s['relative_divergence_p99'] if s['relative_divergence_p99'] is not None else '-':>10} "
              f"{s['relative_divergence_max'] if s['relative_divergence_max'] is not None else '-':>10}")
    print(f"wrote {out.relative_to(config.REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
