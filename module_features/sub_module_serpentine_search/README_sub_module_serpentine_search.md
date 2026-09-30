# Serpentine search

`module_features/sub_module_serpentine_search/` is the serpentine search: a hand's research outside the chain over
one asset's state — its feature set, its barrier geometry and its hyper-parameter point — under a profile a hand
drafted. Its rules are `module_features/sub_module_serpentine_search/skill_serpentine_search.md`, beside its code; its
method, its thresholds and their limits are `module_features/skills/methodology_features.md` § The serpentine search.

- **A turn** — `make features-serpentine-turn`, one one-off container of the `features` runner per asset — reads the
  profile, the asset's `best_params` from `<TICKER>_parameters.json`, the contract, the asset's active state — the
  promoted `<TICKER>_feature_set.json` and `<TICKER>_barriers.json`, else the default set and
  `START_BY_COORDINATE_DEFAULT` — the state file, its ledger and the answer on disk. It carries the search as far as
  the answers allow: it appends what an answer adds to the ledger `<TICKER>_serpentine_search_trials.jsonl`, writes
  `<TICKER>_serpentine_search.json` at the top of every round, and leaves either the next question,
  `<TICKER>_score_request.json` — written over the one it answers before the spent answer is removed — or a finished
  search, the question and the answer removed. It computes no metric of a state.
- **The answer** is `module_ml`'s: `make ml-score` (`module_ml.score`, one one-off container of the `ml` runner per
  asset) scores the states the question names — a trial row per state, or a study and its candidate per beam parent —
  and writes `<TICKER>_score_response.json` once the whole question is answered, each study's points in
  `store/trials/score_trials/ticker=<TICKER>/`.
- **The loop** — `make features-serpentine-search [ASSET=<TICKER>]`, never inside `all` — is a turn, then `ml-score`
  and a turn again while the turn leaves a question, each step a one-off container of its runner; it resumes where
  the files stand, and `JOBS=n` runs n assets side by side, one at a time otherwise.
  `make tmux-features-serpentine-search ASSET=<TICKER>` is its detached twin in the tmux session
  `features-serpentine-search-<ticker>` — `<project>-features-serpentine-search-<ticker>` under
  `COMPOSE_PROJECT_NAME=<project>`, which the session is handed — alive after the terminal closes and gone with the
  search; a rerun resumes.
- **The profile**, `<TICKER>_serpentine_search_profile.json`, is drafted by the terminal's `draft` or by hand, never
  derived: the columns admitted per timeframe, the columns the search starts from (`null` for the asset's own set),
  the grid of each barrier coordinate — a one-point grid pins it, and the terminal offers `GRID_BY_COORDINATE_DEFAULT`
  — the loops a round runs, and the asset's noise sigma, `path_cagr_noise_standard_deviation`: `null` on the asset's
  first searches, the calibration runs, whose last turn prints the estimate a hand may draft into the file.
- **The promotion** — `make features-serpentine-search-promote ASSET=<TICKER>`, one asset and never fanned out —
  copies the proposal's whole state (`promote.py`) and runs `ml-all` for the asset, whose study starts from the
  promoted point (`SERPENTINE-SEARCH-PROMOTION-IS-A-HAND`).
- **The reset** — `make features-serpentine-search-reset ASSET=<TICKER>` — removes the search's own files and keeps
  its inputs and its profile; it runs no stage. What a change of data or configuration asks of a hand before the next
  search is one rule, `SERPENTINE-SEARCH-ONE-SEARCH-IS-ONE-EXPERIMENT`.
