# Skill: self-explaining naming conventions

Every name in this repository — a variable, a parameter, a function, a key, a
directory — must explain itself, so an agent never has to guess.

- **The name carries the information.** What a thing is, what it measures and
  in what unit are readable from the identifier alone, without opening another
  file — and without redundancy: a name repeats nothing its scope already
  states.
- **The measure is thoughts, not tokens.** A name is good when it minimises
  the number of thoughts an agent must think to use it correctly. Every
  obscure identifier forces a chain of decoding steps before the real work
  starts, and those steps are the cost — not the characters saved.
- **Self-explaining names are the interface.** Agents understand and extend
  this repository through its names; a name that needs a lookup turns every
  reader into an archaeologist.
- **Names are derived, not invented — the way BEM derives CSS class names.**
  Every layer has a closed grammar, fixed in `AGENTS.md`: a verb from a closed
  list for functions that act, no verb at all for functions that *are* a
  quantity, `<what>_<unit>` for quantities, `<population>_rows` for index
  arrays, `<kind>_<detail>/` for directories. Given the layer, the name
  follows; there is nothing left to invent, and nothing to argue about.
- **Units belong to quantities.** A name holding a number says its unit —
  counts, rates, durations, sizes, intervals — while enumerations, paths and
  names carry none, a collection keeps the unit of its values, and a local
  abbreviation is free inside one function.
- **The kind comes first, so siblings sort together.** A listing is read by eye
  before it is parsed. The eye takes a pattern for free and the mind enjoys
  finding simple logic inside a complicated subject; a scattered listing
  charges for both, because the reader has to scan and then remember where
  things live. If renaming would place things of one kind next to each other,
  rename them — `module_*` beside `module_*`, `store_*` beside `store_*`.
- **One concept, one name.** A synonym forces the reader to decide whether two
  names are one thing or two — a thought the code should never demand.
- **The glossary confirms, it never decodes.** `glossary.md` registers what a
  name already says; if the register is needed to understand the name, the
  name is wrong.
- **A name gives way to a more derivable one.** The test is not whether the old
  name still works, but whether the family's grammar yields a name that
  classifies better, shows its family sooner or sorts with its siblings — when
  it does, the rename is the cheap part and the reasoning step it removes is
  paid back on every later reading. A serialised name (an artifact key, a
  parquet or database column, a feature) is a contract with the files on disk,
  so it moves only together with everything that writes, reads or stores it, in
  one commit.

## Minting a new convention

The grammars above are not the last ones this repository will need. A new one
is worth establishing when it meets all eight conditions, and it is not a
convention when it misses any:

- **Closed vocabulary.** The allowed words can be listed. `load_`, `write_`,
  `fetch_`, `parse_`, `to_`, `build_` is a list; "use a sensible verb" is not.
- **Derivable.** A reader can construct the correct name without asking anyone
  and without reading a second document.
- **Checkable by grep.** A violation can be found mechanically — `ls -1d */`
  for the sorting rule, a pattern for the verb list. A rule nobody can test is
  a preference.
- **One authority.** The rule lives in exactly one place, `AGENTS.md`, and
  every other document points at it. Two copies of a rule drift, and the drift
  is discovered by the reader who trusted the wrong copy.
- **It must be able to fail.** There is a name the rule forbids. A rule that
  excludes nothing describes taste, not structure.
- **Scope.** A convention states which language, layer and object kind it
  governs; a rule with no stated scope collects exceptions instead of naming
  them.
- **Boundary.** A convention states where an external format overrides it —
  the Lean raw tree keeps Lean's casing and layout, and the adapter speaks the
  external vocabulary. A named exception is a boundary; an unnamed one is rot.
- **Migration cost.** A convention is minted only when the ambiguity it
  removes is worth more than the one-time cost of the renames it forces.

Mint at the **third** occurrence of a pattern: two is a coincidence, three is a
convention. Write it into `AGENTS.md` in the same commit that makes the third
name follow it, and state what it forbids — the forbidden form is the half of
the rule that does the work.

## Neuro-optical consistency

Names are architecture visible to the eye. Top-level persisted state starts
with `store_`; top-level responsibilities start with `module_`; siblings of one
kind keep the kind token in the same position, so they sort into one block.
The same concept keeps the same semantic root across the filesystem, Python,
JSON and the interface, and a top-level path constant mirrors the exact
directory token it names. Internal asset folders are the ticker in capitals;
an external format keeps its required spelling at the adapter boundary.
One-letter names are reserved for loop indices, the symbols of a published
equation inside its own kernel, and tiny geometry callbacks — a domain object
carries its semantic name even inside a function. A name must remove a
reasoning step, not merely satisfy a pattern. The sorting mechanics live in
`skill_sorting_files_naming_standard.md`; the names the project enacted, with
their rejected forms, live in `act_naming_conventions.md`.

## Checks

Every grammar row of `AGENTS.md` has one read-only command, and the command
has an expected answer. Run them before a merge and after any rename; a rule
whose command cannot fail is a preference, so each one names the hit it would
report.

```
kind-first blocks     ls -1d */
                      → module_data module_ml module_monitoring module_skills module_visualisation, then store_assets_artifacts store_db store_raw_1m
collation invariance  for d in module_monitoring module_skills store_assets_artifacts store_db store_raw_1m; do diff <(LC_COLLATE=C ls -1 $d) <(LC_COLLATE=en_US.UTF-8 ls -1 $d); done
                      → empty (the packages are absent from the loop for the same reason the root is:
                        their listings differ only by the ecosystem-fixed names of row 16)
I/O verbs             git grep -nE '^def (get|process|handle|read|probe|spool|iter|make|run)_' -- '*.py'
                      → empty
constructors          git grep -nE '^def make_|_factory\(' -- '*.py'
                      → empty
private helpers       git grep -nE '^from \.[a-z_]* import .*\b_[a-z]|^from module_[a-z]+\.[a-z_]+ import .*\b_[a-z]' -- '*.py'
                      → empty (a `_` name is never imported across modules)
paths at point of use git grep -n '_DIR /' -- '*.py' | grep -v config.py
                      → empty
Lean names            git grep -n 'trade\.zip\|minute_trade_perp' -- '*.py' | grep -v module_data/lean.py
                      → only the tree diagrams in the two downloader docstrings
statement constants   grep -nE '^[A-Z_]+ = ("""|re\.compile)' module_data/*.py module_ml/*.py module_visualisation/*.py | grep -vE '_(DDL|INSERT|SCAN|PREDICATE|PATTERN|COLUMNS) ='
                      → empty
SQL aliases           grep -nE ' AS (n_|div_|chg|prev|ts_|rows)\b' module_data/status.py
                      → empty
positional reads      grep -nE '\br\[[0-9]+\]' module_data/status.py
                      → empty
count keys            git grep -nE '"(rows|gaps|duplicates|ambiguous|unobservable|trainable|n_[a-z]+)":' -- '*.py'
                      → empty
time suffixes         git grep -nE '"[a-z_]+_ts":' -- '*.py' | grep -vE 'decision_ts|entry_ts|event_end_ts'
                      → empty (the three `_ts` columns are the act's schema boundary)
abbreviation ret      git grep -nE '_ret\b|_ret_' -- '*.py' '*.js' '*.md' ':!store_assets_artifacts/*/*'
                      → only the rejected forms recorded in the act and the register
conversion factors    git grep -n '60_000\|86_400_000' -- '*.py' | grep -v 'module_data/config.py\|module_data/lean.py'
                      → empty
JavaScript verbs      grep -hoE '^function [a-zA-Z]+' module_monitoring/*.js | grep -vE 'function (build|render|format|append|select|init)[A-Z]|^function (validationFolds|mean)$'
                      → empty
make targets          grep -oE '^[a-z][a-z0-9-]*:' Makefile | tr -d : | grep -vE '^(help|setup|all|dashboard|docker-build|docker-up|docker-down|(data|ml|visualisation)-[a-z-]+|docker-(data|ml)-[a-z-]+)$'
                      → empty
.PHONY completeness   comm -3 <(grep -oE '^[a-z][a-z0-9-]*:' Makefile | tr -d : | sort -u) <(sed -n '/^\.PHONY:/,/^$/p' Makefile | tr ' \\' '\n' | grep -v PHONY | grep . | sort -u)
                      → empty
port                  git grep -n 8900 -- Makefile docker-compose.yml
                      → Makefile's `PORT ?=` and the two `${PORT:-8900}` defaults of compose, nothing else
boundaries            the pre-sweep grep of the act, § External vocabularies
                      → hits only inside the owning files listed there
register              python3 -c "import json;g=open('module_skills/glossary.md').read();s=json.load(open('module_monitoring/data_status.json'));m=json.load(open('module_monitoring/ml_status.json'));a=m['assets'][0];k=set(s)|set(s['flow'])|{x for r in s['symbols']+s['canonical_source']+s['venues']['binance'] for x in r}|set(m)|set(m['research_window'])|set(a)|set(a['sample'])|set(a['strategy'])|set(a['strategy']['final_holdout'])|set(a['final_holdout'])|set(a['hyperparameter_search_result']);print(sorted(x for x in k if '\x60'+x+'\x60' not in g))"
                      → [] (every published key is in the register)
```
