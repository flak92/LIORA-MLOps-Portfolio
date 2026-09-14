
## crawled 2026-09-14 05:03 UTC · claude-sonnet-5 · d2fc592
Reviewing `docker-compose.yml` against `AGENTS.md`, `module_skills/glossary.md`, and the cited skills (`skill_agent_first_development.md`, `skill_asset_containers.md`, `skill_determinism.md`, `skill_pre_aws_solution.md`, `skill_scalability_crawler.md`, `skill_self_explaining_naming.md`, `skill_sorting_files_naming_standard.md`).

I checked every service, anchor, mount, environment variable, and literal against the rules text (`x-store-environment`'s five `STORE_*_DIR` plus the thread cap and three mlflow facts, `x-service`/`x-server` roles, the per-service topology table, the socket scope, the port/measurement rules, naming grammar for services/images/project, and the mapping-table exceptions). Every value I checked — `name: liora`, `image: liora-1m-pipeline`, the store env-var set and order, `asset-btc` naming, `127.0.0.1:${PORT:-8900}:8900`, `deploy.resources.limits.memory: 5g` on `ml` alone, the read-only mounts on `dashboard`/`asset-btc`, the single socket mount on `devops`, `group_add: ["${DOCKER_GID:-999}"]`, `user: "${UID:-1000}:${GID:-1000}"` — matches a rule or a table row verbatim, including several passages that are near-literal quotes of `skill_asset_containers.md`.

1. Departures: none found.

2. Unexplained: the fallback literals `1000` (`UID`/`GID`) and `999` (`DOCKER_GID`) are prescribed verbatim by `module_skills/skill_asset_containers.md` § The topology, but neither the file nor the rules say why those specific numbers were chosen as defaults (as opposed to, e.g., `100`/`0`).

3. No repeated, rule-ungoverned pattern stood out on close inspection — the recurring `${VAR:-default}` fallback syntax (`UID`, `GID`, `PORT`, `DOCKER_GID`) is each individually prescribed by name in `skill_asset_containers.md`, and the mixed `"true"`/`"1"` string values on the mlflow variables sit at the external-library boundary (`AGENTS.md` § Canonical vocabulary, the external-vocabulary boundary), so the inconsistency is mlflow's own, not the file's.

4. conformant


## crawled 2026-09-14 07:47 UTC · claude-sonnet-5 · 20ac2db
Reviewing `docker-compose.yml` against `AGENTS.md`, `module_skills/glossary.md`, `skill_agent_first_development.md`, `skill_asset_containers.md`, `skill_determinism.md`, `skill_pre_aws_solution.md`, `skill_scalability_crawler.md`, `skill_self_explaining_naming.md`, and `skill_sorting_files_naming_standard.md`.

1. Departures from a rule
None found. The two anchors, the five services, their store mounts, the `5g` ceiling on `ml` alone, the port mapping `127.0.0.1:${PORT:-8900}:8900`, the socket mount confined to `devops`, `group_add: ["${DOCKER_GID:-999}"]`, `init: true`, `user: "${UID:-1000}:${GID:-1000}"`, the `name: liora` project pin, and the store-variable order (`STORE_RAW_1M_DIR`, `STORE_ASSETS_ARTIFACTS_DIR`, `STORE_TRIALS_DIR`, `STORE_RUN_RECORDS_DIR`, `STORE_STATUS_DIR`) each match `skill_asset_containers.md` § The topology and `module_skills/glossary.md` § Stores / § Asset containers verbatim, including the per-service subset of mounts each runner and resident is given.

2. What the file leaves unexplained
- Line ~63 (`devops` comment): "its environment still carries the five store names from the anchor, because its server imports `module_monitoring/config.py`, which reads two of them at import." Which two `STORE_*_DIR` are read is asserted but not named, and no rule in this file's scope (`AGENTS.md` § Twice by extraction only names `STORE_ASSETS_ARTIFACTS_DIR`, `STORE_STATUS_DIR` as read by `module_monitoring/config.py`, matching "two" — but a reader of this file plus the cited rules alone cannot confirm the count without reading that config module).
- The specific mlflow variable spellings `MLFLOW_DISABLE_TELEMETRY` / `MLFLOW_DISABLE_AGENT_HINT` are asserted by inline comment to be mlflow's own vocabulary, but no rule here names them, so a reader cannot confirm they are mlflow-skinny's real switches rather than invented names — only the file's own prose vouches for them.

3. A pattern seen twice or more that no rule governs
The two YAML anchor identifiers, `&store_environment` (from `x-store-environment`) and `&service` (from `x-service`), are each derived by stripping the `x-` prefix and turning `-` into `_`. No grammar row in `AGENTS.md` § Canonical vocabulary or `skill_self_explaining_naming.md` governs YAML anchor names; a third anchor minted without following this silent pattern (e.g. an anchor named arbitrarily unrelated to its `x-key`) would go unflagged by any written rule.

4. conformant

