# Data terminal

The hand's instrument over the data module: each asset's raw days and whether its canonical series stands, then
one of the module's targets — every target of the root `Makefile` that carries a `##` and that `MENU_TARGET_PATTERN`
matches, today `data-download`, `data-ingest`, `data-status` and `data-all` — started through `make`; then it closes.
Its screens follow the `TUI-DESIGNER-` rows of `module_skills/skill_tui_designer.md`, which every terminal of
this tree obeys; this file says what its screen holds.

```bash
make data-terminal ASSET=BTC            # the TUI over one asset
make data-terminal                      # the TUI over the basket
STORE_RAW_1M_DIR=store/raw_1m STORE_ASSETS_ARTIFACTS_DIR=store/assets_artifacts STORE_STATUS_DIR=store/status python3 -B -m module_data.sub_module_terminal.terminal --tickers BTC -h   # the keys, plain output and the exit codes
```

## The screen

The header block, *Data terminal*, stands over the assets `--tickers` named, their count and how many of them have a
canonical dataset. Then the state table, one row per asset, its columns left out in this order on a narrow terminal:

| column | holds | left out |
|---|---|---|
| `asset` | the ticker | never |
| `canonical dataset` | `yes` / `no` — whether the asset's partition of the canonical family stands | never |
| `binance days`, `bybit days` | one column per venue of `SOURCE_VENUES`, in its order: the day ZIPs that venue's raw leaf holds, `0` where it holds none | after `last day`, in that order |
| `last day` | the greatest `YYYYMMDD` either leaf holds, `—` where neither holds a day | first |

Then the menu, `gum choose` headed *action*: the targets `make help` lists that `MENU_TARGET_PATTERN` matches, in the
Makefile's order, then `quit` (`TUI-DESIGNER-ACTIONS-COME-FROM-MAKEFILE`).

What it knows of an asset it reads through this module's own `config.py` and `lean.py`, the one grammar of the raw
tree: the day ZIPs `lean_day_zip_paths()` finds in the leaf `raw_symbol_dir()` builds for each venue, and whether the
partition `ohlcv_1m_canonical_parquet()` names is there. It opens no partition and reads no snapshot; a count of day
ZIPs and the last day they are named for is presentation.

## The actions

After the menu, the asset form — the assets of `--tickers` as rows, one answered without asking — then the plan:
`target`, the `purpose` its `##` carries and `ASSET`, the line `command  make <target> ASSET=<TICKER>`, and the gate
`<target>?` with the target first and `cancel`. The target's own lines stay on the screen as they come, and the run
ends on the `DONE` block or on the failure block carrying make's exit code. `data-download` and `data-status` are
basket lines — they run the whole basket whatever `ASSET` says, and `data-status` writes one snapshot for the basket —
while `data-ingest` runs the one asset named; the Makefile runs every stage in a one-off container of the `data`
runner, and the terminal names neither the container nor the order of the chain.

The failures it names itself: no terminal on standard input, no gum on `PATH`, no asset named, or a target that
exited non-zero.

## Why it is built this way

| the file | what it is |
|---|---|
| `terminal.py` | the opening screen, the menu read off `make help`, the asset, the plan and its gate, and the one action; the only file that calls `make`; `--tickers` its one argument beside `-h`, `--help` |
| `config.py` | `MENU_TARGET_PATTERN` — which of the Makefile's targets the menu offers — and `OUTPUT_PLAIN`; no descriptor, because `module_data/config.py` is standard library and `terminal.py` imports it, with `lean.py`, for the venues and every path it reads |
| `tui.py` | how a screen is drawn and an answer taken — one file with the four other terminals', the canon's among them |

It imports the standard library and its own package alone and runs on the host's `python3` with gum, in no container
and no virtual environment. No module imports another, and a package for what the terminals share would be the
`common` the contract refuses, so the duplication is paid on purpose: `tui.py`, `OUTPUT_PLAIN`, `HELP_LINE_PATTERN`
and the helpers `_option_rows()`, `_cancelled_exit_code()`, `_failure_exit_code()`, `_make()`, `_target_rows()`,
`_present()`, `_write_target()` and `_tickers()` are each marked `# twice by extraction`, registered in
`module_skills/skill_glossary.md` and changed on every side at once.
