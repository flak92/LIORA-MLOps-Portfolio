# Skill: dashboard conventions

The dashboard is a static dial-up-minimal page; keep it one.

- Plain HTML + CSS + JS only — no frameworks, no build step, no external
  resources (fonts, CDNs, trackers). Everything ships in `dashboard/`.
- Served on **loopback only** (`127.0.0.1`); remote viewing goes through an
  SSH tunnel, never a bind to a public interface.
- CSS classes follow **BEM**: `block__element`, `block--modifier`;
  single-class utility blocks stay single-class.
- Magnitudes are shown as **bars, not colors**; color marks category, bold
  marks the final-OOS row. Sparklines are inline SVG with a dashed reference.
- The page reads two committed snapshots (`status.json`, `ml_status.json`)
  and renders everything client-side; the payload carries only fields the
  page actually reads.
- Verify rendering headless: serve on loopback, `chromium --headless
  --dump-dom`, assert no `undefined`/`NaN` and the expected frames.
