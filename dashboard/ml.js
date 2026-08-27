/* ML Research and ML Assets tabs: one fetch of ml_status.json feeds the
   cross-section table, the four summary views and the per-asset panel.
   Classic script — shares the helpers (cell, bar, pctCell, fmt, num,
   initPills, PILL_HOOKS) defined in app.js. */
"use strict";

const ML_SCHEMA = 2;
const CLASS_NAMES = ["short", "neutral", "long"];
let ML_STATUS = null;

function headerRow(table, labels) {
  const tr = table.querySelector("thead").insertRow();
  labels.forEach((h) => {
    const th = document.createElement("th");
    th.innerHTML = h;
    tr.appendChild(th);
  });
}

function addRows(table, rows) {
  const tbody = table.querySelector("tbody") || table.createTBody();
  rows.forEach((cells) => {
    const tr = tbody.insertRow();
    cells.forEach((c) => (Array.isArray(c) ? cell(tr, c[0], c[1]) : cell(tr, c)));
  });
}

function fillTable(id, headers, rows) {
  const table = document.getElementById(id);
  headerRow(table, headers);
  addRows(table, rows);
}

function makeTable(headers, rows) {
  const table = document.createElement("table");
  table.createTHead();
  headerRow(table, headers);
  addRows(table, rows);
  return table;
}

function shareCell(part, whole) {
  const pctValue = whole ? (100 * part) / whole : 0;
  const wrap = document.createElement("span");
  wrap.appendChild(bar(pctValue));
  wrap.appendChild(document.createTextNode(fmt(part) + " (" + pctValue.toFixed(1) + "%)"));
  return wrap;
}

function meanOf(values) {
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function valSplits(a) {
  return Object.keys(a.validation).sort();
}

/* ---- ML Research tab: the wide cross-section table (unchanged output) ---- */

function renderResearch(s) {
  const table = document.getElementById("ml-assets");
  const tbody = table.querySelector("tbody");
  for (const a of s.assets) {
    const st = a.strategy.test;
    const warn = a.warnings.test_logloss_above_uniform || a.warnings.too_few_trades;
    const tr = tbody.insertRow();
    cell(tr, a.ticker, warn);
    cell(tr, fmt(a.sample.rows));
    cell(tr, a.sample.masked_pct.toFixed(3) + "%");
    cell(tr, fmt(a.sample.class_counts.short) + "/" + fmt(a.sample.class_counts.neutral) +
             "/" + fmt(a.sample.class_counts.long));
    cell(tr, a.hpo.best_params.max_depth + " / " + a.hpo.best_params.eta.toFixed(3) +
             " / " + a.hpo.best_params.num_boost_round);
    cell(tr, a.hpo.best_logloss.toFixed(4));
    cell(tr, a.test.logloss.toFixed(4), a.warnings.test_logloss_above_uniform);
    cell(tr, a.test.balanced_accuracy.toFixed(3));
    cell(tr, a.test.mcc.toFixed(3));
    cell(tr, a.strategy.tau.toFixed(2) + (a.strategy.tau_constraint_met ? "" : " !"),
         a.warnings.tau_fallback);
    cell(tr, num(st.sharpe, 2));
    cell(tr, (100 * st.max_drawdown).toFixed(1) + "%");
    cell(tr, fmt(st.n_trades), a.warnings.too_few_trades);
    cell(tr, (100 * st.hit_rate).toFixed(1) + "%");
    cell(tr, (100 * st.exposure).toFixed(1) + "%");
  }
  table.hidden = false;
}

/* ---- ML Assets tab: four complementary cross-section views ---- */

function viewLabels(s) {
  fillTable("cs-labels",
    ["asset", "rows", "warm-up excl", "masked", "ambiguous", "short", "neutral share",
     "long", "uniq. weight", "scored (test)"],
    s.assets.map((a) => {
      const c = a.sample.class_counts;
      const total = c.short + c.neutral + c.long;
      return [
        [tickerLink(a.ticker)],
        fmt(a.sample.rows),
        fmt(a.sample.n_warmup_excluded),
        [fmt(a.sample.masked) + " (" + a.sample.masked_pct.toFixed(3) + "%)",
         a.sample.masked_pct > 0.1],
        fmt(a.sample.ambiguous),
        fmt(c.short),
        [shareCell(c.neutral, total)],
        fmt(c.long),
        a.sample.uniqueness_weight_mean.toFixed(4),
        fmt(a.segments["split_" + s.config.test_split].n_scored),
      ];
    }));
}

function viewClassification(s) {
  const ln3 = s.baseline_logloss_uniform;
  fillTable("cs-classification",
    ["asset", "val LL F2", "F3", "F4", "mean val LL", "test LL", "&Delta; vs ln 3",
     "gap (test&minus;val)", "bAcc", "MCC"],
    s.assets.map((a) => {
      const splits = valSplits(a);
      const vals = splits.map((k) => a.validation[k].logloss);
      const mean = meanOf(vals);
      const gap = a.test.logloss - mean;
      return [
        [tickerLink(a.ticker)],
        ...vals.map((v) => [v.toFixed(4), v >= ln3]),
        mean.toFixed(4),
        [a.test.logloss.toFixed(4), a.warnings.test_logloss_above_uniform],
        (a.test.logloss - ln3).toFixed(4),
        (gap >= 0 ? "+" : "") + gap.toFixed(4),
        a.test.balanced_accuracy.toFixed(3),
        a.test.mcc.toFixed(3),
      ];
    }));
}

function viewStrategy(s) {
  fillTable("cs-strategy",
    ["asset", "&tau;", "&tau; met", "selection score", "test Sharpe", "degradation",
     "maxDD", "trades", "hit", "avg trade", "exposure", "turnover", "gate share",
     "exits U/L/V/A"],
    s.assets.map((a) => {
      const st = a.strategy.test;
      const sel = a.strategy.selection_score_mean_sharpe;
      const deg = st.sharpe === null || sel === null ? null : st.sharpe - sel;
      const e = st.exit_counts;
      return [
        [tickerLink(a.ticker)],
        a.strategy.tau.toFixed(2),
        [a.strategy.tau_constraint_met ? "yes" : "fallback", a.warnings.tau_fallback],
        num(sel, 2),
        num(st.sharpe, 2),
        deg === null ? "-" : (deg >= 0 ? "+" : "") + deg.toFixed(2),
        (100 * st.max_drawdown).toFixed(1) + "%",
        [fmt(st.n_trades), a.warnings.too_few_trades],
        (100 * st.hit_rate).toFixed(1) + "%",
        (100 * st.avg_trade_ret).toFixed(3) + "%",
        (100 * st.exposure).toFixed(1) + "%",
        (100 * st.turnover).toFixed(2) + "%",
        (100 * st.gate_share).toFixed(2) + "%",
        e.upper + "/" + e.lower + "/" + e.vertical + "/" + e.adverse,
      ];
    }));
}

function viewSearch(s) {
  fillTable("cs-search",
    ["asset", "trials", "best #", "best LL", "trial min/med/max", "depth", "eta",
     "min child", "subsample", "colsample", "lambda", "alpha", "rounds",
     "sha hpo/metrics/strategy"],
    s.assets.map((a) => {
      const v = a.hpo.trial_values.slice().sort((x, y) => x - y);
      const med = v[Math.floor(v.length / 2)];
      const p = a.hpo.best_params;
      const sha = a.artifact_sha256;
      return [
        [tickerLink(a.ticker)],
        a.hpo.n_trials,
        "#" + a.hpo.best_trial,
        a.hpo.best_logloss.toFixed(4),
        v[0].toFixed(3) + " / " + med.toFixed(3) + " / " + v[v.length - 1].toFixed(3),
        p.max_depth,
        p.eta.toFixed(4),
        p.min_child_weight,
        p.subsample.toFixed(3),
        p.colsample_bytree.toFixed(3),
        p.lambda.toFixed(3),
        p.alpha.toFixed(3),
        p.num_boost_round,
        sha.hpo.slice(0, 8) + "/" + sha.metrics.slice(0, 8) + "/" + sha.strategy.slice(0, 8),
      ];
    }));
}

function tickerLink(ticker) {
  const b = document.createElement("button");
  b.className = "linkish";
  b.textContent = ticker;
  b.addEventListener("click", () => selectAsset(ticker));
  return b;
}

function selectAsset(ticker) {
  const group = document.getElementById("asset-pills");
  if (!group) return;
  const b = group.querySelector("button[data-key='" + ticker + "']");
  if (b) b.click();
}

/* ---- ML Assets tab: per-asset panel, eight frames in experiment order ---- */

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

function warningsFrame(a) {
  const active = [];
  if (a.warnings.test_logloss_above_uniform) {
    active.push("locked-test log-loss is at or above the uniform baseline (ln 3)");
  }
  if (a.warnings.too_few_trades) active.push("fewer than 30 trades on the locked test fold");
  if (a.warnings.tau_fallback) {
    active.push("no threshold met the trade-count constraint — deterministic tau = 0 fallback");
  }
  if (!active.length) return null;
  const d = document.createElement("div");
  d.className = "box warn";
  d.textContent = active.map((t) => "! " + t).join("\n");
  return d;
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
  const bounds = s.config.fold_bounds_utc;
  const rows = Object.keys(a.segments).sort().map((k) => {
    const split = parseInt(k.split("_")[1], 10);
    const g = a.segments[k];
    const isTest = split === s.config.test_split;
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
  f.body.appendChild(foot("purge drops training events whose path reaches the pre-test cutoff; "
    + "scored rows exclude label-invalid decisions."));
  return f.frame;
}

function hpoFrame(a, s) {
  const f = frameEl("3. hyper-parameter search");
  const p = a.hpo.best_params;
  f.body.appendChild(kvBox([
    ["trials (TPE, sequential)", a.hpo.n_trials],
    ["best trial", "#" + a.hpo.best_trial],
    ["best objective", a.hpo.best_logloss.toFixed(6) + "  (mean weighted OOS log-loss)"],
    ["max_depth / eta", p.max_depth + " / " + p.eta.toFixed(5)],
    ["min_child_weight", p.min_child_weight],
    ["subsample / colsample", p.subsample.toFixed(3) + " / " + p.colsample_bytree.toFixed(3)],
    ["lambda / alpha", p.lambda.toFixed(3) + " / " + p.alpha.toFixed(3)],
    ["boosting rounds", p.num_boost_round],
  ]));
  const v = a.hpo.trial_values;
  const sorted = v.slice().sort((x, y) => x - y);
  f.body.appendChild(sparkline(v, s.baseline_logloss_uniform, a.hpo.best_trial,
    "objective per trial in TPE order; dashed line = uniform baseline ln 3"));
  f.body.appendChild(foot("objective per trial in TPE order · dashed = uniform baseline (ln 3) · "
    + "vertical = best trial · min " + sorted[0].toFixed(4)
    + " · median " + sorted[Math.floor(sorted.length / 2)].toFixed(4)
    + " · max " + sorted[sorted.length - 1].toFixed(4)));
  return f.frame;
}

function validationFrame(a, s) {
  const ln3 = s.baseline_logloss_uniform;
  const f = frameEl("4. validation (out-of-sample, threshold selection)");
  f.body.appendChild(makeTable(
    ["fold", "log-loss", "&Delta; vs ln 3", "balanced accuracy", "MCC", "scored rows"],
    valSplits(a).map((k) => {
      const m = a.validation[k];
      return [
        "F" + k.split("_")[1],
        [m.logloss.toFixed(6), m.logloss >= ln3],
        (m.logloss - ln3).toFixed(4),
        m.balanced_accuracy.toFixed(4),
        m.mcc.toFixed(4),
        fmt(m.n),
      ];
    })));
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

function testFrame(a, s) {
  const ln3 = s.baseline_logloss_uniform;
  const mean = meanOf(valSplits(a).map((k) => a.validation[k].logloss));
  const f = frameEl("5. locked test (read once, frozen)");
  f.body.appendChild(kvBox([
    ["scored rows", fmt(a.test.n)],
    ["log-loss", a.test.logloss.toFixed(6) + "  (uniform baseline " + ln3.toFixed(6) + ")"],
    ["delta vs baseline", (a.test.logloss - ln3).toFixed(6)],
    ["gap vs mean validation", (a.test.logloss - mean >= 0 ? "+" : "") + (a.test.logloss - mean).toFixed(6)],
    ["balanced accuracy", a.test.balanced_accuracy.toFixed(4)],
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
    (100 * m.avg_trade_ret).toFixed(3) + "%",
    (100 * m.exposure).toFixed(2) + "%",
    (100 * m.turnover).toFixed(3) + "%",
    (100 * m.gate_share).toFixed(2) + "%",
  ];
}

function strategyFrame(a, s) {
  const f = frameEl("6. strategy (model picks the side, hierarchy gates it)");
  f.body.appendChild(kvBox([
    ["tau", a.strategy.tau.toFixed(2) + (a.strategy.tau_constraint_met ? "" : "  (fallback)")],
    ["selection score", num(a.strategy.selection_score_mean_sharpe, 3) + "  (mean validation Sharpe)"],
    ["cost per side", (100 * a.strategy.costs_per_side).toFixed(2) + "%"],
    ["gate", "side = sign(trend_4h) and at least " + s.config.agree_min + " of 3 levels agree"],
  ]));
  const rows = valSplits(a).map((k) => pnlRow("F" + k.split("_")[1], a.strategy.validation[k], false));
  rows.push(pnlRow("F" + s.config.test_split + " (locked)", a.strategy.test, true));
  f.body.appendChild(makeTable(
    ["fold", "Sharpe", "maxDD", "trades", "hit rate", "avg trade", "exposure", "turnover", "gate share"],
    rows));
  f.body.appendChild(subhead("locked-test exits"));
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
  const f = frameEl("7. locked-test equity (unit position, costs included)");
  f.body.appendChild(sparkline(c.equity, 1.0, null,
    "equity on the locked test fold; dashed line = 1.0 (flat)"));
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
  const banner = warningsFrame(a);
  if (banner) host.appendChild(banner);
  [sampleFrame(a), segmentsFrame(a, s), hpoFrame(a, s), validationFrame(a, s),
   testFrame(a, s), strategyFrame(a, s), equityFrame(a), importanceFrame(a)]
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

/* ---- load ---- */

fetch("ml_status.json", { cache: "no-store" })
  .then((r) => { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
  .then((s) => {
    if (s.schema_version !== ML_SCHEMA) {
      throw new Error("schema v" + s.schema_version + ", expected v" + ML_SCHEMA);
    }
    const envelope =
      "research window: [" + s.research_window[0] + " .. " + s.research_window[1] + ") UTC\n" +
      "data_sha256:    " + s.data_sha256 + "\n" +
      "config_sha256:  " + s.config_sha256 + "\n" +
      "versions:       " + Object.entries(s.versions).map((kv) => kv.join(" ")).join(", ") + "\n" +
      "generated:      " + s.generated_at_utc + " UTC";
    document.getElementById("ml-meta").textContent = envelope;
    document.getElementById("asset-meta").textContent = envelope;

    ML_STATUS = s;
    renderResearch(s);
    viewLabels(s);
    viewClassification(s);
    viewStrategy(s);
    viewSearch(s);
    buildAssetPills(s);
  })
  .catch((e) => {
    ["ml-meta", "asset-meta"].forEach((id) => {
      const box = document.getElementById(id);
      box.textContent = "could not load ml_status.json (" + e.message + ") — run `make ml-status`";
      box.className = "box err";
    });
  });
