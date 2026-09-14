# Skill: the scalability crawler — the listed files read against the written rules

`module_skills/sub_module_scalability_crawler/` reads the files a hand lists
against the written rules, writes a report a hand reads, and its snapshot; it
gates nothing, edits nothing and commits nothing (`AGENTS.md` § Values). *The
repository shows the destination, not the road*: the rules draw the destination,
and a report says where one file stands from it.

## The list, the mission, the report

- **The list** is `to_crawl.txt`, kept by hand: a path from the root per line, a
  blank line skipped, a line ending in `/` every file under it in byte order but
  `__pycache__` and the reports. An entry that names nothing, or a file that is
  not UTF-8, ends the crawl in one line.
- **The mission** is `crawlers_mission.md`, kept by hand: what the agent reports
  of one file, and how.
- **The message** for a file is the mission, then `# Rules` with every file of
  `RULE_PATHS` under its path, then `# File under review: <path>` and the file.
  It carries everything, so the agent has no tool and answers in one turn of text.
- **The agent** is `AGENT_COMMAND`: one fresh session of the Claude Code command
  line per file, one after another, in its user's own login. The first failure —
  an exit other than zero, or `AGENT_TIMEOUT_MINUTES` passed — ends the crawl
  with the agent's error; the reports already written stay.
- **The report** of a file is `reports_after_crawled_files/<path>.md`. A crawl
  appends a blank line, the heading `## <YYYY-MM-DD HH:MM> UTC · <model> · <short commit>`,
  the answer as it came and a blank line, and never overwrites or summarises. The
  heading's commit is the one call of git in the sub-module.

## The actuality

`make skills-crawl` ends with `make skills-status`'s work, after a failure too:
`store/status/skills_status.json` holds a row per listed file, sorted by `path`,
with its `report`, its `crawl_count` and its `last_crawled_utc`, read off the
report's headings. No clock enters it, so unchanged reports write the same bytes.
The Scalability tab draws it as one table and adds each file's age against the
browser's clock.

## The schedule

Nothing in the tree schedules a crawl: the `Makefile` never schedules
(`AGENTS.md` § Pre-AWS architectural direction). A host that wants one every
weekday night writes the schedule outside the tree, with its own checkout, the
`PATH` of the shell the agent's command line is installed in and the same user,
whose session the command line runs in — and only once a crawl started by hand
has gone through the whole list without a failure.

The default is a user timer of systemd, because its journal keeps what a crawl
printed — the files it sent, a failure — for `journalctl --user -u skills-crawl`
to read in the morning:

```
# skills-crawl.service, beside the timer in the user's systemd directory
[Service]
Type=oneshot
WorkingDirectory=<checkout>
Environment=PATH=<PATH of the installing shell>
ExecStart=/usr/bin/make skills-crawl
Nice=10

# skills-crawl.timer
[Timer]
OnCalendar=Mon..Fri 02:00
Persistent=true

[Install]
WantedBy=timers.target
```

`systemctl --user enable --now skills-crawl.timer` starts it, and
`loginctl enable-linger` keeps it on a host nobody stays logged in to. The
fallback is a cron line of the same user, its output mailed:

```
MAILTO=<address>
0 2 * * 1-5 cd <checkout> && PATH=<PATH of the installing shell> make skills-crawl
```

`make tmux-skills-crawl` is the crawl a hand starts and may leave. Either way the
morning is the same: `git status` shows the reports that grew and the snapshot,
and a hand reads them and commits them.

## Design rationale

Why each object sits where it does — the answers of
`skill_self_explaining_naming.md` § The naming review; the canon has no
orientation of its own, so its sub-module argues here (`AGENTS.md` § Pre-AWS
architectural direction).

| object | why here | why beside these | why this boundary | answers to |
|---|---|---|---|---|
| `__init__.py` | The package that makes `crawl` and `status` commands of `python3 -m`. | It imports nothing; `module_skills/` stays a folder of documents. | The commands run from the checkout's root. | no row — a reading of the tree that travels with the canon |
| `config.py` | The one surface of configuration: the snapshot's path, the paths kept by hand, `RULE_PATHS`, `AGENT_COMMAND`. | `crawl.py` and `status.py` import it; `STORE_STATUS_DIR` comes from the environment, as in every `config.py`, and every other path is relative to the root. | A rule document or an agent swapped is one line. | no row — a reading of the tree that travels with the canon |
| `crawl.py` | The crawl (its docstring). | It imports `config.py` and `status.py`, and runs git once and the agent's command line over `subprocess`. | It writes the reports and, through `status.py`, the snapshot — nothing else. | no row — a reading of the tree that travels with the canon |
| `status.py` | The snapshot (its docstring). | It imports `config.py`, reads the list and the reports, and writes `skills_status.json`. | A function of the list and the reports. | no row — a reading of the tree that travels with the canon |
| `to_crawl.txt` + `crawlers_mission.md` | The two inputs a hand keeps. | Beside the code that reads them. | Edited by hand, never by a crawl. | no row — a reading of the tree that travels with the canon |
| `reports_after_crawled_files/` | The reports, one per listed file, its path the file's. | Beside the crawler and tracked: documents a hand reads, not state of the chain (`AGENTS.md` § Pre-AWS architectural direction, *Storage is separate from compute*). | Appended by a crawl, committed by a hand. | no row — a reading of the tree that travels with the canon |
| `store/status/skills_status.json` | The snapshot `status.py` writes, tracked like the other three. | In the status store; the route `/store_status/<name>` serves it. | `STORE_STATUS_DIR / skills_status.json` in `config.py`. | STORAGE — status, run and trial objects |
