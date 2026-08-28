# Skill: computing optimisation

Parallelism matters for wall-clock time, with one governing rule:

> **Parallelism is an execution-time optimisation — never at the cost of
> deterministic correctness.**

- Speed comes exclusively from **external parallelism**: independent,
  processes side by side (one asset per process), all under the same fixed
  `SEED`. Never
  from raising thread caps inside a worker — see `skill_determinism.md`.
- Width is **measured at invocation, never hardcoded**: `JOBS = max(1,
  min(cores, available GiB))` in the Makefile — the floor matters, because
  `xargs -P 0` means no limit at all. The machine changes size; a literal
  written for one size is silently wrong on every other. `JOBS=n` overrides.
- Before optimising, **measure the time distribution** — the bottleneck is
  rarely where intuition points. After optimising, compare against the
  run-to-run spread: an improvement within the spread is noise and the
  change is rejected (measured example: reusing a DMatrix across HPO trials
  saved 2–4%, the same order as the spread — rejected).
- A stage that is the only writer to a shared resource stays sequential
  (`ml-bars` and the database).
