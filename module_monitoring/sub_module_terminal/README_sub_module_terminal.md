# Monitoring terminal

The hand's instrument over the monitoring module: the four snapshots the page reads, then one position of the
presentation switch — `on` or `off`, the targets of the Makefile carrying a `##` that `MENU_TARGET_PATTERN` gives
this module — started through `make`; then it closes. Its screens follow the `TUI-DESIGNER-` rows of
`../../module_skills/skill_tui_designer.md`, which every terminal of this tree obeys; this file says what its screen
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
`gum choose` headed *action*: `on`, `off`, then `quit` (`TUI-DESIGNER-ACTIONS-COME-FROM-MAKEFILE`);
`monitoring-terminal` carries no `##` and is no option of the menu it opens.

## The actions

The plan — `target` and the `purpose` its `##` carries —, the line `command  make on` or `command  make off`, and the
gate `on?` or `off?` with the target first and `cancel`; the target's own lines stay on the screen as they come, and
the run ends on the `DONE` block or on the failure block carrying make's exit code. What each position moves is the
Makefile's to say: `on` builds the one image every service runs, brings the one resident, `dashboard`, up, then prints
the page's address and opens it; `off` stops and removes every container of this project. No image, container name or
port is written in `terminal.py`, and a container `on` has brought up stays up when Ctrl-C ends the terminal.

The failures it names itself: no terminal on standard input, no gum on `PATH`, or a target that exited non-zero.

## Why it is built this way

| the file | what it is |
|---|---|
| `terminal.py` | the opening screen, the menu read off `make help`, the plan and its gate, and the one action; the only file that calls `make`; no argument but `-h`, `--help` |
| `config.py` | the status store it reads, `STORE_STATUS_DIR`; the four snapshots it shows, `SNAPSHOT_FILE_NAMES`, in the order of the writers of the page's tabs; the one reader of JSON; `OUTPUT_PLAIN` and `MENU_TARGET_PATTERN` |
| `tui.py` | how a screen is drawn and an answer taken — one file with the four other terminals', the canon's among them |

It imports the standard library and its own package alone and runs on the host's `python3` with gum, in no container
and no virtual environment; the Makefile it calls is the one of the directory it was opened in. No module imports
another, and a package for what the terminals share would be the `common` the contract refuses, so it carries its
copies: `STORE_STATUS_DIR`, `load_json()`, `tui.py`, `OUTPUT_PLAIN`, `HELP_LINE_PATTERN` and the helpers
`_option_rows()`, `_cancelled_exit_code()`, `_failure_exit_code()`, `_make()`, `_target_rows()` and `_write_target()`,
each marked `# twice by extraction`, registered in `module_skills/glossary.md` and changed on every side at once.
