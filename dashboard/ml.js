/* ML Research and ML Assets tabs: one fetch of ml_status.json feeds the
   cross-section table, the four summary views and — through asset.js — the
   per-asset panel. Classic script sharing the helpers (cell, bar, pctCell,
   fmt, num, initPills, PILL_HOOKS) defined in app.js. */
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
