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
- Before writing, check whether an existing module already owns the
  responsibility; extend it rather than wrapping it.
- Prove a change by running the affected stages, not by adding a framework
  that promises to.
