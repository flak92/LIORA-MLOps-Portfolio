/* Pipeline and Data Quality tabs, plus the helpers ml.js and asset.js share:
   formatCount, formatNumber, buildMeter, appendCell, appendHeaderRow,
   appendRows, renderTable, initPills, PILL_HOOKS. Vanilla JS, classic
   scripts sharing one global scope, no external resources. Every function
   takes its verb from the JavaScript row of the AGENTS.md grammar table. */
"use strict";

function formatCount(value) {
  return value === null || value === undefined ? "-" : value.toLocaleString("en-US");
}

function formatBytes(byteCount) {
  if (byteCount === 0) return "0";
  const units = ["B", "KB", "MB", "GB"];
  let i = 0;
  while (byteCount >= 1024 && i < units.length - 1) { byteCount /= 1024; i++; }
  return byteCount.toFixed(i === 0 ? 0 : 1) + " " + units[i];
}

function formatDivergencePercent(value) {
  return value === null || value === undefined ? "-" : (100 * value).toFixed(4) + "%";
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

function appendCell(row, content, warn) {
  const td = document.createElement("td");
  if (content instanceof Node) td.appendChild(content);
  else td.textContent = content;
  if (warn) td.className = "warn";
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

function initPills(root) {
  root.querySelectorAll("[data-pills]").forEach((group) => {
    if (group.dataset.bound === "1") return;
    group.dataset.bound = "1";
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
  const table = document.getElementById(tableId);
  appendHeaderRow(table, ["symbol", "zips", "rows", "coverage", "gaps", "gaps (since first obs.)",
                          "dups", "ohlc bad", "zero-vol", "flat", "first", "last"]);
  const tbody = table.querySelector("tbody");
  for (const row of venueRows) {
    const tr = document.createElement("tr");
    appendCell(tr, row.symbol);
    appendCell(tr, formatCount(row.zip_count));
    appendCell(tr, formatCount(row.row_count));
    appendCell(tr, buildPercentageCell(row.coverage_pct));
    appendCell(tr, formatCount(row.gap_count));
    appendCell(tr, formatCount(row.gap_count_after_first_observation), row.gap_count_after_first_observation > 0);
    appendCell(tr, formatCount(row.duplicate_count), row.duplicate_count > 0);
    appendCell(tr, formatCount(row.ohlc_violation_count), row.ohlc_violation_count > 0);
    appendCell(tr, formatCount(row.zero_volume_bars));
    appendCell(tr, formatCount(row.flat_bars));
    appendCell(tr, row.first_observation_utc || "-");
    appendCell(tr, row.last_observation_utc || "-");
    tbody.appendChild(tr);
  }
}

fetch("data_status.json", { cache: "no-store" })
  .then((response) => { if (!response.ok) throw new Error("HTTP " + response.status); return response.json(); })
  .then((status) => {
    document.getElementById("meta").textContent =
      "generated: " + status.generated_at_utc + " UTC\n" +
      "window:    [" + status.window_start_utc + " .. " + status.window_end_utc + ") UTC\n" +
      "database:  " + formatBytes(status.db_bytes) + "  (duckdb " + status.duckdb_version + ")";
    const flow = status.flow;
    document.getElementById("flow").textContent =
      "flow: " + formatCount(flow.binance_zip_count + flow.bybit_zip_count) + " raw ZIPs" +
      " -> " + formatCount(flow.binance_row_count + flow.bybit_row_count) + " raw rows" +
      " -> " + formatCount(flow.canonical_row_count) + " canonical rows";

    const table = document.getElementById("symbols");
    appendHeaderRow(table, ["symbol", "canonical rows", "real-data share", "ffill bars"]);
    const tbody = table.querySelector("tbody");
    for (const row of status.symbols) {
      const tr = document.createElement("tr");
      appendCell(tr, row.symbol);
      appendCell(tr, formatCount(row.row_count));
      appendCell(tr, buildPercentageCell(row.real_data_pct));
      appendCell(tr, formatCount(row.ffill_bars), row.ffill_bars > 0);
      tbody.appendChild(tr);
    }
    table.hidden = false;

    renderRawSource("raw-binance", status.venues.binance);
    renderRawSource("raw-bybit", status.venues.bybit);

    const canonicalTable = document.getElementById("canonical-source");
    appendHeaderRow(canonicalTable, ["symbol", "rows", "primary", "secondary", "ffill", "zero-vol", "switches",
                                     "max |ret| at switch", "ohlc bad", "flat run (min)", "max |ret| 1m",
                                     "rel. divergence mean", "p99", "max"]);
    const ftbody = canonicalTable.querySelector("tbody");
    for (const row of status.canonical_source) {
      const tr = document.createElement("tr");
      appendCell(tr, row.symbol);
      appendCell(tr, formatCount(row.row_count));
      appendCell(tr, buildPercentageCell(row.binance_pct));
      appendCell(tr, row.bybit_pct.toFixed(2) + "%");
      appendCell(tr, formatCount(row.ffill_bars) + " (" + row.ffill_pct.toFixed(3) + "%)", row.ffill_bars > 0);
      appendCell(tr, formatCount(row.zero_volume_bars));
      appendCell(tr, formatCount(row.source_switch_count));
      appendCell(tr, row.max_abs_return_at_switch === null ? "-" : (100 * row.max_abs_return_at_switch).toFixed(2) + "%");
      appendCell(tr, formatCount(row.ohlc_violation_count), row.ohlc_violation_count > 0);
      appendCell(tr, formatCount(row.longest_flat_run_minutes));
      appendCell(tr, row.max_abs_return_1m === null ? "-" : (100 * row.max_abs_return_1m).toFixed(2) + "%");
      appendCell(tr, formatDivergencePercent(row.relative_divergence_mean));
      appendCell(tr, formatDivergencePercent(row.relative_divergence_p99));
      appendCell(tr, formatDivergencePercent(row.relative_divergence_max));
      ftbody.appendChild(tr);
    }
  })
  .catch((error) => {
    const meta = document.getElementById("meta");
    meta.textContent = "could not load data_status.json (" + error.message + ") — run `make data-status`";
    meta.className = "box err";
  });
