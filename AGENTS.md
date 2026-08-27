# AGENTS — the contract of this repository

The governing contract for every change, human or agent. Read the repo in
this order: **AGENTS.md → module names → Skills_For_The_Project → code.**
(README is general information, not part of the working path.) If a change
conflicts with this file, the change is wrong.

## Values

- **Minimalism.** Every line, file, module and dependency has a concrete
  purpose. If its purpose cannot be named, it goes.
- **Minimum requirements.** A library is added only when the Python standard
  library and the current stack — `duckdb`, `numpy`, `optuna`, `xgboost-cpu` —
  cannot do the job. The lockfile declares direct dependencies only.
- **KISS / YAGNI / DRY / SOLID.** The simplest correct implementation, built
  for the need that exists, never for a hypothetical one. One responsibility
  per module; repeated logic becomes one function, not three copies.
- **UCAS — Useless Click Avoiding System.** Manual steps, clicks and context
  switches that can be automated, are: `make all` runs the whole pipeline
  from a fresh clone, every stage is idempotent, the dashboard opens itself.
- **Main = clean working logic.** No test frameworks, security layers,
  validation frameworks or precautionary guards. What stays are the guards
  the mathematics requires: causality invariants, arithmetic preconditions,
  the fail-closed export. Thread caps (`nthread=1`, `OMP_NUM_THREADS=1`) are
  part of correctness, not a setting.
- **Pipeline-first.** The repository exists to close one full chain:

  ```
  exchange data → ingest → validation necessary for correctness → canonical data
  → features / labels → training / retraining → strategy / results → dashboard
  ```

## Architecture shape

Regular, predictable, symmetrical, easy to scan — the structure should be
recognisable by eye before it is parsed (neuro-optical consistency):

- one obvious responsibility per module; no wrappers without logic of their own;
- analogous names for analogous objects (`download_binance.py` ↔
  `download_bybit.py`, `<kind>_<TICKER>.<ext>` artifacts, `ml-<stage>` ↔
  `docker-ml-<stage>` targets);
- short, predictable paths; no decorative prefixes or suffixes;
- one convention per language: BEM in CSS, snake_case in Python and JSON,
  the same hierarchy everywhere, no accidental exceptions.

## The default choice

For every new change, prefer **the smallest, most modular and most obvious
implementation that correctly closes the full pipeline.**

Project-specific agent instructions live in `Skills_For_The_Project/` — the
only other place agent guidance may exist in this tree.
