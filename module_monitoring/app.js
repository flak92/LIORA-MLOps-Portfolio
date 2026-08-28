/* Pipeline and Data Quality tabs, plus shared helpers used by ml.js and
   asset.js (formatCount, formatBytes, formatNumber, formatDivergencePercent,
   meter, buildPercentageCell, cell, initPills, PILL_HOOKS). Vanilla JS,
   classic scripts sharing one global scope, no external resources. */
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

function meter(pctValue) {
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
  wrap.appendChild(meter(pctValue));
  wrap.appendChild(document.createTextNode(pctValue.toFixed(3) + "%"));
  return wrap;
}

function cell(row, content, warn) {
  const td = document.createElement("td");
  if (content instanceof Node) td.appendChild(content);
  else td.textContent = content;
  if (warn) td.className = "warn";
  row.appendChild(td);
  return td;
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
  const tbody = document.querySelector("#" + tableId + " tbody");
  for (const row of venueRows) {
    const tr = document.createElement("tr");
    cell(tr, row.symbol);
    cell(tr, formatCount(row.zip_count));
    cell(tr, formatCount(row.row_count));
    cell(tr, buildPercentageCell(row.coverage_pct));
    cell(tr, formatCount(row.gap_count));
    cell(tr, formatCount(row.gap_count_after_first_observation), row.gap_count_after_first_observation > 0);
    cell(tr, formatCount(row.duplicate_count), row.duplicate_count > 0);
    cell(tr, formatCount(row.ohlc_violation_count), row.ohlc_violation_count > 0);
    cell(tr, formatCount(row.zero_volume_bars));
    cell(tr, formatCount(row.flat_bars));
    cell(tr, row.first_observation_utc || "-");
    cell(tr, row.last_observation_utc || "-");
    tbody.appendChild(tr);
  }
}

fetch("status.json", { cache: "no-store" })
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
    const tbody = table.querySelector("tbody");
    for (const row of status.symbols) {
      const tr = document.createElement("tr");
      cell(tr, row.symbol);
      cell(tr, formatCount(row.row_count));
      cell(tr, buildPercentageCell(row.real_data_pct));
      cell(tr, formatCount(row.ffill_bars), row.ffill_bars > 0);
      tbody.appendChild(tr);
    }
    table.hidden = false;

    renderRawSource("raw-binance", status.venues.binance);
    renderRawSource("raw-bybit", status.venues.bybit);

    const ftbody = document.querySelector("#canonical-source tbody");
    for (const row of status.canonical_source) {
      const tr = document.createElement("tr");
      cell(tr, row.symbol);
      cell(tr, formatCount(row.row_count));
      cell(tr, buildPercentageCell(row.binance_pct));
      cell(tr, row.bybit_pct.toFixed(2) + "%");
      cell(tr, formatCount(row.ffill_bars) + " (" + row.ffill_pct.toFixed(3) + "%)", row.ffill_bars > 0);
      cell(tr, formatCount(row.zero_volume_bars));
      cell(tr, formatCount(row.source_switch_count));
      cell(tr, row.max_abs_return_at_switch === null ? "-" : (100 * row.max_abs_return_at_switch).toFixed(2) + "%");
      cell(tr, formatCount(row.ohlc_violation_count), row.ohlc_violation_count > 0);
      cell(tr, formatCount(row.longest_flat_run_minutes));
      cell(tr, row.max_abs_return_1m === null ? "-" : (100 * row.max_abs_return_1m).toFixed(2) + "%");
      cell(tr, formatDivergencePercent(row.relative_divergence_mean));
      cell(tr, formatDivergencePercent(row.relative_divergence_p99));
      cell(tr, formatDivergencePercent(row.relative_divergence_max));
      ftbody.appendChild(tr);
    }
  })
  .catch((error) => {
    const meta = document.getElementById("meta");
    meta.textContent = "could not load status.json (" + error.message + ") — run `make status`";
    meta.className = "box err";
  });
