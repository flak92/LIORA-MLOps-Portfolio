# module_data — venue candles in, one canonical market object out

The front door of this module: what it is, where its responsibility stops, how
to run it, and what comes out. The rules themselves live in `skills/` and are
not repeated here — this file orients, the skills bind. *The repository shows
the destination, not the road*.

`module_data` turns two public exchange APIs into **one complete,
provenance-aware canonical 1m market object per asset**. It downloads Binance
USDS-M and Bybit Linear one-minute klines into a QuantConnect Lean-exact ZIP
tree, materialises each venue's series as the asset's partition of that venue's
family, and rebuilds a canonical minute series in which every printed price is
one venue's candle copied verbatim — or an explicitly flagged forward fill — as
the asset's partition of the canonical family, DuckDB the engine in memory and
no database file anywhere.

## Where the responsibility stops

```
external market API → raw venue candles → venue validation
    → the venue families, one partition per asset → canonical 1m market object
```

Everything above that last arrow is this module. The bars of every timeframe of
the register and the feature catalogue belong to `module_features`:
`module_features/bars.py` reads the canonical family and writes the family
`bars`, a family of its own beside these three, downstream of this module's
contract. Labels, hyper-parameter search, XGBoost, strategy selection, research
simulation and every trading decision belong to `module_ml`.

Downstream code is source-neutral. No stage below the canonical object knows
which venue printed a given minute, and none needs venue-specific gap handling
(`CANDLE-CANONICALISATION-NO-VENUE-BELOW-THE-CANONICAL-SERIES`).

That boundary is also the storage seam the repository is prepared for: the raw
tree is written once and never restated, the asset's partitions of the three
families are a pure function of its two raw leaves, and `module_features` reads
the finished canonical partition — never a venue. Raw storage, canonical storage
and the research compute could later become three separate places without a
rule of this module moving. The direction:
[module_skills/skill_pre_aws_solution.md](../module_skills/skill_pre_aws_solution.md).

## Stages

Three stages, in order — `make data-all` runs them so. Each is idempotent and each runs in one-off containers of the `data` runner, `docker compose run --rm -T data`, and exits.

| stage | target | does |
|---|---|---|
| download | `make data-download` | both venues' 1m klines → Lean day ZIPs; skips a day whose ZIP exists; one container per venue for the whole basket, a venue's rate limit being per process |
| ingest | `make data-ingest` | both ZIP trees → the asset's partition of three families — `ohlcv_1m_binance`, `ohlcv_1m_bybit` and the canonical series `ohlcv_1m_canonical` — and each family's `schema.json`; one container per asset, one asset at a time |
| status | `make data-status` | each asset's three partitions, read → stdout tables + `store/status/data_status.json`; one container for the whole basket |

Every stage module exposes `main()` and shares one CLI, so a single asset can be
addressed directly:

```
python -m module_data.ingest --tickers BTC
```

In a shell no launcher set up, export the three `STORE_*_DIR` this module reads — `STORE_RAW_1M_DIR`,
`STORE_ASSETS_ARTIFACTS_DIR`, `STORE_STATUS_DIR` — first; `make` and compose do it for
you (`module_skills/glossary.md` § Stores).

`module_data.status` takes `--tickers` like every stage and reports those of the
assets it was told whose canonical partition stands; the launcher names the whole
basket, and `ASSET` never narrows it. With no canonical partition to read, the
stage stops on one line naming `make data-ingest`.

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

One asset is one partition of each family, `ticker=<TICKER>/` — Hive's
`key=value`, the value the ticker in capitals; the partition names the asset and
no column inside repeats it. Each family's `schema.json` is written by `ingest.py`
beside the partitions, read off the partition it has just written. DuckDB is the
engine, in the stage's memory: no database file exists. The raw tree keeps the
venues separate for good — raw data is the evidence of what a *specific* venue
observed — and its leaf is the symbol in lower case because Lean demands it: a
boundary, not an inconsistency to tidy away. The asset's folder of non-tabular
files, `store/assets_artifacts/ticker=<TICKER>/`, belongs to the modules
downstream; this module writes nothing into it.

Each `module_data` path is built in `config.py` and nowhere else; the one
exception is the Lean tree's own file names, which belong to `lean.py`, the
module's single external-format boundary.

## What you get for a given minute

The four questions a reader asks, each answered by a rule of `skills/skill_candle_canonicalisation.md`
and explained in `skills/methodology_data.md`:

- **Both venues printed a candle** — `CANDLE-CANONICALISATION-PRIMARY-FAILOVER-IS-A-TABLE`; the decision
  table written out is methodology § 7, the volume cases § 8;
- **Only one venue printed a candle** — the same rule; methodology § 8;
- **Neither venue printed a usable candle** — `CANDLE-CANONICALISATION-THE-GRID-IS-COMPLETE`, the forward
  fill; methodology § 8;
- **Both venues printed a candle that traded nothing** — the case where neither venue traded, methodology § 8.

What makes a candle eligible at all, and the absolute that holds across every answer — one venue's candle,
taken whole and verbatim, never an average — is `CANDLE-CANONICALISATION-A-CANDLE-IS-CHOSEN-WHOLE`
(methodology § 6 and § 7); what each minute carries as its evidence is
`CANDLE-CANONICALISATION-PROVENANCE-TRAVELS-WITH-THE-CANDLE` (methodology § 9).

## What the status stage measures

`make data-status` reads each asset's two venue partitions and its canonical one and publishes
per venue and for the canonical series — the candles only: a ZIP is an intermediate file, not
data, and a short or empty one appears as a deficit in `row_count`, `coverage_pct` and
`gap_count`. Which numbers are invariants is `CANDLE-CANONICALISATION-THE-INVARIANTS-ARE-ZERO`
in `skills/skill_candle_canonicalisation.md`, and what each observation means is
`skills/methodology_data.md` § 11; `module_skills/glossary.md` § Data quality
registers the measurement keys and § Payload structure the containers, the envelope and
the per-row facts — between them every key the snapshot carries.

## Extending

Every extension is one edit in the file that owns the fact, and the documents that
name the fact move in the same commit.

| what you add | where, and how much | the gate |
|---|---|---|
| a venue | `download_<venue>.py` beside its siblings, in their shape — `lean.py` writes the day, the probe and the day-completeness abort stay as they are; `SOURCE_VENUES` and the venue's URL, limit and delay constants in `config.py`; in `ingest.py` its CTE, its columns in `joined`, its tier, its `chosen` branch and its `<venue>_valid` column in `CANONICAL_COPY`, and its table in the grid-end `UNION ALL` of `main()` — its venue table, its family and the family's `schema.json` follow from `SOURCE_VENUES` through `VENUE_DDL`, `VENUE_COPY` and `venue_parquet()`; nothing in `status.py` — its scans, aliases, shares and stdout columns are all derived from `SOURCE_VENUES`; the venue-named rules of `skills/skill_candle_canonicalisation.md` — `CANDLE-CANONICALISATION-PRIMARY-FAILOVER-IS-A-TABLE` for the new tier order and `CANDLE-CANONICALISATION-NO-VENUE-BELOW-THE-CANONICAL-SERIES` for the new family — changed on the sheet, `module_skills/skills_sheet.xlsx`, and rendered by `make skills-sync`; the venue-named sections of `skills/methodology_data.md` rewritten for the new tier order — § 1, § 5, the decision table of § 7, the cases of § 8, the provenance table of § 9, the families and stages of § 10, § 12 and the reference observation of § 13; in the register, on the same sheet, the venue beside the others wherever a row lists them — the payload keys are keyed by venue and take it with no edit; then outside this module: nothing in `module_monitoring/`, whose page builds one section, one column and one share cell per entry of `source_venues`, and one more `basket` line in the Makefile's `data-download` | the existing venues' families untouched, and every minute an existing venue still wins identical in every existing column of the canonical series |
| an observation of the snapshot | one alias in a scan of `status.py` — the alias is the key — and its line in the block that publishes it, `venue_block()` or `canonical_source_block()`; its row in the observations table of `skills/methodology_data.md` § 11 and its register row on the sheet, `module_skills/skills_sheet.xlsx`, rendered into `module_skills/glossary.md` — § Data quality for a measurement, § Payload structure for a container or an envelope fact — and the cell that shows it in the monitoring module's `data.js` | the existing keys unchanged; the families untouched |
| a day of the raw tree | never by hand: delete the day's ZIP and rerun `data-download` (`skills/methodology_data.md` § 4) | the canonical series rebuilt by `data-ingest`, identical outside the day but for a forward fill that carries its last close |

A new asset is not an extension of this module: it is a ticker in `TICKERS` of the Makefile (`README.md` § Extending); nothing changes here.

## Docker does not own the data

A container is compute, never the owner of the data: the families a stage writes lie in the
artifacts store, mounted from the host, and DuckDB lives in the stage's memory and ends with
it. What the container supplies and what it never defines is
`CANDLE-CANONICALISATION-THE-CONTAINER-DEFINES-NO-CANDLE` in `skills/skill_candle_canonicalisation.md`;
the paths on either side of the mount are `skills/methodology_data.md` § 10.

## Design rationale

Why each object of this module sits where it does — the answers the naming review asks for
(`SELF-EXPLAINING-NAMING-A-NEW-OBJECT-PASSES-THE-NAMING-REVIEW`) written down, one row per object, analogous pair
or the module's documents; the mapping row it answers to is a row of the mapping table of `module_skills/README.md`
§ The Pre-AWS mapping, cited by its *responsibility* column and never repeated
(`PRE-AWS-SOLUTION-A-PLACEMENT-ANSWERS-TO-ONE-RESPONSIBILITY`).

| object | why here | why beside these | why this boundary | answers to |
|---|---|---|---|---|
| `config.py` | The one file that builds a path of this module (§ What it reads and writes) — `raw_symbol_dir()`, `partition_dir()` with `venue_parquet()` and `ohlcv_1m_canonical_parquet()` over it, `schema_json()` and the snapshot's path `DATA_STATUS_JSON_PATH` — imported by every stage file and by `lean.py`. | `module_features/config.py` and `module_ml/config.py` carry their own copies of `partition_dir()`, `ohlcv_1m_canonical_parquet()`, `schema_json()`, `to_utc_ms()`, the units they use, the ceiling, the `--tickers` parser and `rounded()` — twice by extraction, each copy as its row in `module_skills/glossary.md` § Twice by extraction says — and no module outside this one imports it — `module_monitoring` reads the snapshot's own keys — so no other module builds a path of this one from anything but a copy of its descriptors. | Every stage reaches a store through a descriptor here, so the raw tree, the families' partitions and the snapshot keep the same paths under `/store` whatever disk is mounted there (`module_skills/skill_pre_aws_solution.md`). | one row per descriptor: STORAGE — raw, immutable, one object per UTC day; STORAGE — the canonical market object, one writer at a time; STORAGE — status, run and trial objects |
| `lean.py` | The module's one external-format boundary (`AGENTS.md` § Canonical vocabulary): the day-ZIP and CSV names, `is_full_utc_day()`, `write_lean_zip()` and `lean_day_zip_paths()`. | Both downloaders, `ingest.py`, `status.py` and the terminal import it, and it imports `config.py` alone. | It names only the file inside the venue folder `config.py` builds — the reader that wants this format is placed by `module_skills/skill_pre_aws_solution.md` — so the raw days keep the same names under the same tree on whatever disk holds `store/raw_1m/`. | STRATEGY EXECUTION — absent |
| `download_binance.py` + `download_bybit.py` | SOURCE — the two files of the download stage (§ Stages), each fetching one venue's klines over a keyless public API and writing them as the day ZIPs `lean.py` names (their docstrings). | Twins that differ in the endpoint they speak, both importing `config.py` and `lean.py`, and `ingest.py` reads the trees they leave. | Each writes one ZIP per full UTC day and skips a day whose ZIP exists (§ Stages), so a rerun against the same tree on any disk mounted at `/store/raw_1m` writes only the days that are missing. | STORAGE — raw, immutable, one object per UTC day |
| `ingest.py` | INGEST and CANONICAL in one stage: it writes one asset's partition of the two venue families and of the canonical family, and each family's `schema.json` (§ What it reads and writes), DuckDB the engine in memory. | It imports `config.py` and `lean.py`, reads the ZIP trees the downloaders wrote and writes the canonical family `module_features/bars.py` and `module_ml/labels.py` read, each through its own copy of `ohlcv_1m_canonical_parquet()`; its `load_partition_schema()` is twice by extraction with `module_features/dataset.py` and `module_ml/dataset.py`. | It runs one asset at a time — the `fanout` macro at width 1, whatever `JOBS` says — in a one-off container of the `data` runner (`module_skills/skill_asset_containers.md`), one in-memory connection per asset, closed before the next, and the partitions it writes stay at the paths `venue_parquet()` and `ohlcv_1m_canonical_parquet()` build, whatever disk holds them. | COMPUTE — one stage for one asset |
| `status.py` | The stage that measures this module's own state — scans of the three partitions of each asset it is told, published as one snapshot for the basket (§ What the status stage measures) — placed by `AGENTS.md` § Architecture shape. | It imports `config.py`, `lean.py` for the download cadence and `ingest.py` for the validity predicate it counts the failures of, reads the partitions `ingest.py` wrote, and writes `store/status/data_status.json` for `data.js` to fetch. Its per-venue scans, aliases and shares are derived from `SOURCE_VENUES`, which it publishes as `source_venues`. | It takes `--tickers` like every stage — the launcher passes the basket — and runs once in a one-off container of the `data` runner (§ Stages; `module_skills/skill_pre_aws_solution.md`), writing the snapshot at the one path `DATA_STATUS_JSON_PATH` builds, under the `STORE_STATUS_DIR` the launcher names. | COMPUTE — one stage, one one-off process |
| `__init__.py` | The package that makes `python -m module_data.<stage>` a command (§ Stages), its docstring the module's responsibility in one line. | It names the two venues, the Lean ZIPs and the venue and canonical families per asset, and imports nothing. | The same `python -m module_data.<stage> --tickers <TICKER>` runs in a one-off container of the `data` runner (§ Stages) — the launcher setting the three `STORE_*_DIR` — the command `docker compose run --rm -T data` carries unchanged whichever host starts it. | COMPUTE — one stage, one one-off process |
| `sub_module_terminal/` | The module's own terminal (§ Its sub-module): the hand's instrument over the module's targets that carry a `##` — the three of § Stages and `data-all` — placed by `AGENTS.md` § Canonical vocabulary, the sub-modules row, and § The default choice — a nesting named rather than promoted. | Inside the module whose targets it starts, beside the stages; it imports `config.py` for the venues and the descriptors and `lean.py` for the day ZIPs — standard library both — and its `tui.py` is one file with the other module terminals' and the canon's terminal's, five times by extraction (`module_skills/glossary.md` § Twice by extraction). | It runs on the host's `python3` and gum, in no container and no venv, opens no partition, writes no file and starts everything through `make` — its menu the targets `make help` lists that `MENU_TARGET_PATTERN` gives this module, its one action `make <target> ASSET=<TICKER>`; what its screen holds is ruled by `module_skills/skill_tui_designer.md`. | no row — a hand's instrument on the host, with no part in the chain's dataflow |
| the module's documents — `README_module_data.md` and `skills/` | This orientation and the documents of `skills/` — the Skill rendered from the sheet and the hand-written methodology — filed by ownership (`AGENTS.md` § The default choice). | The orientation points at the documents beside it (§ Its documents), and every rule about this module is a row of the Skill in `skills/` (`AGENTS.md` § Canonical vocabulary, the row *a module's own skills*). | Tracked files under `module_data/` that no stage and no route reads, travelling with the code beside them — the same paths beside the code wherever the code is. | no row — a document that travels with the module's code, filed beside it |

## Its sub-module

`sub_module_terminal/` is the module's own terminal, the Data terminal: `make data-terminal`
opens it on the basket, `make data-terminal ASSET=<TICKER>` on one asset, with each asset's raw
days per venue and whether its canonical series stands. One answer starts one target through
`make` — every target of the root `Makefile` that carries a `##` and that `MENU_TARGET_PATTERN`
gives this module, the three of § Stages and `data-all` — as `make <target> ASSET=<TICKER>`
for the asset chosen, `data-download` and `data-status` staying basket-wide whatever `ASSET`
says; then it closes. It reads through this module's own `config.py` and `lean.py` — the
venues, the raw leaf of each and the canonical partition's path — opens no partition and
computes nothing: a count of day ZIPs and the last day they are named for is presentation, and
everything that runs, runs through the root `Makefile`. Its orientation is
`sub_module_terminal/README_sub_module_terminal.md`; its rules and the standards of its
screens are `module_skills/skill_tui_designer.md`.

## Its documents

| document | answers |
|---|---|
| `skills/skill_candle_canonicalisation.md` | the rules: what a canonical candle is, which venue's candle becomes it, what it carries and where it is stored — rendered from `module_skills/skills_sheet.xlsx` by `make skills-sync`, never edited by hand |
| `skills/methodology_data.md` | the method, for a human: where raw venue candles come from and how they are fetched, the raw tree, the decision table written out, the cases, the columns, the storage, what the status stage measures and the limitations — hand-written |

Project-wide rules — the name register, determinism, the container topology,
the direction `module_skills/skill_pre_aws_solution.md` describes — are in
`module_skills/`, indexed by [module_skills/README.md](../module_skills/README.md).
