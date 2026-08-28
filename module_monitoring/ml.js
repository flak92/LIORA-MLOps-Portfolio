/* ML Research and ML Assets tabs: one fetch of ml_status.json feeds the
   cross-section table, the four summary views and — through asset.js — the
   per-asset panel. Classic script using appendCell, appendHeaderRow,
   appendRows, renderTable, buildMeter, formatCount and formatNumber from
   data.js. */
"use strict";

const CLASS_NAMES = ["short", "neutral", "long"];
let ML_STATUS = null;

function buildTable(headers, rows) {
  const table = document.createElement("table");
  table.createTHead();
  appendHeaderRow(table, headers);
  appendRows(table, rows);
  return table;
}

function buildShareCell(part, whole) {
  const pctValue = whole ? (100 * part) / whole : 0;
  const wrap = document.createElement("span");
  wrap.appendChild(buildMeter(pctValue));
  wrap.appendChild(document.createTextNode(formatCount(part) + " (" + pctValue.toFixed(1) + "%)"));
  return wrap;
}

function mean(values) {
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function validationFolds(asset) {
  return Object.keys(asset.validation).sort();
}

/* ---- ML Research tab: the wide cross-section table ---- */

function renderResearch(mlStatus) {
  const table = document.getElementById("ml-assets");
  appendHeaderRow(table, ["asset", "decisions", "classes &minus;/0/+", "depth/eta/rounds", "prior LL", "model LL",
                          "skill", "&tau; (entry edge threshold)", "Sharpe", "maxDD", "trades", "hit", "exposure"]);
  const tbody = table.querySelector("tbody");
  for (const asset of mlStatus.assets) {
    const finalHoldoutStrategy = asset.strategy.final_holdout;
    const tr = tbody.insertRow();
    appendCell(tr, asset.ticker);
    appendCell(tr, formatCount(asset.sample.decision_count));
    appendCell(tr, formatCount(asset.sample.class_counts.short) + "/" + formatCount(asset.sample.class_counts.neutral) +
             "/" + formatCount(asset.sample.class_counts.long));
    appendCell(tr, asset.hyperparameter_search_result.best_params.max_depth + " / " + asset.hyperparameter_search_result.best_params.eta.toFixed(3) +
             " / " + asset.hyperparameter_search_result.best_params.num_boost_round);
    appendCell(tr, asset.final_holdout.prior_logloss.toFixed(4));
    appendCell(tr, asset.final_holdout.model_logloss.toFixed(4));
    appendCell(tr, (100 * asset.final_holdout.relative_logloss_skill).toFixed(2) + "%");
    appendCell(tr, asset.strategy.entry_edge_threshold.toFixed(2) + (asset.strategy.entry_edge_threshold_constraint_met ? "" : " !"));
    appendCell(tr, formatNumber(finalHoldoutStrategy.sharpe, 2));
    appendCell(tr, (100 * finalHoldoutStrategy.max_drawdown).toFixed(1) + "%");
    appendCell(tr, formatCount(finalHoldoutStrategy.trade_count));
    appendCell(tr, finalHoldoutStrategy.hit_rate === null ? "-" : (100 * finalHoldoutStrategy.hit_rate).toFixed(1) + "%");
    appendCell(tr, (100 * finalHoldoutStrategy.exposure).toFixed(1) + "%");
  }
  table.hidden = false;
}

/* ---- ML Assets tab: four complementary cross-section views ---- */

function renderLabels(mlStatus) {
  renderTable("cs-labels",
    ["asset", "decisions", "warm-up excl", "trainable rows", "short", "neutral share",
     "long", "scored (holdout)"],
    mlStatus.assets.map((asset) => {
      const classCounts = asset.sample.class_counts;
      const total = classCounts.short + classCounts.neutral + classCounts.long;
      return [
        [buildTickerLink(asset.ticker)],
        formatCount(asset.sample.decision_count),
        formatCount(asset.sample.warmup_excluded_decision_count),
        formatCount(asset.sample.trainable_row_count) + " (" + asset.sample.trainable_row_pct.toFixed(3) + "%)",
        formatCount(classCounts.short),
        [buildShareCell(classCounts.neutral, total)],
        formatCount(classCounts.long),
        formatCount(asset.final_holdout.scored_row_count),
      ];
    }));
}

function renderClassification(mlStatus) {
  const foldKeys = validationFolds(mlStatus.assets[0]);
  renderTable("cs-classification",
    ["asset", ...foldKeys.map((foldKey) => "val skill F" + foldKey.split("_")[1]),
     "mean val skill", "holdout prior LL", "holdout model LL", "holdout skill"],
    mlStatus.assets.map((asset) => {
      const folds = validationFolds(asset);
      const foldSkills = folds.map((foldKey) => asset.validation[foldKey].relative_logloss_skill);
      return [
        [buildTickerLink(asset.ticker)],
        ...foldSkills.map((skill) => (100 * skill).toFixed(2) + "%"),
        (100 * mean(foldSkills)).toFixed(2) + "%",
        asset.final_holdout.prior_logloss.toFixed(4),
        asset.final_holdout.model_logloss.toFixed(4),
        (100 * asset.final_holdout.relative_logloss_skill).toFixed(2) + "%",
      ];
    }));
}

function renderStrategy(mlStatus) {
  renderTable("cs-strategy",
    ["asset", "entry edge threshold", "constraint met", "selection score", "holdout Sharpe", "degradation",
     "maxDD", "trades", "hit", "avg trade", "exposure", "final equity",
     "exits: upper/lower/vertical/ambiguous"],
    mlStatus.assets.map((asset) => {
      const finalHoldoutStrategy = asset.strategy.final_holdout;
      const selectionScore = asset.strategy.selection_score_mean_sharpe;
      const holdoutDegradation = finalHoldoutStrategy.sharpe === null || selectionScore === null
        ? null : finalHoldoutStrategy.sharpe - selectionScore;
      const exitCounts = finalHoldoutStrategy.exit_counts;
      return [
        [buildTickerLink(asset.ticker)],
        asset.strategy.entry_edge_threshold.toFixed(2),
        asset.strategy.entry_edge_threshold_constraint_met ? "yes" : "fallback",
        formatNumber(selectionScore, 2),
        formatNumber(finalHoldoutStrategy.sharpe, 2),
        holdoutDegradation === null ? "-" : (holdoutDegradation >= 0 ? "+" : "") + holdoutDegradation.toFixed(2),
        (100 * finalHoldoutStrategy.max_drawdown).toFixed(1) + "%",
        formatCount(finalHoldoutStrategy.trade_count),
        finalHoldoutStrategy.hit_rate === null ? "-" : (100 * finalHoldoutStrategy.hit_rate).toFixed(1) + "%",
        finalHoldoutStrategy.average_trade_return === null ? "-" : (100 * finalHoldoutStrategy.average_trade_return).toFixed(3) + "%",
        (100 * finalHoldoutStrategy.exposure).toFixed(1) + "%",
        formatNumber(finalHoldoutStrategy.final_equity, 3),
        exitCounts.upper_barrier + "/" + exitCounts.lower_barrier + "/" + exitCounts.vertical + "/" + exitCounts.ambiguous,
      ];
    }));
}

function renderSearch(mlStatus) {
  renderTable("cs-search",
    ["asset", "trials", "best LL", "depth", "eta",
     "min child", "subsample", "colsample", "lambda", "alpha", "rounds"],
    mlStatus.assets.map((asset) => {
      const bestParameters = asset.hyperparameter_search_result.best_params;
      return [
        [buildTickerLink(asset.ticker)],
        asset.hyperparameter_search_result.trial_count,
        asset.hyperparameter_search_result.best_logloss.toFixed(4),
        bestParameters.max_depth,
        bestParameters.eta.toFixed(4),
        bestParameters.min_child_weight,
        bestParameters.subsample.toFixed(3),
        bestParameters.colsample_bytree.toFixed(3),
        bestParameters.lambda.toFixed(3),
        bestParameters.alpha.toFixed(3),
        bestParameters.num_boost_round,
      ];
    }));
}

function buildTickerLink(ticker) {
  const button = document.createElement("button");
  button.className = "ticker-link";
  button.textContent = ticker;
  button.addEventListener("click", () => selectAsset(ticker));
  return button;
}

function selectAsset(ticker) {
  const group = document.getElementById("asset-pills");
  if (!group) return;
  const button = group.querySelector("button[data-key='" + ticker + "']");
  if (button) button.click();
}

/* ---- load ---- */

fetch("ml_status.json", { cache: "no-store" })
  .then((response) => { if (!response.ok) throw new Error("HTTP " + response.status); return response.json(); })
  .then((mlStatus) => {
    const envelope =
      "research window: [" + mlStatus.research_window.start_utc + " .. " + mlStatus.research_window.end_utc + ") UTC\n" +
      "seed:            " + mlStatus.research_window.seed + "\n" +
      "generated:       " + mlStatus.generated_at_utc + " UTC";
    document.getElementById("ml-meta").textContent = envelope;
    document.getElementById("asset-meta").textContent = envelope;

    ML_STATUS = mlStatus;
    renderResearch(mlStatus);
    renderLabels(mlStatus);
    renderClassification(mlStatus);
    renderStrategy(mlStatus);
    renderSearch(mlStatus);
    buildAssetPills(mlStatus);
  })
  .catch((error) => {
    ["ml-meta", "asset-meta"].forEach((id) => {
      const box = document.getElementById(id);
      box.textContent = "could not load ml_status.json (" + error.message + ") — run `make ml-status`";
      box.className = "box err";
    });
  });
