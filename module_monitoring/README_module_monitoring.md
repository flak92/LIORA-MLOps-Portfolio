# module_monitoring — what the runtime modules measured, made readable

The front door of this module: what it is, where its responsibility stops, and
how to run it. The page's own conventions and the developer-experience drawing
are `skills/` and are not repeated here. *The repository shows the destination,
not the road*.

`module_monitoring` computes nothing about the market. It presents what
`module_data` and `module_ml` already measured about themselves, and it runs
the one server that serves it.

## Where the responsibility stops

It reads snapshots; it never opens an asset's database and never recomputes a
number. Every value on the page was produced by the module that owns it —
`module_data/status.py` and `module_ml/status.py`. A metric that does not exist
in a snapshot does not appear on the page.

The same line is a storage seam: the two snapshots are status objects this
module reads and never produces, and the run record is the run object it writes
— about the run, not about the market; the page and its scripts are static
files; only the registry, run and proxy routes are a running process. The
direction:
[../module_skills/skill_pre_aws_solution.md](../module_skills/skill_pre_aws_solution.md).

## What it runs

| piece | entry | does |
|---|---|---|
| the server | `make docker-up` | one server, two roles by `ASSET`: the dashboard, or one asset container reporting itself |
| the run recorder | `make docker-all-record` | wraps every stage of a run, samples resources, writes `store_run_records/<run_id>/` |
| the drawing | `make monitoring-dx-update` | redraws the tracked git tree as one self-contained page, in two views: the tree as tracked, and the same tree seated on the primitives the Pre-AWS mapping names |
| the DevOps panel | `make docker-up` | `sub_module_devops`: the containers, networks and volumes, and the one container that holds the docker socket |

The dashboard is published on the host at `127.0.0.1:8900` and reaches the
asset containers by compose service name. The two snapshots it reads,
`data_status.json` and `ml_status.json`, are committed so the page opens on a
fresh clone.

## Its normative skills

| document | answers |
|---|---|
| `skills/skill_dashboard_conventions.md` | the static page, its BEM classes and its state |
| `skills/skill_developer_experience_drawing.md` | the drawing and its configuration surface, key by key |
| `skills/skill_devops_panel.md` | the DevOps panel: its views, the action allowlist and its guard, and the one socket |

The compose topology and the container endpoint are a contract between the
infrastructure and all three runtime modules, so they live in
[../module_skills/skill_asset_containers.md](../module_skills/skill_asset_containers.md),
not here. The rest of the repository-wide rules are indexed by
[../module_skills/README.md](../module_skills/README.md).
