/* ML Assets tab: the per-asset panel. Classic script — uses the helpers from
   app.js (bar, fmt, num) and the table builders from ml.js (makeTable,
   shareCell, valSplits, CLASS_NAMES, ML_STATUS). */
"use strict";

function frameEl(title) {
  const f = document.createElement("div");
  f.className = "frame";
  const h = document.createElement("div");
  h.className = "frame__head";
  h.textContent = title;
  const b = document.createElement("div");
  b.className = "frame__body";
  f.append(h, b);
  return { frame: f, body: b };
}

function kvBox(pairs) {
  const d = document.createElement("div");
  d.className = "box";
  d.textContent = pairs.map((kv) => (kv[0] + ":").padEnd(26) + kv[1]).join("\n");
  return d;
}

/* single-series line with a dashed reference level; no legend needed, the
   frame title names the series. Native <title> carries the hover summary. */
function sparkline(values, baseline, caption) {
  const NS = "http://www.w3.org/2000/svg";
  const W = 700;
  const H = 120;
  const lo = Math.min(baseline, ...values);
  const hi = Math.max(baseline, ...values);
  const span = hi - lo || 1;
  const x = (i) => (W * i) / Math.max(1, values.length - 1);
  const y = (v) => H - ((v - lo) / span) * H;

  const svg = document.createElementNS(NS, "svg");
  svg.setAttribute("viewBox", "0 0 " + W + " " + H);
  svg.setAttribute("preserveAspectRatio", "none");
  svg.setAttribute("class", "spark");
  const tip = document.createElementNS(NS, "title");
  tip.textContent = caption;
  const base = document.createElementNS(NS, "line");
  base.setAttribute("x1", 0);
  base.setAttribute("x2", W);
  base.setAttribute("y1", y(baseline));
  base.setAttribute("y2", y(baseline));
  base.setAttribute("class", "spark__base");
  const line = document.createElementNS(NS, "polyline");
  line.setAttribute("class", "spark__line");
  line.setAttribute("points", values.map((v, i) => x(i).toFixed(1) + "," + y(v).toFixed(1)).join(" "));
  svg.append(tip, base, line);
  return svg;
}

function foot(text) {
  const p = document.createElement("p");
  p.className = "foot";
  p.textContent = text;
  return p;
}

function headerLine(a, s) {
  const d = document.createElement("p");
  d.className = "sub";
  d.textContent = a.ticker + " · " + s.research_window[0].slice(0, 7) + " → "
    + s.research_window[1].slice(0, 7) + " · " + fmt(a.sample.rows) + " decisions";
  return d;
}

function labelFrame(a) {
  const f = frameEl("LABEL — triple barrier on the canonical 1m path");
  const c = a.sample.class_counts;
  const total = c.short + c.neutral + c.long;
  f.body.appendChild(makeTable(["class", "count", "share"], CLASS_NAMES.map((n) => [
    n, fmt(c[n]), [shareCell(c[n], total)],
  ])));
  f.body.appendChild(kvBox([
    ["ambiguous labels", fmt(a.sample.ambiguous) + " (" + a.sample.ambiguous_pct.toFixed(3) + "%)"],
    ["warm-up excluded", fmt(a.sample.n_warmup_excluded) + " decisions"],
    ["mean uniqueness weight", a.sample.uniqueness_weight_mean.toFixed(4)],
  ]));
  return f.frame;
}

function modelFrame(a, s) {
  const f = frameEl("MODEL — skill against the training class prior");
  const p = a.hpo.best_params;
  f.body.appendChild(kvBox([
    ["parameters", "depth " + p.max_depth + " · eta " + p.eta.toFixed(4)
      + " · rounds " + p.num_boost_round + " · subsample " + p.subsample.toFixed(2)],
    ["search", a.hpo.n_trials + " Optuna trials · best mean F2-F4 log-loss "
      + a.hpo.best_logloss.toFixed(6)],
  ]));
  const rows = valSplits(a).map((k) => ["F" + k.split("_")[1], a.validation[k]]);
  rows.push(["F" + s.test_fold + " (final OOS)", a.test]);
  f.body.appendChild(makeTable(
    ["fold", "prior log-loss", "model log-loss", "skill", "MCC", "scored rows"],
    rows.map(([label, m], i) => {
      const name = document.createElement("span");
      name.textContent = label;
      if (i === rows.length - 1) name.className = "diag";
      return [[name], m.prior_logloss.toFixed(6), m.model_logloss.toFixed(6),
              (100 * m.skill).toFixed(2) + "%", m.mcc.toFixed(4), fmt(m.n)];
    })));
  f.body.appendChild(foot("skill = 1 − model / prior: what the model adds beyond knowing "
    + "how often each class occurs. The prior comes from the training rows of that fold."));
  return f.frame;
}

function strategyFrame(a, s) {
  const f = frameEl("STRATEGY — model picks the side, the hierarchy gates it");
  f.body.appendChild(kvBox([
    ["tau", a.strategy.tau.toFixed(2) + (a.strategy.tau_constraint_met ? "" : "  (fallback)")],
    ["gate", "side = sign(trend_4h) and at least " + s.gate_min_agree + " of 3 levels agree"],
    ["cost per side", (100 * a.strategy.costs_per_side).toFixed(2)
      + "%  (execution-cost-adjusted, excluding funding)"],
  ]));
  const rows = valSplits(a).map((k) => pnlRow("F" + k.split("_")[1], a.strategy.validation[k], false));
  rows.push(pnlRow("F" + s.test_fold + " (final OOS)", a.strategy.test, true));
  f.body.appendChild(makeTable(
    ["fold", "Sharpe", "maxDD", "trades", "hit rate", "avg trade", "exposure", "final equity"],
    rows));
  const c = a.strategy.equity_curve;
  f.body.appendChild(sparkline(c.equity, 1.0,
    "equity on the final OOS fold; dashed line = 1.0 (flat)"));
  f.body.appendChild(foot("final OOS equity: start 1.000 · low "
    + Math.min(...c.equity).toFixed(3) + " · end " + c.equity_final.toFixed(3)
    + " · dashed line = 1.0. Sharpe is annualised from the 15m equity series, "
    + "the drawdown is measured on the 1m path."));
  return f.frame;
}

function featuresFrame(a) {
  const f = frameEl("FEATURES — XGBoost total gain");
  const items = Object.entries(a.gain_importance).sort((x, y) => y[1] - x[1]);
  const max = items[0][1] || 1;
  f.body.appendChild(makeTable(["feature", "total gain"], items.map((kv) => {
    const wrap = document.createElement("span");
    wrap.appendChild(bar((100 * kv[1]) / max));
    wrap.appendChild(document.createTextNode(fmt(Math.round(kv[1]))));
    return [kv[0], [wrap]];
  })));
  return f.frame;
}

function renderAsset(ticker) {
  const s = ML_STATUS;
  const host = document.getElementById("asset-detail");
  if (!s || !host) return;
  const a = s.assets.find((x) => x.ticker === ticker);
  if (!a) return;
  host.textContent = "";
  host.appendChild(headerLine(a, s));
  [labelFrame(a), modelFrame(a, s), strategyFrame(a, s), featuresFrame(a)]
    .forEach((el) => host.appendChild(el));
}

function pnlRow(label, m, isTest) {
  const name = document.createElement("span");
  name.textContent = label;
  if (isTest) name.className = "diag";
  return [
    [name],
    num(m.sharpe, 2),
    (100 * m.max_drawdown).toFixed(1) + "%",
    fmt(m.n_trades),
    (100 * m.hit_rate).toFixed(1) + "%",
    m.avg_trade_ret === null ? "-" : (100 * m.avg_trade_ret).toFixed(3) + "%",
    (100 * m.exposure).toFixed(2) + "%",
    num(m.final_equity, 4),
  ];
}

function buildAssetPills(s) {
  const group = document.getElementById("asset-pills");
  s.assets.forEach((a, i) => {
    const b = document.createElement("button");
    b.className = "pill" + (i === 0 ? " pill--active" : "");
    b.dataset.key = a.ticker;
    b.textContent = a.ticker;
    group.appendChild(b);
  });
  PILL_HOOKS.asset = renderAsset;
  initPills(document);                 /* no-op: the group was bound while empty */
  /* pills arrive after load, so select here; #TICKER deep-links one asset */
  const wanted = decodeURIComponent(location.hash.slice(1)).toUpperCase();
  const start = group.querySelector("button[data-key='" + wanted + "']")
    || group.querySelector("button");
  if (start) start.click();
}
