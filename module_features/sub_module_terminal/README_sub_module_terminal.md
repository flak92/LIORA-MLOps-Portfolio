# Features terminal

The hand's instrument over the feature module: per asset, how many timeframes its bars and its catalogue hold a
partition for, whether its contract stands, where its serpentine search profile stands and how many state
evaluations the search's ledger holds; then one action — a target of the module started through `make`, or one of the serpentine
search's own: draft the profile, read the recorded search, promote the proposal; then it closes. Its screens follow the
`TUI-DESIGNER-` rows of `module_skills/skill_tui_designer.md`, which every terminal of this tree obeys; this file
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
| `state evaluations` | the lines of the search's ledger, `—` where no ledger holds a state evaluation | first |

Then the menu: the targets `make help` lists that `MENU_TARGET_PATTERN` matches
(`TUI-DESIGNER-ACTIONS-COME-FROM-MAKEFILE`), then the terminal's own `draft` and `recorded search`, then `quit`.

It reads the artifacts store by the descriptors its `config.py` carries: the partitions by name, no parquet opened,
and the contract, the profile, the search's progress and its ledger as JSON. It reads no snapshot:
`features_status.json` is only as fresh as the last `make features-status`, and a catalogue written a minute ago
would read as absent. The one comparison it makes is the `profile` cell — the profile it holds against the profile the
recorded search was run with, as parsed objects and never bytes, because the search records that profile verbatim
among its inputs. The snapshot's `inputs_current`, which the page reads, is a wider question — it folds the
parameters, the catalogue and the asset's own search state — and stays `module_features/status.py`'s, because answering it
needs numpy.

## The actions

After the menu, the asset form — the assets of `--tickers` as rows, one answered without asking. Then:

- **a target** — the plan and the gate (`TUI-DESIGNER-A-PLAN-NAMES-WHAT-WILL-RUN`, `TUI-DESIGNER-A-GATE-IS-NOT-A-GUARD`).
  `features-status` folds the whole basket whatever `ASSET` says. `tmux-features-serpentine-search` starts the search
  detached, alive after this terminal closes; there is no stop here: `tmux attach -t` its session and Ctrl-C stop it,
  as `make help` says, and a rerun resumes.
- **`features-serpentine-search-promote`**, the target `PROMOTE_TARGET` names — its own screen, whose plan shows the
  search state it promotes: the asset, the proposal's state evaluation, the coordinates it moves and what it writes,
  `<TICKER>_feature_set.json`, `<TICKER>_barriers.json` and `<TICKER>_hyperparameter_point.json` — then the line
  `command  make features-serpentine-search-promote ASSET=<TICKER>` and the gate `promote the proposal of <TICKER>?`.
  A search proposes one search state at most, so nothing is chosen before the gate. The target copies the proposal and
  reruns the asset's ML chain, `ml-all`, whose lines stay on the screen and which computes the final holdout; the
  `DONE` block says whose lines they are.
- **draft** — four forms under the steps table. *columns to admit*: every column of the contract in catalogue order,
  timeframe-major, those the profile admits chosen at the start and all of them when there is no profile — so a
  column the catalogue does not offer on a timeframe cannot be admitted on it. *start search state*: the asset's own,
  or the recorded search's champion. *coordinates to search*: the coordinates of `GRID_BY_COORDINATE_DEFAULT`, each with its
  grid; the grid itself is not asked — it is one preset, and another grid is a hand's edit of the file. *search axes*:
  the search axes of a round in the order of `SERPENTINE_SEARCH_AXES`. The drafted profile carries every coordinate: one
  left unticked is pinned to where the asset stands — its promoted `<TICKER>_barriers.json`, else
  `START_BY_COORDINATE_DEFAULT` — the value the search starts from, and its grid becomes that one point, which has no
  neighbour, so its search family makes no move. The asset's noise sigma is carried over unchanged, a hand's edit of the
  file. Then the changes table, `parameter | now | after`, or the line `no profile changes`; a recorded search run
  under another profile puts one `WARN` line above the gate — the next turn starts a new search and overwrites the
  search's progress —, a fact about how the search resumes and not a refusal. The gate
  `draft <TICKER>_serpentine_search_profile.json?` offers `draft` — absent when nothing changes —, `back` and
  `cancel`. A draft needs the contract: without it the run ends on the failure block, whose *next* is
  `make features-catalogue ASSET=<TICKER>`.
- **recorded search** — writes nothing and ends on its last table: the state table, `parameter | value` — the asset,
  the profile, the coordinates searched, the search axes, the state evaluations and the rounds, the selection
  hypotheses and their terms by search axis as the search counted them at a round boundary, whether it converged,
  the champion and the proposal count — then the path table and the proposals table, or the lines `no accepted
  move` and `no proposal`. Which state evaluations the path and the proposals hold comes from the search's progress;
  each one's numbers from its line of the ledger; the coordinates a proposal moves are that line against the asset's
  own search state the search recorded in its inputs. The word is
  *recorded search* and not *status*, which is a stage's.

The tables the actions draw beyond the state table, and the order a narrow terminal leaves their columns out in; the
steps table (`step`, `state`, `choice`), the start search state form, the search axes form and the changes table drop none:

| table | columns | left out, in turn |
|---|---|---|
| the path table | `#`, `round`, `search axis`, `search family`, `state evaluation`, `path CAGR`, `path Calmar`, `path maxDD`, `trades` | `trades`, `path maxDD`, `path Calmar`, `search family` |
| the proposals table | `#`, `state evaluation`, `coordinates moved`, `path CAGR`, `path Calmar`, `path maxDD`, `trades` | `path maxDD`, `trades`, `path Calmar`, `coordinates moved` |
| the columns form | `column`, `timeframe`, `definition` | `definition`, `timeframe` |
| the coordinates form | `coordinate`, `grid`, `points` | `points`, `grid` |

The failures it names itself: no terminal on standard input, no gum on `PATH`, no asset named, no contract to draft
from, no recorded search to read, no proposal to promote, or a target that exited non-zero.

## Why it is built this way

| the file | what it is |
|---|---|
| `terminal.py` | the opening screen, the menu and the actions — a target started through make, the draft, the recorded search, the promotion; the only file that calls `make`, and the one that writes the profile; `--tickers` its one argument beside `-h`, `--help` |
| `config.py` | registered copies of the store read, the descriptors of the files it shows, the promotion's target, the search axes, the start geometry and the grid the draft offers, and the readers and the writer of JSON; `OUTPUT_PLAIN` and `MENU_TARGET_PATTERN` |
| `tui.py` | how a screen is drawn and an answer taken — one file with every other terminal's |

It runs on the host's `python3` with gum and imports the standard library and its own package alone
(`TUI-DESIGNER-ONE-TERMINAL-PER-MODULE`): `module_features/config.py` imports numpy, so what it reads of this module
and of the serpentine search is carried in its own `config.py`, registered in `module_skills/skill_glossary.md`
§ Twice by extraction with what it shares with the other terminals. The profile is written in the tree's canonical
JSON form, so the same decisions write the same bytes and a draft that changes nothing leaves git unmoved.
