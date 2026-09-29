# Monitoring terminal

The hand's instrument over the monitoring module: the four snapshots the page reads, then one position of the
presentation switch — `on` or `off`, every target of the Makefile carrying a `##` that `MENU_TARGET_PATTERN` gives
this module — started through `make`; then it closes. Its rules are `skill_monitoring_terminal.md`, beside this file,
and the standards of its screens `../../module_skills/skill_tui_designer.md`, which every terminal of this tree obeys.

```bash
make monitoring-terminal                # the TUI over the status store the Makefile exports
STORE_STATUS_DIR=store/status python3 -B -m module_monitoring.sub_module_terminal.terminal -h   # the actions, the keys, plain output and the exit codes
```

It computes nothing and writes nothing: the snapshots it reads through its own `config.py`, its menu it reads off
`make help`, and everything that runs, runs through `make` — the Makefile is where the image, the resident and every
container of this project are named.

| the file | what it is |
|---|---|
| `terminal.py` | the opening screen, the menu read off `make help`, the plan and its gate, and the one action; the only file that calls `make` |
| `config.py` | the status store and the four snapshots it shows, the one reader of JSON, `MENU_TARGET_PATTERN` — which of the Makefile's targets the menu offers — and plain output |
| `tui.py` | how a screen is drawn and an answer taken — one file with every other terminal's and the crawler's, five times by extraction |
