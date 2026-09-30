# Monitoring terminal

The hand's instrument over the monitoring module: the four snapshots the page reads, then one position of the
presentation switch started through `make`; then it closes. Its screens follow the `TUI-DESIGNER-` rows of
`module_skills/skill_tui_designer.md`, which every terminal of this tree obeys; this file says what its screen
holds.

```bash
make monitoring-terminal                # the TUI over the status store the Makefile exports
STORE_STATUS_DIR=store/status python3 -B -m module_monitoring.sub_module_terminal.terminal -h   # the keys, plain output and the exit codes
```

## The screen

The header block, *Monitoring terminal*, stands over how many of the four snapshots are there. Then the snapshots
table, one row per name of `SNAPSHOT_FILE_NAMES` in the status store: `snapshot`, the file name, and
`generated_at_utc` as the file carries it — `—` where the file carries no such key, as `skills_status.json` does not,
`absent` where the file is not there. It holds the identifier and one value, so no column is left out. Then the menu,
the targets `make help` lists that `MENU_TARGET_PATTERN` matches (`TUI-DESIGNER-ACTIONS-COME-FROM-MAKEFILE`), then the
plan and the gate (`TUI-DESIGNER-A-PLAN-NAMES-WHAT-WILL-RUN`, `TUI-DESIGNER-A-GATE-IS-NOT-A-GUARD`). What each position
moves is the Makefile's to say (`ASSET-CONTAINERS-ON-RAISES-THE-RESIDENT-OFF-TAKES-EVERYTHING-DOWN`); no image, container
name or port is written in `terminal.py`, and a container `on` has brought up stays up when Ctrl-C ends the terminal.

The failures it names itself: no terminal on standard input, no gum on `PATH`, or a target that exited non-zero.

## Why it is built this way

| the file | what it is |
|---|---|
| `terminal.py` | the opening screen, the menu read off `make help`, the plan and its gate, and the one action; the only file that calls `make`; no argument but `-h`, `--help` |
| `config.py` | the status store it reads, `STORE_STATUS_DIR`; the four snapshots it shows, `SNAPSHOT_FILE_NAMES`, in the order of the writers of the page's tabs; the one reader of JSON; `OUTPUT_PLAIN` and `MENU_TARGET_PATTERN` |
| `tui.py` | how a screen is drawn and an answer taken — one file with every other terminal's |

It runs on the host's `python3` with gum and imports the standard library and its own package alone
(`TUI-DESIGNER-ONE-TERMINAL-PER-MODULE`); what it shares with the other terminals is registered in
`module_skills/skill_glossary.md` § Twice by extraction.
