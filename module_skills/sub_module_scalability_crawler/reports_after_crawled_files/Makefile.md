
## crawled 2026-09-14 04:58 UTC · claude-sonnet-5 · d2fc592
## Departures

None found — no clear rule violation identified in this file against the enumerated grammars, the stores contract, the naming conventions or the rejected-vocabulary list.

## Unexplained

- `python3 -B -m module_skills.sub_module_scalability_crawler.crawl` (skills-crawl) and `python3 -B -m module_skills.sub_module_scalability_crawler.status` (skills-status): the `-B` flag (suppress bytecode caching) carries no comment, and neither the rules nor the rest of the file explain why these two invocations alone disable `.pyc` generation while every other Python invocation in the file runs inside a container where the question does not arise.

## Twice-or-more pattern, ungoverned

- `$(if $(ASSET),,$(error ASSET=<TICKER> is required))` appears identically in `ml-feature-set-promote` and `tmux-ml-feature-set-search` — no grammar row or skill states the form of an argument-presence guard on a hand-only target; the form it would forbid is a hand-only, single-asset target silently falling back to the whole `TICKER_LIST`/`TICKERS_CSV` instead of erroring when `ASSET` is unset.

## Closing

conformant


## crawled 2026-09-14 07:43 UTC · claude-sonnet-5 · 20ac2db
# Departures

None found — every target follows `<module>-<stage>` / `<module>-all` / `tmux-<module>-<stage>`, `skills-crawl`/`skills-status`/`tmux-skills-crawl` match their named exception, and the bare lifecycle set (`all`, `build`, `help`, `on`, `off`, `all-record`) plus the two ticker aliases (`btc-all`, `btc-lifecycle`) match `AGENTS.md` § Canonical vocabulary's grammar row exactly. `PORT`, `JOBS`, `DOCKER_GID`, `TICKERS`/`TICKER_LIST`/`TICKERS_CSV`, `RUN_ID`, `FEATURE_SET_SEARCH_SESSION`, `RECORDED_STAGES`, the `run`/`fanout`/`basket` macros and the `STORE_*_DIR` exports each match their described form in `glossary.md` § Stores, § Asset containers, § Run record and `module_skills/skill_pre_aws_solution.md` § The Makefile is the developer interface / § Docker is compute.

# Unexplained

1. `python3 -B -m module_skills.sub_module_scalability_crawler.crawl` and the matching `-B` on `skills-status` (lines under `skills-crawl:`, `skills-status:`) — the `-B` flag has no comment in the file and no rule text addresses it; a reader cannot tell why bytecode caching is suppressed here and nowhere else.
2. `FEATURE_SET_SEARCH_SESSION = feature-set-$(shell echo $(ASSET) | tr A-Z a-z)` — the lowercasing of the ticker has no comment. `glossary.md` § Metrics writes the session as `feature-set-<ticker>` with a lower-case placeholder, unlike the upper-case `<TICKER>` used everywhere else in the same documents, so the rules hint at the intent but never state it; the file itself gives no reason.

# Unguided repetition

1. `MLFLOW_DISABLE_TELEMETRY := true` / `MLFLOW_DISABLE_AGENT_HINT := 1`, with the comment stating both are "off here and in docker-compose.yml" — an identical value asserted to exist in two files, the exact shape `glossary.md` § Twice by extraction exists to register, but neither variable appears in that table or is marked `# twice by extraction` at either definition.
2. The `tmux has-session -t <session> 2>/dev/null && echo '<session> is already running …' || tmux new-session -d -s <session> …` guard, written out identically in `tmux-ml-feature-set-search` and `tmux-skills-crawl` — a repeated conditional with no shared derivation, in a document whose `module_skills/skill_pre_aws_solution.md` § The Makefile is the developer interface states "no recipe branches on state, retries, sleeps or waits for a condition."

# conformant

