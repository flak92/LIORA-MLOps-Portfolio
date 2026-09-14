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
  that is not UTF-8, ends the program in one line when it is read — by a crawl,
  an add or the snapshot; the menu's header counts the list's entries without
  reading them, so such an entry is removed in the menu.
- **The mission** is `crawlers_mission.md`, kept by hand: what the agent reports
  of one file, and how.
- **The vendors** are `vendors_for_crawling.toml`, kept by hand (§ Vendors).
- **The message** for a file is the mission, then `# Rules` with every file of
  `RULE_PATHS` and of `MODULE_RULE_PATHS` under its path — the canon, then the
  orientation and the skills of the module the file's first path segment names,
  of which a root file, or one under `module_skills/`, has none — then `# File under review: <path>` and the
  file, each line after its number.
  It carries everything, so the agent needs no tool and answers in one turn of text.
- **The agent** is the command line `build_command()` built: one fresh session per
  chosen file, one after another, in its user's own login, its stderr on the
  screen as it runs. The first failure — an exit other than zero, an empty answer
  or `AGENT_TIMEOUT_MINUTES` passed — ends the crawl with one line naming the
  file, `the agent gave no answer` or the minutes it ran past, and exit 1; the
  reports already written stay.
- **The report** of a file is `reports_after_crawled_files/<path>.md`. A crawl
  appends a blank line, the heading `## crawled <YYYY-MM-DD HH:MM> UTC · <vendor> · <labels> · <short commit>`,
  its labels the options chosen in the vendor's forms, the answer as it came and
  a blank line, and never overwrites or summarises. `REPO_ROOT` and the heading's
  commit are the sub-module's two calls of git.

## Vendors

`vendors_for_crawling.toml` holds one table per vendor, in the menu's order; its
header says what a table holds. After the vendor the menu asks each form its
table has — `model`, `effort`, `permissions`, in that order — and
`build_command()` appends to `command` the `args` of the option chosen in each.
The first option is preselected, so a crawl with the defaults is an Enter per
form, and a form the table lacks is not asked. The code knows no vendor and no
flag: a vendor, a model or a flag is a line of the file. The first `permissions`
option lets the agent use no tool — a crawl is one message and one answer — and
a vendor is `active` once one run of its command line on one file showed it
answering from the message alone.

## The menu

`make skills-crawl` opens the crawler's menu: a `gum style` header,
*Scalability crawler* over `<n> path(s) listed`, then `gum choose`
headed *action*, and the prompts of the action a hand chooses.

- **crawl** — `gum choose` headed *vendor*, one line per active vendor off
  `load_active_vendors()` in the file's order. Without the vendor's command line
  on the `PATH` the program ends in one line, `<cli> is not on PATH — install it
  and log in`, exit 1; with it, the vendor's forms (§ Vendors), then
  `gum choose --no-limit` headed *files to crawl*, every listed file preselected
  in the list's order — the queue a hand keeps — each line
  `<path> · <last_crawled_utc or never> · <crawl_count>` off
  `build_skills_status()`. Each chosen file in turn prints
  `crawling <path> · <vendor>` and goes with the mission and the rules to the
  agent, its answer appended to its report.
- **add a path** — `gum input`: an entry already listed writes nothing; any other
  that `status.load_entry_paths()` refuses ends the program in one line, exit 1,
  nothing written; the rest is appended through `write_list()`.
- **remove a path** — `gum choose` headed *path to remove*, among the list's
  entries: every line equal to it leaves `to_crawl.txt` through
  `write_list()`, and no report is removed.

`_gum()` reads a hand's answer off gum's stdout, gum drawing on stderr. No answer
in the menu or any prompt after it — Esc, Ctrl-C, no terminal, nothing chosen or typed — ends the
program with exit 0 and nothing written, not even the snapshot.

Without gum on the `PATH` (`AGENTS.md` § Values, *Minimum requirements*) the
program ends in one line that says where to install gum 2, exit 1; a
`vendors_for_crawling.toml` with no active vendor ends it the same way.

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
| `README_sub_module_scalability_crawler.md` | The front door: the two commands, the three files kept by hand and the loop. | Beside the files it names; the rules stay in this skill, which it cites. | It restates no rule and decides nothing. | no row — a reading of the tree that travels with the canon |
| `config.py` | The one surface of configuration (its docstring). | `crawl.py` and `status.py` import it; `STORE_STATUS_DIR` comes from the environment, as in every `config.py`; the sub-module's own files are read from `SUB_MODULE_DIR`, a listed path and a rule from `REPO_ROOT`. | A rule document swapped is one line; a vendor is a table of `vendors_for_crawling.toml`, not a line here. | no row — a reading of the tree that travels with the canon |
| `crawl.py` | The menu and the crawl (its docstring). | It imports `config.py` and `status.py`, reads the active vendors through `load_active_vendors()`, builds the agent's command line through `build_command()`, and runs gum, git once and that command line over `subprocess`. | It writes the reports, the list through `write_list()` and, through `status.py`, the snapshot — nothing else. | no row — a reading of the tree that travels with the canon |
| `status.py` | The snapshot (its docstring). | It imports `config.py`, reads the list and the reports, and writes `skills_status.json`; its `load_entry_paths()` is the list's one rule, which the menu's add also uses. | A function of the list and the reports. | no row — a reading of the tree that travels with the canon |
| `to_crawl.txt` + `crawlers_mission.md` + `vendors_for_crawling.toml` | The three inputs a hand keeps. | Beside the code that reads them. | `to_crawl.txt` edited by a hand in the file or in the menu, `crawlers_mission.md` and `vendors_for_crawling.toml` by hand alone; never by a crawl. | no row — a reading of the tree that travels with the canon |
| `reports_after_crawled_files/` | The reports, one per listed file, its path the file's. | Beside the crawler and tracked: documents a hand reads, not state of the chain (`AGENTS.md` § Pre-AWS architectural direction, *Storage is separate from compute*). | Appended by a crawl, committed by a hand. | no row — a reading of the tree that travels with the canon |
| `store/status/skills_status.json` | The snapshot `status.py` writes, tracked like the other three. | In the status store; the route `/store_status/<name>` serves it. | `STORE_STATUS_DIR / skills_status.json` in `config.py`. | STORAGE — status, run and trial objects |
