# module_monitoring — what the runtime modules measured, made readable

The orientation of this module: what it is, where its responsibility stops and how to run it. The page's rules are
`skills/skill_dashboard_conventions.md`; the terminal's are the canon's `module_skills/skill_tui_designer.md`.

`module_monitoring` computes nothing about the market. It presents what `module_data`, `module_features` and
`module_ml` already measured about themselves, what `record.py` measured around every stage of a recorded run and where
the canon's crawler stands; it runs the one server that serves the page, and it carries the terminal a hand switches
that server from.

## Where the responsibility stops

```
status/*.json + run_records/index.json + run_records/<run_id>/<stage>.json → one composed page
```

It reads snapshots and run records by relative path and never recomputes a number: every value on the page was
produced by the program that owns it — `module_data/status.py`, `module_features/status.py`, `module_ml/status.py`,
`module_skills/sub_module_scalability_crawler/status.py` and `record.py` — and what the page adds is presentation
arithmetic (`DASHBOARD-CONVENTIONS-PRESENTATION-ARITHMETIC-ONLY`).

## What it runs

| piece | entry | does |
|---|---|---|
| the server | the `dashboard` service of `make on` | `python -m module_monitoring.serve`, the resident's own `command:` — the page's files under `/`, the status store under `/status/`, the run-records store under `/run_records/`; every other path, and every directory, is 404 |
| the terminal | `make monitoring-terminal` | `sub_module_terminal`: the four snapshots on one screen, then `on` or `off` through `make` — on the host, in no container |
| the presentation switch | `make on` / `make off` | the one resident up with the page's address printed and opened, and every container of this project stopped and removed (`ASSET-CONTAINERS-ON-RAISES-THE-RESIDENT-OFF-TAKES-EVERYTHING-DOWN`) |

The dashboard has no target of its own: it is a service's `command:` in `docker-compose.yml`, mounting the tree and the
two stores it serves read-only, published on the host's loopback alone
(`DASHBOARD-CONVENTIONS-REACHABLE-ON-LOOPBACK-ONLY`); a reader on another machine comes through the tunnel of
`README.md` § Quickstart. The page reads, by relative path (`DASHBOARD-CONVENTIONS-THE-PAGE-READS-BY-RELATIVE-PATH`):

| file | written by | the tab that reads it |
|---|---|---|
| `status/data_status.json` | `module_data.status` | Pipeline and Data Quality |
| `status/features_status.json` | `module_features.status` | Features, ML Research |
| `status/ml_status.json` | `module_ml.status` | ML Research, ML Assets |
| `status/skills_status.json` | the canon's crawler | Scalability |
| `run_records/index.json` and the records it lists | `record.py`, under `make all-record` | Lifecycle |

The four snapshots are committed, so the page opens on a fresh clone; the run records are not, and the Lifecycle tab
says so until the first recorded run.

## Extending

| to add | change |
|---|---|
| a tab | one `<button class="pill" data-key="<key>">` in the `data-pills="tab"` nav, one `<section data-panel="tab" data-key="<key>" hidden>` and one section script in the list at the end of `index.html`, which `initPills` of `page.js` wires by `data-key`; in the same commit every list of the tabs (`DASHBOARD-CONVENTIONS-A-TAB-MOVES-EVERY-LIST-OF-THE-TABS`); a script that holds what it fetched for another script adds a state global, named in `DASHBOARD-CONVENTIONS-TWO-STATE-GLOBALS` |
| a file the page reads | nothing here while it lies in the status store or the run-records store: the page names it under `status/` or `run_records/`, and the server needs no edit; a third store is one entry of `STORE_DIR_BY_ROUTE_PREFIX` in `config.py` and its read-only mount on the `dashboard` service (`DASHBOARD-CONVENTIONS-ONE-SERVER-OF-THREE-PREFIXES`); every key the file carries enters the register in the same commit |
| a column or a cell | one edit in the render function that emits the row, the header being built beside it (`DASHBOARD-CONVENTIONS-A-TABLE-BUILDS-ITS-HEADER-BESIDE-ITS-ROWS`); the key it reads is the snapshot's, registered by the module that measured it |
| a provider or an asset | nothing here: the data views build one part per entry of the snapshot's `source_venues`, the ML views one pill and one PROPOSALS frame per asset (`DASHBOARD-CONVENTIONS-A-SECTION-BUILDS-ONE-PART-PER-MEMBER`) |
| an action of the terminal | a target of the Makefile carrying a `##` whose name `MENU_TARGET_PATTERN` of `sub_module_terminal/config.py` matches |

## Design rationale

Why each object of this module sits where it does, one row per object or analogous pair; the last column is the
responsibility of the mapping table in `module_skills/README.md` § The Pre-AWS mapping it answers to
(`PRE-AWS-SOLUTION-A-PLACEMENT-ANSWERS-TO-ONE-RESPONSIBILITY`).

| object | why here | why beside these | why this boundary | answers to |
|---|---|---|---|---|
| `config.py` | The one place this module builds a path: the server's port and address, this module's own directory, the suffixes a page file carries, and the two stores the page reads, each under the prefix the page names it by. | `serve.py` imports it; it reads `STORE_STATUS_DIR` and `STORE_RUN_RECORDS_DIR` from the environment the launcher sets. | Its stores are the `STORE_*_DIR` the launcher names. | MONITORING — a small reader process |
| `serve.py` | The one server (`DASHBOARD-CONVENTIONS-ONE-SERVER-OF-THREE-PREFIXES`): three prefixes, each translated the way `http.server` translates a path from the directory it names, and 404 for every other path and every directory. | It imports `config.py` alone and holds no route of its own: the page names every file it reads. | It binds `CONTAINER_PORT` inside its container, and compose publishes it on loopback alone. | MONITORING — a small reader process |
| `index.html` + `style.css` | The page and its one stylesheet (`DASHBOARD-CONVENTIONS-ONE-STATIC-PAGE`). | `index.html` links `style.css` and loads `page.js`, `data.js`, `asset.js`, `features.js`, `ml.js`, `run.js` and `scalability.js` in that order. | Served from `module_monitoring/`, the page opens at the same address through the tunnel. | MONITORING — the static dashboard |
| `page.js` | The functions every section loads — the UTC parser and the `format`, `build`, `append`, `render` and `init` families — and the state the tab machinery keeps. | `index.html` loads it first; it calls no section script. | It writes into no section's element (`DASHBOARD-CONVENTIONS-TOOLKIT-WRITES-NO-SECTION`). | MONITORING — the static dashboard |
| `asset.js`, `data.js`, `features.js`, `ml.js`, `run.js`, `scalability.js` | The section scripts, one per tab family (their header comments). | Analogous scripts over `page.js`, each fetching the files of its tabs; `ml.js` feeds `asset.js` and `features.js`. | Each renders what a snapshot or a run record holds, by relative path. | MONITORING — the static dashboard |
| `__init__.py` | The package that makes `python -m module_monitoring.serve` a command, its docstring the module's responsibility in one line. | It imports nothing. | The same command is the `dashboard` service's (`docker-compose.yml`). | MONITORING — a small reader process |
| `sub_module_terminal/` | The module's terminal, the hand's instrument over its switch (`AGENTS.md` § Canonical vocabulary, the row *sub-modules*). | It shows the four snapshots the page reads and starts `on` or `off` through `make` and nothing else. | It runs on the host's `python3` with gum and computes nothing (`TUI-DESIGNER-ONE-TERMINAL-PER-MODULE`). | no row — a hand's instrument over the Makefile, beside the module whose targets it starts |
| `store/status/data_status.json` + `store/status/features_status.json` + `store/status/ml_status.json` + `store/status/skills_status.json` | Status objects the three status stages and the crawler write into the status store and the page reads, committed so the page opens on a fresh clone. | Outside this module, in the status store; `serve.py` serves that store under `/status/`. | Their paths are `STORE_STATUS_DIR / <name>` in the configs that write them and the one prefix of this module's config that reads them. | STORAGE — status, run and trial objects |
| the module's documents — `README_module_monitoring.md`, `skills/` and the sub-module's README | This orientation, the page's rules and the sub-module's orientation, filed by ownership (`AGENTS.md` § The default choice). | Every rule about the page sits in `skills/` (`AGENTS.md` § Canonical vocabulary, the row *a module's own skills*); the terminal's are the canon's. | Tracked files under `module_monitoring/` that no stage reads and the server never serves. | no row — a document that travels with the module's code, beside it |
