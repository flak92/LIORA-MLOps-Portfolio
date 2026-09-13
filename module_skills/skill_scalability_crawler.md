# Skill: the scalability crawler — the tree counted against its contract

`module_skills/sub_module_scalability_crawler/` counts the tracked tree against
`AGENTS.md` and the skills and writes the count into
`store/status/skills_status.json`. Nothing waits on the numbers: no target of the
chain, no service and no merge depends on them (`AGENTS.md` § Values). *The
repository shows the destination, not the road*: the contract draws the
destination, and the count says how far the tree stands from it.

`make skills-status` runs it on the host (`AGENTS.md` § Canonical vocabulary, the
row Makefile targets). Run it on a clean tree: the snapshot names the last commit
that touched what it reads, `measured_at_commit`, and that commit's time,
`measured_at_commit_utc`. It carries no clock of its own, so an unchanged tree
measures to the same bytes, and `git diff --quiet -- store/status/skills_status.json`
says whether the committed snapshot is current. A commit that changes what the
snapshot reads is followed by one that commits the snapshot alone.

## The registry

Every metric is one row of `METRICS` in `status.py` — its name, its family, its
kind, the rule it counts, cited by document and section and never restated, and
the measurement that counts it — so each metric is named once. A kind is one of
the two `glossary.md` § Data quality names. Each metric publishes its value and at
most `EXAMPLES_PER_METRIC_COUNT` places it found, `path:line — name`, sorted; where
the name is itself the forbidden form — a debt marker, a cloud noun — the place
carries the category word instead.

A measurement is one of six kinds, and a closed list of `config.py` is its
argument:

- `path_segment_in` — a segment of a tracked path;
- `python_name_prefix_in` — a Python name by its prefix, its suffix or its whole
  form, beside the names the contract lets stand;
- `json_key_in` — a key of a tracked JSON file;
- `token_in_files` — a token bounded by anything but a word character, outside its
  seats — a document or one section of it — and outside the forms it stands in;
- `regex_in_prose` — a pattern in Markdown prose, fences and inline code blanked;
- `ast_rule` — a structural rule, named for what it reads: the imports, the store
  literals, the design rationale, the register, the references, the registered
  copies, the enumerations.

A word added to a list the contract closes is one line of `config.py` and no
code. The families a rule compares against are read off the tree and never
listed: the modules are the `module_*` directories, in the order `all:` of the
`Makefile` names them and the rest after in byte order; the snapshots are
`store/status/*_status.json`; the stores are `STORES` of the `Makefile`; the tabs
are the buttons of `#tabs`; the section scripts are the scripts the page loads
beside `page.js`.

The files in scope — `files_in_scope_count`, the Python and the prose — are every
tracked file but the stores, which are derived, and the dated reviews,
`REPORT_*.md` (`MEASURED_SCOPE_PATHSPECS`). Of the stores only the keys of their
JSON and their file names are read, and never the snapshot this stage writes. A
file git does not track is not counted.

## The rules a metric reads by

- **A key of a published object** has its row when `glossary.md` writes the name
  in a backtick outside a never cell. The keys of a dictionary keyed by data are
  data, not names: a dictionary is keyed by data when it is named
  `<what>_by_<dimension>`, or when every key holds a digit or is a string value
  the same file carries. One keyed by data and named without `_by_` is an
  observation; its rename is a proposal and never an edit, because a serialised
  name moves with everything that writes or reads it
  (`skill_self_explaining_naming.md`).
- **A registered copy** of `glossary.md` § Twice by extraction compares as that
  section promises: a function as its syntax tree, `ast.dump`, so a comment never
  drifts; a constant as its value; an owner that derives by an expression what
  another owner writes as a literal is not compared with it.
- **An enumeration** is two or more members of one family joined by nothing but
  separators — commas, `and`, `or`, slashes, backticks — or a number word before
  the family's noun, and it is incomplete when it names fewer members than the
  family holds. The families are the snapshots, the tabs, the stores, the modules
  and the section scripts; make targets and compose services are named two at a
  time, by example, everywhere, and are not counted. A legitimate subset — the
  computational snapshots, the pipeline stores — stays an example for a reader
  to judge.
- **A path in backticks** (`AGENTS.md` § Architecture shape) resolves by six
  rules, and nothing else forgives it:
  1. whitespace, `://` or a leading slash is not a path of the tree;
  2. a trailing slash names a directory;
  3. a path resolves against its document's directory, the document's module
     directory and the root;
  4. every `<…>` placeholder reads as `*`, and a pattern resolves when it matches a
     tracked path or a store of `STORES`; a path under a store resolves when `.gitignore`
     keeps it out of the tree — state the store holds and git never tracks;
  5. a never cell, a what-it-forbids cell, § Rejected vocabulary and § Skills
     absent here, described name a path to refuse it, not to reference it;
  6. a token is a path only when its first segment is a tracked entry of the root
     or of the document's own directory, or the parent directory.

  A reference the six rules do not resolve is corrected in the prose that holds
  it.
- **A placement is argued** (`AGENTS.md` § Pre-AWS architectural direction) where
  its directory argues it: a runtime module's orientation, this sub-module's
  § Design rationale below, and, for the documents of `module_skills/`, the index
  that links them (`DESIGN_RATIONALE_SOURCE_BY_DIRECTORY`). A row that names a
  directory covers the files under it.
- **A word of the contract** is counted wherever a hyphen or a space bounds it,
  except in the forms it stands in: a cloud noun inside the repository's own word
  or inside the rejected form § Rejected vocabulary spells
  (`CLOUD_NOUN_STANDING_FORMS`). An interface word of § Rejected vocabulary is not
  counted where the register enacts it: a name in a backtick of a code cell, or a
  word of a UI label cell, of `glossary.md`.

## The shape

`shape` reads the rows of `AGENTS.md` § The shape at the measured commit, and
no others. `SHAPE_EVIDENCE_BY_CONDITION` in `config.py` names each row's evidence
once: a metric of `METRICS`, and the row holds when that invariant reads zero; or,
where no count can say it, the target that proves the row by hand, and `holds` is
then null. A row the contract adds is one entry there; a row with no entry shows
no evidence.

## The review record

`store/status/skills_review.json` holds one row per reviewed file — its `path`,
the `blob_id` it reviewed, the `canon_id` it was reviewed under, its `verdict`,
its `self_explaining_level` with the line that earns it as `evidence`, and its
`findings` — and the `proposals` a review wrote. `crawl.py` writes it, through
one function; `status.py` and the page read it. A row counts while its file is
still the blob the row names, and is stale while the canon's content is not the
`canon_id` the row names; the canon is `CANON_PATHSPECS` — `AGENTS.md`,
`module_skills/*.md` and `module_*/skills/*.md`. The writer keeps the rows
sorted by path and the proposals by pattern, drops a row whose file left the
list and a proposal made under another canon, and rewrites the file only when
its content changes. The review's share, `files_reviewed_pct`, is taken over the
files the list names; every other file in scope is measured and never reviewed.

## The pass

`make skills-crawl` runs one bounded pass, and `make tmux-skills-crawl` runs the
same pass in the tmux session `skills-crawl`, which outlives the terminal —
`tmux attach -t skills-crawl` to watch it, Ctrl-C to stop it. A pass:

1. stops, in one line, when an entry of `CRAWL_PATHSPECS` names no tracked file
   — a misspelt path never empties the queue in silence — when the checkout is not clean — a file git does not
   track is work in progress, so scratch belongs in a gitignored path — when
   branch `scalability-crawler` holds a commit the checkout has not merged, or
   when the agent's command line is not on `PATH`;
2. is skipped, saying `skipped: activity at <path>`, when anything under the
   checkout changed within `QUIET_PROBE_SECONDS`: a stage writing into a store is
   activity, and the crawler's own two files in the status store are not;
3. queues the files `CRAWL_PATHSPECS` names — a list kept by hand in
   `config.py`, a file, a document or a whole folder added at a time — whose row
   is missing, whose blob is not the row's or whose canon is not the row's —
   unreviewed, changed, stale, in that order —
   the amendable files first and the review-only files last: the crawler's own,
   the canon and the root's. An empty queue ends the pass before anything is
   created;
4. opens a worktree beside the checkout on branch `scalability-crawler` and
   measures its invariants, the base of the ratchet;
5. reviews at most `CRAWL_PASS_BATCH_COUNT` batches, each at most
   `CRAWL_BATCH_FILE_COUNT` files of one module and one mode, one agent at a time.
   Every attempt starts from the committed files. An amendment is kept when every
   edit stays inside the batch — its files, the module's orientation and the
   glossary, and nothing in a review-only batch — when every edited Python file
   still compiles, and when no invariant, measured by the checkout's own code,
   exceeds the base. A failed attempt is tried once more, its failure in the
   brief; then the batch is reverted, and the files the agent edited — every file
   of the batch, when no attempt answered — are `deferred` with the failure as
   their finding, while the others keep their verdict;
6. commits each batch once — the kept amendments with the review record, the
   commit's body its report: every file's verdict and findings, the proposals,
   the turns and seconds of every attempt, the failure — and, after the last
   batch, the snapshot alone, its body the sums of the pass and the listed files
   left for the next one; then removes the worktree and prints the two commands a
   morning has: `git merge --no-ff --no-edit scalability-crawler` or
   `git branch -D scalability-crawler`. `git log scalability-crawler` is the
   morning's report; a pass the probe skipped commits nothing.

A launch of the agent that returns no result is a configuration error: the pass
exits 1 with the agent's own error and writes no row. The checkout is never
written; a change to it during the pass stops the pass. After the merge the next
pass goes on from the record.

## The reviewer

The reviewer is Claude Sonnet 5 through its command line, `AGENT_COMMAND` in
`config.py`: the brief on stdin and one JSON envelope on stdout, the tools a
review needs and none that creates a file, no question it could wait on, and
none of the user's settings, MCP servers or sessions. The brief,
`crawl_brief_template.md`, cites the rules the reviewer judges by and restates
none: the reviewer amends what the grammar derives without a decision, writes a
finding for everything else, and proposes a convention at two occurrences; the
page marks the third (`skill_self_explaining_naming.md` § Minting a new
convention).

## One commit per batch

A row names the blob it reviewed and the canon it was reviewed under — git's own
identities, read off the index once the amendment is staged — and never a
commit. A file is current while its blob and the canon are the ones its row
names, whatever merge brought them: a squash, a rebase and a `--no-ff` merge
leave the same blobs, so one commit per batch carries everything a later pass
reads.

## The schedule

Nothing in the tree schedules a pass: the `Makefile` never schedules
(`AGENTS.md` § Pre-AWS architectural direction). A host that wants one every
weekday night writes the schedule outside the tree, with its own checkout and the
`PATH` of the shell the reviewer's command line is installed in, in one of two
forms.

The default is a user timer of systemd, because its journal keeps what a pass
printed — `skipped: activity at …`, a stop, the summary — for
`journalctl --user -u skills-crawl` to read in the morning:

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
fallback is a cron line, its output mailed:

```
MAILTO=<address>
0 2 * * 1-5 cd <checkout> && PATH=<PATH of the installing shell> make skills-crawl
```

A timer or a cron line needs no terminal; `make tmux-skills-crawl` is the pass a
hand starts and may leave. Either way the morning is the same:
`git log --oneline HEAD..scalability-crawler`, then one command —
`git merge --no-ff --no-edit scalability-crawler` or
`git branch -D scalability-crawler`.

## Design rationale

Why each object of this sub-module sits where it does — the answers of
`skill_self_explaining_naming.md` § The naming review, one row per object; the
canon has no orientation of its own, so its sub-module argues here
(`AGENTS.md` § Pre-AWS architectural direction). The mapping row is
`skill_pre_aws_solution.md` § The mapping table, cited by its *responsibility*
column.

| object | why here | why beside these | why this boundary | answers to |
|---|---|---|---|---|
| `__init__.py` | The package that makes `python3 -m module_skills.sub_module_scalability_crawler.status` a command, its docstring the sub-module's responsibility in one line. | It imports nothing, and `module_skills/` above it stays a folder of documents with no package file. | The same command runs from whichever checkout git names as its root. | no row — a measurement of the tree that travels with the canon, run by a hand on the host |
| `config.py` | The one surface of configuration (its docstring): where the snapshot lands, the files in scope, the canon, the closed lists each read off a section of the contract or a skill, and its copy of `rounded()` — twice by extraction (`glossary.md` § Twice by extraction). | `status.py` imports it and nothing else does; it reads `STORE_STATUS_DIR` from the environment the `Makefile` sets, as every `config.py` does, and asks git where the checkout is, `REPO_ROOT` — never `__file__`. | A word the contract adds to a closed list is one line here, so the count follows the contract without a change of code. | no row — a measurement of the tree that travels with the canon, run by a hand on the host |
| `status.py` | The measurement: the six kinds, the structural rules, `METRICS` naming each metric once, and the snapshot assembled from them (its docstring). | It imports `config.py` alone, reads the tracked files through git and the review record from the status store, and writes `skills_status.json`; no module imports it. | A function of the tree it reads: the same commit measures to the same bytes on any host. | no row — a measurement of the tree that travels with the canon, run by a hand on the host |
| `crawl.py` | The pass (its docstring): the queue, the worktree, the attempts, the three conditions an amendment is kept by, and the one writer of the review record. | It imports `config.py` and `status.py` — the queue and the ratchet are the measurement's own functions — and runs git and the agent's command line over `subprocess`; no module imports it. | It writes only branch `scalability-crawler` and a worktree beside the checkout, so the checkout stays as its owner left it on whatever host runs the pass. | no row — a measurement of the tree that travels with the canon, run by a hand on the host |
| `crawl_brief_template.md` | The brief every batch sends the reviewer, its placeholders filled by `crawl.py`: what to read, what to judge and amend, and the form of the answer. | Beside `crawl.py`, its one reader; it cites `AGENTS.md` and the skills and restates neither (`glossary.md` § Documentation ownership, the brief excepted). | The same brief reaches whichever reviewer the command line names. | no row — a measurement of the tree that travels with the canon, run by a hand on the host |
| `store/status/skills_status.json` + `store/status/skills_review.json` | The snapshot `status.py` writes and the review record `crawl.py` writes — status objects beside the computational snapshots, tracked like them. | In the status store, outside this sub-module and every module (`AGENTS.md` § Pre-AWS architectural direction, *Storage is separate from compute*); the route `/store_status/<name>` serves them as it serves every snapshot. | Their paths are `STORE_STATUS_DIR / <name>` in `config.py`, under whatever disk is mounted for the store. | STORAGE — status, run and trial objects |
