
## crawled 2026-09-14 04:55 UTC · claude-sonnet-5 · d2fc592
**Departures**

- `module_skills/glossary.md` § Documentation ownership (the CLAUDE.md row: "the working path, the modules by name and the documents that hold the rules — it points and holds none") — lines under `## Running it`: "Everything goes through the Makefile. `make help` lists every target with its one-line purpose — read the targets there, never from prose." — current form: a fourth topic (Makefile/`make help` usage, with the directive "never from prose") added beyond the three the register names; the form the rule derives: CLAUDE.md holds only the working path, the modules by name, and the documents that hold the rules, and "carries no rule of its own" (the file's own opening line) — a usage directive is a rule, not a pointer to one of those three.

**Left unexplained**

- The line "Sections of `AGENTS.md` worth naming: § Values, § Architecture shape, § Canonical vocabulary, § Rejected vocabulary, § The default choice, § The shape — what holds the project together, § Skills absent here, described." — why these seven and not others (e.g. § Pre-AWS architectural direction, a section AGENTS.md itself treats as load-bearing) is not decodable from this file or from AGENTS.md/glossary.md alone.

**Pattern seen twice, ungoverned**

- `<citation>` followed by an em dash and an imperative reading directive, used twice: "`module_skills/skill_agent_first_development.md` — read it once before proposing structure" and "`make help` lists every target with its one-line purpose — read the targets there, never from prose." No cited rule governs whether a pointer document may append an imperative directive after a citation versus leaving the citation bare; the pattern would forbid a bare citation with no trailing instruction.

departures: 1


## crawled 2026-09-14 07:39 UTC · claude-sonnet-5 · 20ac2db
## Departures

1. `module_skills/glossary.md` § Documentation ownership (CLAUDE.md row, *never* column: "a rule written in it") — lines 36–39: `## Running it\n\nEverything goes through the Makefile. \`make help\` lists every target with its one-line purpose — read the targets there, never from prose.` — the row derives CLAUDE.md as pointing only to "the working path, the modules by name and the documents that hold the rules," and "it points and holds none"; this section asserts normative reading guidance ("never from prose") itself rather than naming a document that holds it.

## Unexplained

- Lines 32–34: the criterion for which `AGENTS.md` sections are "worth naming" is not stated, and `§ Pre-AWS architectural direction` — a section the canon cross-references repeatedly (`glossary.md` § Pre-AWS direction and elsewhere) — is omitted with no stated reason a reader can decode from this file or the rules alone.
- Lines 36–39: the placement of Makefile/`make help` guidance is not decodable from the door's scope as defined by `module_skills/glossary.md` § Documentation ownership (working path, modules, documents holding rules) — no rule says the door also names how to run the project.

## Ungoverned repeated pattern

- The imperative "read X [in full/once] before Y" construction appears twice — lines 7–8 ("Read it in full before the first edit of a session") and lines 28–30 ("read it once before proposing structure") — with no grammar in the register governing how a pointer's imperative clause is phrased; a third instance would be free to diverge in wording with nothing to stop it.

## conformant?

departures: 1

