# Skills terminal

`module_skills/sub_module_terminal/` is the canon's terminal, the Skills terminal: `make skills-terminal` opens it.
Its screens follow the `TUI-DESIGNER-` rows of `module_skills/skill_tui_designer.md`; the crawl it starts is no TUI,
and the one rule of that document that reaches it is `TUI-DESIGNER-A-STARTED-PROCESS-PRINTS-ONE-LINE-PER-STEP`.

```bash
make skills-terminal                                                                       # the TUI over the tree and its sheet
STORE_STATUS_DIR=store/status python3 -B -m module_skills.sub_module_terminal.terminal -h   # the keys, plain output and the exit codes
```

## The screen

Its header block names the root of the tree and the sheet it works on, `skills_sheet.xlsx`. Its state table,
`parameter | value`, is the crawl as its two files hold it: the active vendor of `vendors_for_crawling.toml`, `none`
where no vendor is active, and, counted off the snapshot `skills_status.json`, how many controlled files stand
`pending`, `running`, `done`, `failed` and `interrupted` — `absent` where there is no snapshot. Its menu is every
target of the Makefile that carries a `##` and whose name `MENU_TARGET_PATTERN` gives the canon — today `skills-sync`,
`skills-configurables` and `skills-crawl`, in the Makefile's order — then `quit`; `skills-terminal` carries no `##`
and is no option of the menu it opens.

## The actions

One answer shows the plan — the target and the purpose its `##` carries —, the line `command  make <target>` and the
gate `<target>?`; `make <target>` then runs with its lines on this screen, a crawl's one line per controlled file among
them, and the run ends on the `DONE` block or on the failure block carrying make's exit code; then it closes. The
failures it names itself: no terminal on standard input, no gum on `PATH`, or a target that exited non-zero.

## Why it is built this way

Outside an action it creates no domain state and writes nothing: the root and the sheet it reads from
`module_skills/config.py`, the two crawl files through the crawler's `config.py`, and it counts what it shows. It
imports the standard library and its own package alone, runs on the host's `python3` with gum, in no container and no
virtual environment, and takes no argument but `-h`, `--help`. Its `config.py` holds `MENU_TARGET_PATTERN` and
`OUTPUT_PLAIN`; its `tui.py` is one file with the four module terminals', and `OUTPUT_PLAIN`, `HELP_LINE_PATTERN` and
the helpers `_option_rows()`, `_cancelled_exit_code()`, `_failure_exit_code()`, `_make()`, `_target_rows()` and
`_write_target()` are the copies it shares with them, each marked `# twice by extraction`.
