# Features terminal

The hand's instrument over the feature module: per asset, how many timeframes its bars and its catalogue hold a
partition for, whether its contract stands, where its serpentine search profile stands and how many trials the
search's ledger holds; then one action — a target of the module started through `make`, or one of the serpentine
search's own: draft the profile, read the recorded search, promote the proposal; then it closes. Its screens follow the
`TUI-DESIGNER-` rows of `../../module_skills/skill_tui_designer.md`, which every terminal of this tree obeys; this file
says what its screens hold.

```bash
make features-terminal                  # the TUI over the basket
make features-terminal ASSET=BTC        # the TUI over one asset — ASSET= names it, as for every stage
STORE_ASSETS_ARTIFACTS_DIR=store/assets_artifacts python3 -B -m module_features.sub_module_terminal.terminal -h   # the keys, plain output and the exit codes
```

## The screen

The header block, *Features terminal*, stands over the assets `--tickers` named, their count and how many of them
hold a contract. Then the state table, one row per asset, its columns left out in this order on a narrow terminal:

| column | holds | left out |
|---|---|---|
| `asset` | the ticker | never |
| `bars` | how many timeframes the asset's partition of the `bars` family holds, `0` where none | never |
| `catalogue` | the same count for the `catalogue` family | third |
| `contract` | `yes` / `no` — whether `<TICKER>_catalogue.json` stands | fourth |
| `profile` | where the asset's profile stands against the recorded search: `not drafted`, `no search`, `matches the search` or `differs from the search` | second |
| `trials` | the lines of the search's ledger, `—` where no ledger names a trial | first |

Then the menu, `gum choose` headed *action*: the targets `make help` lists that `MENU_TARGET_PATTERN` matches — the
module's stages, `features-all`, the serpentine search's targets and its `tmux-` twin — in the Makefile's
order, then the terminal's own `draft` and `recorded search`, then `quit`; `features-terminal` carries no `##` and is
no option of the menu it opens (`TUI-DESIGNER-ACTIONS-COME-FROM-MAKEFILE`).

It reads the artifacts store by the descriptors its `config.py` carries: the partitions by name, no parquet opened,
and the contract, the profile, the search's state file and its ledger as JSON. It reads no snapshot:
`features_status.json` is only as fresh as the last `make features-status`, and a catalogue written a minute ago
would read as absent. The one comparison it makes is the `profile` cell — the profile it holds against the profile the
recorded search was run with, as parsed objects and never bytes, because the search records that profile verbatim
among its inputs. The snapshot's `inputs_current`, which the page reads, is a wider question — it folds the
parameters, the catalogue and the asset's own state — and stays `module_features/status.py`'s, because answering it
needs numpy.

## The actions

After the menu, the asset form — the assets of `--tickers` as rows, one answered without asking. Then:

- **a target** — the plan, `target`, the `purpose` its `##` carries and `ASSET`, the line
  `command  make <target> ASSET=<TICKER>` and the gate `<target>?`; the target's own lines stay on the screen as they
  come, and the run ends on the `DONE` block or on the failure block carrying make's exit code. `features-status`
  folds the whole basket whatever `ASSET` says — the Makefile passes `TICKERS_CSV`. `tmux-features-serpentine-search`
  starts the search detached in the tmux session `features-serpentine-search-<ticker>` — its name behind the compose
  project's under `COMPOSE_PROJECT_NAME` — alive after this terminal closes; there is no stop here: `tmux attach -t`
  that session and Ctrl-C stop it, as `make help` says, and a rerun resumes.
- **`features-serpentine-search-promote`**, the target `PROMOTE_TARGET` names — its own screen, whose plan shows the
  state it promotes: the asset, the proposal's trial, the coordinates it moves and what it writes,
  `<TICKER>_feature_set.json` and `<TICKER>_barriers.json` — then the line
  `command  make features-serpentine-search-promote ASSET=<TICKER>` and the gate `promote the proposal of <TICKER>?`.
  A search proposes one state at most, so nothing is chosen before the gate. The target copies the proposal and
  reruns the asset's ML chain, `ml-all`, whose lines stay on the screen and which computes the final holdout; the
  `DONE` block says whose lines they are.
- **draft** — four forms under the steps table. *columns to admit*: every column of the contract in catalogue order,
  timeframe-major, those the profile admits chosen at the start and all of them when there is no profile — so a
  column the catalogue does not offer on a timeframe cannot be admitted on it. *start state*: the asset's own, or the
  recorded search's champion. *coordinates to search*: the coordinates of `GRID_BY_COORDINATE_DEFAULT`, each with its
  grid; the grid itself is not asked — it is one preset, and another grid is a hand's edit of the file. *loops*: the
  loops of a round in the order of `SERPENTINE_SEARCH_ROUND_LOOPS`. The drafted profile carries every coordinate: one
  left unticked is pinned to where it stands — the first point of the grid the profile holds, or
  `START_BY_COORDINATE_DEFAULT` when there is no profile yet — and its grid becomes that one point, which has no
  neighbour, so its family makes no move. The asset's noise sigma is carried over unchanged, a hand's edit of the
  file. Then the changes table, `parameter | now | after`, or the line `no profile changes`; a recorded search run
  under another profile puts one `WARN` line above the gate — the next turn starts a new state and overwrites the
  state file —, a fact about how the search resumes and not a refusal. The gate
  `draft <TICKER>_serpentine_search_profile.json?` offers `draft` — absent when nothing changes —, `back` and
  `cancel`. A draft needs the contract: without it the run ends on the failure block, whose *next* is
  `make features-catalogue ASSET=<TICKER>`.
- **recorded search** — writes nothing and ends on its last table: the state table, `parameter | value` — the asset,
  the profile, the coordinates searched, the loops, the trials and the rounds, the trials by loop as the search
  counted them at a round boundary, whether it converged, the champion trial and the proposal count — then the path
  table and the proposals table, or the lines `no accepted move` and `no proposal`. Which trials the path and the
  proposals hold comes from the state file; each trial's numbers from its line of the ledger; the coordinates a
  proposal moves are that line against the asset's own state the search recorded in its inputs. The word is
  *recorded search* and not *status*, which is a stage's.

The tables the actions draw beyond the state table, and the order a narrow terminal leaves their columns out in; the
steps table (`step`, `state`, `choice`), the start state form, the loops form and the changes table drop none:

| table | columns | left out, in turn |
|---|---|---|
| the path table | `#`, `round`, `loop`, `family`, `trial`, `path CAGR`, `path Calmar`, `path maxDD`, `trades` | `trades`, `path maxDD`, `path Calmar`, `family` |
| the proposals table | `#`, `trial`, `coordinates moved`, `path CAGR`, `path Calmar`, `path maxDD`, `trades` | `path maxDD`, `trades`, `path Calmar`, `coordinates moved` |
| the columns form | `column`, `timeframe`, `definition` | `definition`, `timeframe` |
| the coordinates form | `coordinate`, `grid`, `points` | `points`, `grid` |

The failures it names itself: no terminal on standard input, no gum on `PATH`, no asset named, no contract to draft
from, no recorded search to read, no proposal to promote, or a target that exited non-zero.

## Why it is built this way

| the file | what it is |
|---|---|
| `terminal.py` | the opening screen, the menu and the actions — a target started through make, the draft, the recorded search, the promotion; the only file that calls `make`, and the one that writes the profile; `--tickers` its one argument beside `-h`, `--help` |
| `config.py` | registered copies of the store read, the descriptors of the files it shows, the promotion's target, the loops, the start geometry and the grid the draft offers, and the readers and the writer of JSON; `OUTPUT_PLAIN` and `MENU_TARGET_PATTERN` |
| `tui.py` | how a screen is drawn and an answer taken — one file with the four other terminals', the canon's among them |

It imports the standard library and its own package alone and runs on the host's `python3` with gum, in no container
and no virtual environment. It cannot import `module_features/config.py`, which imports `.indicators`
and numpy with it, nor the serpentine search's `config.py`, which imports that one, so what it reads of them is
carried in its own `config.py`; and no module imports another, so what the terminals share is carried too — `tui.py`,
`OUTPUT_PLAIN`, `HELP_LINE_PATTERN` and the helpers `_option_rows()`, `_cancelled_exit_code()`,
`_failure_exit_code()`, `_make()`, `_target_rows()`, `_present()`, `_write_target()` and `_tickers()`. Each copy is
marked `# twice by extraction`, registered in `module_skills/skill_glossary.md` and changed on every side at once. The
profile is written by `write_json()` in the tree's canonical JSON form, so the same decisions write the same bytes and
a draft that changes nothing leaves git unmoved.
