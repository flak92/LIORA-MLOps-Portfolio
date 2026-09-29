# Data terminal

The hand's instrument over the data module: each asset's raw days and whether its canonical series stands, then
one of the module's targets — every target of the root `Makefile` that carries a `##` and that `MENU_TARGET_PATTERN`
matches, `data-download`, `data-ingest`, `data-status` and `data-all` — started through `make`; then it closes. Its
rules are `skill_data_terminal.md`, beside this file, and the standards of its screens
`../../module_skills/skill_tui_designer.md`, which every terminal of this tree obeys.

```bash
make data-terminal ASSET=BTC            # the TUI over one asset
make data-terminal                      # the TUI over the basket
STORE_RAW_1M_DIR=store/raw_1m STORE_ASSETS_ARTIFACTS_DIR=store/assets_artifacts STORE_STATUS_DIR=store/status python3 -B -m module_data.sub_module_terminal.terminal --tickers BTC -h   # the actions, the keys, plain output and the exit codes
```

It computes nothing and writes nothing of its own: the venues, each venue's raw leaf and the canonical partition it
reads through this module's own `config.py` and `lean.py` — the day ZIPs a leaf holds and whether the partition is
there, no file opened — its menu it reads off `make help`, and everything that runs, runs through `make`, as
`make <target> ASSET=<TICKER>` for the asset chosen on its screen — the Makefile is where the module's stages are
named.

| the file | what it is |
|---|---|
| `terminal.py` | the opening screen, the menu read off `make help`, the plan and its gate, and the one action; the only file that calls `make` |
| `config.py` | `MENU_TARGET_PATTERN` — which of the Makefile's targets the menu offers — and plain output |
| `tui.py` | how a screen is drawn and an answer taken — one file with every other terminal's and the crawler's, five times by extraction |
