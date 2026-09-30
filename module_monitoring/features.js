/* Features tab: the serpentine search of every asset as the feature layer's snapshot publishes it — the cross-section
   of the searches, then each asset's PROPOSALS — measured against the ML snapshot's own numbers. Classic script using
   buildMeter, buildFrame, buildTable, buildKeyValueBox, buildFootnote, renderTable, formatCount, formatNumber,
   formatPercent, mean, validationFolds and buildConfigurablesTable from page.js, and FEATURES_STATUS from ml.js, which
   calls renderSerpentineSearch and renderFeatureConfigurables once both snapshots are in. */
"use strict";

/* an asset's serpentine search as the feature layer's snapshot publishes it; null while it has none, and for an
   asset the snapshot does not name */
function serpentineSearch(ticker) {
  const entry = FEATURES_STATUS.assets.find((asset) => asset.ticker === ticker);
  return entry ? entry.serpentine_search : null;
}

/* how a serpentine search ended — converged at a proven fixed point or stopped by its round budget — and in progress
   while it has no outcome */
function formatSearchOutcome(search) {
  return search.search_outcome === null ? "in progress" : search.search_outcome.replace(/_/g, " ");
}

/* what the serpentine search found: the proposal with what it adds and removes against the active search state, the
   validation skill it was chosen on and what the strategy would do with it; the delta against the asset's mean
   validation skill is page arithmetic, like the mean validation skill itself */
function formatColumnChanges(proposal, timeframes) {
  return timeframes.map((timeframe) =>
    proposal.added_columns_by_timeframe[timeframe].map((name) => "+" + name + "_" + timeframe)
      .concat(proposal.removed_columns_by_timeframe[timeframe].map((name) => "\u2212" + name + "_" + timeframe)).join(" "))
    .filter((changes) => changes.length).join(" · ");
}

function buildProposalsFrame(asset) {
  const frame = buildFrame("PROPOSALS — the one search state the serpentine search may propose on the validation folds; none is promoted by itself");
  const search = serpentineSearch(asset.ticker);
  if (search === null) {
    frame.body.appendChild(buildFootnote("no serpentine search yet — run `make features-serpentine-search ASSET=" + asset.ticker + "`"));
    return frame.frame;
  }
  /* a recorded serpentine search conditioned on another set or other parameters compares against a baseline that
     has gone, so the frame states that and shows nothing rather than a delta against the wrong set */
  if (!search.search_inputs_current) {
    frame.body.appendChild(buildFootnote("the serpentine search predates the asset's search state, its profile, its parameters or a "
      + "record of the search — run `make features-serpentine-search ASSET=" + asset.ticker + "`"));
    return frame.frame;
  }
  const timeframes = FEATURES_STATUS.catalogue.timeframes.map((entry) => entry.timeframe);
  const folds = validationFolds(asset);
  const meanValidationSkill = mean(folds.map((fold) => asset.validation[fold].relative_logloss_skill));
  frame.body.appendChild(buildKeyValueBox([
    ["serpentine search", search.state_evaluation_count + " state evaluations in " + search.round_count + " rounds · "
      + search.selection_hypothesis_count + " selection hypotheses · " + formatSearchOutcome(search)
      + (search.beam_changed === null ? "" : ", its last round " + (search.beam_changed ? "changing" : "leaving") + " the beam")
      + " · the active search state's mean validation skill " + formatPercent(meanValidationSkill, 2)],
  ]));
  frame.body.appendChild(buildTable(
    ["#", "state evaluation", "columns added / removed", "path CAGR", "path Calmar", "path PF",
     ...folds.map((fold) => "CAGR F" + fold.split("_")[1]),
     ...folds.map((fold) => "trades F" + fold.split("_")[1]),
     "mean skill", "&Delta; vs active", "&tau;"],
    search.proposals.map((proposal) => {
      const delta = proposal.mean_relative_logloss_skill - meanValidationSkill;
      return [
        proposal.proposal, proposal.state_evaluation_index, formatColumnChanges(proposal, timeframes),
        formatPercent(proposal.validation_path.cagr, 2),
        formatNumber(proposal.validation_path.calmar, 2),
        formatNumber(proposal.validation_path.profit_factor, 2),
        ...folds.map((fold) => formatPercent(proposal.validation[fold].cagr, 2)),
        ...folds.map((fold) => formatCount(proposal.validation[fold].trade_count)),
        formatPercent(proposal.mean_relative_logloss_skill, 2),
        (delta >= 0 ? "+" : "") + (100 * delta).toFixed(2) + " pp",
        proposal.entry_edge_threshold.toFixed(2),
      ];
    })));
  frame.body.appendChild(buildFootnote("the proposal is the search's champion: every validation fold scores it at or "
    + "above the search state the serpentine search started from, each move to it having raised the CAGR of every fold under "
    + "the trade floor at its own entry edge threshold, and the CAGR of its validation path — F2, F3 and F4 chained into "
    + "one walk-forward equity — beats the start's by more than the noise of every selection hypothesis the search tested. The model's "
    + "own skill is reported beside it and was not selected on. Nothing here touched the final holdout."));
  return frame.frame;
}

/* every asset's serpentine search in one table, then each asset's PROPOSALS; the delta of the proposal's mean
   validation skill against the asset's is page arithmetic, like the mean validation skill */
function renderSerpentineSearch(mlStatus) {
  const meanValidationSkill = (asset) => mean(validationFolds(asset).map((fold) => asset.validation[fold].relative_logloss_skill));
  const deltas = mlStatus.assets.map((asset) => {
    const search = serpentineSearch(asset.ticker);
    const proposal = search && search.search_inputs_current && search.proposals.length ? search.proposals[0] : null;
    return proposal === null ? null : proposal.mean_relative_logloss_skill - meanValidationSkill(asset);
  });
  const widestDelta = Math.max(0, ...deltas.filter((delta) => delta !== null));
  renderTable("serpentine-search",
    ["asset", "state evaluations", "selection hypotheses", "rounds", "outcome", "proposal &Delta; skill"],
    mlStatus.assets.map((asset, i) => {
      const search = serpentineSearch(asset.ticker);
      const delta = deltas[i];
      const deltaCell = document.createElement("span");
      if (delta !== null) {
        deltaCell.appendChild(buildMeter(widestDelta > 0 ? (100 * Math.max(0, delta)) / widestDelta : 0));
        deltaCell.appendChild(document.createTextNode((delta >= 0 ? "+" : "") + (100 * delta).toFixed(2) + " pp"));
      } else if (search === null) deltaCell.textContent = "no serpentine search yet";
      else if (!search.search_inputs_current) deltaCell.textContent = "the serpentine search predates the asset's search state, its profile, its parameters or a record of the search";
      else if (search.search_outcome === null) deltaCell.textContent = "no proposal before the search's outcome";
      else deltaCell.textContent = "no proposal";
      return [
        asset.ticker,
        search === null ? "-" : formatCount(search.state_evaluation_count),
        search === null ? "-" : formatCount(search.selection_hypothesis_count),
        search === null ? "-" : formatCount(search.round_count),
        search === null ? "-" : formatSearchOutcome(search),
        deltaCell,
      ];
    }));
  const host = document.getElementById("features-detail");
  mlStatus.assets.forEach((asset) => host.appendChild(buildProposalsFrame(asset)));
}

/* the feature module's CONFIGURABLES — its own and the serpentine search's records — as its snapshot publishes them */
function renderFeatureConfigurables(featuresStatus) {
  const frame = buildFrame("CONFIGURABLES — what an operator may set in the feature module, each value written once in its config.py");
  frame.body.appendChild(buildConfigurablesTable(featuresStatus.configurables));
  document.getElementById("features-configurables").appendChild(frame.frame);
}
