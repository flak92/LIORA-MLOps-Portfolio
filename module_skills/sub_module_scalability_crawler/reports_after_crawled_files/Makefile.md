
## crawled 2026-09-14 04:58 UTC · claude-sonnet-5 · d2fc592
## Departures

None found — no clear rule violation identified in this file against the enumerated grammars, the stores contract, the naming conventions or the rejected-vocabulary list.

## Unexplained

- `python3 -B -m module_skills.sub_module_scalability_crawler.crawl` (skills-crawl) and `python3 -B -m module_skills.sub_module_scalability_crawler.status` (skills-status): the `-B` flag (suppress bytecode caching) carries no comment, and neither the rules nor the rest of the file explain why these two invocations alone disable `.pyc` generation while every other Python invocation in the file runs inside a container where the question does not arise.

## Twice-or-more pattern, ungoverned

- `$(if $(ASSET),,$(error ASSET=<TICKER> is required))` appears identically in `ml-feature-set-promote` and `tmux-ml-feature-set-search` — no grammar row or skill states the form of an argument-presence guard on a hand-only target; the form it would forbid is a hand-only, single-asset target silently falling back to the whole `TICKER_LIST`/`TICKERS_CSV` instead of erroring when `ASSET` is unset.

## Closing

conformant

