# module_data — venue candles in, one canonical market object out

The front door of this module: what it is, where its responsibility stops, how
to run it, and what comes out. The rules themselves live in `skills/` and are
not repeated here — this file orients, the skills bind. *The repository shows
the destination, not the road*.

`module_data` turns two public exchange APIs into **one complete,
provenance-aware canonical 1m market object per asset**. It downloads Binance
USDS-M and Bybit Linear one-minute klines into a QuantConnect Lean-exact ZIP
tree, materialises both venues into the asset's own DuckDB file, and rebuilds a
canonical minute series in which every printed price is one venue's candle
copied verbatim — or an explicitly flagged forward fill.

## Where the responsibility stops

```
external market API → raw venue candles → venue validation
    → per-asset market database → canonical 1m market object
```

Everything above that last arrow is this module. Feature engineering, labels,
hyper-parameter search, XGBoost, strategy selection, research simulation and
every trading decision belong to `module_ml`. So do the 15m/1h/4h aggregations:
they live in the same database file but are written by `module_ml/bars.py`,
downstream of this module's contract.

Downstream code is source-neutral. No stage below the canonical object knows
which venue printed a given minute, and none needs venue-specific gap handling.

That boundary is also the storage seam the repository is prepared for: the raw
tree is written once and never restated, the asset's database is a pure function
of its two raw leaves, and `module_ml` reads the finished canonical object —
never a venue. Raw storage, canonical storage and the research compute could
later become three separate places without a rule of this module moving. The
direction:
[../module_skills/skill_pre_aws_solution.md](../module_skills/skill_pre_aws_solution.md).

## Stages

Three stages, in order. Each is idempotent and each has a container twin.

| stage | local | in containers | does |
|---|---|---|---|
| download | `make data-download` | `make docker-data-download` | both venues' 1m klines → Lean day ZIPs; skips a day whose ZIP exists |
| ingest | `make data-ingest` | `make docker-data-ingest` | both ZIP trees → the asset's DuckDB, then rebuilds the canonical series |
| status | `make data-status` | `make docker-data-status` | read-only scans → stdout tables + `module_monitoring/data_status.json` |

Every stage module exposes `main()` and shares one CLI, so a single asset can be
addressed directly:

```
python -m module_data.ingest --tickers BTC
```

`module_data.status` is the exception: it takes no `--tickers` and always
reports the whole basket.

## What it reads and writes

```
store_raw_1m/cryptofuture/<venue>/minute/<symbol>/YYYYMMDD_trade.zip   the Lean day ZIP — skills/skill_candle_canonicalisation.md § 3

store_assets_artifacts/<TICKER>/<TICKER>_research_ohlcv.duckdb
    ├── ohlcv_1m_binance      written here
    ├── ohlcv_1m_bybit        written here
    ├── ohlcv_1m_canonical    written here — the product
    ├── ohlcv_15m_canonical   written by module_ml/bars.py
    ├── ohlcv_1h_canonical    written by module_ml/bars.py
    └── ohlcv_4h_canonical    written by module_ml/bars.py

module_monitoring/data_status.json   the status snapshot the dashboard reads
```

One asset is one database file; the file names the asset and no table inside
repeats it. The raw tree keeps the venues separate for good — raw data is the
evidence of what a *specific* venue observed.

Each `module_data` path is built in `config.py` and nowhere else; the one
exception is the Lean tree's own file names, which belong to `lean.py`, the
module's single external-format boundary.

## What you get for a given minute

The four questions a reader asks, each answered in `skills/skill_candle_canonicalisation.md`:

- **Both venues printed a candle** — § 6 (the decision table) and § 7 (the volume cases);
- **Only one venue printed a candle** — § 9;
- **Neither venue printed a usable candle** — § 10 (the forward fill);
- **Both venues printed a candle that traded nothing** — § 7, case D.

What makes a candle eligible at all is § 4; the two absolutes that hold across every answer are § 5.

## What the status stage measures

`make data-status` scans each database read-only and publishes per venue and for the canonical
series; which numbers are invariants and which are observations is § 16 of
`skills/skill_candle_canonicalisation.md`, and `../module_skills/glossary.md` § Data quality
registers every key the snapshot carries.

## Docker and the database

A container is compute, never the owner of the database; what Docker does and does not define
is § 15 of the same skill.

## Its normative skills

| document | answers |
|---|---|
| `skills/skill_candle_canonicalisation.md` | what a canonical candle is, which venue's candle becomes it, where it is stored |
| `skills/methodology_data.md` | where raw venue candles come from and how they are fetched |

Repository-wide rules — the name register, determinism, the container topology,
the Pre-AWS direction — are in `../module_skills/`, indexed by
[../module_skills/README.md](../module_skills/README.md).
