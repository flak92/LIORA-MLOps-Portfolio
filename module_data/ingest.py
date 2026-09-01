"""Load both venue ZIP trees into the asset's DuckDB and rebuild its canonical series, one asset at a time.

The canonical table ohlcv_1m_canonical is a PRIMARY-FAILOVER series: every canonical bar is ONE venue's
candle copied verbatim — no weighting, no rounding — or an explicitly flagged forward fill. The validity
predicate, the decision table the SQL below encodes, the volume rule that chooses the venue and the
provenance columns are this module's own contract, skills/skill_candle_canonicalisation.md. It is the
normative source; this file is its one implementation and keeps no second copy of it.
"""

from __future__ import annotations

import csv
import io
import tempfile
import zipfile
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from . import config
from .lean import LEAN_DAY_ZIP_NAME_PATTERN, lean_day_zip_paths

VENUE_DDL = """
CREATE TABLE IF NOT EXISTS ohlcv_1m_{venue} (
  timestamp_ms BIGINT  NOT NULL,   -- bar OPEN, UTC epoch ms
  open   DOUBLE,
  high   DOUBLE,
  low    DOUBLE,
  close  DOUBLE,
  volume DOUBLE                    -- BASE volume (Lean convention)
);
"""

CANONICAL_DDL = """
CREATE TABLE IF NOT EXISTS ohlcv_1m_canonical (
  timestamp_ms BIGINT  NOT NULL,   -- full grid: every minute of the window
  open   DOUBLE,
  high   DOUBLE,
  low    DOUBLE,
  close  DOUBLE,
  volume DOUBLE,                   -- verbatim venue volume (0 on ffill rows)
  source         VARCHAR,          -- 'binance' / 'bybit' / 'ffill'
  zero_volume    BOOLEAN,          -- the winning candle was valid and traded nothing
  binance_valid  BOOLEAN,          -- Binance row present with intact OHLC
  bybit_valid    BOOLEAN,          -- Bybit row present with intact OHLC
  rel_divergence DOUBLE            -- |c_bin - c_byb| / mid when both valid (QC only)
);
"""

OHLC_INTACT_PREDICATE = """(isfinite(open) AND isfinite(high) AND isfinite(low)
          AND isfinite(close) AND isfinite(volume)
          AND open > 0 AND high > 0 AND low > 0 AND close > 0 AND volume >= 0
          AND low <= least(open, close) AND high >= greatest(open, close))"""

# use_binance: the primary venue wins whenever it is valid and either traded, or Bybit did not trade
# either; end_ms is the asset's own grid end, the last minute either venue printed for it
CANONICAL_INSERT = """
INSERT INTO ohlcv_1m_canonical
WITH
raw_1m_binance_rows AS (
  SELECT timestamp_ms, open, high, low, close, volume,
         {ohlc_intact_predicate} AS valid
  FROM ohlcv_1m_binance
),
raw_1m_bybit_rows AS (
  SELECT timestamp_ms, open, high, low, close, volume,
         {ohlc_intact_predicate} AS valid
  FROM ohlcv_1m_bybit
),
grid AS (
  SELECT t AS timestamp_ms FROM range({start_ms}, {end_ms}, {step_ms}) r(t)
),
joined AS (
  SELECT g.timestamp_ms,
         binance.open  AS binance_open,  binance.high   AS binance_high,
         binance.low   AS binance_low,   binance.close  AS binance_close,
         binance.volume AS binance_volume,
         coalesce(binance.valid, false) AS binance_valid,
         bybit.open  AS bybit_open,  bybit.high   AS bybit_high,
         bybit.low   AS bybit_low,   bybit.close  AS bybit_close,
         bybit.volume AS bybit_volume,
         coalesce(bybit.valid, false) AS bybit_valid
  FROM grid g
  LEFT JOIN raw_1m_binance_rows AS binance USING (timestamp_ms)
  LEFT JOIN raw_1m_bybit_rows   AS bybit   USING (timestamp_ms)
),
tiered AS (
  SELECT *,
         (binance_valid AND (binance_volume > 0 OR NOT (bybit_valid AND bybit_volume > 0))) AS use_binance,
         (NOT (binance_valid AND (binance_volume > 0 OR NOT (bybit_valid AND bybit_volume > 0))) AND bybit_valid) AS use_bybit
  FROM joined
),
chosen AS (
  SELECT timestamp_ms, binance_valid, bybit_valid,
         CASE WHEN use_binance THEN 'binance' WHEN use_bybit THEN 'bybit' ELSE 'ffill' END AS source,
         CASE WHEN use_binance THEN binance_volume = 0 WHEN use_bybit THEN bybit_volume = 0 ELSE false END AS zero_volume,
         CASE WHEN use_binance THEN binance_open WHEN use_bybit THEN bybit_open END AS chosen_open,
         CASE WHEN use_binance THEN binance_high WHEN use_bybit THEN bybit_high END AS chosen_high,
         CASE WHEN use_binance THEN binance_low WHEN use_bybit THEN bybit_low END AS chosen_low,
         CASE WHEN use_binance THEN binance_close WHEN use_bybit THEN bybit_close END AS chosen_close,
         CASE WHEN use_binance THEN binance_volume WHEN use_bybit THEN bybit_volume END AS chosen_volume,
         CASE WHEN binance_valid AND bybit_valid
              THEN abs(binance_close - bybit_close) / ((binance_close + bybit_close) / 2) END AS rel_divergence
  FROM tiered
),
filled AS (
  SELECT *,
         -- own close on candle rows, previous canonical close on ffill rows
         last_value(chosen_close IGNORE NULLS) OVER (
           ORDER BY timestamp_ms
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
         ) AS last_known_close
  FROM chosen
)
SELECT timestamp_ms,
       coalesce(chosen_open, last_known_close) AS open,
       coalesce(chosen_high, last_known_close) AS high,
       coalesce(chosen_low, last_known_close) AS low,
       coalesce(chosen_close, last_known_close) AS close,
       coalesce(chosen_volume, 0) AS volume,
       source,
       zero_volume,
       binance_valid,
       bybit_valid,
       rel_divergence
FROM filled
ORDER BY timestamp_ms;
"""

CSV_COLUMNS = "{'timestamp_ms':'BIGINT','open':'DOUBLE','high':'DOUBLE','low':'DOUBLE','close':'DOUBLE','volume':'DOUBLE'}"


def utc_midnight_ms(yyyymmdd: str) -> int:
    return int(datetime.strptime(yyyymmdd, "%Y%m%d").replace(tzinfo=UTC).timestamp() * config.MILLISECONDS_PER_SECOND)


def parse_zip(zip_path: Path) -> Iterator[tuple[int, str, str, str, str, str]]:
    """Yield (epoch_ms, open, high, low, close, volume) from one Lean minute ZIP."""
    midnight_ms = utc_midnight_ms(LEAN_DAY_ZIP_NAME_PATTERN.match(zip_path.name).group(1))
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(zf.namelist()[0]) as f:
            for row in csv.reader(io.TextIOWrapper(f, encoding="utf-8", newline="")):
                yield (midnight_ms + int(row[0]), row[1], row[2], row[3], row[4], row[5])


def write_venue_spool(ticker: str, venue: str, spool_csv: Path) -> int:
    """Write all of one asset's bars from one venue into a temp CSV; return the row count."""
    row_count = 0
    with spool_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        for zip_path in lean_day_zip_paths(config.raw_symbol_dir(ticker, venue)):
            for ts, o, h, lo, c, v in parse_zip(zip_path):
                w.writerow((ts, o, h, lo, c, v))
                row_count += 1
    return row_count


def main() -> int:
    args = config.build_ticker_parser("Lean ZIPs (both venues) -> the asset's DuckDB + primary-failover canonical series").parse_args()
    # one database per asset; its canonical grid ends at that asset's own raw maximum over both venues
    for ticker in config.parse_tickers(args.tickers):
        symbol = config.symbol(ticker)
        path = config.research_ohlcv_duckdb(ticker)
        path.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(path))
        con.execute(f"SET memory_limit='{config.DUCKDB_MEMORY_LIMIT}'")
        con.execute("SET threads=1")   # float summation must not be reordered
        con.execute("SET preserve_insertion_order=false")
        for venue in config.SOURCE_VENUES:
            con.execute(VENUE_DDL.format(venue=venue))
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as ntf:
                spool_csv = Path(ntf.name)
            try:
                venue_row_count = write_venue_spool(ticker, venue, spool_csv)
                con.execute(f"DELETE FROM ohlcv_1m_{venue}")
                con.execute(
                    f"INSERT INTO ohlcv_1m_{venue} SELECT * FROM read_csv('{spool_csv}', header=false, columns={CSV_COLUMNS})"
                )
                print(f"{venue} {symbol}: {venue_row_count} rows loaded", flush=True)
            finally:
                spool_csv.unlink(missing_ok=True)
        end_ms = con.execute(
            """SELECT max(timestamp_ms) FROM (SELECT timestamp_ms FROM ohlcv_1m_binance
                                              UNION ALL
                                              SELECT timestamp_ms FROM ohlcv_1m_bybit)"""
        ).fetchone()[0] + config.CANONICAL_GRID_INTERVAL_MS
        con.execute(CANONICAL_DDL)
        con.execute("DELETE FROM ohlcv_1m_canonical")
        con.execute(
            CANONICAL_INSERT.format(
                start_ms=config.DATA_WINDOW_START_MS, end_ms=end_ms,
                step_ms=config.CANONICAL_GRID_INTERVAL_MS, ohlc_intact_predicate=OHLC_INTACT_PREDICATE
            )
        )
        canonical_row_count = con.execute("SELECT count(*) FROM ohlcv_1m_canonical").fetchone()[0]
        con.close()
        print(f"canonical {symbol}: {canonical_row_count} rows in {path.name} (window start {config.DATA_WINDOW_START_UTC})", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
