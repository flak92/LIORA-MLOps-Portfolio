# Scalability crawler

Reads the files a hand lists against the written rules and appends each agent's answer to the file's
report. Its rules are `../skill_scalability_crawler.md`.

```bash
make skills-crawl     # the menu: crawl (vendor, model, effort, permissions, files), add a path or remove a path
make skills-status    # store/status/skills_status.json again, after to_crawl.txt was edited by hand
```

Kept by hand: `to_crawl.txt`, the list; `crawlers_mission.md`, what the agent reports; and
`vendors_for_crawling.toml`, the vendors and their forms.

## The loop

A rule is written through `../skill_self_explaining_naming.md` § Minting a new convention: a pattern
the reports show a third time is minted or declined in one commit with its register row, and the same
file is crawled again. A file is read against the canon and the documents of its own module, which
`MODULE_RULE_PATHS` in `config.py` finds through `{module}`, so a skill is assigned to crawling by the
module it sits in. The queue is the order of `to_crawl.txt`. An unexplained finding is the missing
sentence, proposed for the owner of the file to accept.
