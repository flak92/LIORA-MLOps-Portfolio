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
`pending`, `running`, `done`, `failed` and `interrupted` — `absent` where there is no snapshot. Then the menu, the
targets `make help` lists that `MENU_TARGET_PATTERN` gives the canon (`TUI-DESIGNER-ACTIONS-COME-FROM-MAKEFILE`), then
the plan and the gate (`TUI-DESIGNER-A-PLAN-NAMES-WHAT-WILL-RUN`, `TUI-DESIGNER-A-GATE-IS-NOT-A-GUARD`); a crawl's one
line per controlled file stays on the screen as it comes. The failures it names itself: no terminal on standard input,
no gum on `PATH`, or a target that exited non-zero.

## Why it is built this way

Outside an action it writes nothing: the root and the sheet it reads from `module_skills/config.py`, the two crawl
files through the crawler's `config.py`, and it counts what it shows. It runs on the host's `python3` with gum,
imports the standard library and its own package alone (`TUI-DESIGNER-ONE-TERMINAL-PER-MODULE`) and takes no argument
but `-h`, `--help`; its `config.py` holds `MENU_TARGET_PATTERN` and `OUTPUT_PLAIN`, and what it shares with the module
terminals is registered in `module_skills/skill_glossary.md` § Twice by extraction.
