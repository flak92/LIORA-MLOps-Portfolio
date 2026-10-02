# Scalability crawler

Reads every controlled file of the files matrix against the Skills marked for it, through the one active vendor, and
writes one current report per file and the snapshot. It gates nothing, commits nothing and draws no screen of its
own: `make skills-terminal`, the canon's terminal, offers it among the `skills-` targets. Its rules are
`skill_scalability_crawler.md`, beside this file.

```bash
make skills-crawl     # make skills-sync, then every controlled file sent with its marked Skills to the active vendor; Ctrl-C ends it, the reports already written stay
```

## What it reads and what it writes

- **Kept by hand:** the files matrix, the `files` tab of `module_skills/skills_sheet.xlsx`
  (`SCALABILITY-CRAWLER-MATRIX-IS-PATH-BY-SKILL`); `crawlers_mission.md`, what the vendor receives and how it answers;
  and `vendors_for_crawling.toml`, one table per vendor (`SCALABILITY-CRAWLER-VENDOR-IS-DATA`,
  `SCALABILITY-CRAWLER-ONE-VENDOR-IS-ACTIVE`).
- **Sent** once per controlled file: the file, the Skills marked for it and the mission; the answer names the
  `rule_id` of every departure (`SCALABILITY-CRAWLER-FINDING-NAMES-A-RULE`).
- **Written:** one current report per file under `store/status/reports_after_crawled_files/`
  (`SCALABILITY-CRAWLER-ONE-CURRENT-REPORT-PER-FILE`) and `store/status/skills_status.json`, which the page's
  Scalability tab shows (`SCALABILITY-CRAWLER-SNAPSHOT-KEEPS-ITS-KEYS`).

## What a crawl prints

The files go one after another, in the order of their paths, one line on stdout after each file's result and one
closing line after the last, in the form of the register's row for the crawl's progress.

`done` says the report was written, not that the file conforms: read the report. What ends a crawl and what does not:
`SCALABILITY-CRAWLER-REFUSAL-IS-ONE-LINE` and `SCALABILITY-CRAWLER-FAILED-FILE-DOES-NOT-STOP-THE-CRAWL`.

## Design rationale

Why each object sits where it does; the canon's sub-module argues its objects here.

| object | why here | why this boundary | answers to |
|---|---|---|---|
| `__init__.py` | The package that makes `crawl` a command of `python3 -m`. | It imports nothing, so the crawl runs from the root of the tree without a stage of any module. | no row — a reading of the tree that travels with the canon |
| `config.py` | The one surface of configuration (its docstring). | `STORE_STATUS_DIR` from the environment, as in every `config.py`; its own files from `SUB_MODULE_DIR`; the root of the tree and the sheet from `module_skills/config.py`. | no row — a reading of the tree that travels with the canon |
| `crawl.py` | The crawl (its docstring). | It reads the sheet through `module_skills/sheet.py`, the vendor, the mission and the rendered Skills, runs the vendor's `argv` over `subprocess`, resets the reports and writes each report, the snapshot through `status.py`; it takes no argument. | no row — a reading of the tree that travels with the canon |
| `status.py` | The snapshot (its docstring). | One row per controlled file, and the one writer of the snapshot, whole through `write_text()` of `module_skills/sync.py`. | no row — a reading of the tree that travels with the canon |
| `crawlers_mission.md`, `vendors_for_crawling.toml` | Two of the three inputs a hand keeps, beside the code that reads them; the third, the files matrix, is a tab of the sheet. | Edited by hand alone, never by a crawl. | no row — a reading of the tree that travels with the canon |
| `store/status/reports_after_crawled_files/`, `store/status/skills_status.json` | What a crawl writes: one report per controlled file, its path the file's, and the snapshot. | In the status store, not beside the code: generated state, the reports never committed and the snapshot served to the page under `/status/`. | STORAGE — status, run and trial objects |
