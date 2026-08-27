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
# Tier order: traded Binance > traded Bybit > no-trade Binance > no-trade Bybit
# > forward fill. use_b collapses tiers 1 and 3: Binance wins whenever it is
# valid and either traded or the Bybit candle did not trade either.
CANONICAL_INSERT = """
INSERT INTO ohlcv_1m_canonical
WITH
b AS (
  SELECT timestamp_ms, open, high, low, close, volume,
         (isfinite(open) AND isfinite(high) AND isfinite(low)
          AND isfinite(close) AND isfinite(volume)
          AND open > 0 AND high > 0 AND low > 0 AND close > 0 AND volume >= 0
          AND low <= least(open, close) AND high >= greatest(open, close)) AS valid
  FROM ohlcv_1m_binance WHERE symbol = '{sym}'
),
y AS (
  SELECT timestamp_ms, open, high, low, close, volume,
         (isfinite(open) AND isfinite(high) AND isfinite(low)
          AND isfinite(close) AND isfinite(volume)
          AND open > 0 AND high > 0 AND low > 0 AND close > 0 AND volume >= 0
          AND low <= least(open, close) AND high >= greatest(open, close)) AS valid
  FROM ohlcv_1m_bybit WHERE symbol = '{sym}'
),
grid AS (
  SELECT t AS timestamp_ms FROM range({start_ms}, {end_ms}, {step_ms}) r(t)
),
joined AS (
  SELECT g.timestamp_ms,
         b.open AS o_b, b.high AS h_b, b.low AS l_b, b.close AS c_b, b.volume AS v_b,
         coalesce(b.valid, false) AS b_valid,
         y.open AS o_y, y.high AS h_y, y.low AS l_y, y.close AS c_y, y.volume AS v_y,
         coalesce(y.valid, false) AS y_valid
  FROM grid g
  LEFT JOIN b USING (timestamp_ms)
  LEFT JOIN y USING (timestamp_ms)
),
tiered AS (
  SELECT *,
         (b_valid AND (v_b > 0 OR NOT (y_valid AND v_y > 0))) AS use_b,
         (NOT (b_valid AND (v_b > 0 OR NOT (y_valid AND v_y > 0))) AND y_valid) AS use_y
  FROM joined
),
chosen AS (
  SELECT timestamp_ms, b_valid, y_valid,
         CASE WHEN use_b THEN 'binance' WHEN use_y THEN 'bybit' ELSE 'ffill' END AS source,
         CASE WHEN use_b THEN v_b = 0 WHEN use_y THEN v_y = 0 ELSE false END AS zero_volume,
         CASE WHEN use_b THEN o_b WHEN use_y THEN o_y END AS o_c,
         CASE WHEN use_b THEN h_b WHEN use_y THEN h_y END AS h_c,
         CASE WHEN use_b THEN l_b WHEN use_y THEN l_y END AS l_c,
         CASE WHEN use_b THEN c_b WHEN use_y THEN c_y END AS c_c,
         CASE WHEN use_b THEN v_b WHEN use_y THEN v_y END AS v_c,
         CASE WHEN b_valid AND y_valid
              THEN abs(c_b - c_y) / ((c_b + c_y) / 2) END AS rel_divergence
  FROM tiered
),
filled AS (
  SELECT *,
         -- own close on candle rows, previous canonical close on ffill rows
         last_value(c_c IGNORE NULLS) OVER (
           ORDER BY timestamp_ms
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
         ) AS c_known
  FROM chosen
)
SELECT '{sym}' AS symbol,
       timestamp_ms,
       coalesce(o_c, c_known) AS open,
       coalesce(h_c, c_known) AS high,
       coalesce(l_c, c_known) AS low,
       coalesce(c_c, c_known) AS close,
       coalesce(v_c, 0)       AS volume,
       source,
       zero_volume,
       b_valid AS binance_valid,
       y_valid AS bybit_valid,
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


def spool_symbol(ticker: str, venue: str, tmp: Path) -> int:
    """Write all of one symbol's bars from one venue into a temp CSV; return the row count."""
    sym = config.symbol(ticker)
    n = 0
    with tmp.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        for zp in iter_zip_paths(config.raw_symbol_dir(ticker, venue)):
            for ts, o, h, lo, c, v in parse_zip(zp):
                w.writerow((sym, ts, o, h, lo, c, v))
                n += 1
    return n


def main() -> int:
    ap = config.ticker_parser("Lean ZIPs (both venues) -> DuckDB + canonical fused series")
    args = ap.parse_args()
    tickers = config.parse_tickers(args.tickers)

    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(config.DB_PATH))
    # small-host safety: spill early instead of hitting the allocator ceiling
    con.execute("SET memory_limit='4GB'")
    con.execute("SET threads=2")
    con.execute("SET preserve_insertion_order=false")
    for venue in config.VENUES:
        con.execute(VENUE_DDL.format(venue=venue))
        for t in tickers:
            sym = config.symbol(t)
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as ntf:
                tmp = Path(ntf.name)
            try:
                n = spool_symbol(t, venue, tmp)
                con.execute(f"DELETE FROM ohlcv_1m_{venue} WHERE symbol = ?", [sym])
                con.execute(
                    f"INSERT INTO ohlcv_1m_{venue} SELECT * FROM read_csv('{tmp}', header=false, columns={CSV_COLUMNS})"
                )
                print(f"{venue} {sym}: {n} rows loaded", flush=True)
            finally:
                tmp.unlink(missing_ok=True)
    end_ms = con.execute(
        """SELECT max(timestamp_ms) FROM (SELECT timestamp_ms FROM ohlcv_1m_binance
                                          UNION ALL
                                          SELECT timestamp_ms FROM ohlcv_1m_bybit)"""
    ).fetchone()[0] + config.GRID_STEP_MS
    old_cols = {
        r[0]
        for r in con.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'ohlcv_1m_canonical'"
        ).fetchall()
    }
    if old_cols and "source" not in old_cols:  # pre-failover schema: rebuild from scratch
        con.execute("DROP TABLE ohlcv_1m_canonical")
    con.execute(CANONICAL_DDL)
    for t in tickers:
        sym = config.symbol(t)
        con.execute("DELETE FROM ohlcv_1m_canonical WHERE symbol = ?", [sym])
        con.execute(
            CANONICAL_INSERT.format(
                sym=sym, start_ms=config.START_MS, end_ms=end_ms, step_ms=config.GRID_STEP_MS
            )
        )
        print(f"canonical {sym}: rebuilt", flush=True)
    n = con.execute("SELECT count(*) FROM ohlcv_1m_canonical").fetchone()[0]
    print(f"ohlcv_1m_canonical: {n} rows (window start {config.START_UTC})", flush=True)
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
