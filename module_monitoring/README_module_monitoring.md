# module_monitoring — what the runtime modules measured, made readable

The front door of this module: what it is, where its responsibility stops, and
how to run it. The page's own conventions and the DevOps panel are `skills/` and
are not repeated here. *The repository shows the destination, not the road*.

`module_monitoring` computes nothing about the market. It presents what
`module_data`, `module_features` and `module_ml` already measured about
themselves and the dates `skills_status.json` holds, and it runs the one
server that serves it.

## Where the responsibility stops

It reads snapshots; it never opens an asset's database and never recomputes a
number. Every value on the page comes from a snapshot — the three
`module_data/status.py`, `module_features/status.py` and `module_ml/status.py` write, and the fourth, `skills_status.json`. A metric that does not exist
in a snapshot does not appear on the page.

The same line is a storage seam: the four snapshots are status objects this module reads and never produces, and the run record is the run object `record.py` writes from outside every stage and this module reads
— about the run, not about the market; the page and its scripts are static
files; only the run and proxy routes are a running process. The
direction:
[../module_skills/skill_pre_aws_solution.md](../module_skills/skill_pre_aws_solution.md).

## What it runs

| piece | entry | does |
|---|---|---|
| the server | `make on` | one server, the `dashboard` resident |
| the DevOps panel | `make on` | `sub_module_devops`, the `devops` resident: the containers, networks and volumes, and the one container that holds the docker socket |

`make on` brings the two residents up
together, in the one image, `liora-1m-pipeline`, and prints the address.

The dashboard is published on the host at `127.0.0.1:<port>` — the address
`make on` prints (`../module_skills/skill_asset_containers.md` § The
topology). The four snapshots it reads,
`store/status/data_status.json`, `store/status/features_status.json`, `store/status/ml_status.json` and
`store/status/skills_status.json`,
live in the status store beside the other stores, are served under `/store_status/<name>`, and are committed so the page opens on a fresh clone.

## Design rationale

Why each object of this module sits where it does — the answers of
`../module_skills/skill_self_explaining_naming.md` § The naming review written
down, one row per object, analogous pair or the module's documents; the mapping
row it answers to is `../module_skills/skill_pre_aws_solution.md` § The mapping
table, cited by its *responsibility* column and never repeated.

| object | why here | why beside these | why this boundary | answers to |
|---|---|---|---|---|
| `config.py` | The one place this module builds a path or a URL (its docstring): the directory of a run record under `store/run_records/<run_id>/`, the panel's compose service name on the internal port, the polling cadence, the bound on a proxied exchange (`PANEL_FETCH_TIMEOUT_SECONDS`; the panel's own Engine bound is `ENGINE_EXCHANGE_TIMEOUT_SECONDS` in `sub_module_devops/config.py`) and `MODULE_MONITORING_DIR` — this module's own directory, the web root `serve.py` serves the page from. | `serve.py` and `sub_module_devops/serve.py` import it, it reads `STORE_RUN_RECORDS_DIR` and `STORE_STATUS_DIR` from the environment the launcher sets, and the per-asset artifact paths stay in the configs of the modules that produce them (its docstring). | Its address is a compose service name on `CONTAINER_PORT` and its record root is the `STORE_RUN_RECORDS_DIR` the launcher names, so a reader reaches `devops` by the same name and a record lands in the same store on whatever host runs the services. | MONITORING — a small reader process |
| `serve.py` | The one server, the dashboard (its docstring; `../module_skills/skill_asset_containers.md` § The topology): its directory with its run and proxy routes. | It serves `module_monitoring/` as a directory — the page, its scripts and `sub_module_devops/` — maps the route `/store_status/<name>` onto `store_status_file()` of `config.py` for the snapshots, answers `/runs/<run_id>` with the stage records `record.py` left, and imports nothing of another module. | It binds `CONTAINER_PORT` inside its container and compose publishes the dashboard on loopback alone (§ What it runs; `skills/skill_dashboard_conventions.md`), so a reader reaches it through the tunnel (`ssh -L`, `README.md` § Quickstart) whichever host runs it. | MONITORING — a small reader process |
| `index.html` + `style.css` | The page and its one stylesheet — plain HTML and CSS that `serve.py` serves as files from its directory (`skills/skill_dashboard_conventions.md`). | `index.html` links `style.css` and loads `page.js`, `data.js`, `asset.js`, `ml.js`, `run.js` and `scalability.js` in that order, and `sub_module_devops/index.html` links the same stylesheet. | Served from `module_monitoring/` on `CONTAINER_PORT`, the page opens at the same address through the tunnel whichever host serves it. | MONITORING — the static dashboard |
| `page.js` | The functions both pages load — `millisecondsSinceEpoch`, the one parser of the UTC text the snapshots and the recorder write, and the `format`, `build`, `append`, `render` and `init` families, `buildTable` and `renderTable` among them — and `PILL_HOOKS`, the state the pill machinery keeps (its header comment). | `index.html` loads it first and `sub_module_devops/index.html` loads it too, so `data.js`, `asset.js`, `ml.js`, `run.js`, `scalability.js` and `devops.js` call it and it calls none of them. | It writes into no page-specific element, so the panel a directory below loads the same file from the same root wherever the server runs. | MONITORING — the static dashboard |
| `asset.js`, `data.js`, `ml.js`, `run.js`, `scalability.js` | The section scripts of the status page, one per tab family — the ML assets panel, the pipeline and data-quality tabs, the ML research tabs, the lifecycle tab, the scalability tab (their header comments). | Analogous scripts over `page.js`: `data.js` fetches `/store_status/data_status.json`, naming no provider — it builds one section, one column and one share cell per entry of the snapshot's `source_venues`, and sets each asset's observation lag and measurement age against its `download_cadence_minutes`, `ml.js` fetches `/store_status/ml_status.json` and `/store_status/features_status.json` and feeds `asset.js`; `run.js` fetches `runs` and `runs/<run_id>`, and `scalability.js` fetches `/store_status/skills_status.json`. | Each renders numbers a snapshot or the run record already holds and derives no result of its own — only presentation arithmetic over what was measured, which `skills/skill_dashboard_conventions.md` licenses (§ Where the responsibility stops), so the page reads the same snapshot names and the same `/runs` routes wherever it is served. | MONITORING — the static dashboard |
| `__init__.py` | The package that makes `python -m module_monitoring.serve` a command, its docstring the module's responsibility in one line. | It names the server and the record it reads, and imports nothing. | The same `python -m module_monitoring.serve` is the `dashboard` service's command (`docker-compose.yml`), unchanged whichever host starts it. | MONITORING — a small reader process |
| `sub_module_devops/` | The engine's views: its own `serve.py` speaks the Docker Engine API over the one socket, with its own `config.py`, `main()`, page and scripts (`skills/skill_devops_panel.md` § The one socket, and what containment means). | Nested because the dashboard serves its own directory (`skills/skill_devops_panel.md` § Why a sub-module, and why that name), and the dashboard proxies its API under `/devops/*` by service name while its page loads `page.js`. | The socket is mounted into `devops` and no other service, and `devops` publishes no port (`../module_skills/skill_asset_containers.md` § The topology), so the panel is reached only through the dashboard's proxy — the same socket path and the same route behind the tunnel, whichever host's daemon it reads. | INFRASTRUCTURE — the engine's views |
| `store/status/data_status.json` + `store/status/features_status.json` + `store/status/ml_status.json` + `store/status/skills_status.json` | Status objects in the status store that the page reads — the three `module_data/status.py`, `module_features/status.py` and `module_ml/status.py` write, and the fourth, `skills_status.json` — committed so the page opens on a fresh clone (§ What it runs). | Outside this module, in the status store beside the other stores; `serve.py` maps the route segment `STORE_STATUS_ROUTE_SEGMENT` onto `store_status_file()` under `STORE_STATUS_DIR` — `/store_status/data_status.json` in `data.js`, and in `ml.js` and `scalability.js` the one prefix `/store_status/` with their file names. | Their paths are `STORE_STATUS_DIR / <name>` in the configs of the three modules that write them and in this module's config that reads them; the five points that turned when the snapshots left this directory — two path constants, the served root, two literal fetches — are the ones `../module_skills/skill_pre_aws_solution.md` § What stays as it is, and why, named; the third snapshot arrived by the same route. | STORAGE — status and run objects |
| the module's documents — `README_module_monitoring.md` and `skills/` | This orientation and the normative documents of `skills/`, filed by ownership (`../AGENTS.md` § The default choice). | The orientation points at the documents beside it (§ Its normative skills), and every rule about this module sits in `skills/` (`../AGENTS.md` § Canonical vocabulary, the row *a module's own skills*). | Tracked files under `module_monitoring/` that no stage and no route reads, travelling with the code beside them — the same paths beside the code wherever the code is. | no row — a document that travels with the task's code, seated beside its module |

## Its normative skills

| document | answers |
|---|---|
| `skills/skill_dashboard_conventions.md` | the static page, its BEM classes and its state |
| `skills/skill_devops_panel.md` | the DevOps panel: its views, the action allowlist and its guard, and the one socket |

The compose topology is a contract between the
infrastructure and all four runtime modules, so it lives in
[../module_skills/skill_asset_containers.md](../module_skills/skill_asset_containers.md),
not here. The rest of the project-wide rules are indexed by
[../module_skills/README.md](../module_skills/README.md).
