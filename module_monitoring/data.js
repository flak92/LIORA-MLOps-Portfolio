/* Pipeline and Data Quality tabs. Classic script using the formatters, cells, tables, frames and
   DATA_STATUS_LOADED of page.js — this file is what renders that snapshot into the status page.

   It names no provider. The snapshot publishes the venue set in its tier order as `source_venues`, and every
   per-provider section, column and share cell is derived from it: a provider added to the pipeline appears
   here with no edit to this file or to index.html. */
"use strict";

/* the columns whose only correct value is zero — duplicate and invalid rows per venue, OHLC violations on the
   canonical series.
   They are marked as a category, not a magnitude, so a reader knows which numbers he may be alarmed by:
   after a change of provider these must still be zero, while every observation beside them is expected to move. */
const VENUE_INVARIANT_HEADERS = ["dups", "invalid"];
const CANONICAL_INVARIANT_HEADERS = ["ohlc bad"];

/* named by their header, so an invariant is added by naming it — never by counting columns */
function renderInvariantColumns(table, invariantHeaders) {
  const headerCells = [...table.querySelectorAll("thead th")];
  const columns = invariantHeaders
    .map((label) => headerCells.findIndex((cell) => cell.textContent === label))
    .filter((column) => column >= 0);
  table.querySelectorAll("thead tr, tbody tr").forEach((row) => {
    columns.forEach((column) => row.cells[column] && row.cells[column].classList.add("invariant"));
  });
}

/* the share of the grid that was observed rather than invented: page arithmetic over two published counts */
function realDataPct(canonicalRow) {
  return canonicalRow.row_count
    ? (100 * (canonicalRow.row_count - canonicalRow.ffill_bars)) / canonicalRow.row_count : 0;
}

/* ---- Pipeline tab: the series research consumes ---- */

function renderPipeline(status) {
  document.getElementById("meta").textContent =
    "generated: " + status.generated_at_utc + " UTC\n" +
    "window:    from " + status.window_start_utc + " UTC\n" +
    "providers: " + status.source_venues.join(", ") + "  (tier order)";

  const rawRowCount = status.source_venues.reduce((total, venue) =>
    total + status.venues[venue].reduce((venueTotal, row) => venueTotal + row.row_count, 0), 0);
  const canonicalRowCount = status.canonical_source.reduce((total, row) => total + row.row_count, 0);
  document.getElementById("flow").textContent =
    "flow: " + formatCount(rawRowCount) + " raw rows"
    + " -> " + formatCount(canonicalRowCount) + " canonical rows";

  /* no "first" column: the canonical grid is full from window_start_utc by construction, so the envelope
     above already states it; a provider's own first printed minute is a venue row, on the other tab */
  renderTable("pipeline",
    ["symbol", "rows", "last", "real-data share", "ffill bars", "ffill run (min)", "flat run (min)"],
    status.canonical_source.map((row) => [
      row.symbol, formatCount(row.row_count),
      row.last_observation_utc || "-",
      buildPercentageCell(realDataPct(row)),
      [formatCount(row.ffill_bars), row.ffill_bars > 0],
      [formatCount(row.longest_ffill_run_minutes), row.longest_ffill_run_minutes > 0],
      formatCount(row.longest_flat_run_minutes),
    ]));
  document.getElementById("pipeline").hidden = false;
}

/* ---- Data Quality tab: one section per provider, then the object they were merged into ---- */

function renderRawSources(status) {
  const host = document.getElementById("raw-sources");
  host.textContent = "";
  status.source_venues.forEach((venue) => {
    const frame = buildFrame(venue);
    const table = buildTable(
      ["symbol", "rows", "coverage", "gaps", "gaps (since first obs.)", "dups", "invalid",
       "zero-vol", "flat", "last close", "first", "last"],
      status.venues[venue].map((row) => [
        row.symbol, formatCount(row.row_count), buildPercentageCell(row.coverage_pct),
        formatCount(row.gap_count),
        [formatCount(row.gap_count_after_first_observation), row.gap_count_after_first_observation > 0],
        [formatCount(row.duplicate_count), row.duplicate_count > 0],
        [formatCount(row.invalid_row_count), row.invalid_row_count > 0],
        formatCount(row.zero_volume_bars), formatCount(row.flat_bars),
        formatNumber(row.last_close, 2),
        row.first_observation_utc || "-", row.last_observation_utc || "-",
      ]));
    renderInvariantColumns(table, VENUE_INVARIANT_HEADERS);
    frame.body.appendChild(table);
    host.appendChild(frame.frame);
  });
}

function renderCanonicalSource(status) {
  const venues = status.source_venues;
  renderTable("canonical-source",
    ["symbol", "rows", ...venues, "ffill", "ffill run (min)", "zero-vol", "flat run (min)", "repeated",
     "switches", "max |ret| at switch", "max |ret| 1m", "rel. divergence p99", "max", "ohlc bad"],
    status.canonical_source.map((row) => {
      const shares = row.source_share_pct_by_venue;
      return [
        row.symbol, formatCount(row.row_count),
        /* the primary tier carries the bar; the tiers below it are read against it as numbers */
        ...venues.map((venue, tier) => (tier === 0 ? buildPercentageCell(shares[venue])
                                                   : shares[venue].toFixed(3) + "%")),
        [formatCount(row.ffill_bars), row.ffill_bars > 0],
        [formatCount(row.longest_ffill_run_minutes), row.longest_ffill_run_minutes > 0],
        formatCount(row.zero_volume_bars), formatCount(row.longest_flat_run_minutes),
        [formatCount(row.repeated_candle_count), row.repeated_candle_count > 0],
        formatCount(row.source_switch_count),
        formatPercent(row.max_abs_return_at_switch, 2), formatPercent(row.max_abs_return_1m, 2),
        formatPercent(row.relative_divergence_p99, 4), formatPercent(row.relative_divergence_max, 4),
        [formatCount(row.ohlc_violation_count), row.ohlc_violation_count > 0],
      ];
    }));
  renderInvariantColumns(document.getElementById("canonical-source"), CANONICAL_INVARIANT_HEADERS);
}

DATA_STATUS_LOADED.then((status) => {
  if (status instanceof Error) {
    const meta = document.getElementById("meta");
    meta.textContent = "could not load /store_status/data_status.json (" + status.message + ") — run `make data-status`";
    meta.className = "box err";
    return;
  }
  renderPipeline(status);
  renderRawSources(status);
  renderCanonicalSource(status);
});
