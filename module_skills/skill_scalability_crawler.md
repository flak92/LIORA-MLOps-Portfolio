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

## The review record

`store/status/skills_review.json` holds one row per reviewed file — its `path`,
the `blob_id` it reviewed, the `canon_id` it was reviewed under, its `verdict`,
its `self_explaining_level` with the line that earns it as `evidence`, and its
`findings` — and the `proposals` a review wrote. `status.py` reads it and never
writes it. A row counts while its file is still the blob the row names, and is
stale while the canon's content is not the `canon_id` the row names; the canon
is `CANON_PATHSPECS` — `AGENTS.md`, `module_skills/*.md` and
`module_*/skills/*.md`.

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
| `store/status/skills_status.json` + `store/status/skills_review.json` | The snapshot `status.py` writes and the review record it reads — status objects beside the computational snapshots, tracked like them. | In the status store, outside this sub-module and every module (`AGENTS.md` § Pre-AWS architectural direction, *Storage is separate from compute*); the route `/store_status/<name>` serves them as it serves every snapshot. | Their paths are `STORE_STATUS_DIR / <name>` in `config.py`, under whatever disk is mounted for the store. | STORAGE — status, run and trial objects |
