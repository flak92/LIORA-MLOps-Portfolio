# Skill: the scalability crawler — the listed files read against the written rules

`module_skills/sub_module_scalability_crawler/` reads the files a hand lists
against the written rules, writes a report a hand reads, and its snapshot. A
hand runs it in a terminal, one action per run; it gates nothing, edits no file
but its list and commits nothing (`AGENTS.md` § Values). *The repository shows the
destination, not the road*: the rules draw the destination, and a report says
where one file stands from it.

## The list, the mission, the report

- **The list** is `to_crawl.txt`, kept by a hand, in the file or through the
  menu: a path from the root per line, a blank line skipped, a folder every
  file under it in byte order but `__pycache__` and the reports. An entry is read
  as a path, so `./x` and `x/` are `x`. An entry that names nothing, or a file
  that is not UTF-8, ends the program in one line; the menu's header counts the
  listed files, so such an entry stops the program before the menu, and a hand
  fixes it in the file.
- **The mission** is `crawlers_mission.md`, kept by hand: what the agent reports
  of one file, and how.
- **The message** for a file is the mission, then `# Rules` with every file of
  `RULE_PATHS` under its path, then `# File under review: <path>` and the file.
  It carries everything, so the agent has no tool and answers in one turn of text.
- **The agent** is `AGENT_COMMAND`: one fresh session of the Claude Code command
  line per chosen file, one after another, in its user's own login. The first
  failure, an exit other than zero or `AGENT_TIMEOUT_MINUTES` passed, ends the
  crawl with a line naming the file and the agent's exit code and error, or the
  minutes it ran past, and exit 1; the reports already written stay.
- **The report** of a file is `reports_after_crawled_files/<path>.md`. A crawl
  appends a blank line, the heading `## crawled <YYYY-MM-DD HH:MM> UTC · <model> · <short commit>`,
  the answer as it came and a blank line, and never overwrites or summarises. The
  heading's commit is the one call of git in the sub-module.

## The menu

`make skills-crawl` opens the crawler's menu: a `gum style` header,
*Scalability crawler* over `<n> file(s) listed · <model>`, then `gum choose`
headed *action*, and one prompt for the action a hand chooses.

- **crawl** — `gum choose --no-limit` headed *files to crawl*, every listed file
  preselected, each line `<path> · <last_crawled_utc or never> · <crawl_count>`
  off `build_skills_status()`. Each chosen file in turn prints `crawling <path>`
  and goes with the mission and the rules to the agent, its answer appended to
  its report.
- **add a path** — `gum input`: an entry `status.load_entry_paths()` refuses ends
  the program in one line, exit 1, nothing written; an entry already listed
  writes nothing; any other is appended through `write_list()`.
- **remove a path** — `gum choose` headed *path to remove*, among the list's
  entries: the first line that matches leaves `to_crawl.txt` through
  `write_list()`, and no report is removed.

`_gum()` reads a hand's answer off gum's stdout, gum drawing on stderr. No answer
in the menu or its prompt — Esc, Ctrl-C, no terminal, nothing chosen or typed — ends the
program with exit 0 and nothing written, not even the snapshot.

Without gum on the `PATH` (`AGENTS.md` § Values, *Minimum requirements*) the
program ends in one line that says where to install gum 2, exit 1, as it does
without the agent's command line.

After a run `git status` shows the reports that grew, the list if a path was
added or removed, and the snapshot; a hand reads them and commits them.

## The actuality

Every action of `make skills-crawl` that changes something ends with
`make skills-status`'s work, a failed crawl too.
`store/status/skills_status.json` holds a row per listed file, sorted by `path`,
with its `report`, its `crawl_count` and its `last_crawled_utc`, read off the
report's headings. No clock enters it, so unchanged reports write the same bytes.
The Scalability tab draws it as one table and adds each file's age against the
browser's clock.

## Design rationale

Why each object sits where it does — the answers of
`skill_self_explaining_naming.md` § The naming review; the canon has no
orientation of its own, so its sub-module argues here (`AGENTS.md` § Pre-AWS
architectural direction).

| object | why here | why beside these | why this boundary | answers to |
|---|---|---|---|---|
| `__init__.py` | The package that makes `crawl` and `status` commands of `python3 -m`. | It imports nothing; `module_skills/` stays a folder of documents. | The commands run from the checkout's root. | no row — a reading of the tree that travels with the canon |
| `config.py` | The one surface of configuration: the snapshot's path, the paths kept by hand, `RULE_PATHS`, `AGENT_COMMAND`. | `crawl.py` and `status.py` import it; `STORE_STATUS_DIR` comes from the environment, as in every `config.py`, and every other path is relative to the root. | A rule document or an agent swapped is one line. | no row — a reading of the tree that travels with the canon |
| `crawl.py` | The menu and the crawl (its docstring). | It imports `config.py` and `status.py`, and runs gum, git once and the agent's command line over `subprocess`. | It writes the reports, the list through `write_list()` and, through `status.py`, the snapshot — nothing else. | no row — a reading of the tree that travels with the canon |
| `status.py` | The snapshot (its docstring). | It imports `config.py`, reads the list and the reports, and writes `skills_status.json`; its `load_entry_paths()` is the list's one rule, which the menu's add also uses. | A function of the list and the reports. | no row — a reading of the tree that travels with the canon |
| `to_crawl.txt` + `crawlers_mission.md` | The two inputs a hand keeps. | Beside the code that reads them. | `to_crawl.txt` edited by a hand in the file or in the menu, `crawlers_mission.md` in an editor alone; never by a crawl. | no row — a reading of the tree that travels with the canon |
| `reports_after_crawled_files/` | The reports, one per listed file, its path the file's. | Beside the crawler and tracked: documents a hand reads, not state of the chain (`AGENTS.md` § Pre-AWS architectural direction, *Storage is separate from compute*). | Appended by a crawl, committed by a hand. | no row — a reading of the tree that travels with the canon |
| `store/status/skills_status.json` | The snapshot `status.py` writes, tracked like the other three. | In the status store; the route `/store_status/<name>` serves it. | `STORE_STATUS_DIR / skills_status.json` in `config.py`. | STORAGE — status, run and trial objects |
