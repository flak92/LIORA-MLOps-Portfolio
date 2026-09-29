# CLAUDE.md — the way into the contract

@AGENTS.md

The line above loads `AGENTS.md` whole: it is the governing contract, and this
file adds no rule of its own, so nothing here can disagree with it. It exists
because an agent session loads this filename and not `AGENTS.md`.

## The working path

`AGENTS.md` → module names → `README_module_<name>.md` → the module's own
`skills/` and the skills beside its sub-modules → code. `README.md` is general
information, not part of that path.

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
Every skill and the register are rendered from `module_skills/skills_sheet.xlsx`
by `make skills-sync` and never edited by hand: a rule changes on the sheet.
How an agent is expected to work here is
`module_skills/skill_agent_first_development.md` — read it once before
proposing structure.

Sections of `AGENTS.md` worth naming: § Values, § Architecture shape,
§ Canonical vocabulary, § Rejected vocabulary, § The default choice,
§ The shape — what holds the project together, § Skills absent here, described.

## Running it

Everything goes through the Makefile. `make help` lists every action target with
its one-line purpose — read the targets there, never from prose. The entries that
open a module's terminal, `make <module>-terminal`, are not actions and carry no
line there.
