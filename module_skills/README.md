# Project skills — the index

Where every rule of the project is written down. This file links; it holds no
rule of its own, so nothing here can disagree with the document it points at.
*The repository shows the destination, not the road*.

Ownership decides location, and `AGENTS.md` § The default choice holds the rule:
a module's own skills live in that module's repository, the skills that cross
modules live here, in `module_skills/` of `LIORA-MLOps-Portfolio-Orchestration`
— the canon, of which every module repository carries a read-only copy stamped
by `distributed_from.md`. A link to a module's skill is an absolute URL, because
a relative path would resolve from neither the canon nor a copy; wherever you
read this file, those links point at the same document.

## Cross-cutting — the skills in this directory

| skill | what it governs |
|---|---|
| [glossary.md](glossary.md) | the name register: one concept, one name, in code, artifacts and interface — and the register of the duplicates no module may import across |
| [skill_agent_first_development.md](skill_agent_first_development.md) | how an agent works on this project — subtract, don't add |
| [skill_asset_containers.md](skill_asset_containers.md) | the compose topology — four images, three runners, three residents —, the container endpoint and the scoped socket rule: the runtime contract every module runs inside |
| [skill_determinism.md](skill_determinism.md) | bit parity, thread caps and where speed is allowed to come from |
| [skill_developer_experience_drawing.md](skill_developer_experience_drawing.md) | the developer-experience drawing of the whole tracked tree — the Orchestration repository's own, served by the dashboard — its two views and its configuration surface |
| [skill_pre_aws_solution.md](skill_pre_aws_solution.md) | the Pre-AWS direction: which local boundary answers to which standard cloud primitive, the twelve classes, the four seat paragraphs, the ladder, the non-goals, what the split added and what it did not, and why none of it is built |
| [skill_self_explaining_naming.md](skill_self_explaining_naming.md) | names derived from a closed grammar, and how a new convention is minted |
| [skill_sorting_files_naming_standard.md](skill_sorting_files_naming_standard.md) | taxonomic ordering, zero-padding and the timeframe slot standard |

## Described, not written

Skills that exist as rows and not as files, each placed by ownership, with the
one condition under which it is written:
[../AGENTS.md](../AGENTS.md) § Skills absent here, described. This index holds
no row of it.

## module_data — `LIORA-MLOps-Portfolio-module-data`

Orientation: [README_module_data.md](https://github.com/flak92/LIORA-MLOps-Portfolio-module-data/blob/main/module_data/README_module_data.md)

| skill | what it governs |
|---|---|
| [skill_candle_canonicalisation.md](https://github.com/flak92/LIORA-MLOps-Portfolio-module-data/blob/main/module_data/skills/skill_candle_canonicalisation.md) | candle validity, the primary-failover decision table, volume, forward fill, provenance and the canonical storage |
| [methodology_data.md](https://github.com/flak92/LIORA-MLOps-Portfolio-module-data/blob/main/module_data/skills/methodology_data.md) | the venue endpoints, units and time, and the limitations of acquisition |

## module_features — `LIORA-MLOps-Portfolio-module-features`

Orientation: [README_module_features.md](https://github.com/flak92/LIORA-MLOps-Portfolio-module-features/blob/main/module_features/README_module_features.md)

| skill | what it governs |
|---|---|
| [skill_feature_taxonomy.md](https://github.com/flak92/LIORA-MLOps-Portfolio-module-features/blob/main/module_features/skills/skill_feature_taxonomy.md) | the timeframe register, the terms, the composition grammar, the scope nesting and the warm-up |
| [methodology_features.md](https://github.com/flak92/LIORA-MLOps-Portfolio-module-features/blob/main/module_features/skills/methodology_features.md) | every catalogued feature definition, equation by equation, with its histories and citations |

## module_ml — `LIORA-MLOps-Portfolio-module-ml`

Orientation: [README_module_ml.md](https://github.com/flak92/LIORA-MLOps-Portfolio-module-ml/blob/main/module_ml/README_module_ml.md)

| skill | what it governs |
|---|---|
| [methodology_ml.md](https://github.com/flak92/LIORA-MLOps-Portfolio-module-ml/blob/main/module_ml/skills/methodology_ml.md) | the research layer equation by equation, with its citations |

## module_monitoring — `LIORA-MLOps-Portfolio-module-monitoring`

Orientation: [README_module_monitoring.md](https://github.com/flak92/LIORA-MLOps-Portfolio-module-monitoring/blob/main/module_monitoring/README_module_monitoring.md)

| skill | what it governs |
|---|---|
| [skill_dashboard_conventions.md](https://github.com/flak92/LIORA-MLOps-Portfolio-module-monitoring/blob/main/module_monitoring/skills/skill_dashboard_conventions.md) | the static page, its BEM classes and its state |
| [skill_devops_panel.md](https://github.com/flak92/LIORA-MLOps-Portfolio-module-monitoring/blob/main/module_monitoring/skills/skill_devops_panel.md) | the DevOps panel: its views, the action allowlist and its guard, and the one docker socket |
