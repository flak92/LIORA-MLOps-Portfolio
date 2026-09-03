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

## Docker does not own the database

A container is compute, never the owner of the database; what Docker does and does not define
is § 15 of the same skill.

## Design rationale

Why each object of this module sits where it does — the answers of
`../module_skills/skill_self_explaining_naming.md` § The naming review written
down, one row per object, analogous pair or the module's documents; the mapping
row it answers to is `../module_skills/skill_pre_aws_solution.md` § The mapping
table, cited by its *responsibility* column and never repeated.

| object | why here | why beside these | why this boundary | answers to |
|---|---|---|---|---|
| `config.py` | The one file that builds a path of this module (§ What it reads and writes) — `TICKERS`, `raw_symbol_dir()`, `artifact_dir()`, `research_ohlcv_duckdb()` and the snapshot's path — imported by every stage file and by `lean.py`. | `../module_ml/config.py` re-exports its `TICKERS`, `artifact_dir()` and `research_ohlcv_duckdb()`, and `../module_monitoring/config.py`, `serve.py` and `record.py` import it, so no other module builds a path of this one. | Every stage reaches a store through a descriptor here, so the raw tree, the asset folder and the snapshot keep the same paths under `/app` whatever disk is mounted there (`../module_skills/skill_pre_aws_solution.md` § The volume is the home, the store is the copy). | one row per descriptor: STORAGE — raw, immutable, one object per UTC day; STORAGE — one prefix per asset; STORAGE — status and run objects |
| `lean.py` | The module's one external-format boundary (`../AGENTS.md` § Canonical vocabulary): the day-ZIP and CSV names, `is_full_utc_day()`, `write_lean_zip()` and `lean_day_zip_paths()`. | Both downloaders, `ingest.py` and `status.py` import it, and it imports `config.py` alone. | It names only the file inside the venue folder `config.py` builds — the reader that wants this format is seated by `../module_skills/skill_pre_aws_solution.md` § Module boundaries are extraction boundaries — so the raw days keep the same names under the same tree on whatever disk holds `store_raw_1m/`. | STRATEGY EXECUTION — absent |
| `download_binance.py` + `download_bybit.py` | SOURCE — the two files of the download stage (§ Stages), each fetching one venue's klines over a keyless public API and writing them as the day ZIPs `lean.py` names (their docstrings). | Twins that differ in the endpoint they speak, both importing `config.py` and `lean.py`, and `ingest.py` reads the trees they leave. | Each writes one ZIP per full UTC day and skips a day whose ZIP exists (§ Stages), so a rerun against the same tree on any disk mounted at `/app` writes only the days that are missing. | STORAGE — raw, immutable, one object per UTC day |
| `ingest.py` | INGEST and CANONICAL in one stage: it writes the two venue tables and the canonical table of one asset's database file (§ What it reads and writes). | It imports `config.py` and `lean.py`, reads the ZIP trees the downloaders wrote and writes the table `../module_ml/bars.py` reads. | It runs one asset at a time inside `asset-<ticker>` through the one `dockerfanout` line (`../module_skills/skill_asset_containers.md` § The topology), and the file it writes stays at the path `research_ohlcv_duckdb()` builds, under the same whole-file lock, whatever disk holds it. | COMPUTE — one stage for one asset |
| `status.py` | The stage that measures this module's own state — read-only scans of every asset's database, published as one snapshot for the basket (§ What the status stage measures) — placed by `../AGENTS.md` § Architecture shape. | It imports `config.py` and `lean.py`, scans the databases `ingest.py` wrote and counts the ZIPs the downloaders left, and writes `../module_monitoring/data_status.json` for `page.js` to fetch. | It takes no `--tickers` and runs only in the one-off `pipeline` (§ Stages; `../module_skills/skill_pre_aws_solution.md` § The resident container is a local mechanism), writing the snapshot at the one path `MODULE_MONITORING_DATA_STATUS_JSON_PATH` builds. | COMPUTE — one stage, one one-off process |
| `__init__.py` | The package that makes `python -m module_data.<stage>` a command (§ Stages), its docstring the module's responsibility in one line. | It names the two venues, the Lean ZIPs and the one database per asset, and imports nothing. | The same `python -m module_data.<stage> --tickers <TICKER>` runs in the venv, in `pipeline` and in `asset-<ticker>` (§ Stages), the command `docker compose run --rm -T pipeline` carries unchanged. | COMPUTE — one stage, one one-off process |
| the module's documents — `README_module_data.md` and `skills/` | This orientation and the normative documents of `skills/`, filed by ownership (`../AGENTS.md` § The default choice). | The orientation points at the documents beside it (§ Its normative skills), and every rule about this module sits in `skills/` (`../AGENTS.md` § Canonical vocabulary, the row *a module's own skills*). | Tracked files under `module_data/` that no process reads, travelling with the code beside them — the same paths beside the code wherever the code is. | no row — a document that travels with the task's code, seated beside its module |

## Its normative skills

| document | answers |
|---|---|
| `skills/skill_candle_canonicalisation.md` | what a canonical candle is, which venue's candle becomes it, where it is stored |
| `skills/methodology_data.md` | where raw venue candles come from and how they are fetched |

Repository-wide rules — the name register, determinism, the container topology,
the Pre-AWS direction — are in `../module_skills/`, indexed by
[../module_skills/README.md](../module_skills/README.md).
