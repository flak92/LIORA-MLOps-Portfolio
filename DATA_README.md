**IMPORTANT: TO KEEP DATA GAPS OUT OF THE ML LAYER AND MAINTAIN HIGH DATA
QUALITY WITHOUT INVENTING EXTRA TECHNIQUES AND WORKAROUNDS, WE COMBINE
1-MINUTE DATA FROM TWO EXCHANGES — BINANCE AND BYBIT — IN A SINGLE DATABASE,
USING THE QUANTCONNECT LEAN DATA FORMAT. AS A RESULT, ML MODELS CONSUME ONE
CANONICAL, CONTINUOUS DATA SERIES.**

# DATA_README — Canonical 1m OHLCV Database

How `db/1m_raw_data_db.duckdb` and the per-asset Parquet files are created:
sources and endpoints, units and time, the fusion definition, the schema and
the known v1 limitations.

## 1. Methodology — Cross-Exchange OHLCV Consolidation

Raw one-minute OHLCV observations from Binance USDS-M and Bybit Linear USDT
perpetual markets are synchronized to a common UTC one-minute grid and
consolidated into a single canonical market series. Following cross-exchange
cryptocurrency aggregation methodologies in the literature, venue prices are
weighted by their relative trading activity. For each minute, the Binance and
Bybit open, high, low and close observations are aggregated using weights
proportional to the **USDT notional (dollar-volume) proxy** `q = close x
base_volume` computed per venue and minute. Base-asset trading volumes are
summed across both venues. If an observation is unavailable from one venue, the
available venue receives unit weight. Only simultaneous absence from both
venues constitutes a canonical data gap; such observations are deterministically
forward-filled using the previous close with zero volume. Data-source
availability, cross-exchange price divergence, duplicates and other integrity
anomalies are recorded by the DATA INGEST quality-monitoring layer and exposed
through the project dashboard. Consequently, downstream indicator calculation
and XGBoost/LSTM pipelines operate exclusively on a continuous canonical
t,O,H,L,C,V series and require no exchange-specific gap-handling logic.
(Volume-weighted cross-venue aggregation in the spirit of published crypto
reference-rate methodologies such as the CME CF Reference Rates and Coin
Metrics Reference Rates.)

## 2. Sources & endpoints

**Binance USDS-M futures** — `GET https://fapi.binance.com/fapi/v1/klines`
with `symbol=<SYM>USDT`, `interval=1m`, `startTime`/`endTime` bounding one full
UTC day, `limit=1500` (one request per day). A kline row is `[openTime, open,
high, low, close, volume, closeTime, quoteVolume, ...]`; **columns 0–5** are
kept — the bar-open timestamp, four prices and the **base-asset volume**.
Before any download the oldest candle of every symbol is probed
(`startTime=0&limit=1`); the run aborts if any listing is younger than the
window start, which guarantees full Binance coverage of the window.

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
60 000 ms grid; the window is `2021-01-01 00:00 UTC` (inclusive) to the most
recent UTC midnight (exclusive); volume is **base-asset volume**, never quote
turnover; the unit of download work is one full UTC day = one ZIP (idempotent
backfill and top-up with the same command).

## 4. Fusion

**A source is a venue that actually traded**: a bar counts only if it has
`volume > 0` and intact OHLC invariants (`high >= max(open, close, low)`,
`low <= min(open, close, high)`). Zero-volume bars — maintenance placeholders
or simply minutes without trades — and OHLC-broken bars are not sources; they
contribute neither price nor volume.

| case | weight w (Binance) | O/H/L/C | volume |
|---|---|---|---|
| both venues traded | `q_bin / (q_bin + q_byb)` | `w*x_bin + (1-w)*x_byb` | `v_bin + v_byb` |
| one venue traded | `1.0` / `0.0` | that venue verbatim | that venue |
| no venue traded (canonical gap) | n/a (NULL) | previous fused close (all four) | `0`, `is_ffill=true` |

`q = close x base_volume` is the USDT notional (dollar-volume) proxy per venue
and minute. Properties:

- The **same weight `w` is applied to all four price columns**, so the OHLC
  ordering invariants survive by construction (and survive rounding, which is
  monotonic). Canonical H/L are therefore weighted means of the venue extremes
  — **index semantics**, not a cross-venue max/min.
- **Volume is always the sum**, never an average — no artificial level shift
  when the second venue starts trading.
- Weights are per-minute, computed only from that minute's bars — no
  lookahead, no full-sample fitting. A venue enters with small volume, so its
  weight rises continuously from ~0: at every symbol's boundary minute the
  canonical return differs from the pure-Binance return by at most 2.8e-05
  (typical cross-venue basis is ~1e-3).
- Since both-venue bars have `q > 0` by definition, the weight denominator is
  never zero.
- Forward-fill uses the previous **fused** close; rows before a symbol's first
  observation stay NULL and are monitored as `leading_null` (pinned to 0 by
  the Binance listing probe).
- Canonical prices are rounded to the coarser venue tick's decimals + 1 guard
  digit (per symbol, ticks probed 2026-08-26); volumes to 3 decimals. Raw
  venue tables are never rounded.

**Boundary table** — first minute with both venues trading, per symbol (BTC
and LINK trade on Bybit from the window start):

| symbol | first both-venue minute (UTC) | | symbol | first both-venue minute (UTC) |
|---|---|---|---|---|
| BTCUSDT | 2021-01-01 00:00 | | TRXUSDT | 2021-08-31 13:14 |
| ETHUSDT | 2021-03-15 00:00 | | DOGEUSDT | 2021-06-02 10:44 |
| BNBUSDT | 2021-06-29 07:18 | | ZECUSDT | 2021-11-24 07:46 |
| XRPUSDT | 2021-05-13 09:34 | | LINKUSDT | 2021-01-01 00:00 |
| SOLUSDT | 2021-10-15 00:00 | | ADAUSDT | 2021-03-18 07:53 |

Reference points found in the data: during the synchronized Binance Futures
maintenance window (59 minutes from 2021-03-02 01:01 UTC, all 10 symbols) the
canonical BTC series switches to Bybit entirely (`w_binance = 0`, real volume,
zero flat bars); the largest cross-venue divergences are the 2021-05-19 crash
(LINK/ADA/ETH) and the FTX collapse on 2022-11-09 (SOL) — real market
dislocations on both venues, not data errors.

## 5. Database schema

`ohlcv_1m_binance` and `ohlcv_1m_bybit` — raw, verbatim from the ZIP trees:

| column | type | meaning |
|---|---|---|
| `symbol` | VARCHAR | e.g. `BTCUSDT` |
| `timestamp_ms` | BIGINT | bar OPEN, UTC epoch ms, 60 000 ms grid |
| `open, high, low, close` | DOUBLE | venue trade prices |
| `volume` | DOUBLE | base-asset volume of that venue |

`ohlcv_1m_canonical` — the fused series, rebuilt deterministically per symbol
on every `make ingest`; what exports and ML read:

| column | type | meaning |
|---|---|---|
| `symbol` | VARCHAR | asset symbol |
| `timestamp_ms` | BIGINT | bar OPEN, UTC epoch ms; full grid, no missing minutes |
| `open, high, low, close` | DOUBLE | notional-weighted cross-exchange prices, tick-rounded |
| `volume` | DOUBLE | sum of venue base volumes (0 on forward-filled gaps) |
| `src_count` | TINYINT | venues that actually traded that minute (0, 1, 2) |
| `is_ffill` | BOOLEAN | true on forward-filled canonical gaps (`src_count = 0`) |
| `rel_divergence` | DOUBLE | `abs(close_bin - close_byb) / mid` when both traded |
| `w_binance` | DOUBLE | the Binance weight actually used (NULL on gaps) |

**Exports**: `assets/Asset_<TICKER>/1m_<TICKER>_data.parquet` (zstd) carries
only `timestamp_ms, open, high, low, close, volume` — identical row counts for
every asset, continuous, no NULLs. **Semantics: a canonical two-venue index,
not raw exchange data.** Use it for ML and indicators; for Lean backtests use
the per-venue raw ZIP trees. The whole database is a pure function of the two
raw trees: rebuilding from a clean `db/` (`make ingest export`) reproduces
bit-identical Parquet files.

## 6. Known limitations (v1)

- **Single-venue minutes have nothing to switch to.** When only one venue is
  listed and that venue returns a maintenance placeholder, the minute becomes
  a canonical forward-fill (`src_count = 0`) — which is also exactly what the
  placeholder encodes (last price, zero volume).
- **No cross-exchange divergence cutoff.** Strongly diverging minutes are real
  market dislocations; the notional weighting dampens the low-volume side, and
  the full per-symbol distribution (mean / p99 / max) is exposed in
  monitoring. A hard `|Δclose|` cutoff is deliberately not applied in v1 —
  with two sources there is no median to define an objective outlier.
- **Phantom returns during dislocations.** When the venues disagree by `d` and
  the per-minute weight moves by `Δw`, the canonical close can move by
  ≈ `d·Δw` without either venue moving — a property of any per-minute-weighted
  index. Measured per symbol as `max_phantom_ret` in monitoring (the canonical
  1m move minus the larger of the two venues' own moves). ML labelling in
  minutes with high `rel_divergence` should account for this.
