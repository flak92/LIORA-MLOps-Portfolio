# Skill: dashboard conventions

The dashboard is a static dial-up-minimal page; keep it one. *The repository shows the destination, not the road*: no
linter, no build step, no framework.

- Plain HTML + CSS + JS only — no frameworks, no build step, no external
  resources (fonts, CDNs, trackers). Everything ships in `module_monitoring/`.
- **The toolkit is one file, the sections are their own.** `page.js` holds what
  every page shares — the one parser of a payload's UTC text, formatters, cells,
  tables, frames and pills — and writes
  into no page-specific element, so a second
  page loads it without inheriting the first page's markup. `data.js`, `ml.js`,
  `asset.js`, `features.js`, `run.js` and `scalability.js` render the status page's sections.
- **The desktop viewport is the only target.**
- Reachable on **loopback only** (`127.0.0.1`): the server binds `0.0.0.0`
  inside its container's own namespace and compose publishes the dashboard on
  `127.0.0.1:${PORT}` alone. Remote viewing goes through an
  SSH tunnel, never a bind to a public interface of the host.
- JavaScript follows native **lowerCamelCase**; file-scope functions take their
  verb from the closed list in the JavaScript row of the AGENTS.md grammar table
  (`build`, `render`, `format`, `append`, `select`, `init`, `fetch`); a domain
  object (an asset, a payload, a strategy block) is never a one-letter alias,
  while equation and geometry locals may stay short inside one tight kernel;
  booleans answer a question. A table builds its header beside its rows, in the
  render function that emits the cells (`appendHeaderRow`, `renderTable`) —
  `index.html` carries an empty `<thead>` for a table it knows the number of, so
  adding a column is one edit in one file. A section with as many tables as the
  payload has members builds them with `buildTable`, which makes its own `<thead>`,
  and `index.html` carries the host element instead (the bullet below).
- CSS classes follow **BEM**: `block__element`, `block--modifier`;
  single-class utility blocks stay single-class.
- Magnitudes are shown as **bars, not colours**; colour marks category, bold
  marks the final-holdout row. Sparklines are inline SVG with a dashed reference.
  One category is marked that way on the data views: `invariant`,
  on the cells of a column whose only correct value is zero
  (`module_data/skills/skill_candle_canonicalisation.md` § 16),
  so a reader can tell the numbers he may be alarmed by from the ones a change of data
  provider is expected to move. Such columns are named by their header in the render
  function, never counted by position.
- **A section with as many parts as the payload has members builds them, and names
  none.** The data views take the provider set from the snapshot's `source_venues` and
  build one frame, one column and one share cell per entry, the way the ML assets panel
  builds one frame per asset; `index.html` carries the host element, not the parts. A
  provider added to the pipeline therefore changes no file of this module.
- The page reads four committed snapshots (`data_status.json`, `features_status.json`,
  `ml_status.json`, `skills_status.json`) and renders everything client-side —
  `data.js` the data snapshot as it arrives, the other three held in
  `FEATURES_STATUS`, `ML_STATUS` and `SKILLS_STATUS`; a snapshot carries what its module measured, and the page
  renders what it reads — a key the page does not read stays the module's own. The Lifecycle tab reads the newest recorded run
  through `run_records/index.json` and the records it lists, and renders it as it arrives — three state globals in all;
  the pill-hook registry `PILL_HOOKS` is not state. Every file the page reads it names by a relative path, `status/` or
  `run_records/`, beside its own files.
- The page computes no domain or model results — only presentation arithmetic
  over already measured values (shares, a cross-fold mean, a difference of two
  reported metrics, a report's age against the clock). Moving
  those into the payload would grow it without adding a fact.

## Extending

- **A tab** is one `<button class="pill" data-key="<key>">` in `#tabs`, one
  `<section id="tab-<key>" data-panel="tab" data-key="<key>" hidden>`, and one section
  script in the list at the end of `index.html` — `initPills` in `page.js` wires them by
  `data-key`; then its row in `README_module_monitoring.md` § Design rationale, and the
  enumerations that name the tabs move in the same commit: `README.md` § Quickstart and
  § Dashboard, and `module_skills/glossary.md` § The page. A section that fetches a
  new object adds a state global, and the sentence above that counts them moves with it.
- **A file the page reads** is named by its path under `status/` or `run_records/` and needs no edit of the
  server, which serves those two prefixes and the page's own files and nothing else; a third store is one entry of
  `STORE_DIR_BY_ROUTE_PREFIX` in `config.py` and its read-only mount on the `dashboard` service, and the places that
  list the prefixes move in the same commit — `serve.py`'s docstring, `README_module_monitoring.md` § Design
  rationale, `module_skills/skill_pre_aws_solution.md` § The mapping table. Every key a new file carries enters
  `module_skills/glossary.md`.
- **A column or a cell** is one edit in the render function that emits the row, because the
  header is built beside the rows.

