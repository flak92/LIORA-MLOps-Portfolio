/* ML Assets tab: the per-asset panel. Classic script — uses the helpers from
   app.js (cell, bar, fmt, num) and the table builders from ml.js (makeTable,
   shareCell, meanOf, valSplits, CLASS_NAMES, ML_STATUS). */
"use strict";

function frameEl(title) {
  const f = document.createElement("div");
  f.className = "frame";
  const h = document.createElement("div");
  h.className = "frame-head";
  h.textContent = title;
  const b = document.createElement("div");
  b.className = "frame-body";
  f.append(h, b);
  return { frame: f, body: b };
}

function kvBox(pairs) {
  const d = document.createElement("div");
  d.className = "box";
  d.textContent = pairs.map((kv) => (kv[0] + ":").padEnd(26) + kv[1]).join("\n");
  return d;
}

function subhead(text) {
  const p = document.createElement("p");
  p.className = "subhead";
  p.textContent = text;
  return p;
}

/* single-series line with a dashed reference level; no legend needed, the
   frame title names the series. Native <title> carries the hover summary. */
function sparkline(values, baseline, markIndex, caption) {
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
  base.setAttribute("class", "spark-base");
  const line = document.createElementNS(NS, "polyline");
  line.setAttribute("class", "spark-line");
  line.setAttribute("points", values.map((v, i) => x(i).toFixed(1) + "," + y(v).toFixed(1)).join(" "));
  svg.append(tip, base, line);

  if (markIndex !== null && markIndex !== undefined) {
    const mark = document.createElementNS(NS, "line");
    mark.setAttribute("x1", x(markIndex));
    mark.setAttribute("x2", x(markIndex));
    mark.setAttribute("y1", 0);
    mark.setAttribute("y2", H);
    mark.setAttribute("class", "spark-mark");
    svg.appendChild(mark);
  }
  return svg;
}

function foot(text) {
  const p = document.createElement("p");
  p.className = "foot";
  p.textContent = text;
  return p;
}

function sampleFrame(a) {
  const f = frameEl("1. sample contract");
  const c = a.sample.class_counts;
  const total = c.short + c.neutral + c.long;
  f.body.appendChild(kvBox([
    ["decision rows", fmt(a.sample.rows)],
    ["warm-up excluded", fmt(a.sample.n_warmup_excluded) + " decisions before the first usable 4H bar"],
    ["masked", fmt(a.sample.masked) + " (" + a.sample.masked_pct.toFixed(4) + "%)"],
    ["ambiguous", fmt(a.sample.ambiguous) + " (both barriers in one minute)"],
    ["mean uniqueness weight", a.sample.uniqueness_weight_mean.toFixed(4)],
  ]));
  f.body.appendChild(makeTable(["class", "count", "share"], CLASS_NAMES.map((n) => [
    n, fmt(c[n]), [shareCell(c[n], total)],
  ])));
  return f.frame;
}

function segmentsFrame(a, s) {
  const f = frameEl("2. splits and segments");
  const bounds = s.folds.bounds_utc;
  const rows = Object.keys(a.segments).sort().map((k) => {
    const split = parseInt(k.split("_")[1], 10);
    const g = a.segments[k];
    const isTest = split === s.folds.test;
    const label = document.createElement("span");
    label.textContent = "F" + split + (isTest ? " (locked test)" : "");
    if (isTest) label.className = "diag";
    return [
      [label],
      "[" + bounds[split - 1] + " .. " + bounds[split] + ")",
      fmt(g.n_train),
      fmt(g.n_purged),
      fmt(g.n_window),
      fmt(g.n_scored),
      [shareCell(g.n_scored, g.n_window)],
    ];
  });
  f.body.appendChild(makeTable(
    ["fold", "window (UTC)", "train rows", "purged", "window rows", "scored", "scored share"], rows));
  f.body.appendChild(foot("purge drops training events that had not finished when the "
    + "out-of-sample block opened; scored rows exclude label-invalid decisions."));
  return f.frame;
}

function hpoFrame(a) {
  const f = frameEl("3. hyper-parameter search");
  const p = a.hpo.best_params;
  f.body.appendChild(kvBox([
    ["trials (TPE, sequential)", a.hpo.n_trials],
    ["best objective", a.hpo.best_logloss.toFixed(6) + "  (mean weighted OOS log-loss)"],
    ["max_depth / eta", p.max_depth + " / " + p.eta.toFixed(5)],
    ["min_child_weight", p.min_child_weight],
    ["subsample / colsample", p.subsample.toFixed(3) + " / " + p.colsample_bytree.toFixed(3)],
    ["lambda / alpha", p.lambda.toFixed(3) + " / " + p.alpha.toFixed(3)],
    ["boosting rounds", p.num_boost_round],
  ]));
  return f.frame;
}


function validationFrame(a) {
  const f = frameEl("4. validation (out-of-sample, threshold selection)");
  f.body.appendChild(makeTable(
    ["fold", "prior log-loss", "model log-loss", "skill", "MCC", "scored rows"],
    valSplits(a).map((k) => {
      const m = a.validation[k];
      return [
        "F" + k.split("_")[1],
        m.prior_logloss.toFixed(6),
        m.model_logloss.toFixed(6),
        (100 * m.skill).toFixed(2) + "%",
        m.mcc.toFixed(4),
        fmt(m.n),
      ];
    })));
  f.body.appendChild(foot("skill = 1 - model / prior: the information the model adds "
    + "beyond knowing how often each class occurs. The prior comes from the training rows."));
  return f.frame;
}


function renderConfusion(cm) {
  const colSum = (j) => cm.reduce((acc, r) => acc + r[j], 0) || 1;
  const rows = cm.map((row, i) => {
    const tot = row.reduce((x, y) => x + y, 0) || 1;
    const cells = row.map((v, j) => {
      const wrap = document.createElement("span");
      const track = bar((100 * v) / tot);
      track.className = "bar-track mini";
      wrap.appendChild(track);
      wrap.appendChild(document.createTextNode(fmt(v)));
      if (i === j) wrap.className = "diag";
      return [wrap];
    });
    return [CLASS_NAMES[i], ...cells, ((100 * row[i]) / tot).toFixed(1) + "%"];
  });
  rows.push(["precision", ...[0, 1, 2].map((j) => ((100 * cm[j][j]) / colSum(j)).toFixed(1) + "%"), ""]);
  return makeTable(["true \\ predicted", "short", "neutral", "long", "recall"], rows);
}

function testFrame(a) {
  const meanSkill = meanOf(valSplits(a).map((k) => a.validation[k].skill));
  const f = frameEl("5. final out-of-sample fold");
  f.body.appendChild(kvBox([
    ["scored rows", fmt(a.test.n)],
    ["prior log-loss", a.test.prior_logloss.toFixed(6)],
    ["model log-loss", a.test.model_logloss.toFixed(6)],
    ["skill", (100 * a.test.skill).toFixed(2) + "%"],
    ["mean validation skill", (100 * meanSkill).toFixed(2) + "%"],
    ["MCC", a.test.mcc.toFixed(4)],
  ]));
  f.body.appendChild(subhead("confusion matrix (bar length = share of the true class)"));
  f.body.appendChild(renderConfusion(a.test.confusion));
  return f.frame;
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

function strategyFrame(a, s) {
  const f = frameEl("6. strategy (model picks the side, hierarchy gates it)");
  f.body.appendChild(kvBox([
    ["tau", a.strategy.tau.toFixed(2) + (a.strategy.tau_constraint_met ? "" : "  (fallback)")],
    ["selection score", num(a.strategy.selection_score_mean_sharpe, 3) + "  (mean validation Sharpe)"],
    ["cost per side", (100 * a.strategy.costs_per_side).toFixed(2) + "%  (execution-cost-adjusted, excluding funding)"],
    ["gate", "side = sign(trend_4h) and at least " + s.gate_min_agree + " of 3 levels agree"],
  ]));
  const rows = valSplits(a).map((k) => pnlRow("F" + k.split("_")[1], a.strategy.validation[k], false));
  rows.push(pnlRow("F" + s.folds.test + " (locked)", a.strategy.test, true));
  f.body.appendChild(makeTable(
    ["fold", "Sharpe", "maxDD", "trades", "hit rate", "avg trade", "exposure", "final equity"],
    rows));
  f.body.appendChild(subhead("final-OOS exits"));
  const e = a.strategy.test.exit_counts;
  const total = e.upper + e.lower + e.vertical + e.adverse || 1;
  f.body.appendChild(makeTable(["exit", "count", "share"],
    [["upper barrier", fmt(e.upper), [shareCell(e.upper, total)]],
     ["lower barrier", fmt(e.lower), [shareCell(e.lower, total)]],
     ["vertical (timeout)", fmt(e.vertical), [shareCell(e.vertical, total)]],
     ["ambiguous (adverse)", fmt(e.adverse), [shareCell(e.adverse, total)]]]));
  return f.frame;
}

function equityFrame(a) {
  const c = a.strategy.equity_curve;
  const f = frameEl("7. final-OOS equity (fixed quantity, costs included)");
  f.body.appendChild(sparkline(c.equity, 1.0, null,
    "equity on the final OOS fold; dashed line = 1.0 (flat)"));
  const lo = Math.min(...c.equity);
  f.body.appendChild(foot(
    "start " + c.equity[0].toFixed(3)
    + " · min " + lo.toFixed(3)
    + " · final " + c.equity_final.toFixed(3)
    + " · max drawdown " + (100 * a.strategy.test.max_drawdown).toFixed(1) + "%"
    + " · " + c.equity.length + " weekly points from " + fmt(c.n_source) + " daily"
    + " · dashed = 1.0"));
  return f.frame;
}

function importanceFrame(a) {
  const f = frameEl("8. feature attribution (XGBoost total gain)");
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
  [sampleFrame(a), segmentsFrame(a, s), hpoFrame(a), validationFrame(a),
   testFrame(a), strategyFrame(a, s), equityFrame(a), importanceFrame(a)]
    .forEach((el) => host.appendChild(el));
}

function buildAssetPills(s) {
  const group = document.getElementById("asset-pills");
  s.assets.forEach((a, i) => {
    const b = document.createElement("button");
    b.className = "pill" + (i === 0 ? " active" : "");
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
