/* ML Assets tab: the per-asset panel. Classic script — uses buildMeter, buildFrame,
   buildKeyValueBox, buildFootnote, formatCount, formatNumber and formatPercent from page.js,
   and buildTable, buildShareCell, validationFolds, CLASS_NAMES and ML_STATUS from ml.js. */
"use strict";

/* single-series line with a dashed reference level; no legend needed, the
   frame title names the series. Native <title> carries the hover summary. */
function buildSparkline(values, baseline, caption) {
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

function buildHeaderLine(asset, mlStatus) {
  const line = document.createElement("p");
  line.className = "sub";
  line.textContent = asset.ticker + " · " + mlStatus.research_window.start_utc.slice(0, 7) + " → "
    + mlStatus.research_window.end_utc.slice(0, 7) + " · " + formatCount(asset.sample.decision_count) + " decisions";
  return line;
}

function buildLabelFrame(asset) {
  const frame = buildFrame("LABEL — triple barrier on the canonical 1m path");
  const classCounts = asset.sample.class_counts;
  const total = classCounts.short + classCounts.neutral + classCounts.long;
  frame.body.appendChild(buildTable(["class", "count", "share"], CLASS_NAMES.map((className) => [
    className, formatCount(classCounts[className]), buildShareCell(classCounts[className], total),
  ])));
  frame.body.appendChild(buildKeyValueBox([
    ["trainable rows", formatCount(asset.sample.trainable_row_count) + " of " + formatCount(asset.sample.decision_count)
      + " (" + asset.sample.trainable_row_pct.toFixed(3) + "%)"],
    ["excluded", formatCount(asset.sample.ambiguous_event_count) + " ambiguous · "
      + formatCount(asset.sample.unobservable_entry_count) + " unobservable entry"],
    ["warm-up excluded", formatCount(asset.sample.warmup_excluded_decision_count) + " decisions"],
  ]));
  return frame.frame;
}

function buildModelFrame(asset, mlStatus) {
  const frame = buildFrame("MODEL — skill against the training class prior");
  const bestParameters = asset.hyperparameter_search_result.best_params;
  frame.body.appendChild(buildKeyValueBox([
    ["parameters", "depth " + bestParameters.max_depth + " · eta " + bestParameters.eta.toFixed(4)
      + " · rounds " + bestParameters.num_boost_round + " · subsample " + bestParameters.subsample.toFixed(2)],
    ["search", asset.hyperparameter_search_result.trial_count + " Optuna trials · best mean F2–F4 log-loss "
      + asset.hyperparameter_search_result.best_logloss.toFixed(6)],
  ]));
  const rows = validationFolds(asset).map((foldKey) => ["F" + foldKey.split("_")[1], asset.validation[foldKey]]);
  rows.push(["F" + mlStatus.final_holdout_fold_id + " — final holdout (out-of-sample)", asset.final_holdout]);
  frame.body.appendChild(buildTable(
    ["fold", "prior log-loss", "model log-loss", "rel. skill", "scored rows"],
    rows.map(([label, metrics], i) => {
      const name = document.createElement("span");
      name.textContent = label;
      if (i === rows.length - 1) name.className = "final-holdout";
      return [name, metrics.prior_logloss.toFixed(6), metrics.model_logloss.toFixed(6),
              formatPercent(metrics.relative_logloss_skill, 2), formatCount(metrics.scored_row_count)];
    })));
  frame.body.appendChild(buildFootnote("skill = 1 − model / prior: what the model adds beyond knowing "
    + "how often each class occurs. The prior comes from the training rows of that fold."));
  return frame.frame;
}

function buildStrategyFrame(asset, mlStatus) {
  const frame = buildFrame("STRATEGY — model picks the side, the hierarchy gates it");
  frame.body.appendChild(buildKeyValueBox([
    ["entry edge threshold (τ)", asset.strategy.entry_edge_threshold.toFixed(2) + (asset.strategy.entry_edge_threshold_constraint_met ? "" : "  (fallback)")],
    ["gate", "side = sign(" + mlStatus.trend_gate_feature + ") and at least " + mlStatus.minimum_agreeing_trend_timeframes + " of 3 timeframes agree"],
    ["cost per side", formatPercent(asset.strategy.execution_cost_rate_per_trade_side, 2)
      + "  (execution-cost-adjusted, excluding funding)"],
  ]));
  const rows = validationFolds(asset).map((foldKey) => buildPnlRow("F" + foldKey.split("_")[1], asset.strategy.validation[foldKey], false));
  rows.push(buildPnlRow("F" + mlStatus.final_holdout_fold_id + " — final holdout (out-of-sample)", asset.strategy.final_holdout, true));
  frame.body.appendChild(buildTable(
    ["fold", "Sharpe", "maxDD", "trades", "hit rate", "avg trade", "exposure", "final equity"],
    rows));
  const equityCurve = asset.strategy.equity_curve;
  frame.body.appendChild(buildSparkline(equityCurve.equity, 1.0,
    "equity on the final holdout fold; dashed line = 1.0 (flat)"));
  frame.body.appendChild(buildFootnote("final holdout equity: start 1.000 · end "
    + asset.strategy.final_holdout.final_equity.toFixed(3) + " · dashed line = 1.0. Sharpe is annualised "
    + "from the 15m equity series and the drawdown measured on the 1m path, "
    + "both from the starting capital; the curve above is weekly-sampled."));
  return frame.frame;
}

function buildFeaturesFrame(asset) {
  const frame = buildFrame("FEATURES — XGBoost total gain");
  const items = Object.entries(asset.gain_importance).sort((a, b) => b[1] - a[1]);
  const max = items[0][1] || 1;
  frame.body.appendChild(buildTable(["feature", "total gain"], items.map((kv) => {
    const wrap = document.createElement("span");
    wrap.appendChild(buildMeter((100 * kv[1]) / max));
    wrap.appendChild(document.createTextNode(formatCount(Math.round(kv[1]))));
    return [kv[0], wrap];
  })));
  return frame.frame;
}

function renderAsset(ticker) {
  const mlStatus = ML_STATUS;
  const host = document.getElementById("asset-detail");
  const asset = mlStatus.assets.find((candidate) => candidate.ticker === ticker);
  host.textContent = "";
  host.appendChild(buildHeaderLine(asset, mlStatus));
  [buildLabelFrame(asset), buildModelFrame(asset, mlStatus), buildStrategyFrame(asset, mlStatus), buildFeaturesFrame(asset)]
    .forEach((el) => host.appendChild(el));
}

function buildPnlRow(label, pnlMetrics, isFinalHoldout) {
  const name = document.createElement("span");
  name.textContent = label;
  if (isFinalHoldout) name.className = "final-holdout";
  return [
    name,
    formatNumber(pnlMetrics.sharpe, 2),
    formatPercent(pnlMetrics.max_drawdown, 1),
    formatCount(pnlMetrics.trade_count),
    formatPercent(pnlMetrics.hit_rate, 1),
    formatPercent(pnlMetrics.average_trade_return, 3),
    formatPercent(pnlMetrics.exposure, 2),
    formatNumber(pnlMetrics.final_equity, 4),
  ];
}

function buildAssetPills(mlStatus) {
  const group = document.getElementById("asset-pills");
  mlStatus.assets.forEach((asset, i) => {
    const button = document.createElement("button");
    button.className = "pill" + (i === 0 ? " pill--active" : "");
    button.dataset.key = asset.ticker;
    button.textContent = asset.ticker;
    group.appendChild(button);
  });
  PILL_HOOKS.asset = renderAsset;
  /* pills arrive after load, so select here; #TICKER deep-links one asset */
  const wanted = decodeURIComponent(location.hash.slice(1)).toUpperCase();
  const start = group.querySelector("button[data-key='" + wanted + "']")
    || group.querySelector("button");
  if (start) start.click();
}
