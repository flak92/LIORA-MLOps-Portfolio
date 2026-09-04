/* ML Research and ML Assets tabs: one fetch of ml_status.json feeds the
   cross-section table, the catalogue frame, the four summary views and — through
   asset.js — the per-asset panel. Classic script using appendCell, appendHeaderRow,
   appendRows, renderTable, buildMeter, buildTickerLink, formatCount,
   formatNumber and formatPercent from page.js. */
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
  renderTable("ml-assets",
    ["asset", "decisions", "classes &minus;/0/+", "depth/eta/rounds", "prior LL", "model LL",
     "skill", "&tau; (entry edge threshold)", "Sharpe", "maxDD", "trades", "hit", "exposure"],
    mlStatus.assets.map((asset) => {
      const finalHoldoutStrategy = asset.strategy.final_holdout;
      const bestParameters = asset.hyperparameter_search_result.best_params;
      return [
        asset.ticker, formatCount(asset.sample.decision_count),
        formatCount(asset.sample.class_counts.short) + "/" + formatCount(asset.sample.class_counts.neutral)
          + "/" + formatCount(asset.sample.class_counts.long),
        bestParameters.max_depth + " / " + bestParameters.eta.toFixed(3) + " / " + bestParameters.num_boost_round,
        asset.final_holdout.prior_logloss.toFixed(4), asset.final_holdout.model_logloss.toFixed(4),
        formatPercent(asset.final_holdout.relative_logloss_skill, 2),
        asset.strategy.entry_edge_threshold.toFixed(2) + (asset.strategy.entry_edge_threshold_constraint_met ? "" : " !"),
        formatNumber(finalHoldoutStrategy.sharpe, 2), formatPercent(finalHoldoutStrategy.max_drawdown, 1),
        formatCount(finalHoldoutStrategy.trade_count), formatPercent(finalHoldoutStrategy.hit_rate, 1),
        formatPercent(finalHoldoutStrategy.exposure, 1),
      ];
    }));
  document.getElementById("ml-assets").hidden = false;
}

/* ---- ML Research tab: the catalogue frame — the register, every definition with its terms and histories, the nesting ---- */

function formatTerm(term) {
  if (term.indicator === null) return term.inputs[0];
  return term.indicator + term.parameter_bars + " (" + term.parameter_word + " " + term.parameter_bars
    + " bars of " + term.inputs.join(", ") + ")";
}

/* a history as a bar on one time scale across every timeframe, so a level's reach is compared by eye */
function buildHistoryCell(hours, longestHours) {
  if (hours === undefined) return "-";
  const wrap = document.createElement("span");
  wrap.appendChild(buildMeter((100 * hours) / longestHours));
  wrap.appendChild(document.createTextNode(hours + " h"));
  return wrap;
}

function renderCatalogue(mlStatus) {
  const catalogue = mlStatus.catalogue;
  const timeframes = catalogue.timeframes.map((entry) => entry.timeframe);
  document.getElementById("catalogue-register").textContent =
    catalogue.timeframes.map((entry) =>
      entry.timeframe.padEnd(5) + (entry.duration_ms / MILLISECONDS_PER_SECOND / 60) + " min · "
      + entry.bars_per_day + " bars per day · "
      + (entry.ratio_to_lower === null ? "the decision timeframe" : entry.ratio_to_lower + "× the level below")
      + " · " + entry.slot).join("\n")
    + "\nwarm-up: " + catalogue.warmup.top_timeframe_bars + " bars of " + timeframes[timeframes.length - 1]
    + " · first decision " + catalogue.warmup.end_utc + " UTC";
  const longestHours = Math.max(...catalogue.definitions.flatMap((definition) =>
    Object.values(definition.history_hours_by_timeframe)));
  renderTable("catalogue",
    ["definition", "terms", "range", ...timeframes.map((timeframe) => "history " + timeframe), "warm-up (bars)", "default set"],
    catalogue.definitions.map((definition) => [
      definition.feature_definition,
      definition.terms.map(formatTerm).join(" · ")
        + (definition.operators.length ? " · " + definition.operators.join(", ") : "")
        + (definition.normaliser ? " · " + definition.normaliser : ""),
      definition.range,
      ...timeframes.map((timeframe) => buildHistoryCell(definition.history_hours_by_timeframe[timeframe], longestHours)),
      formatCount(definition.warmup_bars),
      definition.definition_in_default_set ? "yes" : "-",
    ]));
  document.getElementById("catalogue-nesting").textContent = "nesting — one level, one domain of time: "
    + catalogue.nesting.map((pair) => "longest on " + pair.lower + " " + pair.lower_longest_history_hours
      + " h < shortest on " + pair.upper + " " + pair.upper_shortest_history_hours + " h").join(" · ");
}

/* ---- ML Assets tab: four complementary cross-section views ---- */

function renderLabels(mlStatus) {
  renderTable("cs-labels",
    ["asset", "decisions", "warm-up excluded", "trainable rows", "short", "neutral share",
     "long", "scored (holdout)"],
    mlStatus.assets.map((asset) => {
      const classCounts = asset.sample.class_counts;
      const total = classCounts.short + classCounts.neutral + classCounts.long;
      return [
        buildTickerLink(asset.ticker, selectAsset),
        formatCount(asset.sample.decision_count),
        formatCount(asset.sample.warmup_excluded_decision_count),
        formatCount(asset.sample.trainable_row_count) + " (" + asset.sample.trainable_row_pct.toFixed(3) + "%)",
        formatCount(classCounts.short),
        buildShareCell(classCounts.neutral, total),
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
        buildTickerLink(asset.ticker, selectAsset),
        ...foldSkills.map((skill) => formatPercent(skill, 2)),
        formatPercent(mean(foldSkills), 2),
        asset.final_holdout.prior_logloss.toFixed(4),
        asset.final_holdout.model_logloss.toFixed(4),
        formatPercent(asset.final_holdout.relative_logloss_skill, 2),
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
        buildTickerLink(asset.ticker, selectAsset),
        asset.strategy.entry_edge_threshold.toFixed(2),
        asset.strategy.entry_edge_threshold_constraint_met ? "yes" : "fallback",
        formatNumber(selectionScore, 2),
        formatNumber(finalHoldoutStrategy.sharpe, 2),
        holdoutDegradation === null ? "-" : (holdoutDegradation >= 0 ? "+" : "") + holdoutDegradation.toFixed(2),
        formatPercent(finalHoldoutStrategy.max_drawdown, 1),
        formatCount(finalHoldoutStrategy.trade_count),
        formatPercent(finalHoldoutStrategy.hit_rate, 1),
        formatPercent(finalHoldoutStrategy.average_trade_return, 3),
        formatPercent(finalHoldoutStrategy.exposure, 1),
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
        buildTickerLink(asset.ticker, selectAsset),
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

function selectAsset(ticker) {
  document.querySelector("#asset-pills button[data-key='" + ticker + "']").click();
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
    renderCatalogue(mlStatus);
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
