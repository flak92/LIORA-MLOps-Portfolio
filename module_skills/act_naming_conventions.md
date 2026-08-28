# Act: naming conventions — the enacted names of this project

`AGENTS.md` holds the grammars — how a name is derived. This act holds the
decisions — which exact names the project enacted where a grammar left a
choice. One authority each: a rule lives in the contract, a decision lives
here, and a new decision enters this act in the commit that enacts it. Every
entry names the rejected form, because the rejected form is what stops the
next reader from reinventing it.

## Enacted names

| # | enacted | not | why |
|---|---|---|---|
| 1 | `module_data/`, `module_ml/`, `module_monitoring/`, `module_skills/` | `data_module`, `src`, `module_guidance`, `module_skills_for_the_project` | kind first so siblings sort together; the shortest name whose kind-first files say the rest; "for the project" repeats the scope it lives in |
| 2 | `store_Assets_artifacts/` | `store_research_artifacts`, `store_assets_artifacts` | the capital A signals what the folder holds — one `<TICKER>/` in capitals per asset; the eye reads the signal before the parser reads the contents |
| 3 | `store_db/` | `db`, `store_database` | kind first; `db` is unambiguous in this technical context |
| 4 | `store_raw_data_ss-01-hh-dd-MM/` | `store_raw_1m`, `raw_downloaded_1m_data` | the timeframe slot standard (§ below): every future raw store sorts from the finest granularity to the coarsest |
| 5 | `<TICKER>/` in capitals inside `store_Assets_artifacts/` | `btc`, `BTCUSDT` | the ticker is the project's asset identity; the exchange symbol belongs to the adapter boundary |
| 6 | Lean raw tree spelling: `cryptofuture/<venue>/minute/<symbol lowercase>/`, `YYYYMMDD_trade.zip` | project-cased variants | external-format boundary — Lean's vocabulary wins inside the store it defines |
| 7 | guidance files: `act_*`, `skill_*`, `methodology_*`, `glossary.md` | bare topic names | kind first inside the folder, same rule as the tree above it |
| 8 | `canonical_ss-01-hh-dd-MM.parquet` | `canonical_1m.parquet` | a file with a timeframe in its name follows the slot standard |

## The timeframe slot standard

A filesystem name that carries a timeframe writes it as five fixed slots,
finest to coarsest: `ss-mm-hh-dd-MM` (seconds, minutes, hours, days, months).
The active granularity is a zero-padded number in its slot; every inactive
slot keeps its unit letters as a placeholder.

| timeframe | slots |
|---|---|
| 1 second | `01-mm-hh-dd-MM` |
| 1 minute | `ss-01-hh-dd-MM` |
| 15 minutes | `ss-15-hh-dd-MM` |
| 1 hour | `ss-mm-01-dd-MM` |
| 4 hours | `ss-mm-04-dd-MM` |
| 1 day | `ss-mm-hh-01-MM` |
| 1 month | `ss-mm-hh-dd-01` |

Why it sorts: ASCII digits precede letters, so a filled slot beats a
placeholder at the same position and finer granularity always lists first —
verified identical under `LC_COLLATE=C` and `en_US.UTF-8`. Zero-padding keeps
numeric order inside a slot; the fixed slot count keeps listings
column-aligned. The mechanics are the subject of
`skill_sorting_files_naming_standard.md`.

In a Python identifier the slot dashes become underscores:
`store_raw_data_ss-01-hh-dd-MM/` mirrors to
`STORE_RAW_DATA_SS_01_HH_DD_MM_DIR`.

## The serialized-schema boundary

The slot standard governs filesystem names. Serialized schema — DuckDB tables
(`ohlcv_1m_canonical`, `ohlcv_15m_canonical`…), parquet columns, feature names
(`centered_rsi14_15m`) and artifact keys — keeps the compact `1m/15m/1h/4h`
tokens: those names are contracts with the files on disk, and a schema
migration is not a naming cleanup. They adopt the standard only at the next
schema-breaking change, recorded here when it happens.
