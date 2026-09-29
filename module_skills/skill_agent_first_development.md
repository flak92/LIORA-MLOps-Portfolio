# Skill: agent-first development

How to work on this repository as an agent. *The repository shows the destination, not the road* — subtract, don't add.

- Build **maximal minimalism with scalable logic**: shape every change so a
  reader needs as few thoughts as the task allows — the shortest chain of
  reasoning, not the fewest characters — but mathematical and logical
  correctness never pays for it. When economy and correctness conflict,
  correctness wins.
- This repository is **academic, not production**. Subtract, don't add:
  no test suites, no security layers, no precautionary guardrails, no
  workflow. The guards that stay are the ones the computation itself requires.
- The goal of every change is one thing: **the full pipeline runs end to end**
  — data → canonical → features/labels → training → strategy → dashboard —
  without excess additions around it.
- **Stable, unambiguous names are part of the economy.** Several names for one
  concept multiply the thoughts an agent must think, forcing it to decide
  whether `test`, `test_fold` and `F5` are one thing or three. One concept,
  one name — one thought — and the name must be self-explanatory before it is
  project-specific (`skill_self_explaining_naming.md`). Every new name
  goes into `glossary.md` in the same commit that introduces it; a synonym
  never enters.
- Before writing, check whether an existing module already owns the
  responsibility; extend it rather than wrapping it. A new `module_<domain>`
  exists only for a distinct responsibility with a stable input/output
  boundary and at least one independently consumable outcome. Runtime
  dependencies follow pipeline direction — downstream consumes upstream
  artifacts, upstream never imports downstream. No `utils`, `common`, `core`,
  `manager` or `service` modules: the responsibility already has an owner.
- Repeated project knowledge has one owner, and the repetitions are derived
  from it — the rule and its limit are in `AGENTS.md` § Canonical vocabulary,
  with `Derived, never drafted` beside it. This file does not restate them: two
  copies of a rule drift, and the drift is found by the reader who trusted the
  wrong one.
- **Ownership decides where a rule is written** — `AGENTS.md` § The default
  choice; check it before you place a document.
- Prove a change by running the affected stages, not by adding a framework
  that promises to.
- **Place a change by responsibility and lifetime, never by convenience.**
  Which class a function belongs to, which store it writes and whether it runs
  as a one-off are decided before it is written; `skill_pre_aws_solution.md`
  holds the classes, the one antipattern and the mapping, and
  `skill_self_explaining_naming.md` § The naming review the eight questions.
