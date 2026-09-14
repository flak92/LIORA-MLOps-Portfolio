
## crawled 2026-09-14 04:53 UTC · claude-sonnet-5 · d2fc592
## Departures

1. `AGENTS.md` § Canonical vocabulary — line: `**UCAS — Useless Click Avoiding System.**` (§ Values) — current form: a coined, project-specific acronym introduced with no corresponding entry in `module_skills/glossary.md` — the form the rule derives: a glossary row registering the name in the same commit, as `module_skills/glossary.md` § Pre-AWS direction does for the comparably coined term "Pre-AWS."

2. `AGENTS.md` § Canonical vocabulary — line: `(neuro-optical consistency)` (§ Architecture shape, "names also define visual structure" bullet) — current form: a second coined term with no glossary entry — the form the rule derives: registered in `module_skills/glossary.md` under the same rule.

## Left unexplained

- The identifiers `D01`–`D18` (§ The shape — what holds the project together): the letter `D` is never expanded (Definition? Design? Direction?) anywhere in the file or in the cited rules — a reader cannot decode what the prefix stands for from the file and the rules alone.

## Pattern seen twice or more, ungoverned

- The citation form `` `<path>` § <heading text> `` (e.g. `` (`module_skills/skill_pre_aws_solution.md` § The mapping table) ``) recurs dozens of times through the file. `AGENTS.md` § Architecture shape fixes only half of it — "A reference is a path in backticks, always" — but no rule fixes the `§ <heading>` half; it would forbid a citation to the same section written another way (a numbered subsection, a paraphrase, or a bare "see Values").

## conformant

departures: 2


## crawled 2026-09-14 07:38 UTC · claude-sonnet-5 · 20ac2db
# Review: AGENTS.md

## 1. Departures

- **`AGENTS.md` § Canonical vocabulary** (domain-abbreviation rule: *"Domain abbreviations (ATR, RSI, EMA, OHLCV, UTC, OOS, HPO, XGBoost) stay and are spelled out on first use in the documentation"*) — § Values: *"a finite, positive ATR at every decision, asserted beside it"* — current form: bare `ATR`, never expanded anywhere in the file — the rule derives: `Average True Range (ATR)` on this first use, `ATR` thereafter, the same discipline the file itself applies correctly to `QuantConnect Lean` → `Lean` later in the same section.

- **`AGENTS.md` § Canonical vocabulary** (same domain-abbreviation rule) — § Rejected vocabulary, module and file stems: *"a per-asset OHLCV parquet"* — current form: bare `OHLCV`, never expanded anywhere in the file — the rule derives: spelled out in full on this first use.

## 2. Left unexplained

- "**sunset note**" — named twice (§ Pre-AWS architectural direction: *"a ticker may name a convenience alias in the Makefile, with its sunset note"*; § Canonical vocabulary, Makefile targets row: *"a ticker alias of a lifecycle target carries its own sunset note"*) but neither this file nor the accompanying rules state what a sunset note must contain or where it lives — a reader knows the object is required but not its form.

## 3. Ungoverned repeated pattern

- Per-asset examples switch, with no stated rule, between the literal demonstration ticker and the generic placeholder: the Makefile-targets/artifact-files grammar row gives `BTC_features_ss-15-hh-dd-MM.parquet`, `BTC_features_ss-mm-04-dd-MM.parquet`, while the "Derived, never drafted" list and every other per-asset example in the same file use `<TICKER>_parameters.json`, `<TICKER>_catalogue.json`, etc. No rule says when an example should use `BTC` versus `<TICKER>`; a third instance of either choice would still be unconstrained.

## 4. Verdict

departures: 2

