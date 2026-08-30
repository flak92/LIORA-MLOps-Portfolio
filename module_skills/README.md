# Repository skills — the index

Where every rule of this repository is written down. This file links; it holds
no rule of its own, so nothing here can disagree with the document it points
at. *The repository shows the destination, not the road*.

Ownership decides location, and `AGENTS.md` § The default choice holds the rule:

```
a rule about one module          → module_<name>/skills/
a rule about several, or the repo → module_skills/
one module's orientation          → module_<name>/README_module_<name>.md
```

A skill exists **once**, in the directory its ownership names. There is no
second copy anywhere in this tree.

## Cross-cutting — the skills in this directory

| skill | what it governs |
|---|---|
| [glossary.md](glossary.md) | the name register: one concept, one name, in code, artifacts and interface |
| [skill_agent_first_development.md](skill_agent_first_development.md) | how an agent works on this repository — subtract, don't add |
| [skill_asset_containers.md](skill_asset_containers.md) | the compose topology, the container endpoint and the scoped socket rule — the runtime contract every module runs inside |
| [skill_determinism.md](skill_determinism.md) | bit parity, thread caps and where speed is allowed to come from |
| [skill_self_explaining_naming.md](skill_self_explaining_naming.md) | names derived from a closed grammar, and how a new convention is minted |
| [skill_sorting_files_naming_standard.md](skill_sorting_files_naming_standard.md) | taxonomic ordering, zero-padding and the timeframe slot standard |

`skill_asset_containers.md` is the worked example of the cross-cutting
boundary: it describes one image, the `pipeline` and `asset-<ticker>` services,
the Makefile fan-out, the memory ceilings, the bind mount and the dashboard's
reach into the asset containers — a contract between the infrastructure and
`module_data`, `module_ml` and `module_monitoring` alike. It belongs to no
single module, so it stays here.

## module_data

Orientation: [../module_data/README_module_data.md](../module_data/README_module_data.md)

| skill | what it governs |
|---|---|
| [../module_data/skills/skill_candle_canonicalisation.md](../module_data/skills/skill_candle_canonicalisation.md) | candle validity, the primary-failover decision table, volume, forward fill, provenance and the canonical storage |
| [../module_data/skills/methodology_data.md](../module_data/skills/methodology_data.md) | the venue endpoints, units and time, and the limitations of acquisition |

## module_ml

Orientation: [../module_ml/README_module_ml.md](../module_ml/README_module_ml.md)

| skill | what it governs |
|---|---|
| [../module_ml/skills/methodology_ml.md](../module_ml/skills/methodology_ml.md) | the research layer equation by equation, with its citations |

## module_monitoring

Orientation: [../module_monitoring/README_module_monitoring.md](../module_monitoring/README_module_monitoring.md)

| skill | what it governs |
|---|---|
| [../module_monitoring/skills/skill_dashboard_conventions.md](../module_monitoring/skills/skill_dashboard_conventions.md) | the static page, its BEM classes and its state |
| [../module_monitoring/skills/skill_developer_experience_drawing.md](../module_monitoring/skills/skill_developer_experience_drawing.md) | the developer-experience drawing and its configuration surface |
| [../module_monitoring/skills/skill_devops_panel.md](../module_monitoring/skills/skill_devops_panel.md) | the DevOps panel: its views, the action allowlist and its guard, and the one docker socket |
