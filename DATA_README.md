**IMPORTANT: TO KEEP DATA GAPS OUT OF THE ML LAYER AND MAINTAIN HIGH DATA
QUALITY WITHOUT INVENTING EXTRA TECHNIQUES AND WORKAROUNDS, WE COMBINE
1-MINUTE DATA FROM TWO EXCHANGES — BINANCE AND BYBIT — IN A SINGLE DATABASE,
USING THE QUANTCONNECT LEAN DATA FORMAT. AS A RESULT, ML MODELS CONSUME ONE
CANONICAL, CONTINUOUS DATA SERIES.**

# DATA_README — Canonical 1m OHLCV Database

How `db/1m_raw_data_db.duckdb` and the per-asset Parquet files are created:
sources and endpoints, units and time, the canonical source-priority
definition, the schema and the known limitations.

## 1. Methodology — primary-failover consolidation (v2)

Raw one-minute OHLCV observations from Binance USDS-M and Bybit Linear USDT
perpetual markets are synchronized to a common UTC one-minute grid and
consolidated into a single canonical market series. **Every canonical bar is
one venue's candle copied verbatim** — prices and volume of a single exchange,
never a blend: per minute, the highest-priority existing tier wins (traded
Binance candle, then traded Bybit candle, then a valid no-trade candle from
either venue in the same order), and only a minute with no valid candle on
both venues is a canonical gap, deterministically forward-filled with the
previous canonical close and zero volume. Data-source shares, source
switches, the largest move at a switch, cross-exchange divergence and every
other integrity anomaly are recorded by the DATA INGEST quality-monitoring
layer and exposed through the project dashboard. Consequently, downstream
indicator calculation and ML pipelines operate exclusively on a continuous
canonical t,O,H,L,C,V series whose every printed price existed on a real
exchange, and require no exchange-specific gap-handling logic.

## 2. Sources & endpoints

**Binance USDS-M futures** — `GET https://fapi.binance.com/fapi/v1/klines`
with `symbol=<SYM>USDT`, `interval=1m`, `startTime`/`endTime` bounding one full
UTC day, `limit=1500` (one request per day). A kline row is `[openTime, open,
high, low, close, volume, closeTime, quoteVolume, ...]`; **columns 0–5** are
kept — the bar-open timestamp, four prices and the **base-asset volume**.
Before any download the oldest candle of every symbol is probed
(`startTime=0&limit=1`); the run aborts if any listing is younger than the
window start, which guarantees full Binance coverage of the window. An empty
response for a post-listing day aborts the run instead of persisting a
skip-forever empty ZIP.

**Bybit linear perpetuals** — `GET https://api.bybit.com/v5/market/kline` with
`category=linear` (trade klines — **not** mark-price or index-price klines),
`symbol=<SYM>USDT`, `interval=1`, `start`/`end`, `limit=1000`; one UTC day =
two 720-minute windows. A row is `[start, open, high, low, close, volume,
turnover]`; **columns 0–5** are kept. `volume` for linear contracts is the
base-asset quantity (contract multiplier 1) — verified against Binance:
per-symbol total-volume ratios are 0.07–0.37, i.e. the same unit. The list is
returned newest-first and is sorted ascending before writing. A day with no
data (before the symbol's Bybit listing) is stored as a ZIP with an empty CSV,
so the question is asked once and never again.

Both downloaders write identical QC Lean-exact day ZIPs
(`YYYYMMDD_trade.zip` → `YYYYMMDD_<symbol>_minute_trade_perp.csv`, headerless
`offset_ms_from_utc_midnight,open,high,low,close,volume`) into
`raw_downloaded_1m_data/cryptofuture/<venue>/minute/<symbol>/` — verified
byte-identical against an independent production downloader, including a
re-download of a historical day (exchanges do not restate klines).

## 3. Units & time

UTC everywhere; timestamps are **bar OPEN** epoch milliseconds on a strict
60 000 ms grid; the data window is `2021-01-01 00:00 UTC` (inclusive) to the
most recent UTC midnight (exclusive); volume is **base-asset volume**, never
quote turnover; the unit of download work is one full UTC day = one ZIP
(idempotent backfill and top-up with the same command). Prices and volumes
are stored exactly as the exchanges printed them — no rounding at any layer.

## 4. Canonical source priority

A venue candle is **valid** when all values are finite, prices are positive,
volume is non-negative and the OHLC ordering holds
(`low <= min(open, close) <= max(open, close) <= high`). For every minute of
the grid the first existing tier wins:

| Tier | Condition | `source` |
|---|---|---|
| 1 | Binance candle valid, `volume > 0` | `binance` |
| 2 | Bybit candle valid, `volume > 0` | `bybit` |
| 3 | Binance candle valid, `volume = 0` | `binance` (+ `zero_volume`) |
| 4 | Bybit candle valid, `volume = 0` | `bybit` (+ `zero_volume`) |
| 5 | none of the above | `ffill`: `O = H = L = C =` previous canonical close, `V = 0` |

Properties:

- A traded candle on either venue outranks a no-trade candle (an exchange
  maintenance placeholder on Binance never outranks a real Bybit minute);
  a valid no-trade candle still outranks fabrication.
- Prices and volume are **copied verbatim** from the winning venue — no
  weighting, no averaging, no rounding. Every canonical price existed on a
  real exchange, so cross-venue "phantom returns" are zero by construction.
- The only place a cross-venue basis difference can enter the series is a
  minute whose source differs from the previous minute — monitored as
  `source_switches` and `max_abs_ret_at_switch` per symbol.
- `rel_divergence` (`|c_bin − c_byb| / mid` when both candles are valid) is a
  **data-quality signal only** — it is never a model feature.
- Rows before a symbol's first valid candle would stay NULL; the Binance
  listing probe pins this to zero and the export invariants enforce it.

## 5. Database schema

`ohlcv_1m_binance` and `ohlcv_1m_bybit` — raw, verbatim from the ZIP trees:

| column | type | meaning |
|---|---|---|
| `symbol` | VARCHAR | e.g. `BTCUSDT` |
| `timestamp_ms` | BIGINT | bar OPEN, UTC epoch ms, 60 000 ms grid |
| `open, high, low, close` | DOUBLE | venue trade prices |
| `volume` | DOUBLE | base-asset volume of that venue |

`ohlcv_1m_canonical` — the primary-failover series, rebuilt deterministically
per symbol on every `make ingest`; what exports and ML read:

| column | type | meaning |
|---|---|---|
| `symbol` | VARCHAR | asset symbol |
| `timestamp_ms` | BIGINT | bar OPEN, UTC epoch ms; full grid, no missing minutes |
| `open, high, low, close` | DOUBLE | verbatim venue prices (ffill rows: previous close) |
| `volume` | DOUBLE | verbatim venue volume (0 on ffill rows) |
| `source` | VARCHAR | `binance` / `bybit` / `ffill` |
| `zero_volume` | BOOLEAN | tier 3/4: valid candle without trades |
| `binance_valid`, `bybit_valid` | BOOLEAN | candle present with intact OHLC |
| `rel_divergence` | DOUBLE | cross-venue close divergence when both valid (QC only) |

**Exports**: `assets/Asset_<TICKER>/1m_<TICKER>_data.parquet` (zstd) carries
only `timestamp_ms, open, high, low, close, volume` — identical row counts for
every asset (full grid), continuous, no NULLs. Export is **fail-closed**: the
Parquet is written to a temp file and replaced only after asserting the full
grid row count, distinct on-grid timestamps, no NULL / non-finite values and
intact OHLC on every row; a failing assertion leaves the previous file
untouched. **Semantics: a canonical primary-failover series, not raw exchange
data of a single venue.** Use it for ML and indicators; for Lean backtests use
the per-venue raw ZIP trees. The whole database is a pure function of the two
raw trees: rebuilding from a clean `db/` reproduces bit-identical Parquet
files.

## 6. Known limitations

- **Single-venue minutes have nothing to fail over to.** When only one venue
  is listed and that venue prints a no-trade candle, the canonical bar is that
  candle (flagged `zero_volume`); when it prints nothing, the bar is a forward
  fill.
- **Source switches carry the cross-venue basis.** A switch between venues can
  move the canonical close by the current Binance–Bybit basis without either
  venue moving; the count and the largest such move are monitored per symbol
  (`source_switches`, `max_abs_ret_at_switch`). No smoothing is applied — the
  switch is visible, not hidden.
- **No cross-exchange divergence cutoff.** Strongly diverging minutes are real
  market dislocations; the per-symbol distribution (mean / p99 / max) is
  exposed in monitoring.

## 7. Changelog

- **v2 (2026-08-26, WO-ML-001 v2).** The v1 canonical series was a per-minute
  notional-weighted index of both venues. Measured on the full window it
  produced weight-shift "phantom returns" up to 7.8 % in one minute (SOL,
  2022-11-09) — moves no venue printed — and rounded prices to present-day
  tick sizes. Replaced by the primary-failover definition above: verbatim
  venue candles, no weighting, no rounding, phantom returns zero by
  construction; `max_phantom_ret` monitoring retired, `source_switches` /
  `max_abs_ret_at_switch` added.
- **v1 (2026-08-26).** Notional-weighted two-venue index (superseded).
