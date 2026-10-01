# module_data — venue candles in, one canonical market object out

The orientation of this module: what it is, where its responsibility stops, how to run it and what comes out.
Its rules are `skills/skill_candle_canonicalisation.md`, its method for a human `skills/methodology_data.md`.

`module_data` turns two public exchange APIs into **one complete, provenance-aware canonical 1m market object per
asset**. It downloads Binance USDS-M and Bybit Linear one-minute klines into a QuantConnect Lean-exact ZIP tree,
materialises each venue's series as the asset's partition of that venue's family, and rebuilds a canonical minute
series in which every printed price is one venue's candle copied verbatim — or an explicitly flagged forward fill —
as the asset's partition of the canonical family, DuckDB the engine in memory and no database file anywhere.

## Where the responsibility stops

```
external market API → raw venue candles → venue validation
    → the venue families, one partition per asset → canonical 1m market object
```

Everything above that last arrow is this module. The bars of every timeframe of the register and the feature
catalogue belong to `module_features`, whose `bars.py` reads the canonical family; labels, the hyper-parameter
search, XGBoost, the strategy and every trading decision belong to `module_ml`. Downstream code is source-neutral:
no stage below the canonical object knows which venue printed a minute
(`CANDLE-CANONICALISATION-NO-VENUE-BELOW-THE-CANONICAL-SERIES`).

## Stages

Three stages, in order — `make data-all` runs them so — each idempotent, each in one-off containers of the `data`
runner.

| stage | target | does |
|---|---|---|
| download | `make data-download` | both venues' 1m klines → Lean day ZIPs; skips a day whose ZIP exists; one container per venue for the whole basket, a venue's rate limit being per process |
| ingest | `make data-ingest` | both ZIP trees → the asset's partition of `ohlcv_1m_binance`, `ohlcv_1m_bybit` and the canonical series `ohlcv_1m_canonical`, and each family's `schema.json`; one asset at a time |
| status | `make data-status` | each asset's three partitions → stdout tables and `store/status/data_status.json`; once for the whole basket |

Every stage exposes `main()` and the one `--tickers` parser, so an asset can be addressed directly —
`python -m module_data.ingest --tickers BTC` — in a shell that exports the three `STORE_*_DIR` this module reads,
`STORE_RAW_1M_DIR`, `STORE_ASSETS_ARTIFACTS_DIR` and `STORE_STATUS_DIR`; `make` and compose do it for you. With no
canonical partition to read, the status stage stops on one line naming `make data-ingest`.

## What it reads and writes

```
store/raw_1m/cryptofuture/<venue>/minute/<symbol>/YYYYMMDD_trade.zip   the Lean day ZIP — skills/methodology_data.md § 5

store/assets_artifacts/
    ├── ohlcv_1m_binance/
    │   ├── schema.json                                  the family's columns and types, as data
    │   └── ticker=<TICKER>/ohlcv_1m_binance.parquet     written here — Binance's minutes as printed
    ├── ohlcv_1m_bybit/
    │   ├── schema.json
    │   └── ticker=<TICKER>/ohlcv_1m_bybit.parquet       written here — Bybit's minutes as printed
    └── ohlcv_1m_canonical/
        ├── schema.json
        └── ticker=<TICKER>/ohlcv_1m_canonical.parquet   written here — the product

store/status/data_status.json   the status snapshot the dashboard reads
```

The raw tree keeps the venues apart for good (`CANDLE-CANONICALISATION-RAW-VENUES-STAY-APART`); its leaf is the
symbol in lower case because Lean demands it. The asset's folder `store/assets_artifacts/ticker=<TICKER>/` belongs
to the modules downstream: this module writes nothing into it.

## What you get for a given minute

The four questions a reader asks, each answered by a rule of `skills/skill_candle_canonicalisation.md` and explained
in `skills/methodology_data.md`:

- **Both venues printed a candle** — `CANDLE-CANONICALISATION-PRIMARY-FAILOVER-IS-A-TABLE`; the decision table is
  methodology § 7, the volume cases § 8;
- **Only one venue printed a candle** — the same rule; methodology § 8;
- **Neither venue printed a usable candle** — `CANDLE-CANONICALISATION-THE-GRID-IS-COMPLETE`, the forward fill;
  methodology § 8;
- **Both venues printed a candle that traded nothing** — methodology § 8.

A candle is taken whole and verbatim, never averaged (`CANDLE-CANONICALISATION-A-CANDLE-IS-CHOSEN-WHOLE`), and every
minute carries its evidence (`CANDLE-CANONICALISATION-PROVENANCE-TRAVELS-WITH-THE-CANDLE`).

## What the status stage measures

`make data-status` reads each asset's two venue partitions and its canonical one and publishes the candles per venue
and for the canonical series; a short or empty ZIP shows as a deficit in `row_count`, `coverage_pct` and `gap_count`.
Which numbers are invariants is `CANDLE-CANONICALISATION-THE-INVARIANTS-ARE-ZERO`, what each observation means
`skills/methodology_data.md` § 11, and every key the register's § Data quality and § Payload structure.

## Extending

Every extension is one edit in the file that owns the fact, and the documents that name the fact move in the same
commit.

| what you add | where, and how much | the gate |
|---|---|---|
| a venue | `download_<venue>.py` beside its siblings, in their shape — `lean.py` writes the day, the probe and the day-completeness abort stay as they are; `SOURCE_VENUES` and the venue's URL, limit and delay constants in `config.py`; in `ingest.py` its CTE, its columns in `joined`, its tier, its `chosen` branch and its `<venue>_valid` column in `CANONICAL_COPY`, and its table in the grid-end `UNION ALL` of `main()` — its venue table, its family and the family's `schema.json` follow from `SOURCE_VENUES`; nothing in `status.py`, whose scans, aliases, shares and columns derive from `SOURCE_VENUES`; the venue-named rules — `CANDLE-CANONICALISATION-PRIMARY-FAILOVER-IS-A-TABLE` for the tier order and `CANDLE-CANONICALISATION-NO-VENUE-BELOW-THE-CANONICAL-SERIES` for the family — changed on the sheet; the venue-named sections of `skills/methodology_data.md` — § 1, § 5, the decision table of § 7, the cases of § 8, the provenance table of § 9, the families and stages of § 10 and § 12; the register wherever a row lists the venues; nothing in `module_monitoring/`, whose page builds one part per entry of `source_venues`; and one more `basket` line in the Makefile's `data-download` | the existing venues' families untouched, and every minute an existing venue still wins identical in every existing column of the canonical series |
| an observation of the snapshot | one alias in a scan of `status.py` — the alias is the key — and its line in `venue_block()` or `canonical_source_block()`; its row in the observations table of `skills/methodology_data.md` § 11, its register row on the sheet, and the cell that shows it in `module_monitoring/data.js` | the existing keys unchanged; the families untouched |
| a day of the raw tree | never by hand: delete the day's ZIP and rerun `data-download` (`skills/methodology_data.md` § 4) | the canonical series rebuilt by `data-ingest`, identical outside the day but for a forward fill that carries its last close |

A new asset is not an extension of this module: it is a ticker in `TICKERS` of the Makefile (`README.md` §
Extending).

## Design rationale

Why each object of this module sits where it does, one row per object or analogous pair; the last column is the
responsibility of the mapping table in `module_skills/README.md` § The Pre-AWS mapping it answers to
(`PRE-AWS-SOLUTION-A-PLACEMENT-ANSWERS-TO-ONE-RESPONSIBILITY`).

| object | why here | why beside these | why this boundary | answers to |
|---|---|---|---|---|
| `config.py` | The one file that builds a path of this module — `raw_symbol_dir()`, `partition_dir()` with `venue_parquet()` and `ohlcv_1m_canonical_parquet()` over it, `schema_json()` and `DATA_STATUS_JSON_PATH` — imported by every stage file and by `lean.py`. | The other modules carry registered copies of the descriptors they read, and none imports this file. | Every stage reaches a store through a descriptor here (`PRE-AWS-SOLUTION-A-PATH-IS-BUILT-BY-ONE-DESCRIPTOR`). | one row per descriptor: STORAGE — raw, immutable, one object per UTC day; STORAGE — the canonical market object, one writer at a time; STORAGE — status, run and trial objects |
| `lean.py` | The module's one external-format boundary: the day-ZIP and CSV names, `is_full_utc_day()`, `write_lean_zip()` and `load_lean_day_zip_paths()`. | Both downloaders, `ingest.py`, `status.py` and the terminal import it; it imports `config.py` alone. | It names only the file inside the venue folder `config.py` builds. | STORAGE — raw, immutable, one object per UTC day |
| `download_binance.py` + `download_bybit.py` | SOURCE — the two files of the download stage, each fetching one venue's klines over a keyless public API and writing them as the day ZIPs `lean.py` names. | Twins that differ in the endpoint they speak; `ingest.py` reads the trees they leave. | Each writes one ZIP per full UTC day and skips a day whose ZIP exists, so a rerun writes only the days that are missing. | STORAGE — raw, immutable, one object per UTC day |
| `ingest.py` | INGEST and CANONICAL in one stage: one asset's partition of the two venue families and of the canonical family, and each family's `schema.json`. | It reads the ZIP trees the downloaders wrote and writes the canonical family `module_features/bars.py` and `module_ml/labels.py` read. | One asset at a time, whatever `JOBS` says, one in-memory connection per asset. | COMPUTE — one stage for one asset |
| `status.py` | The stage that measures this module's own state — scans of each asset's three partitions, published as one snapshot for the basket. | It reads the partitions `ingest.py` wrote, with `ingest.py`'s validity predicate, and writes the snapshot `data.js` fetches; its per-venue parts derive from `SOURCE_VENUES`, published as `source_venues`. | Once for the whole basket, at the one path `DATA_STATUS_JSON_PATH` builds. | COMPUTE — one stage, one one-off process |
| `__init__.py` | The package that makes `python -m module_data.<stage>` a command, its docstring the module's responsibility in one line. | It imports nothing. | The same command runs in a one-off container of the `data` runner. | COMPUTE — one stage, one one-off process |
| `sub_module_terminal/` | The module's own terminal, the hand's instrument over the module's targets that carry a `##` (`AGENTS.md` § Canonical vocabulary, the sub-modules row). | Inside the module whose targets it starts; it reads this module's `config.py` and `lean.py`, standard library both. | It runs on the host's `python3` and gum, opens no partition, writes no file and starts everything through `make` (`TUI-DESIGNER-ONE-TERMINAL-PER-MODULE`). | no row — a hand's instrument on the host, with no part in the chain's dataflow |
| the module's documents — `README_module_data.md` and `skills/` | This orientation, the rendered Skill and the hand-written methodology, filed by ownership (`AGENTS.md` § The default choice). | Every rule about this module is a row of the Skill in `skills/` (`AGENTS.md` § Canonical vocabulary, the row *a module's own skills*). | Tracked files under `module_data/` that no stage and no route reads. | no row — a document that travels with the module's code, filed beside it |

## Its sub-module

`sub_module_terminal/` is the Data terminal: `make data-terminal` opens it on the basket, `make data-terminal
ASSET=<TICKER>` on one asset, with each asset's raw days per venue and whether its canonical series stands, then
starts one target through `make`; `data-download` and `data-status` stay basket-wide whatever `ASSET` says. Its
orientation is `sub_module_terminal/README_sub_module_terminal.md`.
