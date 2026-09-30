# Methodology — from raw 1m venue candles to the canonical series

How each venue's one-minute observations are fetched and made durable (§ 1–§ 4),
and how the two venues' candles become one canonical series (§ 5–§ 13): the raw
tree, validity, the decision table, forward fill, provenance, storage, what the
status stage measures and the limitations of each step. This is reference for a
human; the rules it explains are the rows of
[skill_candle_canonicalisation.md](skill_candle_canonicalisation.md), rendered from
the sheet and cited here by their `rule_id`. The guards in the code are the
mathematics' own — the seven named in `AGENTS.md`.

## 1. Sources & endpoints

**Binance USDS-M futures** — `GET https://fapi.binance.com/fapi/v1/klines`
with `symbol=<SYM>USDT`, `interval=1m`, `startTime`/`endTime` bounding one full
UTC day, `limit=1500` (one request per day). A kline row is `[openTime, open,
high, low, close, volume, closeTime, quoteVolume, ...]`; **columns 0–5** are
kept — the bar-open timestamp, four prices and the **base-asset volume**.
Before any download the oldest candle of every symbol is probed
(`startTime=0&limit=1`); the run aborts if any listing is younger than the
data window's start, which guarantees full Binance coverage of the data window. An empty
response for a post-listing day aborts the run instead of persisting a
skip-forever empty ZIP.

**Bybit linear perpetuals** — `GET https://api.bybit.com/v5/market/kline` with
`category=linear` (trade klines — **not** mark-price or index-price klines),
`symbol=<SYM>USDT`, `interval=1`, `start`/`end`, `limit=1000`; one UTC day =
two 720-minute request windows. A row is `[start, open, high, low, close, volume,
turnover]`; **columns 0–5** are kept. `volume` for linear contracts is the
base-asset quantity (contract multiplier 1), the same unit as Binance's. The list is
returned newest-first and is sorted ascending before writing. A day with no
data (before the symbol's Bybit listing) is stored as a ZIP with an empty CSV,
so the question is asked once and never again. The listing day itself may
begin at the first traded minute and hold a partial file — a property of raw
per-day storage, not a canonical gap: the canonical grid is rebuilt downstream
from both providers, and every later day must be complete.

Both downloaders write the same QuantConnect Lean-exact day ZIP, once, because
exchanges do not restate klines; the tree's shape and the file names are § 5, and
the two venues' raw data never share a file
(`CANDLE-CANONICALISATION-RAW-VENUES-STAY-APART`).

## 2. Retries, backoff and pacing

Every request carries `USER_AGENT` = `liora-module-data/1.0`. A request is tried up to
`REQUEST_ATTEMPT_COUNT` times (`fetch_klines()`) with an exponential backoff that starts at one
second and doubles: Binance retries on HTTP 418 and 429, sleeping at least what
`Retry-After` asks; Bybit retries on `retCode 10006`, its rate-limit code, and raises
on any other code. Between two written days the downloader sleeps a fixed
`BINANCE_REQUEST_DELAY_SECONDS` = 0.2 s or `BYBIT_REQUEST_DELAY_SECONDS` = 0.1 s, never
after a skipped day. A venue's rate limit is budgeted per process, which is why the
launcher runs one process per venue and never fans the download out per asset.

## 3. Units & time

UTC everywhere; timestamps are **bar OPEN** epoch milliseconds on a strict
60 000 ms grid; the data window is `2021-01-01 00:00 UTC` (inclusive) to the
most recent UTC midnight (exclusive); volume is **base-asset volume**, never
quote turnover; the unit of download work is one UTC calendar day = one ZIP
(idempotent backfill and top-up with the same command); a listing-day ZIP may
begin at the first available minute. Prices and volumes are stored exactly as
the exchanges printed them — no rounding at any layer.

## 4. Known limitations of acquisition

- **A short post-listing day stops the download.** A day after a symbol's first
  traded day that a venue genuinely printed with fewer than 1440 minutes is
  indistinguishable from a truncated response, so the download stage aborts on
  it with no override (`download_binance.py`, `download_bybit.py`).
- **Only Binance is probed for its listing date.** The probe that guarantees
  full coverage of the data window runs against Binance alone; Bybit's first traded
  day is discovered from the ZIPs already on disk and from the first day a run
  finds printed, so a Bybit listing inside the data window is normal and its
  pre-listing days are stored as empty files.
- **Idempotence is by file presence.** A day whose ZIP exists is never
  re-fetched. Correcting a day means deleting its ZIP, which is deliberate:
  exchanges do not restate klines, and a silent refetch would erase the
  evidence of what was originally observed.

## 5. The raw tree

Raw candles are kept as the evidence of one venue's observation, in a
Lean-exact tree with one leaf per venue and symbol — the leaf built by
`raw_symbol_dir()` in `config.py`, the names by `lean.py`:

```
store/raw_1m/cryptofuture/<venue>/minute/<symbol lowercase>/YYYYMMDD_trade.zip
    └── YYYYMMDD_<symbol lowercase>_minute_trade_perp.csv
        headerless: offset_ms_from_utc_midnight,open,high,low,close,volume
```

The leaf carries the symbol in lower case because Lean demands it, while a
partition of a family carries the ticker in capitals, `ticker=<TICKER>/` — a
boundary, not an inconsistency to tidy away (`AGENTS.md` § Architecture shape).
A Lean backtest reads these per-venue trees.

After the downloaders both venues carry this one candle schema. A difference of
transport, paging or ordering — Binance's one request per day, used in the order
it returns and checked minute by minute by `is_full_utc_day()`; Bybit's two
request windows, returned newest-first and sorted — is resolved inside the downloader
that speaks the venue, and `ingest.py` reads every tree through the one
`parse_zip()` (`CANDLE-CANONICALISATION-ONE-CANDLE-SCHEMA-AFTER-THE-DOWNLOADERS`).

Each venue's leaf stays its own, one ZIP per UTC day: raw data is the proof of
what one venue observed, and a raw file combining two venues would destroy the one
thing it is kept for (`CANDLE-CANONICALISATION-RAW-VENUES-STAY-APART`).

## 6. Candle validity

Before a candle may win a minute it must be valid, and validity is a property of
one venue's candle alone: it never consults the other venue. The test is
`OHLC_INTACT_PREDICATE` in `ingest.py`, written once and imported by `status.py`
(`CANDLE-CANONICALISATION-A-CANDLE-IS-CHOSEN-WHOLE`):

```
valid =
    finite(O, H, L, C, V)
    AND O > 0 AND H > 0 AND L > 0 AND C > 0
    AND V >= 0
    AND L <= min(O, C)
    AND H >= max(O, C)
```

The first three lines judge the values, the last two the geometry: a low above
the open or the close, or a high below either, is a candle that contradicts
itself. A candle that fails any line is invalid, and for the decision table an
invalid candle and an absent one are the same thing. A minute with no row at all
is likewise invalid rather than NULL: the grid is joined to each venue's table
and `coalesce(<venue>.valid, false)` folds absence into `false`, so the table
never has to tell the two apart.

## 7. The decision table

Binance is the primary venue and Bybit the secondary — the tier order of
`SOURCE_VENUES` in `config.py`, published as `source_venues`. For every minute
of the grid exactly one row below applies; it is the table the SQL of
`CANONICAL_COPY` in `ingest.py` encodes
(`CANDLE-CANONICALISATION-PRIMARY-FAILOVER-IS-A-TABLE`):

| Binance | Bybit | O, H, L, C | V | `source` | `zero_volume` |
|---|---|---|---|---|---|
| valid, V > 0 | valid, V > 0 | Binance | Binance | `binance` | false |
| valid, V > 0 | valid, V = 0 | Binance | Binance | `binance` | false |
| valid, V = 0 | valid, V > 0 | **Bybit** | **Bybit** | `bybit` | false |
| valid, V = 0 | valid, V = 0 | Binance | 0 | `binance` | **true** |
| valid | missing / invalid | Binance | Binance | `binance` | Binance's V = 0 |
| missing / invalid | valid | Bybit | Bybit | `bybit` | Bybit's V = 0 |
| missing / invalid | missing / invalid | previous close | 0 | `ffill` | false |

Read as a priority ladder, the same table is four tiers and a fallback: a traded
Binance candle, then a traded Bybit candle, then a valid no-trade candle from
either venue in the same order, then forward fill. A traded candle on either
venue outranks a no-trade candle — a maintenance placeholder on Binance never
outranks a real Bybit minute — and a valid no-trade candle still outranks
fabrication. `zero_volume` is true exactly when the winning candle traded
nothing, so it is false on every forward-filled minute: `ffill_bars` and
`zero_volume_bars` count disjoint sets of minutes.

The winner is taken whole, its four prices and its volume as the venue printed
them, unrounded (`CANDLE-CANONICALISATION-A-CANDLE-IS-CHOSEN-WHOLE`). None of
these is a canonical candle:

```
O, H, L, C from Binance, V from Bybit
H = max(Binance.H, Bybit.H)
L = min(Binance.L, Bybit.L)
C = average(Binance.C, Bybit.C)
```

An average prints quotes that existed nowhere. A per-minute index weighted by the
two venues moves its printed price whenever the weights shift, by up to the
relative divergence of the two closes (§ 9) — whose largest value on the data window
the snapshot publishes as `relative_divergence_max` — a move no venue made. A
canonical candle is therefore one candle a single venue actually printed, or an
explicitly flagged forward fill.

## 8. Volume, and the minutes each venue printed

Volume is the only field that can move the choice away from the primary venue.
When both candles are valid, four cases are exhaustive:

| case | Binance V | Bybit V | the canonical minute |
|---|---|---|---|
| A — both traded | > 0 | > 0 | the whole Binance candle: the primary wins whenever it traded |
| B — only the primary traded | > 0 | = 0 | the whole Binance candle: Bybit's no-trade minute changes nothing |
| C — only the secondary traded | = 0 | > 0 | the whole Bybit candle, `source = bybit` |
| D — neither traded | = 0 | = 0 | the whole Binance candle, `V = 0`, `zero_volume = true` |

Case C is the failover the table exists for: a no-trade placeholder carries no
information about the minute, and a traded candle does. In case D both venues
agree nothing traded; the primary's own quotes are kept and the minute is
flagged, so the status stage can count it.

**A candle on both venues.** Whichever venue wins, `binance_valid` and
`bybit_valid` are both true on the stored row and `rel_divergence` is measured
(§ 9): the losing venue is recorded as present, never as having contributed a
value.

**A candle on one venue.** The valid venue's candle is the canonical one, whole;
`zero_volume` is that candle's `V = 0`, and `rel_divergence` is NULL. A
single-venue minute has nothing to fail over to: a no-trade candle stays,
flagged, and no candle at all falls through to the forward fill.

**No valid candle on either venue.** The minute has no candle to take and is
closed deterministically by forward fill, with `P` the previous canonical close:

```
O = H = L = C = P        V = 0        source = ffill        zero_volume = false
```

A forward-filled minute is not an exchange observation. It keeps the grid
complete (`CANDLE-CANONICALISATION-THE-GRID-IS-COMPLETE`) and stays marked by
its provenance, so no reader mistakes it for a printed candle; it carries the
previous close only — never the previous high or low, which would invent a range
no venue quoted. Before the first valid candle on either venue there is no
previous close, and such a minute carries NULL prices with `source = ffill`. The
listing probe and the full-day check of § 1 give every minute of the data window a
Binance row; for the current basket the snapshot's `ffill_bars` of zero shows no
such minute.

## 9. Provenance and relative divergence

The canonical family stores the chosen candle together with the evidence for the
choice, written by `ingest.py`, the stage that chose it
(`CANDLE-CANONICALISATION-PROVENANCE-TRAVELS-WITH-THE-CANDLE`). Eleven columns;
the last five are provenance and data quality, never model inputs:

| column | type | meaning |
|---|---|---|
| `timestamp_ms` | BIGINT | bar open, UTC epoch ms, on the minute grid |
| `open`, `high`, `low`, `close` | DOUBLE | the winning venue's prices, verbatim; the previous canonical close on a forward-filled minute |
| `volume` | DOUBLE | the winning venue's base-asset volume, verbatim; 0 on a forward-filled minute |
| `source` | VARCHAR | `binance`, `bybit` or `ffill` — the provenance of the minute |
| `zero_volume` | BOOLEAN | the winning candle was valid and traded nothing |
| `binance_valid` | BOOLEAN | a Binance row was present and passed the validity test |
| `bybit_valid` | BOOLEAN | a Bybit row was present and passed the validity test |
| `rel_divergence` | DOUBLE | the cross-venue close divergence, when both venues are valid |

The family's `schema.json` carries these columns and types as data. The asset is
not a column: its partition, `ticker=<TICKER>/`, names it once.

`source` is what makes a source switch visible. Within a minute nothing is
combined, so no averaging distortion exists to measure; between two minutes the
series may change venue and carry the cross-venue basis, which is why
`source_switch_count` and `max_abs_return_at_switch` are measured (§ 11) rather
than smoothed away.

When both venues have a valid candle:

```
                 abs(binance_close - bybit_close)
rel_divergence = ---------------------------------
                 (binance_close + bybit_close) / 2
```

It is computed whenever both candles are valid, whichever venue won and whatever
the volume: it measures the pair, not the choice, and it is NULL on every other
minute. It is a quality measurement, never a selection rule
(`CANDLE-CANONICALISATION-PRIMARY-FAILOVER-IS-A-TABLE`): a large divergence
averages nothing, changes no primary, drops no minute and synthesises no candle.
Strongly diverging minutes are real market dislocations; the status stage exposes
the distribution as `relative_divergence_p99` and `relative_divergence_max`, and
a divergence policy would be a change of the rules, not a tuning decision.

## 10. Storage, stages and the container

An asset is one partition, `ticker=<TICKER>/`, of each of three families under
`STORE_ASSETS_ARTIFACTS_DIR`, each family's `schema.json` beside its partitions;
DuckDB is the engine in the stage's memory, and no database file exists:

| family | written by | holds |
|---|---|---|
| `ohlcv_1m_binance` | `module_data/ingest.py` | the Binance raw tree, materialised as printed |
| `ohlcv_1m_bybit` | `module_data/ingest.py` | the Bybit raw tree, materialised as printed |
| `ohlcv_1m_canonical` | `module_data/ingest.py` | the canonical series: the full grid with its provenance |
| `bars` | `module_features/bars.py` | its aggregations on the timeframes of the register, downstream of this module |

The canonical series is stored once and every reader reads that partition
(`CANDLE-CANONICALISATION-THE-CANONICAL-SERIES-IS-STORED-ONCE`); below it no
stage asks which venue printed a minute
(`CANDLE-CANONICALISATION-NO-VENUE-BELOW-THE-CANONICAL-SERIES`).

| stage | input | output | responsibility | module |
|---|---|---|---|---|
| download Binance | Binance's REST endpoint | raw Lean day ZIPs | preserve the venue's evidence | `module_data` |
| download Bybit | Bybit's REST endpoint | raw Lean day ZIPs | preserve the venue's evidence | `module_data` |
| ingest a venue | the venue's raw tree | its partition of `ohlcv_1m_<venue>` | materialise the minutes as printed | `module_data` |
| canonicalisation | the two venue tables | its partition of `ohlcv_1m_canonical` | primary-failover selection | `module_data` |
| aggregation | the canonical partition | the partitions of `bars` | exact UTC-aligned aggregation inside the research window | `module_features` |

Ingest rebuilds unconditionally: per asset one in-memory connection pinned to one
thread, each venue table loaded afresh from its ZIP tree, the canonical partition
rebuilt from the two, every write ordered — so the same raw tree writes the same
partitions, and the grid ends at the asset's own last raw minute over both
venues (`CANDLE-CANONICALISATION-INGEST-REBUILDS-FROM-THE-RAW-TREE`).

DuckDB here is an engine inside the stage's process, not a service. There is no
container → network → database server; there is

```
Python process in a one-off container → the mounted store → Parquet partitions
```

The store is mounted by name — `STORE_ASSETS_ARTIFACTS_DIR` names it on either
side of the mount — so a partition's path is a prefix swap:

| host | container |
|---|---|
| `store/assets_artifacts/ohlcv_1m_canonical/ticker=BTC/ohlcv_1m_canonical.parquet` | `/store/assets_artifacts/ohlcv_1m_canonical/ticker=BTC/ohlcv_1m_canonical.parquet` |

The container starts the process and gives it its user, its environment and the
stores it touches; it defines nothing of the candle, and every rule above holds
identically when the same stage runs in a shell that exports the three
`STORE_*_DIR` (`CANDLE-CANONICALISATION-THE-CONTAINER-DEFINES-NO-CANDLE`).

## 11. Invariants and observations

`module_data/status.py` reads each asset's three partitions and publishes what it
finds in `store/status/data_status.json`. Three numbers are invariants, and a
non-zero value is a defect (`CANDLE-CANONICALISATION-THE-INVARIANTS-ARE-ZERO`):

```
duplicate_count      == 0     per venue
invalid_row_count    == 0     per venue
ohlc_violation_count == 0     on the canonical series
```

`invalid_row_count` counts the venue rows that fail `ingest.py`'s own
`OHLC_INTACT_PREDICATE`, imported rather than restated (§ 6): such a row never
wins a minute and would otherwise be counted nowhere, because `coverage_pct` and
`gap_count` are built from the timestamps present, not from the rows usable. On
the page an invariant column is marked as such: after a change of provider the
invariants must still be zero, while the observations beside them are expected
to move.

Every other number is an observation. It describes the market and the venues,
and no value of it is by itself a failure:

| observation | what a non-zero value means |
|---|---|
| `gap_count` | minutes a venue never printed; the canonical grid closes them |
| `gap_count_after_first_observation` | a venue's gaps counted from its first printed minute, so a listing inside the data window is not a gap |
| `coverage_pct` | the share of the grid a venue printed; the real-data and forward-fill shares are the page's arithmetic over `row_count` and `ffill_bars`, not keys |
| `zero_volume_bars` | candles that traded nothing — on a venue the raw `volume = 0`; on the canonical series the stored `zero_volume`, set only when the winning candle traded nothing. One name, two objects, and on the canonical series false on every forward-filled minute |
| `flat_bars` | a venue's minutes that traded nothing and quoted one price — `volume = 0` and `open = high = low = close` on the raw table, no validity test consulted; a subset of that venue's `zero_volume_bars` |
| `last_close` | a venue's last printed close; every other number here is dimensionless, so nothing else in the snapshot would notice a delivery under the wrong symbol |
| `ffill_bars` | minutes with no valid candle on either venue |
| `longest_ffill_streak_minutes` | the longest unbroken streak of forward fill. `ffill_bars` alone cannot tell a provider dark for three days from one dropping scattered minutes over years; the first is a fabricated regime, the second noise |
| `longest_flat_streak_minutes` | the longest unbroken streak of flat minutes on the canonical series. A forward-filled minute satisfies the flat geometry too and is not one of them: a canonical minute is forward-filled, flat or traded, decided in that order, or fabrication would be reported as a quiet market |
| `repeated_candle_count` | canonical minutes repeating the previous candle verbatim while volume was printed — a feed frozen on its last bar, which no flatness count can see: the timestamps differ, the geometry is intact and the volume is not zero |
| `source_share_pct_by_venue` | the share of minutes each venue won, keyed by venue in the tier order of `source_venues`; a share below the primary's is evidence the failover works, not a fault |
| `source_switch_count` | the places the cross-venue basis can enter a return |
| `max_abs_return_1m` | the largest one-minute absolute return on the canonical series |
| `max_abs_return_at_switch` | the largest one-minute absolute return at a source switch — the basis a switch let in |
| `relative_divergence_p99`, `relative_divergence_max` | the 99th percentile and the largest of the cross-venue close divergence |

A venue's `zero_volume_bars` above zero is not a fault either: what such a minute
means depends on whether it won the canonical selection.

## 12. Known limitations of the canonical series

These are properties of the method, not defects to be smoothed away; the
limitations of acquisition are § 4.

- **A single-venue minute has nothing to fail over to.** When only one venue is
  listed and it prints a no-trade candle, the canonical minute is that candle,
  flagged `zero_volume`; when it prints nothing, the minute is a forward fill.
  Case C of § 8 needs two listed venues to choose between.
- **A source switch carries the cross-venue basis, and is the only place it can
  enter.** Changing venue between two minutes can move the canonical close by
  the current Binance–Bybit basis without either venue having moved. Within a
  minute nothing is combined; a return that spans a switch may carry the basis,
  which is what `source_switch_count` and `max_abs_return_at_switch` measure. No
  smoothing is applied: the switch is visible, not hidden.
- **There is no cross-venue divergence cutoff.** Strongly diverging minutes are
  real market dislocations and are kept; only the distribution is exposed (§ 9).
- **The grid can begin before the data does.** Minutes before the first valid
  candle on either venue carry NULL prices with `source = ffill` (§ 8); for the
  current basket there are none.

## 13. Naming

This method uses one vocabulary:

```
raw candle          venue candle        valid candle
canonical candle    primary venue       secondary venue
primary-failover    zero-volume candle  ffill
provenance          relative divergence venue selection
canonicalisation
```

The word *merge* is avoided: it suggests mixing O, H, L, C and V across venues,
which `CANDLE-CANONICALISATION-A-CANDLE-IS-CHOSEN-WHOLE` forbids — say *venue
selection*, *canonicalisation* or *primary-failover selection* instead. The
register's rejected synonyms of the canonical series — *fused series*, *index*,
*blended price* — are in `module_skills/skill_glossary.md` § Market object.
