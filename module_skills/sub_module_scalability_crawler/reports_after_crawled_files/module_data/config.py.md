
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

