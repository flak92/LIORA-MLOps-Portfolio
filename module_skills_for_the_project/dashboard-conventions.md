# Skill: dashboard conventions

The dashboard is a static dial-up-minimal page; keep it one.

- Plain HTML + CSS + JS only — no frameworks, no build step, no external
  resources (fonts, CDNs, trackers). Everything ships in `module_monitoring/`.
- Reachable on **loopback only** (`127.0.0.1`): `make dashboard` binds it
  directly, and the container binds `0.0.0.0` inside its own namespace while
  compose publishes it on `127.0.0.1` alone. Remote viewing goes through an
  SSH tunnel, never a bind to a public interface of the host.
- CSS classes follow **BEM**: `block__element`, `block--modifier`;
  single-class utility blocks stay single-class.
- Magnitudes are shown as **bars, not colours**; colour marks category, bold
  marks the final-holdout row. Sparklines are inline SVG with a dashed reference.
- The page reads two committed snapshots (`status.json`, `ml_status.json`)
  and renders everything client-side; the payload carries only fields the
  page actually reads.
- The page computes no domain or model results — only presentation arithmetic
  over already measured snapshots (shares, a cross-fold mean, a difference of
  two reported metrics). Moving those into the payload would grow it without
  adding a fact.
- Verify rendering headless: serve on loopback, `chromium --headless
  --dump-dom`, assert no `undefined`/`NaN` and the expected frames.
