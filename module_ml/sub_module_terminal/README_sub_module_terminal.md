# ML terminal

The hand's instrument over the ML module: each asset's artifacts, then one action — a target of this module that
carries a `##` in the Makefile: a stage of the chain (labels, hpo, train, strategy, status), the chain whole (all) or
the scoring of a request (score) — started through `make` for one asset; then it closes. Its rules are
`skill_ml_terminal.md`, beside this file, and the standards of its screens `../../module_skills/skill_tui_designer.md`,
which every terminal of this tree obeys.

```bash
make ml-terminal ASSET=BTC              # the TUI over one asset
make ml-terminal                        # the TUI over the basket
STORE_ASSETS_ARTIFACTS_DIR=store/assets_artifacts STORE_TRIALS_DIR=store/trials STORE_STATUS_DIR=store/status python3 -B -m module_ml.sub_module_terminal.terminal --tickers BTC -h   # the actions, the keys, plain output and the exit codes
```

It computes nothing and writes nothing of its own. Per asset it reads the feature layer's contract,
`<TICKER>_catalogue.json`, for the decision timeframe the labels partition is named by, and looks whether the labels,
the parameters, the model evaluation and the strategy evaluation stand; it reads no snapshot and no file of the
serpentine search, whose draft, reading and promotion are the features terminal's. Its menu is `make help` read by
name: every target `MENU_TARGET_PATTERN` matches, in the Makefile's order — so a target is an option by carrying a
`##`, and the program keeps no second list of them; `ml-terminal` itself carries none, an entry not being an action.
Everything that runs, runs through `make` with `ASSET=<TICKER>`: the Makefile is where a stage is named and where its
container is.

| the file | what it is |
|---|---|
| `terminal.py` | the opening screen, the menu of targets, the asset, the plan and its gate; the only file that calls `make` |
| `config.py` | the reader `module_ml/dataset.py` cannot lend a host without duckdb and numpy, the pattern of the targets its menu offers, plain output |
| `tui.py` | how a screen is drawn and an answer taken — one file with every other terminal's and the crawler's, five times by extraction |
