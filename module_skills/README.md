# The canon — the index

Where every rule of the project is written down, and the canon's prose that is no rule. Every Skill and
`module_skills/skill_glossary.md` is rendered from `module_skills/skills_sheet.xlsx` by `make skills-sync` and never edited by
hand; this file links to each, holds no rule of its own, and keeps what the rules leave out — the explanations, the
worked examples and the mapping read forward — so nothing here can disagree with a rule. A rule is cited by its
`rule_id`. *The repository shows the destination, not the road*.

Ownership decides location, and `AGENTS.md` § The default choice holds the rule: a module's own Skills live in that
module's `skills/` or beside its sub-module, the Skills that cross modules live here, in `module_skills/` — the canon,
with its two sub-modules: the scalability crawler, which reads every controlled file of the sheet's files matrix against
the Skills marked for it, and the canon's terminal. A rule two sub-modules draw on crosses them and lives here too —
`skill_tui_designer.md` holds the rules of every terminal of the tree; a rule about one sub-module alone stays beside
its code, as the serpentine search's and the crawler's do. Each rule is one row of the sheet, rendered once, and a Skill
is named below by the path it holds in the tree.

## Cross-cutting — the skills in this directory

| skill | what it governs |
|---|---|
| [skill_agent_first_development.md](skill_agent_first_development.md) | how an agent works on this project — extend the owner, register a name in its commit, prove a change by running it; subtract, don't add |
| [skill_asset_containers.md](skill_asset_containers.md) | the compose topology: one image, three runners and one resident under two anchors, the store mounts each service is given, the `fanout` and `basket` macros, the host user, the one memory ceiling and the measured host port; the runtime contract every module runs inside |
| [skill_determinism.md](skill_determinism.md) | bit parity, thread caps, the one seed and the pinned orders, and where speed is allowed to come from |
| [skill_files_and_folders.md](skill_files_and_folders.md) | the kinds of file and folder the tree holds, what each is for, and which are generated |
| [skill_glossary.md](skill_glossary.md) | the name register: one concept, one name, in code, artifacts and interface — and the register of the copies no module may import across |
| [skill_pre_aws_solution.md](skill_pre_aws_solution.md) | the rules that keep every local boundary the one a move onto standard cloud primitives would keep, with nothing built for it; the mapping itself is § The Pre-AWS mapping below |
| [skill_rule_tables.md](skill_rule_tables.md) | a rule as a row of the sheet: its columns, its identifier, and how it is cited |
| [skill_self_explaining_naming.md](skill_self_explaining_naming.md) | names derived from a closed grammar, the naming review, and how a new convention is minted |
| [skill_sorting_files_naming_standard.md](skill_sorting_files_naming_standard.md) | taxonomic ordering, zero-padding and the timeframe slot standard |
| [skill_tui_designer.md](skill_tui_designer.md) | every terminal of the tree, one per module, the canon's among them: its instruments, the screen, states, colour and plain output, tables, lists and forms, the menu read off `make help`, the plan and the gate, feedback, failures, exits and help |

## Described, not written

Skills the tree does not hold yet — each a row of [../AGENTS.md](../AGENTS.md) § Skills absent here, described, placed
by ownership, with the one condition under which it is written. This index holds none of them.

## module_data

Orientation: `module_data/README_module_data.md`

| skill | what it governs |
|---|---|
| `module_data/skills/skill_candle_canonicalisation.md` | the one candle schema of the raw tree, validity, the primary-failover decision table, the complete grid and its forward fill, provenance, the one copy of the canonical series and the invariants of the data snapshot |

Reference for a human, never sent by the crawler: `module_data/skills/methodology_data.md` — the venue endpoints, units
and time, the raw tree, the decision table written out, the volume cases, the columns, the storage, the observations,
and the limitations of acquisition and of the canonical series.

## module_features

Orientation: `module_features/README_module_features.md`

| skill | what it governs |
|---|---|
| `module_features/skills/skill_feature_taxonomy.md` | the timeframe register, the registers of series, indicators, operators and normalisers, the terms and feature definitions and the ids derived from them, the default set, the warm-up and the effective histories, and the two families and the contract the layer writes |
| `module_features/sub_module_serpentine_search/skill_serpentine_search.md` | the serpentine search: the question and the answer, resume and reset, the tracked record, the key of a state, the gate and its noise margin, the beam, the convergence, the proposal and the promotion a hand makes |

Reference for a human, never sent by the crawler: `module_features/skills/methodology_features.md` — every catalogued
feature definition, equation by equation, with its histories and citations, the feature id, and the serpentine
search's objective, gate, margin and stopping.

## module_ml

Orientation: `module_ml/README_module_ml.md`

| skill | what it governs |
|---|---|
| `module_ml/skills/skill_methodology_ml.md` | the research layer's rules: one canonical series read through closed bars, the entry a minute after the decision, the labels, the folds and their weights, the hyper-parameter search and its trials families, the entry edge threshold, the backtest and the artifacts |

Reference for a human, never sent by the crawler: `module_ml/skills/methodology_ml.md` — the research layer equation by
equation, with its citations.

## module_monitoring

Orientation: `module_monitoring/README_module_monitoring.md`

| skill | what it governs |
|---|---|
| `module_monitoring/skills/skill_dashboard_conventions.md` | the static page and its toolkit, the names of its scripts and classes, how it shows a number, the state it keeps, what it reads and by which path, and the one server of three prefixes that serves it on loopback |

## module_skills

Of the canon's two sub-modules, the crawler keeps its rule beside its code; the canon's terminal,
`module_skills/sub_module_terminal/`, has none of its own — its rules are `skill_tui_designer.md`'s.

| skill | what it governs |
|---|---|
| `module_skills/sub_module_scalability_crawler/skill_scalability_crawler.md` | the scalability crawler: the files matrix it reads, the mission, the one active vendor, a report per controlled file and the snapshot |

## Naming, explained

Agents understand and extend this tree through its names, so a name that needs a lookup turns every reader into an
archaeologist. A name costs the thoughts a reader must think to use it correctly, not the characters it saves:
several names for one concept make every reader decide whether `test`, `test_fold` and `F5` are one thing or three,
which is why a synonym never enters the register (`AGENT-FIRST-DEVELOPMENT-NAME-ENTERS-THE-REGISTER`).

Given its layer, a name follows from the grammar the way BEM derives a CSS class, so nothing is left to invent and
nothing to argue about (`SELF-EXPLAINING-NAMING-A-NAME-IS-DERIVED-FROM-ITS-LAYER`). A convention earns its place the
same way (`SELF-EXPLAINING-NAMING-A-CONVENTION-MEETS-EVERY-CONDITION`): two copies of a rule drift, and the drift is
found by the reader who trusted the wrong one; a rule that excludes nothing describes taste, not structure; a named
exception is a boundary, an unnamed one is rot.

## Sorting, explained

The eye reads a listing before any parser does, and every machine sorts it lexicographically: a block of siblings
is taken for free, while a category scattered through the alphabet charges a scan and a memory for every lookup.
`LC_COLLATE=C` compares bytes, a UTF-8 locale folds case and punctuation, and macOS and Windows filesystems compare
without case, so only what every collation agrees on carries an order — a leading category token, and digits
before every letter (`SORTING-FILES-NAMING-STANDARD-A-PATTERN-SORTS-UNDER-EVERY-COLLATION`). Other names may swap:
`crawl.py` lists before `crawlers_mission.md` in byte order and after it under `en_US.UTF-8`.

`01 < 04 < 15` sorts as text the way it counts; unpadded, `1, 4, 15` sorts `1, 15, 4`. Slots of one width line
sibling names up character for character, so a difference shows at the position where it lives and the listing
reads as a table (`SORTING-FILES-NAMING-STANDARD-ZERO-PAD-EVERY-NUMBER`).

`timeframe_slot()` in `module_features/config.py` writes a token into the five slots `ss-mm-hh-dd-MM`, filling the
minute, hour or day slot: `1m` → `ss-01-hh-dd-MM`, `15m` → `ss-15-hh-dd-MM`, `4h` → `ss-mm-04-dd-MM`, `1d` →
`ss-mm-hh-01-MM`. A filled slot is a digit and a placeholder a letter, so a finer token lists first — as long as
each token is written in its coarsest whole unit: `90m` would list before `1h`, and `36h` before `1d`
(`SORTING-FILES-NAMING-STANDARD-TIMEFRAME-SLOTS`).

The slots are for names with siblings of another granularity to sort against. The raw store has none — `raw_1m`
is the one raw child of `store/` — so it keeps the compact token the code and the schema already speak, as every
serialised name does: a family, a feature id and a key are contracts with the files on disk. A partition
`timeframe=<tf>/` carries the compact token as its value, and the columns of a `catalogue` partition carry no
timeframe at all, the partition already saying which; `feature_id()` adds it where no partition stands beside the
name — a column of X, the key of an importance.

A module's orientation carries the module in its name, `README_module_<name>.md`: detached from its folder — in a
search result or a diff — a bare `README.md` no longer says which module it opens.

## Terminals

Five terminals are the hand's instruments over the Makefile, one per module, each the `sub_module_terminal/` of its
module: `make data-terminal`, `make features-terminal`, `make ml-terminal`, `make monitoring-terminal` and
`make skills-terminal`. All five share one `tui.py` and obey one document, `skill_tui_designer.md`, whose
`TUI-DESIGNER-` rows cross them. What a module's terminal shows is its
`sub_module_terminal/README_sub_module_terminal.md`; the canon's is the next section.

They look alike on purpose — neuro-optical consistency (`AGENTS.md` § Architecture shape): a screen is read by eye
before it is understood, so one concept takes one form, a change of form means a change of meaning, and the decision
and the result stand where the eye lands, on the last line. Each screen answers six questions, each in one place:
where am I — the header block and a prompt's header; what is there — the state table; what have I chosen — the steps
table, the plan, the changes; what am I choosing now — the prompt's header and the step shown `CURRENT`; what comes
next — the `PENDING` steps and a gate's question; what exactly runs — the plan's `command` line, verbatim.

What they decline follows from the same reading, and from a hand alone running a terminal, one action per run: Rich,
Textual or curses, the host being the standard library and gum 2; `--json`, the snapshot or the artifact being the
machine-readable state; `--no-input`, `--simple`, `--a11y`, `--no-color` or `--no-animation`, plain output following the
environment and nothing animating; a spinner, a bar or a percentage, since a spinner hides the lines of what a
terminal started, whose length is unknown until it ends; a pager, a second screen to leave before the decision; a
coloured cell, which gum strips and the word already says; `--lang`, the tree speaking one language, British English.

## Its terminal — the Skills terminal

`sub_module_terminal/` is the canon's terminal, the Skills terminal: `make skills-terminal` opens it, its header block
naming the root of the tree and the sheet it works on, `skills_sheet.xlsx`. Its state table, `parameter | value`, is
the crawl as its two files hold it: the active vendor of `vendors_for_crawling.toml`, `none` where no vendor is
active, and, counted off the snapshot `skills_status.json`, how many controlled files stand `pending`, `running`,
`done`, `failed` and `interrupted` — `absent` where there is no snapshot. Its menu is every target of the Makefile that
carries a `##` and whose name `MENU_TARGET_PATTERN` gives the canon — today `skills-sync`, `skills-configurables` and
`skills-crawl`, in the Makefile's order — then `quit`; `skills-terminal` carries no `##` and is no option of the menu
it opens. One answer shows the plan — the target and the purpose its `##` carries —, the line `command  make <target>`
and the gate `<target>?`; `make <target>` then runs with its lines on this screen, a crawl's one line per controlled
file among them, and the run ends on the `DONE` block or on the failure block carrying make's exit code; then it
closes. The failures it names itself: no terminal on standard input, no gum on `PATH`, or a target that exited
non-zero.

```bash
make skills-terminal                                                                       # the TUI over the tree and its sheet
STORE_STATUS_DIR=store/status python3 -B -m module_skills.sub_module_terminal.terminal -h   # the keys, plain output and the exit codes
```

Outside an action it creates no domain state and writes nothing: the root and the sheet it reads from
`module_skills/config.py`, the two crawl files through the crawler's `config.py`, and it counts what it shows. It
imports the standard library and its own package alone, runs on the host's `python3` with gum, in no container and no
virtual environment, and takes no argument but `-h`, `--help`. Its `config.py` holds `MENU_TARGET_PATTERN` and
`OUTPUT_PLAIN`; its `tui.py` is one file with the four module terminals', and `OUTPUT_PLAIN`, `HELP_LINE_PATTERN` and
the helpers `_option_rows()`, `_cancelled_exit_code()`, `_failure_exit_code()`, `_make()`, `_target_rows()` and
`_write_target()` are the copies it shares with them, each marked `# twice by extraction`. Its screens follow the
`TUI-DESIGNER-` rows of `skill_tui_designer.md`; the crawl it starts is no TUI, and the one rule of that document that
reaches it is `TUI-DESIGNER-A-STARTED-PROCESS-PRINTS-ONE-LINE-PER-STEP`.

## The Pre-AWS mapping

LIORA is an academic, portfolio and research demonstration of an MLOps and quant-research architecture. It is not a
production trading system, and not an Amazon Web Services (AWS) deployment. It runs locally: one image under docker
compose, driven by a Makefile. *Pre-AWS* is this repository's word for its shape. The boundaries are drawn so that
they would still be right if local storage, local container execution and the local stage order were replaced by their
standard equivalents on AWS. This section reads the tree that way. *Read forward* means the same object seated
elsewhere, with nothing moved, and nothing of it is built. The rules are `module_skills/skill_pre_aws_solution.md` and
`module_skills/skill_asset_containers.md`; this section restates none of them.

The proof is the whole chain, run end to end on a very small basket: `BTC` today, and at most one to three more. A
second asset proves the architecture, and the hundredth proves nothing more. When production realism and academic
simplicity conflict, simplicity wins, as long as it leaves no boundary a move would have to redraw. Parquet families
partitioned by asset, with DuckDB in memory, are trivial here, and later they are the same files on a durable volume.
A local database server "because the cloud would have one" is the antipattern
(`PRE-AWS-SOLUTION-A-SECOND-BACKEND-EARNS-AN-ABSTRACTION`).

### The twelve classes

Every object is classified before it is placed, and grouped by who writes its state and how long it lives
(`PRE-AWS-SOLUTION-OBJECTS-ARE-GROUPED-BY-WRITER-AND-LIFETIME`, `PRE-AWS-SOLUTION-A-NAME-IS-A-CLASS-NEVER-A-MECHANISM`).

| class | what it is | in this repository |
|---|---|---|
| SOURCE | an external observation, fetched as it came | `module_data/download_binance.py`, `module_data/download_bybit.py` |
| INGEST | raw evidence materialised unchanged, as the asset's partition of each venue family | `module_data/ingest.py`: `ohlcv_1m_binance`, `ohlcv_1m_bybit` |
| CANONICAL | the one research series built from the evidence, and its aggregations | `module_data/ingest.py`: `ohlcv_1m_canonical`, by `CANONICAL_COPY`; `module_data/lean.py`, the raw format it reads; `module_features/bars.py`, the family `bars` |
| STORAGE | where state lives, and the descriptors that name it | the five `store/<content>/` folders; every path descriptor of a `config.py` |
| FEATURE | the catalogue, a pure function of the canonical series, and the contract that names it | `module_features/catalogue.py`, `module_features/indicators.py` |
| LABEL | Y, resolved on the canonical path | `module_ml/labels.py` |
| MODEL | the searches, the fit, the folds, the shared IO, and the promotion that fixes an asset's columns and barriers | `module_ml/hpo.py`, `score.py`, `train.py`, `model.py`, `validation.py`, `dataset.py`; the serpentine search, `module_features/sub_module_serpentine_search/`, which sits with the feature set it moves |
| STRATEGY | the research evaluation of the predictions | `module_ml/strategy.py` |
| ORCHESTRATION | ordering and launching the stages | the Makefile |
| MONITORING | measuring the runtime, dating the crawler's reports, and presenting what was measured | the three modules' `status.py` and the crawler's, `record.py`, `module_monitoring/serve.py` and the page |
| STRATEGY EXECUTION | taking research artifacts and market data into a running strategy | absent here — described: `module_trading/`, its own container on the strategy host |
| INFRASTRUCTURE | the image and the topology | `Dockerfile`, `docker-compose.yml` |

Each module is the seam that one separately run container sits on: `module_data`, `module_features` and `module_ml`
their runners, and `module_monitoring` the resident. None of them is a cloud service of its own. The future
data-storage → feature-compute boundary is the line between `module_data` and `module_features`: the feature layer
reads the finished canonical family as a file, and writes nothing back across it. QuantConnect Lean is a format here,
not a runtime. `module_data/lean.py` writes the raw tree Lean-exact so that a Lean backtest could read it, and no Lean
runtime, container or dependency exists. If strategy execution ever exists, it is `module_trading/`, its own
container beside `module_ml`.

### The seats

The registry stores the image, the service runs it, the instance hosts it, and the state machine says *now the next*.
Each thing gets the cheapest seat that keeps its boundary: one host, one volume, one image. There is no cluster, no
queue and no database process, and no front until a reader outside the host appears.

- **The task host and the store volume.** One Linux container instance, shared by every asset's runs (Amazon ECS on
  Amazon EC2), with its durable disk mounted at `/store` (Amazon EBS). Today: the `./store/<content>:/store/<content>`
  mounts. The move reads `./store/<content>` as `<volume>/<content>`, and no stage notices. A rename.
- **The task definitions, the state machine and the schedule** (Amazon ECS, AWS Step Functions, Amazon EventBridge
  Scheduler). Today: `run --rm -T <runner>` through `fanout` and `basket`, the stage lists, `xargs -P $(JOBS)`,
  `RUN_ID`, and a hand typing `make all`. Read forward, each runner is a task definition on the one image, run per
  stage with the command overridden and per asset with `--tickers <TICKER>`. The stages are states, fanned out by a Map
  over `TICKERS` as wide as `JOBS`, and `run_id` is the execution name. A second asset is one more iteration of the
  Map. A rename.
- **The table families.** `<family>/ticker=<TICKER>/[timeframe=<tf>/]<family>.parquet`, with `schema.json` beside the
  partitions and one stage writing each family. DuckDB is the engine, in memory, and there is no database file. On the
  volume the files sit at the same paths, and every descriptor resolves unchanged. After the run each file is copied
  whole under its store's prefix. A second asset is one more partition of each family. A rename.
- **The strategy host.** A separate Linux instance running QuantConnect Lean (Amazon EC2). It reads the copy, and
  reads its brokerage credentials once at start from a secrets store (AWS Secrets Manager). Absent here — described.

The supporting seats — the registry (Amazon ECR), logs and metrics (Amazon CloudWatch), and the reader behind the
tunnel — are their rows of the mapping table. A service on an instance is chosen because it is the one form in which
*a container is compute, never the owner of state* moves as a rename: a host, a volume and a launcher. A task without
a host (AWS Fargate), or on a host the provider holds (Amazon ECS Managed Instances), takes the disk away. A cluster
(Amazon EKS) adds what one host does not need.

The seats of the local skills, one paragraph each in the table's words:

- **Asset containers** (`module_skills/skill_asset_containers.md`). Each runner — the `x-service` anchor with its own
  mounts — is a task definition on the one image, parameterised by `--tickers`. The resident is a service of the
  container runtime, kept running on the one Linux container instance (Amazon ECS on Amazon EC2). The `fanout` macro's
  `run --rm` is already a task run per stage per asset, so nothing is left to edit. The store mounts become the
  volume's, the one image becomes the task's image, and the `ml` runner's memory ceiling becomes its task's memory.
  `init` and `user` are keys the task definition already has.
- **Determinism** (`module_skills/skill_determinism.md`). The caps travel unchanged — `nthread=1` and DuckDB's
  `threads=1` in the code the task runs, `OMP_NUM_THREADS=1` in the environment of the one task definition — and
  `JOBS` is the width of the Map over `TICKERS` in the state machine (AWS Step Functions): set as it is set here, one
  unless a hand widens a run (`DETERMINISM-THREAD-CAPS-FROZEN-AT-ONE`,
  `DETERMINISM-WIDTH-IS-ONE-UNLESS-A-HAND-WIDENS-A-RUN`).
- **The market object** (`module_data/skills/skill_candle_canonicalisation.md`). On the one Linux container instance
  (Amazon ECS on Amazon EC2), the partitions of `module_data`'s three families sit at the same paths under
  `/store/assets_artifacts` — `ohlcv_1m_binance`, `ohlcv_1m_bybit` and `ohlcv_1m_canonical`, each `ticker=<TICKER>/`
  beside its family's `schema.json` — and the raw tree under `/store/raw_1m`, on the store volume mounted where the
  `./store/<content>` mounts are today. DuckDB stays an engine in the stage's memory, with no database file and no
  database service. After the run each file is copied whole to object storage (Amazon S3) under its store's prefix: a
  copy, never a mount. A managed database earns its place only past the promotion threshold — a second concurrent
  writer of one partition, or a reader that needs one transaction across families (`AGENTS.md` § Skills absent here,
  described, the `skill_database_promotion.md` row). The local rule this answers to is
  `CANDLE-CANONICALISATION-THE-CONTAINER-DEFINES-NO-CANDLE`.

### The mapping table

The *responsibility* column is what a module's § Design rationale cites, spelled exactly as here
(`PRE-AWS-SOLUTION-A-PLACEMENT-ANSWERS-TO-ONE-RESPONSIBILITY`). The column *the same responsibility elsewhere* is
where cloud proper nouns are spoken (`PRE-AWS-SOLUTION-CLOUD-NOUNS-STAY-IN-THE-MAPPING`), and none of its paths is a
proposal for a local directory. *The move* is a rename, one edit, or absent here — described. A row whose move is
absent here — described has no local counterpart.

| this repository has | responsibility | the same responsibility elsewhere | the move |
|---|---|---|---|
| the one image `liora-1m-pipeline`, built from the root `Dockerfile`: the pins on `python:3.12-slim`, no code | COMPUTE — the runtime every stage runs in | one container image in a registry (Amazon ECR), tagged with its commit; the code inside it, where `.:/app` carries it here (the ladder's third phase) | a rename |
| `docker compose run --rm -T <runner> python -m <module>.<stage> --tickers …`, the `basket` macro | COMPUTE — one stage, one one-off process | one run of its runner's task definition, with the command overridden to the stage (`RunTask`, Amazon ECS on Amazon EC2), on the instance every asset's runs share, the store volume mounted; AWS Fargate is the same task without the host, and so without the volume: a sentence here, never a phase | a rename |
| a per-asset stage: one one-off container of its runner per asset, `--tickers <TICKER>`, the `fanout` macro | COMPUTE — one stage for one asset | the same run with `--tickers <TICKER>` overridden, once per asset; no resident borrowed | a rename |
| the compose services under their two anchors: the runners `data`, `features`, `ml` and the resident `dashboard` | INFRASTRUCTURE — the topology | a task definition per runner on the one image, parameterised by `--tickers`, never a unit per asset; `dashboard` a service kept running on the same instance (Amazon ECS) | a rename |
| the Makefile's `DATA_STAGES`, `FEATURES_STAGES` and `ML_STAGES`, which `data-all`, `features-all`, `ml-all` and `all-record` read; `xargs -P $(JOBS)`; `RUN_ID` | ORCHESTRATION — the explicit stage order, the width, the execution identity | a state machine whose states are the stages, each fanned-out state a Map over `TICKERS` as wide as `JOBS`, `run_id` the execution name (AWS Step Functions) | a rename |
| the `./store/<content>:/store/<content>` mounts: the stores each service touches, read-only where it only reads | STORAGE — the home of state | a durable block volume on the instance (Amazon EBS), `./store/<content>` read as `<volume>/<content>`, each store at the path its `STORE_*_DIR` names today; never a network filesystem, never a task's own disk | a rename |
| `store/raw_1m/cryptofuture/<venue>/minute/<symbol>/<YYYYMMDD>_trade.zip` | STORAGE — raw, immutable, one object per UTC day | the same tree on the volume, and its copy under `raw_1m/` after the run, each day object written once (Amazon S3) | a rename |
| the families `ohlcv_1m_binance`, `ohlcv_1m_bybit` and `ohlcv_1m_canonical`, each asset's partition written by `data-ingest`, one asset at a time | STORAGE — the canonical market object, one writer at a time | the same files on the volume, written by the same process and copied whole after the run; never a database process, never a shared network filesystem; a managed database (Amazon RDS) only past the promotion threshold | a rename |
| `store/assets_artifacts/`: each family partitioned `ticker=<TICKER>/`, and the asset's folder `ticker=<TICKER>/` | STORAGE — one partition per asset | the same store on the volume, and its copy under `assets_artifacts/<run_id>/` after the run (Amazon S3), each key the descriptor's path relative to `STORE_ASSETS_ARTIFACTS_DIR`; the `ticker=<TICKER>` segment is the asset | a rename |
| the partitions of `bars`, `catalogue`, `labels` and `oos_predictions`, and the files of the asset's folder | STORAGE — research artifacts | artifact objects under the same version prefix | a rename |
| `store/status/`: the four snapshots, with the crawler's reports untracked beside them; `store/run_records/` with `index.json`; `store/trials/`: `hpo_trials` and `score_trials` | STORAGE — status, run and trial objects | copied whole after the run under `status/`, `run_records/` and `trials/`, each key its path relative to the store; the page reads `status/` and `run_records/` as it does here | a rename |
| a hand typing `make all` or `make all-record`; `download_cadence_minutes` of `data_status.json`; the downloaders' day skip; the rerun table of `module_ml/skills/methodology_ml.md` § 11, read by a human | ORCHESTRATION — the cadence and the rebuild condition, not yet code | a schedule that starts the machine once per `download_cadence_minutes`, at a fixed offset after midnight UTC so that the day asked for is full, per `is_full_utc_day()` (Amazon EventBridge Scheduler); and a condition state between BuildCanonicalData and AggregateBars that reads the volume and launches nothing (a Step Functions choice) | absent here — described |
| a stage's output left in the terminal; no resource sampling | MONITORING — logs and resource metrics | log streams keyed by stage, and metrics (Amazon CloudWatch); the run record holds time, exit code and store difference, nothing else | absent here — described |
| the page's files in `module_monitoring/`, reading `status/` and `run_records/` by relative path | MONITORING — the static dashboard | static objects behind a content-delivery front, under the same relative paths (Amazon S3 with Amazon CloudFront), only once a reader outside the host appears | absent here — described |
| `module_monitoring/serve.py` in the resident `dashboard`: three prefixes, the page's files, `/status/` and `/run_records/`, on loopback; the tunnel `ssh -N -L` | MONITORING — a small reader process | the `dashboard` service kept running on the instance, reached by a port-forward where the tunnel stands and by no public port | a rename |
| the Lean-exact raw tree; no Lean runtime | STRATEGY EXECUTION — absent | the strategy host, a separate container running QuantConnect Lean on its own Linux instance (Amazon EC2), as a backtest task or a container trading live; it reads the `raw_1m/` and `assets_artifacts/` prefixes of the copy and never the volume | absent here — described |
| none: the downloads use public endpoints, the page asks for no credential, and the crawler's vendor runs in its user's own session | STRATEGY EXECUTION — absent; the brokerage credentials a live strategy reads at start | a secret in a secrets store (AWS Secrets Manager), read once by the container running Lean when it starts | absent here — described |
| none: every stage writes the stores through their mounts and exits, and nothing copies | ORCHESTRATION — PublishStores, the copy after the run | a state that runs after the last stage has exited and copies each store whole to its prefix in object storage (Amazon S3), once per run: never a stage's own write, never mid-run | absent here — described |

Every row with a local counterpart reads *a rename*.

### The home and the copy

Locally the working tree is the only home, and nothing copies. Read forward, the home is the store volume, and object
storage is the copy after the run, which no stage writes. PublishStores copies each store whole under a prefix named
as the store is. Each key is the file's path relative to its store: the `store` and `path` pair that a run record's
`store_diff` already carries. The five prefixes are:

- `raw_1m/`, written once;
- `assets_artifacts/<run_id>/`, versioned by the execution name;
- `trials/`;
- `run_records/`;
- `status/`.

A stage never reads the copy (`PRE-AWS-SOLUTION-A-STAGE-KNOWS-A-PATH-NOT-AN-OBJECT-KEY`); only the strategy host does.
The active version is chosen where its reader is, and is never marked inside a file
(`PRE-AWS-SOLUTION-AN-ARTIFACT-CARRIES-NO-RUN-IDENTITY`). Because the page reads `status/` and `run_records/` by
relative path, a front could serve it from the copy unchanged.

### The Makefile, read forward

The state machine's states are the stages. The test of a stage's width is whether it has a one-line state name; a name
with "and" in it would mean the stage is too wide.

| stage | state |
|---|---|
| `data-download` | DownloadMarketData |
| `data-ingest` | BuildCanonicalData |
| `features-bars` | AggregateBars |
| `features-catalogue` | GenerateFeatures |
| `ml-labels` | GenerateLabels |
| `ml-hpo` | SearchHyperparameters |
| `ml-train` | TrainModel |
| `ml-strategy` | EvaluateStrategy |
| `data-status`, `features-status`, `ml-status` | PublishStatus |
| `features-serpentine-turn` | AdvanceSerpentineSearch: outside the daily order, started by a hand |
| `ml-score` | ScoreSearchStates: alternates with the turn while the question `<TICKER>_score_request.json` stands, the one condition any state asks |
| `features-serpentine-search-promote` | PromoteSearchProposal: a hand's choice for one asset, followed by the states of `ml-all` |

The stage lists are the machine's state order. `xargs -P $(JOBS)` is its Map, 1 wide for BuildCanonicalData and
`JOBS` wide above it (one, unless a hand widens it). `RUN_ID` is the execution name. PublishStores, which is no stage,
runs after the last one.

### The ladder

Three phases, all of them elsewhere. Skipping one is a redesign: the idiom without the lift has no volume for the
stores, and a Makefile baked into an image misses the idiom.

- **The lift.** The task host and its volume, this tree checked out onto the volume, and `docker compose` and
  `make all` as they are. The `./store/<content>` mounts already are the volume.
- **The idiom.** A task definition per runner, with `<volume>/<content>` in the mounts it respells. The stages become
  states, with the Map, the execution name and PublishStores, and a schedule starts the machine. The daily order has no
  condition state, because no predicate exists. The Makefile stays the developer interface and stops running the day.
- **The image carries the code.** The root `Dockerfile` copies the packages onto their pins, and the tree mount
  `.:/app` goes; the registry holds the image.

### Rejected forms

| form | why not |
|---|---|
| a shared network filesystem as the volume (Amazon EFS) | one host needs none; a second host writing it would be a second operation writing state at once (`PRE-AWS-SOLUTION-ONE-OPERATION-WRITES-AT-A-TIME-AND-NOTHING-LOCKS`) |
| a managed database now (Amazon RDS) | nothing has crossed the promotion threshold (`PRE-AWS-SOLUTION-NO-DATABASE-PROCESS-BEFORE-THE-PROMOTION-THRESHOLD`) |
| object storage as the first home | a pull and a push around every stage, an adapter, and a second backend nothing has earned |
| a batch service (AWS Batch) | a queue for stages that are already an ordered list |
| a run without a host first (AWS Fargate) | no host, no volume, no store |
| a cluster for one host (Amazon EKS) | a control plane kept running for four services on one host |
| a task on a host the provider holds (Amazon ECS Managed Instances) | no bind mount to a path on a host this project holds |
| a managed web service for the dashboard (AWS App Runner) | the page is on loopback, reached through the tunnel, until a reader outside the host appears |
| a stage as a function run on an event (AWS Lambda) | a stage reads and writes the disk the next stage reads; the search and the training are not short; no event exists |

### What the shape holds

Six things, each a seat above:

- one image;
- the stores, explicit and outside compute, mounted at `/store/<content>` beside the one tree mount;
- the orchestration outside the modules, in one Makefile and one compose file;
- the contracts between modules as files, never imports: `<TICKER>_catalogue.json`, the serpentine search's question
  and answer, the promoted feature set and barriers, the snapshots, the run record, and the copies registered in
  `module_skills/skill_glossary.md` § Twice by extraction;
- the asset as a parameter of the launcher alone;
- a recorder that reads off the stores what a stage wrote.

It holds nothing of a cloud: no template, no registry, no task definition, no adapter, no secrets store, no state
machine and no SDK.

### What stays as it is, and why

| current | problem | Pre-AWS direction | change now? |
|---|---|---|---|
| every status stage folds the basket the launcher names, once, in its module's runner | one object per basket, safe because it has one writer | written only by the one-off `basket` run, never fanned out; a per-asset object and a reader-side fold if the basket grows (`skill_per_asset_status.md`) | no — described |
| `module_ml.status` writes the basket snapshot and each `<TICKER>_README.md` | two namespaces in one stage | the README is an asset artifact of an asset-scoped part, the snapshot a fold over completed assets | no — described |
| the snapshots in `store/status/`, tracked | none | STORAGE of the three computational modules and the crawler, tracked so that a fresh clone opens on real numbers; answers `skill_status_prefix.md` | yes — done |
| the root `Dockerfile` installs the pins and copies no code | the image is a dependency layer | the tree mount carries the code; *the image carries the code* stays elsewhere; answers `skill_image_contents.md` | yes — done |
| `record.py` measures each stage from outside and rewrites `run_records/index.json` | no stage → artifact map anywhere | what a task scheduler records about a task; the stage order stays the Makefile's | yes — done |
| a recorded run stops at the first stage that exits non-zero, keeping its record | the verdict is the exit codes | the judgement an execution record makes anywhere; a clause of `skill_stage_state_machine.md` | yes — done |
| `module_monitoring/serve.py` serves three prefixes and answers 404 for everything else | one process serves the page's files and two stores | static objects behind a front once a reader outside the host appears (`skill_dashboard_front.md`) | no — described |
| no callable asks "does this asset need a rebuild?" | the condition has no home; nothing is wrongly fused | compute stays unconditional (`PRE-AWS-SOLUTION-THE-REBUILD-CONDITION-STAYS-SEPARABLE`) | no — described |
| `btc-all`, `btc-lifecycle` | a ticker in a target name | nothing depends on them; retired when the basket grows, as their sunset notes say | no — described |
| the compose project is named `liora` in the file | none | one name every document can spell; two checkouts on one host share it, so run one at a time or set `COMPOSE_PROJECT_NAME` | yes — done |
| the image is named `liora-1m-pipeline` | none | the project and what the tree is, with no ticker; two checkouts that build one tag share the last build | yes — done |
| `hpo` names the stage and the file, `hyperparameter_search_result` the key | one term in two forms | a domain abbreviation, spelled out where a key has no file name beside it (`AGENTS.md` § Canonical vocabulary) | no — described |

### One day, told forward

For one UTC day, each step says what happens locally and then what would happen elsewhere.

1. **The day closes** at UTC midnight; a day is written only when `is_full_utc_day()` holds. Locally nothing runs by
   itself. Elsewhere the schedule is the only clock.
2. **The schedule.** Locally a hand types `make all-record`, which expands `RUN_ID`. Elsewhere one execution named
   `run_id` starts.
3. **DownloadMarketData.** Locally `data-download` runs one process per venue, skipping any day already on disk.
   Elsewhere two task runs in one state.
4. **BuildCanonicalData.** Locally `fanout` at width 1. Elsewhere a Map, width 1.
5. **PublishStatus for data.** `data_status.json`, written once for the basket.
6. **The rebuild condition, absent.** Every state below runs unconditionally, and a human reads the rerun table.
7. **The research layer**, AggregateBars to EvaluateStrategy. Locally `fanout` at `$(JOBS)`, with PublishStatus for
   features after GenerateFeatures. Elsewhere each per-asset state is a Map as wide as `JOBS`.
8. **PublishStatus for ML, then PublishStores.** `ml_status.json` and each `<TICKER>_README.md`. The copy after them is
   absent here — described.
9. **Logs and metrics.** Locally the terminal, and `store/run_records/<run_id>/<stage>.json`. Elsewhere log streams
   and metrics, absent here — described.
10. **The page.** Locally `make on` and the tunnel. Elsewhere `dashboard` on the task host, behind a port-forward.
11. **The strategy host, absent.** Elsewhere it reads the copy's `raw_1m/` and `assets_artifacts/` prefixes.
12. **The day at rest, in no container.** Locally the working tree and the page. Elsewhere the store volume, the copy
    under five prefixes, and the page.
