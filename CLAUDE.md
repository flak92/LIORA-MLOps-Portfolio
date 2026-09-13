# CLAUDE.md — the way into the contract

This file points; it carries no rule of its own, so nothing here can disagree
with the document it points at. It exists because an agent session loads this
filename and not `AGENTS.md`.

`AGENTS.md` is the governing contract. **Read it in full before the first edit
of a session.** If a change conflicts with it, the change is wrong.

## The working path

`AGENTS.md` → module names → `README_module_<name>.md` → the module's own
`skills/` → code. `README.md` is general information, not part of that path.

## The modules

| module | orientation | its own rules |
|---|---|---|
| `module_data/` | `module_data/README_module_data.md` | `module_data/skills/` |
| `module_features/` | `module_features/README_module_features.md` | `module_features/skills/` |
| `module_ml/` | `module_ml/README_module_ml.md` | `module_ml/skills/` |
| `module_monitoring/` | `module_monitoring/README_module_monitoring.md` | `module_monitoring/skills/` |

## Beside them

`module_skills/` holds the rules that cross modules, indexed by
`module_skills/README.md`. The name register is `module_skills/glossary.md`.
How an agent is expected to work here is
`module_skills/skill_agent_first_development.md` — read it once before
proposing structure.

Sections of `AGENTS.md` worth naming: § Values, § Architecture shape,
§ Canonical vocabulary, § Rejected vocabulary, § The default choice,
§ The shape — what holds the project together, § Skills absent here, described.

## Running it

Everything goes through the Makefile. `make help` lists every target with its
one-line purpose — read the targets there, never from prose.
