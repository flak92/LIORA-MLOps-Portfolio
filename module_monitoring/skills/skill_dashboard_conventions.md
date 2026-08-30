# Skill: dashboard conventions

The dashboard is a static dial-up-minimal page; keep it one. *The repository shows the destination, not the road*: no
linter, no build step, no framework.

- Plain HTML + CSS + JS only — no frameworks, no build step, no external
  resources (fonts, CDNs, trackers). Everything ships in `module_monitoring/`.
- **The desktop viewport is the only target.**
- Reachable on **loopback only** (`127.0.0.1`): the server binds `0.0.0.0`
  inside its container's own namespace and compose publishes the dashboard on
  `127.0.0.1:${PORT}` alone; the asset containers publish no port and are
  reached only through the dashboard's proxy. Remote viewing goes through an
  SSH tunnel, never a bind to a public interface of the host.
- JavaScript follows native **lowerCamelCase**; file-scope functions take their
  verb from the closed list in the JavaScript row of the AGENTS.md grammar table
  (`build`, `render`, `format`, `append`, `select`, `init`, `fetch`); a domain
  object (an asset, a payload, a strategy block) is never a one-letter alias,
  while equation and geometry locals may stay short inside one tight kernel;
  booleans answer a question. A table builds its header beside its rows, in the
  render function that emits the cells (`appendHeaderRow`, `renderTable`) —
  `index.html` carries an empty `<thead>`, so adding a column is one edit in
  one file.
- CSS classes follow **BEM**: `block__element`, `block--modifier`;
  single-class utility blocks stay single-class.
- Magnitudes are shown as **bars, not colours**; colour marks category, bold
  marks the final-holdout row. Sparklines are inline SVG with a dashed reference.
- The page reads two committed snapshots (`data_status.json`, `ml_status.json`)
  into `DATA_STATUS` and `ML_STATUS` and renders everything client-side; the
  payload carries only fields the page reads. The Containers tab reads the live
  endpoints through the dashboard's proxy into `CONTAINER_REGISTRY` and
  `CONTAINER_STATUS`, and the Lifecycle tab reads the newest recorded run through
  `GET /runs` and `GET /runs/<run_id>` into `RUN_RECORD` — five state globals; the pill-hook registry `PILL_HOOKS`,
  the load promise `DATA_STATUS_LOADED` and the poll latch
  `CONTAINER_POLL_IN_FLIGHT` are not state. The tab's behaviour is `../../module_skills/skill_asset_containers.md` § The tab.
- The page computes no domain or model results — only presentation arithmetic
  over already measured values (shares, a cross-fold mean, a difference of two
  reported metrics, a CPU rate from two polls of `cpu_usage_seconds`). Moving
  those into the payload would grow it without adding a fact.
- The status page carries exactly one jump out of itself: the **DX** control in the top right,
  which opens the developer-experience drawing of the tracked tree at
  `sub_module_dx/files_and_folders_visualisation.html`. That page is a derived artifact, redrawn
  only by `make monitoring-dx-update`; the dashboard already serves the directory, so the server's
  routes do not know about it. Its inline renderer is reviewed as a whole and is not bound by the
  closed verb list above, which governs the hand-written dashboard scripts.
  `skill_developer_experience_drawing.md` holds the rest: the configuration surface, the provenance
  stamp and the determinism the page owes.

