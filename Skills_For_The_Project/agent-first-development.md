# Skill: agent-first development

How to work on this repository as an agent.

- Build **maximal minimalism with scalable logic**: spend as few tokens and
  lines as the task allows, but mathematical and logical correctness never
  pays for it. When economy and correctness conflict, correctness wins.
- This repository is **educational, not production**. Subtract, don't add:
  no test suites, no security layers, no precautionary guardrails. The guards
  that stay are the ones the computation itself requires.
- The goal of every change is one thing: **the full pipeline runs end to end**
  — data → canonical → features/labels → training → strategy → dashboard —
  without excess additions around it.
- **Stable, unambiguous names are part of the economy.** Several names for one
  concept multiply the context an agent has to load and vectorise, and force it
  to decide whether `test`, `test_fold` and `F5` are one thing or three. One
  concept, one name — one vector. Every new name goes into `glossary.md` in the
  same commit that introduces it; a synonym never enters.
- Before writing, check whether an existing module already owns the
  responsibility; extend it rather than wrapping it.
- Prove a change by running the affected stages, not by adding a framework
  that promises to.
