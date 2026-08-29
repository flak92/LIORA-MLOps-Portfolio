# Methodology — the canonical 1m OHLCV database

How each asset's `<TICKER>_research_ohlcv.duckdb` is created:
sources and endpoints, units and time, the canonical source-priority
definition, the schema and the known limitations. The guards in the code are
the mathematics' own — the seven named in `AGENTS.md`; *The repository shows the destination, not the road*.

## 1. Methodology — primary-failover consolidation

Raw one-minute OHLCV observations from Binance USDS-M and Bybit Linear USDT
perpetual markets are synchronised to a common UTC one-minute grid and
consolidated into a single canonical market series. **Every canonical bar is
one venue's candle copied verbatim** — prices and volume of a single exchange,
never a blend: per minute, the highest-priority existing tier wins (traded
Binance candle, then traded Bybit candle, then a valid no-trade candle from
either venue in the same order), and only a minute with no valid candle on
both venues is a canonical gap, deterministically forward-filled with the
previous canonical close and zero volume. Data-source shares, source
switches, the largest move at a switch, cross-exchange divergence and every
other integrity anomaly are recorded by the data-layer quality monitoring
(`module_data/status.py`, run by `make data-status`) and exposed through the
project dashboard. Consequently, downstream
indicator calculation and ML pipelines operate exclusively on a continuous
canonical t,O,H,L,C,V series whose every printed price existed on a real
exchange, and require no exchange-specific gap-handling logic.

**What the canonical series is: a continuous canonical research-market
representation, constructed deterministically from the available market
observations.** Every candle in it is a real observation printed by one
provider — the only exception is an explicit forward fill, flagged as such. No
price is an average of two sources, because an average prints quotes that
existed nowhere: a per-minute index weighted by the two venues' notional moves
the printed price whenever the weights shift, which on this window reaches 7.8 %
in a single minute — a move no venue made. This series, and nothing upstream of it, is the object the
research layer studies: features, labels, validation, modelling and the
strategy simulation all read it and none of them knows which provider printed
a given minute ([methodology_ml.md](methodology_ml.md) §2).

The provenance columns (`source`, `zero_volume`, `binance_valid`,
`bybit_valid`, `rel_divergence`) and the per-source statistics below are
**provenance and data quality — never model inputs.** No cross-source
quantity, `rel_divergence` included, is a feature.

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
base-asset quantity (contract multiplier 1), the same unit as Binance's. The list is
returned newest-first and is sorted ascending before writing. A day with no
data (before the symbol's Bybit listing) is stored as a ZIP with an empty CSV,
so the question is asked once and never again. The listing day itself may
begin at the first traded minute and hold a partial file — a property of raw
per-day storage, not a canonical gap: the canonical grid is rebuilt downstream
from both providers, and every later day must be complete.

Both downloaders write identical QuantConnect Lean-exact day ZIPs
(`YYYYMMDD_trade.zip` → `YYYYMMDD_<symbol>_minute_trade_perp.csv`, headerless
`offset_ms_from_utc_midnight,open,high,low,close,volume`) into
`store_raw_1m/cryptofuture/<venue>/minute/<symbol>/`; a day file is written
once, because exchanges do not restate klines.

## 3. Units & time

UTC everywhere; timestamps are **bar OPEN** epoch milliseconds on a strict
60 000 ms grid; the data window is `2021-01-01 00:00 UTC` (inclusive) to the
most recent UTC midnight (exclusive); volume is **base-asset volume**, never
quote turnover; the unit of download work is one UTC calendar day = one ZIP
(idempotent backfill and top-up with the same command); a listing-day ZIP may
begin at the first available minute. Prices and volumes are stored exactly as
the exchanges printed them — no rounding at any layer.

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
- Prices and volume are **copied verbatim** from the winning source — no
  weighting, no averaging, no rounding. Every canonical price existed on a
  real market, so **no averaged synthetic price is introduced** and no shift of
  weights can move a printed price. That is a statement about
  blending *within* a minute: a return that *spans* a source switch may still
  carry the cross-source basis, which is exactly what `source_switch_count` and
  `max_abs_return_at_switch` measure.
- The only place a cross-venue basis difference can enter the series is a
  minute whose source differs from the previous minute — monitored as
  `source_switch_count` and `max_abs_return_at_switch` per symbol.
- `rel_divergence` (`|c_bin − c_byb| / mid` when both candles are valid) is a
  **data-quality signal only** — it is never a model feature.
- Rows before a symbol's first valid candle would stay NULL; the Binance
  listing probe pins this to zero.

## 5. Database schema

`ohlcv_1m_binance` and `ohlcv_1m_bybit` — raw, verbatim from the ZIP trees:

| column | type | meaning |
|---|---|---|
| `symbol` | VARCHAR | e.g. `BTCUSDT` |
| `timestamp_ms` | BIGINT | bar OPEN, UTC epoch ms, 60 000 ms grid |
| `open, high, low, close` | DOUBLE | venue trade prices |
| `volume` | DOUBLE | base-asset volume of that venue |

`ohlcv_1m_canonical` — the primary-failover series, rebuilt deterministically
per symbol on every `make data-ingest`; what the ML stages read:

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

`ohlcv_15m_canonical`, `ohlcv_1h_canonical`, `ohlcv_4h_canonical` — exact
UTC-aligned aggregations of the canonical 1m series, rebuilt by `make ml-bars`
inside the frozen research window (O first, H max, L min, C last, V sum;
`arg_min`/`arg_max` by timestamp for determinism), plus `ffill_bars` and
`zero_volume_bars` — how many minutes inside the bar are forward-filled or
traded nothing. Closed bars only: the window ends at a UTC midnight.

**Where the series lives**: the canonical primary-failover series and its
15m/1h/4h aggregations live **only in the asset's own database**,
`<TICKER>_research_ohlcv.duckdb`; the folder's parquets carry feature columns,
not prices. For Lean backtests use the per-venue raw ZIP trees. Each database
is a pure function of the asset's two raw leaves — rebuilding it from scratch
reproduces it bit-identically — and its grid ends at that asset's own last raw
minute over both venues.

## 6. Known limitations

- **Single-venue minutes have nothing to fail over to.** When only one venue
  is listed and that venue prints a no-trade candle, the canonical bar is that
  candle (flagged `zero_volume`); when it prints nothing, the bar is a forward
  fill.
- **Source switches carry the cross-venue basis.** A switch between venues can
  move the canonical close by the current Binance–Bybit basis without either
  venue moving; the count and the largest such move are monitored per symbol
  (`source_switch_count`, `max_abs_return_at_switch`). No smoothing is applied — the
  switch is visible, not hidden.
- **A source switch is the only place a basis jump can enter.** Within a
  minute nothing is blended, so no averaging artifact exists to measure; between
  two minutes the series can change venue, which is why `source_switch_count`
  and `max_abs_return_at_switch` are monitored per symbol rather than smoothed.
- **No cross-exchange divergence cutoff.** Strongly diverging minutes are real
  market dislocations; the per-symbol distribution (mean / p99 / max) is
  exposed in monitoring.
- **A short post-listing day stops the download.** A day after a symbol's first
  traded day that a venue genuinely printed with fewer than 1440 minutes is
  indistinguishable from a truncated response, so the download stage aborts on
  it with no override (`download_binance.py`, `download_bybit.py`).
