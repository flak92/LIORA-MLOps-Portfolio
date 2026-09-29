# ML terminal

The hand's instrument over the ML module: each asset's artifacts, then one action — a target of this module that
carries a `##` in the Makefile: a stage of the chain, the chain whole or the scoring of a request — started through
`make` for one asset; then it closes. Its screens follow the `TUI-DESIGNER-` rows of
`../../module_skills/skill_tui_designer.md`, which every terminal of this tree obeys; this file says what its screen
holds.

```bash
make ml-terminal ASSET=BTC              # the TUI over one asset
make ml-terminal                        # the TUI over the basket
STORE_ASSETS_ARTIFACTS_DIR=store/assets_artifacts STORE_TRIALS_DIR=store/trials STORE_STATUS_DIR=store/status python3 -B -m module_ml.sub_module_terminal.terminal --tickers BTC -h   # the keys, plain output and the exit codes
```

## The screen

The header block, *ML terminal*, stands over the assets `--tickers` named, their count and how many artifact sets are
complete — `is_artifact_set_complete()`, the one question `status.py` asks: the parameters, the model evaluation and
the strategy evaluation all stand. Then the state table, one row per asset, its columns left out in this order on a
narrow terminal:

| column | holds | left out |
|---|---|---|
| `asset` | the ticker | never |
| `catalogue` | `yes` / `no` — whether the feature layer's contract, `<TICKER>_catalogue.json`, stands | never |
| `labels` | `yes` / `no` — whether the labels partition of the contract's decision timeframe stands; `—` where no contract names it | fourth |
| `parameters` | `yes` / `no` — `<TICKER>_parameters.json` | third |
| `model` | `yes` / `no` — `<TICKER>_model_evaluation.json` | second |
| `strategy` | `yes` / `no` — `<TICKER>_strategy_evaluation.json` | first |

Then the menu, `gum choose` headed *action*: the targets `make help` lists that `MENU_TARGET_PATTERN` matches — the
stages of the chain, `ml-all` and `ml-score` — in the Makefile's order, then `quit`; `ml-terminal` carries no `##`
(`TUI-DESIGNER-ACTIONS-COME-FROM-MAKEFILE`).

Every descriptor it reads is `module_ml/config.py`'s own, imported, that file being standard library: the contract it
reads as JSON, every other file by its presence alone. It reads no snapshot — `ml_status.json` is only as fresh as the
last `make ml-status` — and no file of the serpentine search, whose draft, reading and promotion are the features
terminal's.

## The actions

After the menu, the asset form — the assets of `--tickers` as rows, one answered without asking — then the plan:
`target`, the `purpose` its `##` carries and `ASSET`, the line `command  make <target> ASSET=<TICKER>`, and the gate
`<target>?` with the target first and `cancel`. The target's own lines stay on the screen as they come, and the run
ends on the `DONE` block or on the failure block carrying make's exit code. The terminal knows no order of the chain
and no precondition of a stage: a stage started before the one it reads from fails in its own words, on the file it
did not find, and those words stand above the block. `ml-status` folds the whole basket whatever `ASSET` says; the
Makefile runs every stage in a one-off container of the `ml` runner.

The failures it names itself: no terminal on standard input, no gum on `PATH`, no asset named, or a target that
exited non-zero.

## Why it is built this way

| the file | what it is |
|---|---|
| `terminal.py` | the opening screen, the menu of targets, the asset, the plan and its gate; the only file that calls `make`; `--tickers` its one argument beside `-h`, `--help` |
| `config.py` | `load_json()`, the reader `module_ml/dataset.py` cannot lend a host without duckdb and numpy; `OUTPUT_PLAIN` and `MENU_TARGET_PATTERN` |
| `tui.py` | how a screen is drawn and an answer taken — one file with the four other terminals', the canon's among them |

It imports the standard library and its own package alone and runs on the host's `python3` with gum, in no container
and no virtual environment. The catalogue it reads is a store file the feature layer wrote — the per-asset contract,
crossing as a file and never as an import — so nothing of `module_features` is imported. What it shares with the other
terminals, and the reader `dataset.py` cannot lend it, it carries: `load_json()`, `tui.py`, `OUTPUT_PLAIN`,
`HELP_LINE_PATTERN` and the helpers `_option_rows()`, `_cancelled_exit_code()`, `_failure_exit_code()`, `_make()`,
`_target_rows()`, `_present()`, `_write_target()` and `_tickers()`, each marked `# twice by extraction`, registered in
`module_skills/skill_glossary.md` and changed on every side at once.
