/* Pipeline and Data Quality tabs, plus the code every other script shares (formatters, cells, tables, pills). */
"use strict";

const BYTES_PER_KIBIBYTE = 1024;

function formatCount(value) {
  return value === null || value === undefined ? "-" : value.toLocaleString("en-US");
}

function formatBytes(byteCount) {
  if (byteCount === null || byteCount === undefined) return "-";
  if (byteCount === 0) return "0";
  const units = ["B", "KB", "MB", "GB"];
  let i = 0;
  while (byteCount >= BYTES_PER_KIBIBYTE && i < units.length - 1) { byteCount /= BYTES_PER_KIBIBYTE; i++; }
  return byteCount.toFixed(i === 0 ? 0 : 1) + " " + units[i];
}

/* a share as a percentage string; null-safe, because to_json_safe() writes null for the share a fold without trades cannot report */
function formatPercent(value, decimals) {
  return value === null || value === undefined ? "-" : (100 * value).toFixed(decimals) + "%";
}

function buildMeter(pctValue) {
  const track = document.createElement("span");
  track.className = "meter";
  const fill = document.createElement("span");
  fill.className = "meter__fill";
  fill.style.width = Math.max(0, Math.min(100, pctValue)) + "%";
  track.appendChild(fill);
  return track;
}

function buildPercentageCell(pctValue) {
  const wrap = document.createElement("span");
  wrap.appendChild(buildMeter(pctValue));
  wrap.appendChild(document.createTextNode(pctValue.toFixed(3) + "%"));
  return wrap;
}

function appendCell(row, content, isWarning) {
  const td = document.createElement("td");
  if (content instanceof Node) td.appendChild(content);
  else td.textContent = content;
  if (isWarning) td.className = "warn";
  row.appendChild(td);
  return td;
}

function appendHeaderRow(table, labels) {
  const tr = table.querySelector("thead").insertRow();
  labels.forEach((label) => {
    const th = document.createElement("th");
    th.innerHTML = label;
    tr.appendChild(th);
  });
}

/* a cell is its content, or [content, isWarning] */
function appendRows(table, rows) {
  const tbody = table.querySelector("tbody") || table.createTBody();
  rows.forEach((cells) => {
    const tr = tbody.insertRow();
    cells.forEach((content) => (Array.isArray(content) ? appendCell(tr, content[0], content[1]) : appendCell(tr, content)));
  });
}

function renderTable(id, headers, rows) {
  const table = document.getElementById(id);
  appendHeaderRow(table, headers);
  appendRows(table, rows);
}

/* One pill component for every group: top tabs, summary views, ticker rows.
   A group is [data-pills="NAME"]; its panels carry data-panel="NAME" and a
   matching data-key. Groups without static panels drive a hook instead, so
   pills injected after a fetch work through event delegation. */
const PILL_HOOKS = {};
let DATA_STATUS = null;

function initPills(root) {
  root.querySelectorAll("[data-pills]").forEach((group) => {
    const name = group.dataset.pills;
    const select = (key) => {
      group.querySelectorAll("button").forEach((button) => button.classList.toggle("pill--active", button.dataset.key === key));
      document.querySelectorAll("[data-panel='" + name + "']")
        .forEach((panel) => { panel.hidden = panel.dataset.key !== key; });
      if (PILL_HOOKS[name]) PILL_HOOKS[name](key);
    };
    group.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-key]");
      if (button && group.contains(button)) select(button.dataset.key);
    });
    const first = group.querySelector("button.pill--active") || group.querySelector("button");
    if (first) select(first.dataset.key);
  });
}

/* null-safe formatting: to_json_safe() writes null for non-finite floats */
function formatNumber(value, decimals) {
  return value === null || value === undefined ? "-" : value.toFixed(decimals);
}

initPills(document);

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

const DATA_STATUS_LOADED = fetch("data_status.json", { cache: "no-store" })
  .then((response) => { if (!response.ok) throw new Error("HTTP " + response.status); return response.json(); })
  .then((status) => {
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

    DATA_STATUS = status;
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
  })
  .catch((error) => {
    const meta = document.getElementById("meta");
    meta.textContent = "could not load data_status.json (" + error.message + ") — run `make data-status`";
    meta.className = "box err";
  });
