# Skill: determinism

Two runs of the same experiment must produce the same bits — otherwise
out-of-sample results lose their evidential value.

- Thread caps are frozen at one: `nthread=1` (XGBoost), `OMP_NUM_THREADS=1`.
  Multi-threaded float summation reorders, two runs diverge, backtests stop
  being comparable. Never raise them, on any machine size.
- The seed is fixed (`SEED = 42`), Optuna runs sequentially (`n_jobs=1`,
  TPE seeded) — a parallel study draws trials in nondeterministic order.
- DuckDB aggregations pin their order (`arg_min`/`arg_max` by timestamp,
  explicit `ORDER BY`); artifact writers sort before writing.
- The verification standard for any change that should not alter results is
  **bit-parity**: rerun the affected stages and compare artifact checksums.
  "Looks the same" is not a check; identical bytes are.
