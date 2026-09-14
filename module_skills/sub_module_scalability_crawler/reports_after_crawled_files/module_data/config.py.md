
## crawled 2026-09-14 09:28 UTC · claude-sonnet-5 · f8ebdb0
## Departures

1. `AGENTS.md § The shape — what holds the project together, D14` — line 31, `def to_utc_ms(day: str) -> int:` — current form: no `# twice by extraction` marker at the definition — form the rule derives: `to_utc_ms()` is registered in `module_skills/glossary.md § Twice by extraction` (owners `module_data/config.py`, `module_features/config.py`, `module_ml/config.py`) and D14 requires it "marked `# twice by extraction` where it is defined."

2. `AGENTS.md § The shape — what holds the project together, D14` — line 57, `DUCKDB_MEMORY_LIMIT = "4GB"` — current form: only an unrelated line comment ("DuckDB spills to disk above this ceiling…"), no `# twice by extraction` tag at the definition — form the rule derives: the marker belongs at this line, not only inside the distant block comment at lines 19–21.

3. Same rule — line 58, `STORE_ASSETS_ARTIFACTS_DIR = Path(os.environ["STORE_ASSETS_ARTIFACTS_DIR"])` — no marker at the definition.

4. Same rule — line 59, `STORE_STATUS_DIR = Path(os.environ["STORE_STATUS_DIR"])` — no marker at the definition.

5. Same rule — line 72, `def artifact_dir(ticker: str) -> Path:` — no marker at the definition.

6. Same rule — line 77, `def research_ohlcv_duckdb(ticker: str) -> Path:` — no marker at the definition.

7. Same rule — line 82, `def build_ticker_parser(description: str) -> argparse.ArgumentParser:` — no marker at the definition.

8. Same rule — line 89, `def parse_tickers(tickers_csv: str) -> list[str]:` — no marker at the definition.

(For contrast, `BYTES_PER_KIBIBYTE`, line 27, and `rounded()`, line 94, each carry their own adjacent `# twice by extraction` comment, showing the per-object placement this file otherwise follows.)

## Unexplained

- Lines 19–20, "the --tickers parser" (singular) in the shared comment — a reader cannot tell from the file alone whether this covers `build_ticker_parser()` only or also `parse_tickers()`, both of which the glossary marks twice-by-extraction.
- Line 57, `DUCKDB_MEMORY_LIMIT` — its placement between `STORE_RAW_1M_DIR` (line 55) and `STORE_ASSETS_ARTIFACTS_DIR`/`STORE_STATUS_DIR` (lines 58–59), interrupting the store-read sequence the comment at lines 53–54 introduces, is not explained.

## Ungoverned pattern

Comment placement alternates between a block comment above a group of identifiers (lines 14–15, 19–21, 25–26, 36–37, 41, 53–54) and a trailing same-line comment on a single identifier (lines 17, 47, 28, 56, 60) — seen four or more times each way, with no rule in the register or the skills governing which form an explanatory comment should take.

## Verdict

departures: 8


## crawled 2026-09-14 10:33 UTC · gpt-5.6-luna · 5ce2f1c
AGENTS.md § Canonical vocabulary — constants: lines 37 and 41, `BINANCE_KLINE_REQUEST_LIMIT` / `BYBIT_KLINE_REQUEST_LIMIT`, `<what>_<unit>` is required for numeric counts; propose `BINANCE_KLINE_REQUEST_LIMIT_ROWS` / `BYBIT_KLINE_REQUEST_LIMIT_ROWS`.

What the file leaves unexplained: `USDS-M`, `Linear`, and “failover” in the line 13 comment are not defined by the file or supplied rules.

Pattern not governed: endpoint constants `*_KLINE_URL` occur on lines 36 and 39; this would forbid endpoint constants whose naming grammar is not specified.

departures: 2


## crawled 2026-09-14 13:29 UTC · claude · claude-opus-5 · high · no tools · d1e6681
**1. Departures**

- `AGENTS.md` § The shape, D14 · line 32 · `def to_utc_ms(...)` with no marker; the comment at 19–21 does not name it · `# twice by extraction — identical in module_features/config.py, module_ml/config.py` above the definition
- `AGENTS.md` § The shape, D14 · line 58 · `DUCKDB_MEMORY_LIMIT` is marked only by the comment at 19–21, 37 lines above it · the marker where it is defined
- `AGENTS.md` § The shape, D14 · lines 59–60 · `STORE_ASSETS_ARTIFACTS_DIR`, `STORE_STATUS_DIR` are marked only at 19–21, and that comment omits `module_monitoring/config.py`, which `module_skills/glossary.md` § Twice by extraction names as an owner of `STORE_STATUS_DIR` · the marker at the definitions, naming every owner
- `AGENTS.md` § The shape, D14 · lines 73, 78 · `artifact_dir()`, `research_ohlcv_duckdb()` are marked only at 19–21 as "their descriptors" · the marker at each definition
- `AGENTS.md` § The shape, D14 · lines 83, 90 · `build_ticker_parser()`, `parse_tickers()` are marked only at 19–21 · the marker at the definitions
- `module_skills/glossary.md` § Twice by extraction (the units, equal by value, not by tree) · lines 19–21 · "the units below … are identical in module_features/config.py and module_ml/config.py" · the units marked as equal by value, apart from the byte-identical objects
- `AGENTS.md` § Architecture shape ("A reference is a path in backticks, always") · lines 20–21 · `module_features/config.py`, `module_ml/config.py`, `module_skills/glossary.md` are written bare, while the docstrings at 1–4 and 33 use backticks · each path in backticks
- `AGENTS.md` § Architecture shape (same sentence) · lines 25–26 · `module_ml/config.py`, `module_monitoring/page.js`, `module_skills/glossary.md` are written bare · in backticks
- `AGENTS.md` § Architecture shape (same sentence) · line 69 · `Lean-exact tree: store/raw_1m/cryptofuture/<venue>/minute/<symbol>/` · the path in backticks
- `AGENTS.md` § Architecture shape (same sentence) · line 94 · `identical in module_ml/config.py` · the path in backticks
- `AGENTS.md` § Canonical vocabulary ("One concept, one name") · line 18 against lines 43, 44, 46, 48 · `SOURCE_CANDLE_INTERVAL` beside `BINANCE_KLINE_URL`, `BINANCE_KLINE_REQUEST_LIMIT`, `BYBIT_KLINE_URL`, `BYBIT_KLINE_REQUEST_LIMIT`, two names for the venue's minute bar in one module's symbols · one word across the five names
- `AGENTS.md` § Canonical vocabulary (the external-vocabulary boundary list) · lines 43–49 · Binance and Bybit REST vocabulary (`KLINE`, `REQUEST_LIMIT`, `BYBIT_CATEGORY = "linear"`) is spoken in `module_data/config.py`, but the list names only `download_binance.py` and `download_bybit.py` · either the boundary list names `module_data/config.py` for these values, or the values sit with the downloaders

**2. Unexplained**

- Line 1: "Static configuration" is not decodable while the same file reads the environment (56, 59, 60) and defines seven functions.
- Line 19: "their descriptors" could mean any of four descriptors (`symbol`, `raw_symbol_dir`, `artifact_dir`, `research_ohlcv_duckdb`). The file does not say which two are the registered copies.
- Line 3: "the two status reports" does not say which two. The register's word for the object is snapshot.
- Line 48: "2 windows of 720 minutes" sits beside a limit of 1000. Nothing in the file explains why 720.
- Line 50: the `1.0` in `USER_AGENT` versions something the file does not name. Nothing else in the file carries a version.
- Lines 57–58: the DuckDB ceiling sits between two store reads, under the comment that introduces the stores. The file does not explain that placement.
- Line 70: `LEAN_SECURITY_TYPE_FOLDER` is a named constant, but its sibling segment `"minute"` in the same path is an inline literal. The file does not say why they differ.
- Line 96: the docstring of `rounded` speaks of "a fold without trades", which is a `module_ml` concept, in `module_data`'s copy. The byte-identity reason is not stated at line 94.

**3. Ungoverned patterns**

- Venue-prefixed constants: `BINANCE_*` and `BYBIT_*` repeat the same three roles per venue (43–49). The constants row of the grammar does not say where a venue token goes. A rule would forbid `KLINE_URL_BINANCE`.
- Docstring presence is uneven: `symbol` (64) and `parse_tickers` (90) have none, while every other function has one. A rule would forbid a public function of a `config.py` without a docstring, or a docstring on a one-line descriptor.
- Comment placement is uneven: trailing comments at 17, 28, 48 and 61 sit beside block comments above constants elsewhere. A rule would forbid one of the two placements for a constant's explanation.

departures: 12


## crawled 2026-09-14 13:32 UTC · codex · gpt-5.6-luna · high · no tools · d1e6681
1. Departures

- `AGENTS.md § Canonical vocabulary` — line 15 — `Lean security-type folder name` — `QuantConnect Lean security-type folder name`.
- `AGENTS.md § Architecture shape` — lines 17–18 — bare rule paths in comments — backticked paths.
- `AGENTS.md § Architecture shape` — lines 22–23 — bare rule paths in comments — backticked paths.
- `AGENTS.md § Canonical vocabulary` — line 40 — `BINANCE_KLINE_REQUEST_LIMIT` — `BINANCE_KLINE_REQUEST_LIMIT_ROWS`.
- `AGENTS.md § Canonical vocabulary` — line 43 — `BYBIT_KLINE_REQUEST_LIMIT` — `BYBIT_KLINE_REQUEST_LIMIT_ROWS`.
- `AGENTS.md § Architecture shape` — line 64 — bare Lean-tree path in the docstring — a backticked path.
- `AGENTS.md § Canonical vocabulary` — line 65 — `raw_symbol_dir()` assembles the Lean tree path in `config.py` — external-format path construction in `module_data/lean.py`.
- `module_skills/skill_self_explaining_naming.md § The name carries the information` — line 78 — `ap` — `argument_parser`.
- `AGENTS.md § Canonical vocabulary` — line 88 — `x` — `value`.

2. What the file leaves unexplained

- Line 44 says the Bybit limit is `1000` but describes “2 windows of 720 minutes”; the relationship between those values is unexplained.

3. Repeated pattern with no additional governing rule

None observed.

departures: 9

