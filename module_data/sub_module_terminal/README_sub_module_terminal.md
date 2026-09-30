# Data terminal

The hand's instrument over the data module: each asset's raw days and whether its canonical series stands, then one
of the module's targets started through `make`; then it closes. Its screens follow the `TUI-DESIGNER-` rows of
`module_skills/skill_tui_designer.md`, which every terminal of this tree obeys; this file says what its screen holds.

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

Then the menu, the targets `make help` lists that `MENU_TARGET_PATTERN` matches (`TUI-DESIGNER-ACTIONS-COME-FROM-MAKEFILE`),
then the asset, the plan and the gate (`TUI-DESIGNER-A-PLAN-NAMES-WHAT-WILL-RUN`, `TUI-DESIGNER-A-GATE-IS-NOT-A-GUARD`).
`data-download` and `data-status` run the whole basket whatever `ASSET` says; `data-ingest` runs the one asset named.
What it knows of an asset it reads through this module's own `config.py` and `lean.py`: the day ZIPs of each venue's
leaf and whether the canonical partition is there — no partition opened, no snapshot read.

The failures it names itself: no terminal on standard input, no gum on `PATH`, no asset named, or a target that exited
non-zero.

## Why it is built this way

| the file | what it is |
|---|---|
| `terminal.py` | the opening screen, the menu read off `make help`, the asset, the plan and its gate, and the one action; the only file that calls `make`; `--tickers` its one argument beside `-h`, `--help` |
| `config.py` | `MENU_TARGET_PATTERN` and `OUTPUT_PLAIN`; no descriptor, because `module_data/config.py` is standard library and `terminal.py` imports it, with `lean.py`, for every path it reads |
| `tui.py` | how a screen is drawn and an answer taken — one file with every other terminal's |

It runs on the host's `python3` with gum and imports the standard library and its own package alone
(`TUI-DESIGNER-ONE-TERMINAL-PER-MODULE`); what it shares with the other terminals is registered in
`module_skills/skill_glossary.md` § Twice by extraction.
