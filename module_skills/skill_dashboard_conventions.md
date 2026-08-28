# Skill: dashboard conventions

The dashboard is a static dial-up-minimal page; keep it one.

- Plain HTML + CSS + JS only — no frameworks, no build step, no external
  resources (fonts, CDNs, trackers). Everything ships in `module_monitoring/`.
- Reachable on **loopback only** (`127.0.0.1`): `make dashboard` binds it
  directly, and the container binds `0.0.0.0` inside its own namespace while
  compose publishes it on `127.0.0.1` alone. Remote viewing goes through an
  SSH tunnel, never a bind to a public interface of the host.
- JavaScript follows native **lowerCamelCase**; file-scope functions take their
  verb from the closed list in the JavaScript row of the AGENTS.md grammar table
  (`build`, `render`, `format`, `append`, `select`, `init`);
  a domain object (an asset, a payload, a strategy block) is never a
  one-letter alias, while equation and geometry locals may stay short inside
  one tight kernel; booleans answer a question. A table builds its header
  beside its rows, in the render function that emits the cells
  (`appendHeaderRow`, `renderTable`) — `index.html` carries an empty `<thead>`,
  so adding a column is one edit in one file. No linter, bundler or
  framework enforces this — the review does.
- CSS classes follow **BEM**: `block__element`, `block--modifier`;
  single-class utility blocks stay single-class.
- Magnitudes are shown as **bars, not colours**; colour marks category, bold
  marks the final-holdout row. Sparklines are inline SVG with a dashed reference.
- The page reads two committed snapshots (`data_status.json`, `ml_status.json`)
  and renders everything client-side; the payload carries only fields the
  page actually reads.
- The page computes no domain or model results — only presentation arithmetic
  over already measured snapshots (shares, a cross-fold mean, a difference of
  two reported metrics). Moving those into the payload would grow it without
  adding a fact.
- Verify rendering headless: serve on loopback, `chromium --headless
  --dump-dom`, assert no `undefined`/`NaN` and the expected frames.

## The generated page

`module_monitoring/files_and_folders_visualisation.html` is written by `module_visualisation`, not by hand, and the
rules above bind it only where they still mean something.

- It obeys the ones that matter: plain HTML, CSS and JS, no framework, no build step, and **no
  external resource of any kind** — the whole page, including its data, is one file.
- It carries its data inside itself instead of fetching `data_status.json` / `ml_status.json`, because
  its subject is the repository's own tree rather than anything a stage measured. That is the one
  page for which "reads the two committed snapshots" does not apply.
- Colour on that page separates stories; it encodes no magnitude, so "bars, not colours" is not at
  stake. Edge weight carries the only ordinal distinction there is — folder to folder, or folder to
  file — and it is fixed in the renderer, not configurable.
- The closed verb list for file-scope JavaScript binds the hand-written dashboard scripts. The
  page's inline renderer is a generated artifact reviewed as a whole; the `JavaScript verbs`
  check greps `module_monitoring/*.js` and deliberately does not reach it.
- Verify it the same way as the rest: serve on loopback, `chromium --headless --dump-dom`, and
  assert the file tree rendered — an empty `#tree` means the layout threw before the first frame,
  which is the failure this page actually has. Ignore `undefined` inside the `<script>` block; the
  assertion is about rendered content.
