"""Load both venue ZIP trees into DuckDB and rebuild the canonical fused series.

Per venue and symbol: parse all day-ZIPs, spool rows into a temporary CSV with
absolute timestamps, then DELETE + INSERT ... SELECT FROM read_csv (bulk load,
idempotent re-runs). Timestamps are bar OPEN, UTC epoch ms, on a 60000 ms grid.

The canonical table ohlcv_1m_canonical implements the cross-exchange
consolidation methodology (full text in DATA_README.md):
  - common per-symbol minute grid from the window start to the newest candle;
  - a source is a venue that actually TRADED that minute: volume > 0 and
    intact OHLC invariants (maintenance placeholders and broken bars are not
    sources — they contribute neither price nor volume);
  - venue OHLC weighted by the USDT notional (dollar-volume) proxy
    q = close * base_volume; one source -> unit weight;
  - base volumes are summed across venues;
  - no source at all -> canonical gap, forward-filled with the previous
    fused close and zero volume (is_ffill = true);
  - rows before the first observation stay NULL (leading edge, monitored as
    leading_null and expected to be zero thanks to the Binance listing probe).
"""

from __future__ import annotations

import argparse
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
  volume DOUBLE,                   -- sum of venue base volumes (0 on gaps)
  src_count      TINYINT,          -- 0, 1 or 2 venues present
  is_ffill       BOOLEAN,          -- true on forward-filled canonical gaps
  rel_divergence DOUBLE,           -- |c_bin - c_byb| / mid, when both present
  w_binance      DOUBLE            -- Binance weight actually used
);
"""

# ~3M-row build per symbol keeps memory bounded on small hosts; end_ms is the
# shared global grid end so every symbol covers the identical window.
CANONICAL_INSERT = """
INSERT INTO ohlcv_1m_canonical
WITH
-- USDT notional (dollar-volume) proxy per venue-minute: q = close * base_volume
b AS (
  SELECT timestamp_ms, open, high, low, close, volume,
         close * volume AS notional
  FROM ohlcv_1m_binance
  WHERE symbol = '{sym}'
    AND volume > 0                           -- a source is a venue that TRADED:
    AND high >= greatest(open, close, low)   -- zero-volume placeholders and bars
    AND low  <= least(open, close, high)     -- with broken OHLC are not sources
),
y AS (
  SELECT timestamp_ms, open, high, low, close, volume,
         close * volume AS notional
  FROM ohlcv_1m_bybit
  WHERE symbol = '{sym}'
    AND volume > 0
    AND high >= greatest(open, close, low)
    AND low  <= least(open, close, high)
),
grid AS (
  SELECT t AS timestamp_ms FROM range({start_ms}, {end_ms}, {step_ms}) r(t)
),
joined AS (
  SELECT g.timestamp_ms,
         b.open AS o_b, b.high AS h_b, b.low AS l_b, b.close AS c_b,
         b.volume AS v_b, b.notional AS q_b,
         y.open AS o_y, y.high AS h_y, y.low AS l_y, y.close AS c_y,
         y.volume AS v_y, y.notional AS q_y,
         (b.close IS NOT NULL)::TINYINT + (y.close IS NOT NULL)::TINYINT AS src_count
  FROM grid g
  LEFT JOIN b USING (timestamp_ms)
  LEFT JOIN y USING (timestamp_ms)
),
weighted AS (
  SELECT *,
         CASE
           WHEN src_count = 2 THEN
             CASE WHEN q_b + q_y > 0 THEN q_b / (q_b + q_y)
                  ELSE 0.5   -- both present, both notionals zero: equal split
             END
           WHEN src_count = 1 AND c_b IS NOT NULL THEN 1.0
           WHEN src_count = 1                     THEN 0.0
           -- src_count = 0 -> NULL (canonical gap, forward-filled below)
         END AS w_binance
  FROM joined
),
fused AS (
  SELECT timestamp_ms, src_count, w_binance,
         CASE WHEN src_count = 2 THEN w_binance * o_b + (1 - w_binance) * o_y
              WHEN src_count = 1 THEN coalesce(o_b, o_y) END AS o_f,
         CASE WHEN src_count = 2 THEN w_binance * h_b + (1 - w_binance) * h_y
              WHEN src_count = 1 THEN coalesce(h_b, h_y) END AS h_f,
         CASE WHEN src_count = 2 THEN w_binance * l_b + (1 - w_binance) * l_y
              WHEN src_count = 1 THEN coalesce(l_b, l_y) END AS l_f,
         CASE WHEN src_count = 2 THEN w_binance * c_b + (1 - w_binance) * c_y
              WHEN src_count = 1 THEN coalesce(c_b, c_y) END AS c_f,
         CASE WHEN src_count > 0 THEN coalesce(v_b, 0) + coalesce(v_y, 0) END AS v_f,
         CASE WHEN src_count = 2
              THEN abs(c_b - c_y) / ((c_b + c_y) / 2) END AS rel_divergence
  FROM weighted
),
filled AS (
  SELECT *,
         -- own close on data rows, previous known fused close on gap rows
         last_value(c_f IGNORE NULLS) OVER (
           ORDER BY timestamp_ms
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
         ) AS c_known
  FROM fused
)
SELECT '{sym}' AS symbol,
       timestamp_ms,
       round(coalesce(o_f, c_known), {pdec}) AS open,
       round(coalesce(h_f, c_known), {pdec}) AS high,
       round(coalesce(l_f, c_known), {pdec}) AS low,
       round(coalesce(c_f, c_known), {pdec}) AS close,
       round(coalesce(v_f, 0), {vdec})       AS volume,     -- gap rows: zero volume
       src_count::TINYINT     AS src_count,
       (src_count = 0 AND c_known IS NOT NULL) AS is_ffill,
       rel_divergence,
       w_binance
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
    ap = argparse.ArgumentParser(description="Lean ZIPs (both venues) -> DuckDB + canonical fused series")
    ap.add_argument("--tickers", default=",".join(config.TICKERS), help="comma-separated subset")
    args = ap.parse_args()
    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]

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
    con.execute(CANONICAL_DDL)
    for t in tickers:
        sym = config.symbol(t)
        con.execute("DELETE FROM ohlcv_1m_canonical WHERE symbol = ?", [sym])
        con.execute(
            CANONICAL_INSERT.format(
                sym=sym, start_ms=config.START_MS, end_ms=end_ms, step_ms=config.GRID_STEP_MS,
                pdec=config.PRICE_DECIMALS[t], vdec=config.VOLUME_DECIMALS,
            )
        )
        print(f"canonical {sym}: rebuilt", flush=True)
    n = con.execute("SELECT count(*) FROM ohlcv_1m_canonical").fetchone()[0]
    print(f"ohlcv_1m_canonical: {n} rows (window start {config.START_UTC})", flush=True)
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
