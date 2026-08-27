"""Load both venue ZIP trees into DuckDB and rebuild the canonical series.

Per venue and symbol: parse all day-ZIPs, spool rows into a temporary CSV with
absolute timestamps, then DELETE + INSERT ... SELECT FROM read_csv (bulk load,
idempotent re-runs). Timestamps are bar OPEN, UTC epoch ms, on a 60000 ms grid.

The canonical table ohlcv_1m_canonical is a PRIMARY-FAILOVER series (full text
in DATA_README.md): every canonical bar is ONE venue's candle copied verbatim —
no weighting, no rounding. Per minute, the first existing tier wins:
  1. Binance candle, OHLC intact, volume > 0
  2. Bybit candle,   OHLC intact, volume > 0
  3. Binance candle, OHLC intact, volume = 0   (zero_volume flag)
  4. Bybit candle,   OHLC intact, volume = 0   (zero_volume flag)
  5. none            -> ffill: O=H=L=C = previous canonical close, V = 0
OHLC intact means finite values, positive prices, non-negative volume and
low <= min(open, close) <= max(open, close) <= high. A traded candle on either
venue outranks a no-trade candle; a no-trade candle outranks fabrication.
rel_divergence (|c_bin - c_byb| / mid when both candles are valid) is kept as a
data-quality signal only.
"""

from __future__ import annotations

import csv
import io
import re
import tempfile
import zipfile
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from . import config

ZIP_NAME_RE = re.compile(r"^(\d{8})_trade\.zip$")

VENUE_DDL = """
CREATE TABLE IF NOT EXISTS ohlcv_1m_{venue} (
  symbol       VARCHAR NOT NULL,
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
  symbol       VARCHAR NOT NULL,
  timestamp_ms BIGINT  NOT NULL,   -- full grid: every minute of the window
  open   DOUBLE,
  high   DOUBLE,
  low    DOUBLE,
  close  DOUBLE,
  volume DOUBLE,                   -- verbatim venue volume (0 on ffill rows)
  source         VARCHAR,          -- 'binance' / 'bybit' / 'ffill'
  zero_volume    BOOLEAN,          -- tier 3/4: valid candle without trades
  binance_valid  BOOLEAN,          -- Binance row present with intact OHLC
  bybit_valid    BOOLEAN,          -- Bybit row present with intact OHLC
  rel_divergence DOUBLE            -- |c_bin - c_byb| / mid when both valid (QC only)
);
"""

# ~3M-row build per symbol keeps memory bounded on small hosts; end_ms is the
# shared global grid end so every symbol covers the identical window.
OHLC_INTACT = """(isfinite(open) AND isfinite(high) AND isfinite(low)
          AND isfinite(close) AND isfinite(volume)
          AND open > 0 AND high > 0 AND low > 0 AND close > 0 AND volume >= 0
          AND low <= least(open, close) AND high >= greatest(open, close))"""

# Tier order: traded Binance > traded Bybit > no-trade Binance > no-trade Bybit
# > forward fill. use_binance collapses tiers 1 and 3: Binance wins whenever it is
# valid and either traded or the Bybit candle did not trade either.
CANONICAL_INSERT = """
INSERT INTO ohlcv_1m_canonical
WITH
raw_1m_binance_rows AS (
  SELECT timestamp_ms, open, high, low, close, volume,
         {ohlc_intact} AS valid
  FROM ohlcv_1m_binance WHERE symbol = '{sym}'
),
raw_1m_bybit_rows AS (
  SELECT timestamp_ms, open, high, low, close, volume,
         {ohlc_intact} AS valid
  FROM ohlcv_1m_bybit WHERE symbol = '{sym}'
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
SELECT '{sym}' AS symbol,
       timestamp_ms,
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

CSV_COLUMNS = (
    "{'symbol':'VARCHAR','timestamp_ms':'BIGINT','open':'DOUBLE',"
    "'high':'DOUBLE','low':'DOUBLE','close':'DOUBLE','volume':'DOUBLE'}"
)


def utc_midnight_ms(yyyymmdd: str) -> int:
    return int(datetime.strptime(yyyymmdd, "%Y%m%d").replace(tzinfo=UTC).timestamp() * 1000)


def iter_zip_paths(zip_dir: Path) -> list[Path]:
    return [p for _, p in sorted((p.name[:8], p) for p in zip_dir.glob("*_trade.zip") if ZIP_NAME_RE.match(p.name))]


def parse_zip(zip_path: Path) -> Iterator[tuple[int, str, str, str, str, str]]:
    """Yield (epoch_ms, open, high, low, close, volume) from one Lean minute ZIP."""
    midnight_ms = utc_midnight_ms(ZIP_NAME_RE.match(zip_path.name).group(1))
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        if len(names) != 1:
            raise ValueError(f"{zip_path}: expected 1 CSV inside, got {len(names)}")
        with zf.open(names[0]) as f:
            for row in csv.reader(io.TextIOWrapper(f, encoding="utf-8", newline="")):
                if len(row) != 6:
                    raise ValueError(f"{zip_path}: expected 6 columns, got {len(row)}")
                yield (midnight_ms + int(row[0]), row[1], row[2], row[3], row[4], row[5])


def spool_symbol(ticker: str, venue: str, spool_csv: Path) -> int:
    """Write all of one symbol's bars from one venue into a temp CSV; return the row count."""
    sym = config.symbol(ticker)
    row_count = 0
    with spool_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        for zip_path in iter_zip_paths(config.raw_symbol_dir(ticker, venue)):
            for ts, o, h, lo, c, v in parse_zip(zip_path):
                w.writerow((sym, ts, o, h, lo, c, v))
                row_count += 1
    return row_count


def main() -> int:
    ap = config.ticker_parser("Lean ZIPs (both venues) -> DuckDB + primary-failover canonical series")
    args = ap.parse_args()
    tickers = config.parse_tickers(args.tickers)
    # The canonical grid ends at the global maximum of the raw tables, so
    # rebuilding a subset leaves the other symbols on an older horizon — one
    # database with different observation windows per asset. Acquisition may be
    # per ticker; the canonical dataset is defined for the basket as a whole.
    if set(tickers) != set(config.TICKERS):
        raise SystemExit("canonical ingest is basket-wide — run `make ingest`")

    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(config.DB_PATH))
    # small-host safety: spill early instead of hitting the allocator ceiling
    con.execute("SET memory_limit='4GB'")
    con.execute("SET threads=1")   # float summation must not be reordered
    con.execute("SET preserve_insertion_order=false")
    for venue in config.SOURCE_VENUES:
        con.execute(VENUE_DDL.format(venue=venue))
        for t in tickers:
            sym = config.symbol(t)
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as ntf:
                spool_csv = Path(ntf.name)
            try:
                row_count = spool_symbol(t, venue, spool_csv)
                con.execute(f"DELETE FROM ohlcv_1m_{venue} WHERE symbol = ?", [sym])
                con.execute(
                    f"INSERT INTO ohlcv_1m_{venue} SELECT * FROM read_csv('{spool_csv}', header=false, columns={CSV_COLUMNS})"
                )
                print(f"{venue} {sym}: {row_count} rows loaded", flush=True)
            finally:
                spool_csv.unlink(missing_ok=True)
    end_ms = con.execute(
        """SELECT max(timestamp_ms) FROM (SELECT timestamp_ms FROM ohlcv_1m_binance
                                          UNION ALL
                                          SELECT timestamp_ms FROM ohlcv_1m_bybit)"""
    ).fetchone()[0] + config.CANONICAL_GRID_INTERVAL_MS
    con.execute(CANONICAL_DDL)
    for t in tickers:
        sym = config.symbol(t)
        con.execute("DELETE FROM ohlcv_1m_canonical WHERE symbol = ?", [sym])
        con.execute(
            CANONICAL_INSERT.format(
                sym=sym, start_ms=config.DATA_WINDOW_START_MS, end_ms=end_ms,
                step_ms=config.CANONICAL_GRID_INTERVAL_MS, ohlc_intact=OHLC_INTACT
            )
        )
        print(f"canonical {sym}: rebuilt", flush=True)
    row_count = con.execute("SELECT count(*) FROM ohlcv_1m_canonical").fetchone()[0]
    print(f"ohlcv_1m_canonical: {row_count} rows (window start {config.DATA_WINDOW_START_UTC})", flush=True)
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
