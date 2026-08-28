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
- **Rename only what impedes reading.** A working, honest name stays; churn is
  its own cost — and a serialised name (an artifact key, a parquet or database
  column, a feature) is not a name any more, it is a contract with the files on
  disk. Those change only when the data does.

## Minting a new convention

The grammars above are not the last ones this repository will need. A new one
is worth establishing when it meets all five conditions, and it is not a
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
