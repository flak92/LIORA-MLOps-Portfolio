# module_monitoring — what the runtime modules measured, made readable

The front door of this module: what it is, where its responsibility stops, and
how to run it. The page's rules are `skills/skill_dashboard_conventions.md`; the
terminal's are the canon's `module_skills/skill_tui_designer.md`, with every
other terminal's; none is repeated here. *The repository shows the destination,
not the road*.

`module_monitoring` computes nothing about the market. It presents what
`module_data`, `module_features` and `module_ml` already measured about
themselves, what `record.py` measured around every stage of a recorded run and
where the canon's crawler stands; it runs the one server that serves the page,
and it carries the terminal a hand switches that server from.

## Where the responsibility stops

```
status/*.json + run_records/index.json + run_records/<run_id>/<stage>.json → one composed page
```

It reads snapshots and run records by relative path and never recomputes a
number. Every value on the page was produced by the program that owns it —
`module_data/status.py`, `module_features/status.py`, `module_ml/status.py`,
`module_skills/sub_module_scalability_crawler/status.py` and `record.py`. A
metric that does not exist in a snapshot or a run record does not appear on the
page. A snapshot carries what its module measured and the page renders what it
reads: a key the page does not read stays the module's own. What the page adds is
presentation arithmetic — a share, a mean over the folds, a difference of two
reported numbers, an age against the clock
(`DASHBOARD-CONVENTIONS-PRESENTATION-ARITHMETIC-ONLY`) — and it stays on the page:
written into a payload, it would grow the payload without adding a fact.

The same line is a storage seam: the four snapshots are status objects this
module reads and never produces, and a run record is the run object `record.py`
writes from outside every stage; the page and its scripts are static files, and
the server is a reader of three prefixes and nothing else. The direction:
`module_skills/skill_pre_aws_solution.md`.

## What it runs

| piece | entry | does |
|---|---|---|
| the server | the `dashboard` service of `make on` | `python -m module_monitoring.serve`, the resident's own `command:` — the page's files under `/`, the status store under `/status/`, the run-records store under `/run_records/`; every other path, and every directory, is 404 |
| the terminal | `make monitoring-terminal` | `sub_module_terminal`: the four snapshots on one screen, then `on` or `off` through `make` — on the host, in no container |
| the presentation switch | `make on` / `make off` | the one resident up with the page's address printed and opened, and `docker compose down` — every container of this project stopped and removed |

`make on` builds the one image every service runs, `liora-1m-pipeline`, brings
the one resident up — `dashboard`, a role of that image and not an image of its
own — then prints the page's address and opens it; `make off` is
`docker compose down`. The dashboard has no target of its own: it is a service's
`command:` in `docker-compose.yml`, raised and taken down by that one switch. It
mounts the tree read-only and the two stores it serves read-only, and writes
nothing.

The dashboard is published on the host at `127.0.0.1:<port>` alone — the address
`make on` prints (the topology of `module_skills/skill_asset_containers.md`;
`DASHBOARD-CONVENTIONS-REACHABLE-ON-LOOPBACK-ONLY`); a reader on another machine
comes through the SSH tunnel of `README.md` § Quickstart. The page reads, by
relative path (`DASHBOARD-CONVENTIONS-THE-PAGE-READS-BY-RELATIVE-PATH`):

| file | written by | the tab that reads it |
|---|---|---|
| `status/data_status.json` | `module_data.status` | Pipeline and Data Quality |
| `status/features_status.json` | `module_features.status` | Features, ML Research |
| `status/ml_status.json` | `module_ml.status` | ML Research, ML Assets |
| `status/skills_status.json` | the canon's crawler | Scalability |
| `run_records/index.json` and the records it lists | `record.py`, under `make all-record` | Lifecycle |

The four snapshots are committed, so the page opens on a fresh clone; the run
records are not, and the Lifecycle tab says so until the first recorded run.

## Extending

| to add | change |
|---|---|
| a tab | one `<button class="pill" data-key="<key>">` in the `data-pills="tab"` nav, one `<section data-panel="tab" data-key="<key>" hidden>` and one section script in the list at the end of `index.html`, which `initPills` of `page.js` wires by `data-key`; the tab's row in § Design rationale here, and in the same commit every list of the tabs (`DASHBOARD-CONVENTIONS-A-TAB-MOVES-EVERY-LIST-OF-THE-TABS`); a script that holds what it fetched for another script adds a state global, named in `DASHBOARD-CONVENTIONS-TWO-STATE-GLOBALS` |
| a file the page reads | nothing here while it lies in the status store or the run-records store: the page names it under `status/` or `run_records/`, and the server needs no edit; a third store is one entry of `STORE_DIR_BY_ROUTE_PREFIX` in `config.py` and its read-only mount on the `dashboard` service, and the places that list the prefixes move with it (`DASHBOARD-CONVENTIONS-ONE-SERVER-OF-THREE-PREFIXES`); every key the file carries enters the register in the same commit (`AGENT-FIRST-DEVELOPMENT-NAME-ENTERS-THE-REGISTER`) |
| a column or a cell | one edit in the render function that emits the row, the header being built beside it (`DASHBOARD-CONVENTIONS-A-TABLE-BUILDS-ITS-HEADER-BESIDE-ITS-ROWS`); the key it reads is the snapshot's, registered in `module_skills/skill_glossary.md` by the module that measured it |
| a provider or an asset | nothing here: the data views build one frame, one column and one share cell per entry of the snapshot's `source_venues`, the ML views one pill and one PROPOSALS frame per asset of `assets` (`DASHBOARD-CONVENTIONS-A-SECTION-BUILDS-ONE-PART-PER-MEMBER`) |
| an action of the terminal | a target of the Makefile carrying a `##` whose name `MENU_TARGET_PATTERN` of `sub_module_terminal/config.py` matches |

## Design rationale

Why each object of this module sits where it does — the answers the naming review asks for
(`SELF-EXPLAINING-NAMING-A-NEW-OBJECT-PASSES-THE-NAMING-REVIEW`) written down, one row per object, analogous pair
or the module's documents; the mapping row it answers to is a row of the mapping table of `module_skills/README.md`
§ The Pre-AWS mapping, cited by its *responsibility* column and never repeated
(`PRE-AWS-SOLUTION-A-PLACEMENT-ANSWERS-TO-ONE-RESPONSIBILITY`).

| object | why here | why beside these | why this boundary | answers to |
|---|---|---|---|---|
| `config.py` | The one place this module builds a path (its docstring): the server's port and address, `MODULE_MONITORING_DIR` — this module's own directory, where the page's files are —, the suffixes a page file carries, and the two stores the page reads, each under the prefix the page names it by. | `serve.py` imports it; it reads `STORE_STATUS_DIR` and `STORE_RUN_RECORDS_DIR` from the environment the launcher sets, and the per-asset artifact paths stay in the configs of the modules that produce them. | Its stores are the `STORE_*_DIR` the launcher names, so the server reads the same prefixes from the same stores on whatever host runs the service. | MONITORING — a small reader process |
| `serve.py` | The one server, the dashboard (its docstring; the topology of `module_skills/skill_asset_containers.md`; `DASHBOARD-CONVENTIONS-ONE-SERVER-OF-THREE-PREFIXES`): three prefixes, each translated the way `http.server` translates a path from the directory it names, and 404 for every other path and every directory. | It serves the page's files from this module's directory and the snapshots and the run records from their stores, imports `config.py` alone and nothing of another module, and holds no route of its own: the page names every file it reads. | It binds `CONTAINER_PORT` inside its container and compose publishes the dashboard on loopback alone, so a reader reaches it through the tunnel (`ssh -N -L`, `README.md` § Quickstart) whichever host runs it. | MONITORING — a small reader process |
| `index.html` + `style.css` | The page and its one stylesheet — plain HTML and CSS, read as files (`DASHBOARD-CONVENTIONS-ONE-STATIC-PAGE`). | `index.html` links `style.css` and loads `page.js`, `data.js`, `asset.js`, `features.js`, `ml.js`, `run.js` and `scalability.js` in that order. | Served from `module_monitoring/` on `CONTAINER_PORT`, the page opens at the same address through the tunnel whichever host serves it. | MONITORING — the static dashboard |
| `page.js` | The functions every section loads — `millisecondsSinceEpoch`, the one parser of the UTC text the snapshots and the records carry, and the `format`, `build`, `append`, `render` and `init` families, `buildTable` and `renderTable` among them — and the state the tab machinery keeps (its header comment). | `index.html` loads it first, so the section scripts call it and it calls none of them. | It writes into no section's element (`DASHBOARD-CONVENTIONS-TOOLKIT-WRITES-NO-SECTION`), so every section loads the same file from the same root wherever the server runs. | MONITORING — the static dashboard |
| `asset.js`, `data.js`, `features.js`, `ml.js`, `run.js`, `scalability.js` | The section scripts, one per tab family — the ML assets panel, the pipeline and data-quality tabs, the Features tab, the ML research tabs, the Lifecycle tab, the Scalability tab (their header comments). | Analogous scripts over `page.js`: `data.js` fetches `status/data_status.json`, naming no provider — it builds one section, one column and one share cell per entry of the snapshot's `source_venues`; `ml.js` fetches `status/ml_status.json` and `status/features_status.json` and feeds `asset.js` and `features.js`; `run.js` fetches `run_records/index.json` and the records its newest run lists; `scalability.js` fetches `status/skills_status.json`. | Each renders numbers a snapshot or a run record already holds and derives no result of its own — only presentation arithmetic over what was measured, which `DASHBOARD-CONVENTIONS-PRESENTATION-ARITHMETIC-ONLY` licenses — so the page reads the same relative paths wherever it is served. | MONITORING — the static dashboard |
| `__init__.py` | The package that makes `python -m module_monitoring.serve` a command, its docstring the module's responsibility in one line. | It names the page, what it composes and the server, and imports nothing. | The same `python -m module_monitoring.serve` is the `dashboard` service's command (`docker-compose.yml`), unchanged whichever host starts it. | MONITORING — a small reader process |
| `sub_module_terminal/` | The module's terminal, the hand's instrument over its switch: `terminal.py` with `main()`, its own `config.py`, `tui.py` and its front door `README_sub_module_terminal.md` — the shape every module's terminal shares (`AGENTS.md` § Canonical vocabulary, the row *sub-modules*); its rules are the canon's, `module_skills/skill_tui_designer.md`. | Nested because it is an entry point and not a stage: it shows the four snapshots the page reads, through its own `config.py`, and starts `on` or `off` through `make` and nothing else; `tui.py` is one file with every other terminal's, the canon's among them — five times by extraction. | It runs on the host's `python3` with gum, in no container and no venv, reads the status store the launcher names and computes nothing; the Makefile it calls is the one of the directory it was opened in. | no row — a hand's instrument over the Makefile, beside the module whose targets it starts |
| `store/status/data_status.json` + `store/status/features_status.json` + `store/status/ml_status.json` + `store/status/skills_status.json` | Status objects that `module_data/status.py`, `module_features/status.py`, `module_ml/status.py` and the crawler write into the status store and the page reads, committed so the page opens on a fresh clone (§ What it runs). | Outside this module, in the status store beside the other stores; `serve.py` serves that store under `/status/`, and the page names each snapshot by its file name there. | Their paths are `STORE_STATUS_DIR / <name>` in the configs that write them and the one prefix of this module's config that reads them, so the page reads the same names from the same store on any host. | STORAGE — status, run and trial objects |
| the module's documents — `README_module_monitoring.md`, `skills/` and the sub-module's README | This orientation, the page's rules in `skills/` — rendered from `module_skills/skills_sheet.xlsx` by `make skills-sync`, never edited by hand — and the sub-module's front door, filed by ownership (`AGENTS.md` § The default choice). | The orientation points at the documents beside it (§ Its normative skills), every rule about the page sits in `skills/` (`AGENTS.md` § Canonical vocabulary, the row *a module's own skills*), and the terminal's rules are the canon's, with every other terminal's. | Tracked files under `module_monitoring/` that no stage reads and the server never serves, travelling with the code beside them. | no row — a document that travels with the module's code, beside it |

## Its normative skills

| document | answers |
|---|---|
| `skills/skill_dashboard_conventions.md` | the static page and its toolkit, the names of its scripts and classes, how it shows a number, the state it keeps and the arithmetic it may do, what it reads and by which path, and the one server of three prefixes that serves it on loopback |
| `module_skills/skill_tui_designer.md` | the monitoring terminal with every other terminal: its screens, its actions — here the presentation switch —, what it starts through make, and its exits |

The compose topology is a contract between the
infrastructure and all four runtime modules, so it lives in
`module_skills/skill_asset_containers.md`,
not here. The rest of the project-wide rules are indexed by
`module_skills/README.md`.
