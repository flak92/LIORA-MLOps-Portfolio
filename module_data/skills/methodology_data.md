# Methodology — acquiring the raw 1m venue candles

How each venue's one-minute observations are fetched and made durable: sources
and endpoints, units and time, and the limitations of acquisition itself. What
happens to a candle after it is on disk — validity, primary-failover selection,
forward fill, provenance and the database schema — is
[skill_candle_canonicalisation.md](skill_candle_canonicalisation.md). The guards
in the code are the mathematics' own — the seven named in `AGENTS.md`; *The
repository shows the destination, not the road*.

## 1. Sources & endpoints

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

Both downloaders write the same QuantConnect Lean-exact day ZIP, once, because
exchanges do not restate klines; the tree's shape, the file names and the
prohibition on combining the two venues' raw data are
[skill_candle_canonicalisation.md](skill_candle_canonicalisation.md) § 3.

## 2. Units & time

UTC everywhere; timestamps are **bar OPEN** epoch milliseconds on a strict
60 000 ms grid; the data window is `2021-01-01 00:00 UTC` (inclusive) to the
most recent UTC midnight (exclusive); volume is **base-asset volume**, never
quote turnover; the unit of download work is one UTC calendar day = one ZIP
(idempotent backfill and top-up with the same command); a listing-day ZIP may
begin at the first available minute. Prices and volumes are stored exactly as
the exchanges printed them — no rounding at any layer.

## 3. Known limitations of acquisition

- **A short post-listing day stops the download.** A day after a symbol's first
  traded day that a venue genuinely printed with fewer than 1440 minutes is
  indistinguishable from a truncated response, so the download stage aborts on
  it with no override (`download_binance.py`, `download_bybit.py`).
- **Only Binance is probed for its listing date.** The probe that guarantees
  full coverage of the window runs against Binance alone; Bybit's first traded
  day is discovered from the ZIPs already on disk, so a Bybit listing inside
  the window is normal and its pre-listing days are stored as empty files.
- **Idempotence is by file presence.** A day whose ZIP exists is never
  re-fetched. Correcting a day means deleting its ZIP, which is deliberate:
  exchanges do not restate klines, and a silent refetch would erase the
  evidence of what was originally observed.
