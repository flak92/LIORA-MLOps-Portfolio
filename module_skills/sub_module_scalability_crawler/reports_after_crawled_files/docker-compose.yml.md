
## crawled 2026-09-14 05:03 UTC · claude-sonnet-5 · d2fc592
Reviewing `docker-compose.yml` against `AGENTS.md`, `module_skills/glossary.md`, and the cited skills (`skill_agent_first_development.md`, `skill_asset_containers.md`, `skill_determinism.md`, `skill_pre_aws_solution.md`, `skill_scalability_crawler.md`, `skill_self_explaining_naming.md`, `skill_sorting_files_naming_standard.md`).

I checked every service, anchor, mount, environment variable, and literal against the rules text (`x-store-environment`'s five `STORE_*_DIR` plus the thread cap and three mlflow facts, `x-service`/`x-server` roles, the per-service topology table, the socket scope, the port/measurement rules, naming grammar for services/images/project, and the mapping-table exceptions). Every value I checked — `name: liora`, `image: liora-1m-pipeline`, the store env-var set and order, `asset-btc` naming, `127.0.0.1:${PORT:-8900}:8900`, `deploy.resources.limits.memory: 5g` on `ml` alone, the read-only mounts on `dashboard`/`asset-btc`, the single socket mount on `devops`, `group_add: ["${DOCKER_GID:-999}"]`, `user: "${UID:-1000}:${GID:-1000}"` — matches a rule or a table row verbatim, including several passages that are near-literal quotes of `skill_asset_containers.md`.

1. Departures: none found.

2. Unexplained: the fallback literals `1000` (`UID`/`GID`) and `999` (`DOCKER_GID`) are prescribed verbatim by `module_skills/skill_asset_containers.md` § The topology, but neither the file nor the rules say why those specific numbers were chosen as defaults (as opposed to, e.g., `100`/`0`).

3. No repeated, rule-ungoverned pattern stood out on close inspection — the recurring `${VAR:-default}` fallback syntax (`UID`, `GID`, `PORT`, `DOCKER_GID`) is each individually prescribed by name in `skill_asset_containers.md`, and the mixed `"true"`/`"1"` string values on the mlflow variables sit at the external-library boundary (`AGENTS.md` § Canonical vocabulary, the external-vocabulary boundary), so the inconsistency is mlflow's own, not the file's.

4. conformant

