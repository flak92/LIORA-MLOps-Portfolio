# module_monitoring — what the runtime modules measured, made readable

The front door of this module: what it is, where its responsibility stops, and
how to run it. The page's own conventions and the DevOps panel are `skills/` and
are not repeated here; the developer-experience drawing the page's **DX** jump opens
is the Orchestration repository's, `sub_module_dx/`, governed by
`../module_skills/skill_developer_experience_drawing.md`. *The repository shows the
destination, not the road*.

`module_monitoring` computes nothing about the market. It presents what
`module_data`, `module_features` and `module_ml` already measured about
themselves, and it runs the one server that serves it.

## Where the responsibility stops

It reads snapshots; it never opens an asset's database and never recomputes a
number. Every value on the page was produced by the module that owns it —
`module_data/status.py`, `module_features/status.py` and `module_ml/status.py`. A metric that does not exist
in a snapshot does not appear on the page.

The same line is a storage seam: the three snapshots are status objects this
module reads and never produces, and the run record is the run object the
repository's `record.py` writes from outside every stage and this module reads
— about the run, not about the market; the page and its scripts are static
files; only the registry, run and proxy routes are a running process. The
direction:
[../module_skills/skill_pre_aws_solution.md](../module_skills/skill_pre_aws_solution.md).

## What it runs

| piece | entry | does |
|---|---|---|
| the server | `make on` | one server, two roles by `ASSET`: the dashboard, or one asset container reporting itself |
| the DevOps panel | `make on` | `sub_module_devops`: the containers, networks and volumes, and the one container that holds the docker socket |

The dashboard is published on the host at `127.0.0.1:<port>` — the address
`make on` prints (`../module_skills/skill_asset_containers.md` § The
topology) — and reaches the asset containers by compose service name. The three snapshots it reads,
`store_status/data_status.json`, `store_status/features_status.json` and `store_status/ml_status.json`,
live in the status store beside the other stores, are served under `/store_status/<name>`, and are committed so the page opens on a fresh clone.

## Design rationale

Why each object of this module sits where it does — the answers of
`../module_skills/skill_self_explaining_naming.md` § The naming review written
down, one row per object, analogous pair or the module's documents; the mapping
row it answers to is `../module_skills/skill_pre_aws_solution.md` § The mapping
table, cited by its *responsibility* column and never repeated.

| object | why here | why beside these | why this boundary | answers to |
|---|---|---|---|---|
| `config.py` | The one place this module builds a path or a URL (its docstring): the directory of a run record under `store_run_records/<run_id>/`, the compose services' names on the internal port, the polling cadence, the two units the endpoint converts with, and the asset's database files (`asset_databases()`). | `serve.py` and `sub_module_devops/serve.py` import it, it reads `STORE_RUN_RECORDS_DIR`, `STORE_ASSETS_ARTIFACTS_DIR` (the registry lists that store's asset folders) and `STORE_STATUS_DIR` from the environment the launcher sets, and the per-asset artifact paths stay in the configs of the modules that produce them (its docstring). | Its addresses are compose service names on `CONTAINER_PORT` and its record root is the `STORE_RUN_RECORDS_DIR` the launcher names, so a reader reaches `asset-<ticker>` and `devops` by the same names and a record lands in the same store on whatever host runs the services. | MONITORING — a small reader process |
| `serve.py` | The one server, its role chosen by `ASSET` (its docstring; `../module_skills/skill_asset_containers.md` § The server): the dashboard's directory with its registry, run and proxy routes, or one asset container's `/status`. | It serves `module_monitoring/` as a directory — the page, its scripts, `sub_module_devops/`, and the Orchestration repository's `sub_module_dx/`, which its `docker-compose.yml` binds read-only below this directory — maps the route `/store_status/<name>` onto `store_status_file()` of `config.py` for the snapshots, answers `/runs/<run_id>` with the stage records the repository's `record.py` left, and imports nothing of another module: the asset role reads its rows by `ticker`, sizes the database files that lie in its folder, and takes the research window from the ML snapshot. | It binds `CONTAINER_PORT` inside its container and compose publishes the dashboard on loopback alone (§ What it runs; `skills/skill_dashboard_conventions.md`), so a reader reaches it through the tunnel (`ssh -L`, the Orchestration `README.md` § Quickstart) whichever host runs it. | one row per role: MONITORING — a small reader process; COMPUTE — one stage for one asset — the roles are `../module_skills/skill_pre_aws_solution.md` § The resident container is a local mechanism |
| `index.html` + `style.css` | The page and its one stylesheet — plain HTML and CSS that `serve.py` serves as files from its directory (`skills/skill_dashboard_conventions.md`). | `index.html` links `style.css` and loads `page.js`, `data.js`, `asset.js`, `ml.js` and `run.js` in that order, and `sub_module_devops/index.html` links the same stylesheet. | Served from `module_monitoring/` on `CONTAINER_PORT`, the page opens at the same address through the tunnel whichever host serves it. | MONITORING — the static dashboard |
| `page.js` | The functions both pages load — the `format`, `build` and `append` families — and `DATA_STATUS_LOADED`, the one fetch of `/store_status/data_status.json` (its header comment). | `index.html` loads it first and `sub_module_devops/index.html` loads it too, so `data.js`, `asset.js`, `ml.js`, `run.js`, `containers.js` and `devops.js` call it and it calls none of them. | Its one fetch is root-relative, so the panel a directory below reads the same snapshot from the same root wherever the server runs. | MONITORING — the static dashboard |
| `asset.js`, `data.js`, `ml.js`, `run.js` | The section scripts of the status page, one per tab family — the ML assets panel, the pipeline and data-quality tabs, the ML research tabs, the lifecycle tab (their header comments). | Analogous scripts over `page.js`: `data.js` renders `DATA_STATUS_LOADED`, `ml.js` fetches `/store_status/ml_status.json` and `/store_status/features_status.json` and feeds `asset.js`, and `run.js` fetches `runs` and `runs/<run_id>`. | Each renders numbers a snapshot or the run record already holds and computes none (§ Where the responsibility stops), so the page reads the same three snapshot names and the same `/runs` routes wherever it is served. | MONITORING — the static dashboard |
| `__init__.py` | The package that makes `python -m module_monitoring.serve` a command, its docstring the module's responsibility in one line. | It names the server's two roles and the record it reads, and imports nothing. | The same `python -m module_monitoring.serve` is the `x-server` anchor's command (the Orchestration `docker-compose.yml`), unchanged whichever host starts it. | MONITORING — a small reader process |
| `sub_module_devops/` | The engine's views: its own `serve.py` speaks the Docker Engine API over the one socket, with its own `config.py`, `main()`, page and scripts (`skills/skill_devops_panel.md` § The one socket, and what containment means). | Nested because the dashboard serves its own directory (`skills/skill_devops_panel.md` § Why a sub-module, and why that name), and the dashboard proxies its API under `/devops/*` by service name while its page loads `page.js`. | The socket is mounted into `devops` and no other service, and `devops` publishes no port (`../module_skills/skill_asset_containers.md` § The topology), so the panel is reached only through the dashboard's proxy — the same socket path and the same route behind the tunnel, whichever host's daemon it reads. | INFRASTRUCTURE — the engine's views, the repository's view |
| `store_status/data_status.json` + `store_status/features_status.json` + `store_status/ml_status.json` | Status objects that `module_data/status.py`, `module_features/status.py` and `module_ml/status.py` write into the status store and the page reads, committed so the page opens on a fresh clone (§ What it runs). | Outside this module, in the status store beside the other stores; `serve.py` maps the route segment `STORE_STATUS_ROUTE_SEGMENT` onto `store_status_file()` under `STORE_STATUS_DIR` — `/store_status/data_status.json` in `page.js`, `/store_status/ml_status.json` and `/store_status/features_status.json` in `ml.js` — and its asset role reads the data and ML rows for its ticker. | Their paths are `STORE_STATUS_DIR / <name>` in the three configs that write them and in this module's config that reads them; the five points that turned when the snapshots left this directory — two path constants, the served root, two literal fetches — are the ones `../module_skills/skill_pre_aws_solution.md` § What stays as it is, and why, named; the third snapshot arrived by the same route. | STORAGE — status and run objects |
| the module's documents — `README_module_monitoring.md` and `skills/` | This orientation and the normative documents of `skills/`, filed by ownership (`../AGENTS.md` § The default choice). | The orientation points at the documents beside it (§ Its normative skills), and every rule about this module sits in `skills/` (`../AGENTS.md` § Canonical vocabulary, the row *a module's own skills*). | Tracked files under `module_monitoring/` that no process reads, travelling with the code beside them — the same paths beside the code wherever the code is. | no row — a document that travels with the task's code, seated beside its module |

## Its normative skills

| document | answers |
|---|---|
| `skills/skill_dashboard_conventions.md` | the static page, its BEM classes and its state |
| `skills/skill_devops_panel.md` | the DevOps panel: its views, the action allowlist and its guard, and the one socket |

The compose topology and the container endpoint are a contract between the
infrastructure and all four runtime modules, so they live in
[../module_skills/skill_asset_containers.md](../module_skills/skill_asset_containers.md),
not here. The rest of the repository-wide rules are indexed by
[../module_skills/README.md](../module_skills/README.md).
