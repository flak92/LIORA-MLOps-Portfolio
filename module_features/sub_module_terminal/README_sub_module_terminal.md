# Features terminal

The hand's instrument over the feature module: per asset, how many timeframes its bars and its catalogue hold a
partition for, whether its contract stands, where its serpentine search profile stands and how many trials the
search's ledger holds; then one action — a target of the module started through `make`, or one of the serpentine
search's own: draft the profile, read the recorded search, promote a proposal; then it closes. Its rules are
`skill_features_terminal.md`, beside this file, and the standards of its screens
`../../module_skills/skill_tui_designer.md`, which every terminal of this tree obeys.

```bash
make features-terminal                  # the TUI over the basket
make features-terminal ASSET=BTC        # the TUI over one asset — ASSET= names it, as for every stage
STORE_ASSETS_ARTIFACTS_DIR=store/assets_artifacts python3 -B -m module_features.sub_module_terminal.terminal -h   # the actions, the keys, plain output and the exit codes
```

The menu is the Makefile's: every target `make help` lists — one carrying a `##` — whose name `MENU_TARGET_PATTERN`
matches, `features-<stage>`, `features-all` and a stage's `tmux-` twin, in the Makefile's order, then the terminal's
own `draft` and `recorded search`; `features-terminal` carries no `##` and is no option of the menu it opens. A target
runs as `make <target> ASSET=<TICKER>` after its plan and a gate. The promotion asks for the proposal on its own
screen and runs `make features-serpentine-search-promote ASSET=<TICKER> PROPOSAL=<n>`, which copies the proposal and
reruns the asset's ML chain. `recorded search` reads the state file and its ledger — where the search stands, the
path it took, its proposals — and writes nothing. `draft` writes `<TICKER>_serpentine_search_profile.json`: the
columns admitted, the state the search starts from, the coordinates searched over the preset
`GRID_BY_COORDINATE_DEFAULT` — an unsearched one pinned to one point — and the loops of a round, carrying the
profile's noise sigma over unchanged, which a hand sets in the file.

It computes nothing, and the profile is the one file it writes: what the store holds it reads off the artifacts store
by the descriptors its `config.py` carries, and everything that runs, runs through `make` — the Makefile is where a
container and the order of the chain are named.

| the file | what it is |
|---|---|
| `terminal.py` | the opening screen, the menu and the actions — a target started through make, the draft, the recorded search, the promotion; the only file that calls `make` |
| `config.py` | the store read and the descriptors of the files it shows — registered copies, because `module_features/config.py` imports `.indicators`, and numpy with it, and the serpentine search's `config.py` imports that one —, the promotion's target, the loops, the start geometry and the grid the draft offers, the JSON readers and writer, plain output, and the menu's pattern |
| `tui.py` | how a screen is drawn and an answer taken — one file with every other terminal's and the crawler's, five times by extraction |
