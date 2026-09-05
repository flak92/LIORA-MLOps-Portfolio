/* Pipeline and Data Quality tabs. Classic script using the formatters, cells and tables of page.js,
   and its DATA_STATUS_LOADED — this file is what renders that snapshot into the status page. */
"use strict";

function renderRawSource(tableId, venueRows) {
  renderTable(tableId,
    ["symbol", "zips", "rows", "coverage", "gaps", "gaps (since first obs.)", "dups", "ohlc bad", "zero-vol", "flat", "first", "last"],
    venueRows.map((row) => [
      row.symbol, formatCount(row.zip_count), formatCount(row.row_count), buildPercentageCell(row.coverage_pct),
      formatCount(row.gap_count),
      [formatCount(row.gap_count_after_first_observation), row.gap_count_after_first_observation > 0],
      [formatCount(row.duplicate_count), row.duplicate_count > 0],
      [formatCount(row.ohlc_violation_count), row.ohlc_violation_count > 0],
      formatCount(row.zero_volume_bars), formatCount(row.flat_bars),
      row.first_observation_utc || "-", row.last_observation_utc || "-",
    ]));
}

DATA_STATUS_LOADED.then((status) => {
  if (status instanceof Error) {
    const meta = document.getElementById("meta");
    meta.textContent = "could not load store_status/data_status.json (" + status.message + ") — run `make data-status`";
    meta.className = "box err";
    return;
  }
  document.getElementById("meta").textContent =
    "generated: " + status.generated_at_utc + " UTC\n" +
    "window:    [" + status.window_start_utc + " .. " + status.window_end_utc + ") UTC\n" +
    "databases: " + formatBytes(status.symbols.reduce((total, row) => total + row.db_bytes, 0)) +
    "  (" + status.symbols.length + " files, duckdb " + status.duckdb_version + ")";
  const flow = status.flow;
  document.getElementById("flow").textContent =
    "flow: " + formatCount(flow.binance_zip_count + flow.bybit_zip_count) + " raw ZIPs" +
    " -> " + formatCount(flow.binance_row_count + flow.bybit_row_count) + " raw rows" +
    " -> " + formatCount(flow.canonical_row_count) + " canonical rows";

  renderTable("symbols", ["symbol", "canonical rows", "real-data share", "ffill bars"],
    status.symbols.map((row) => [row.symbol, formatCount(row.row_count), buildPercentageCell(row.real_data_pct),
                                 [formatCount(row.ffill_bars), row.ffill_bars > 0]]));
  document.getElementById("symbols").hidden = false;

  renderRawSource("raw-binance", status.venues.binance);
  renderRawSource("raw-bybit", status.venues.bybit);

  renderTable("canonical-source",
    ["symbol", "rows", "primary", "secondary", "ffill", "zero-vol", "switches", "max |ret| at switch", "ohlc bad",
     "flat run (min)", "max |ret| 1m", "rel. divergence mean", "p99", "max"],
    status.canonical_source.map((row) => [
      row.symbol, formatCount(row.row_count), buildPercentageCell(row.binance_pct), row.bybit_pct.toFixed(2) + "%",
      [formatCount(row.ffill_bars) + " (" + row.ffill_pct.toFixed(3) + "%)", row.ffill_bars > 0],
      formatCount(row.zero_volume_bars), formatCount(row.source_switch_count),
      formatPercent(row.max_abs_return_at_switch, 2),
      [formatCount(row.ohlc_violation_count), row.ohlc_violation_count > 0],
      formatCount(row.longest_flat_run_minutes), formatPercent(row.max_abs_return_1m, 2),
      formatPercent(row.relative_divergence_mean, 4), formatPercent(row.relative_divergence_p99, 4),
      formatPercent(row.relative_divergence_max, 4),
    ]));
});
