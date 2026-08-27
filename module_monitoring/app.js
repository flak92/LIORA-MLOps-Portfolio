/* Pipeline and Data Quality tabs, plus shared helpers used by ml.js.
   Vanilla JS, classic scripts sharing one global scope, no external
   resources. */
"use strict";

function fmt(n) {
  return n === null || n === undefined ? "-" : n.toLocaleString("en-US");
}

function fmtBytes(b) {
  if (b === 0) return "0";
  const units = ["B", "KB", "MB", "GB"];
  let i = 0;
  while (b >= 1024 && i < units.length - 1) { b /= 1024; i++; }
  return b.toFixed(i === 0 ? 0 : 1) + " " + units[i];
}

function fmtDiv(x) {
  return x === null || x === undefined ? "-" : (100 * x).toFixed(4) + "%";
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

function pctCell(pctValue) {
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
      group.querySelectorAll("button").forEach((b) => b.classList.toggle("pill--active", b.dataset.key === key));
      document.querySelectorAll("[data-panel='" + name + "']")
        .forEach((p) => { p.hidden = p.dataset.key !== key; });
      if (PILL_HOOKS[name]) PILL_HOOKS[name](key);
    };
    group.addEventListener("click", (e) => {
      const b = e.target.closest("button[data-key]");
      if (b && group.contains(b)) select(b.dataset.key);
    });
    const first = group.querySelector("button.pill--active") || group.querySelector("button");
    if (first) select(first.dataset.key);
  });
}

/* null-safe formatting: to_json_safe() writes null for non-finite floats */
function fmtNum(x, d) {
  return x === null || x === undefined ? "-" : x.toFixed(d);
}

initPills(document);

function renderRawSource(tableId, list) {
  const tbody = document.querySelector("#" + tableId + " tbody");
  for (const v of list) {
    const tr = document.createElement("tr");
    cell(tr, v.symbol);
    cell(tr, fmt(v.zip_count));
    cell(tr, fmt(v.rows));
    cell(tr, pctCell(v.coverage_pct));
    cell(tr, fmt(v.gaps));
    cell(tr, fmt(v.gaps_after_first_observation), v.gaps_after_first_observation > 0);
    cell(tr, fmt(v.duplicates), v.duplicates > 0);
    cell(tr, fmt(v.ohlc_violations), v.ohlc_violations > 0);
    cell(tr, fmt(v.zero_volume_bars));
    cell(tr, fmt(v.flat_bars));
    cell(tr, v.first_ts || "-");
    cell(tr, v.last_ts || "-");
    tbody.appendChild(tr);
  }
}

fetch("status.json", { cache: "no-store" })
  .then((r) => { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
  .then((s) => {
    document.getElementById("meta").textContent =
      "generated: " + s.generated_at_utc + " UTC\n" +
      "window:    [" + s.window_start + " .. " + s.window_end + ") UTC\n" +
      "database:  " + fmtBytes(s.db_bytes) + "  (duckdb " + s.duckdb_version + ")";
    const f = s.flow;
    document.getElementById("flow").textContent =
      "flow: " + fmt(f.zips_binance + f.zips_bybit) + " raw ZIPs" +
      " -> " + fmt(f.rows_binance + f.rows_bybit) + " raw rows" +
      " -> " + fmt(f.rows_canonical) + " canonical rows -> " + fmt(f.rows_parquet) + " parquet rows";

    const table = document.getElementById("symbols");
    const tbody = table.querySelector("tbody");
    for (const row of s.symbols) {
      const tr = document.createElement("tr");
      cell(tr, row.symbol);
      cell(tr, fmt(row.rows));
      cell(tr, pctCell(row.real_data_pct));
      cell(tr, fmt(row.ffill_bars), row.ffill_bars > 0);
      cell(tr, fmt(row.rows_parquet), row.rows_parquet !== row.rows);
      cell(tr, fmtBytes(row.parquet_bytes));
      tbody.appendChild(tr);
    }
    table.hidden = false;

    renderRawSource("raw-binance", s.venues.binance);
    renderRawSource("raw-bybit", s.venues.bybit);

    const ftbody = document.querySelector("#canonical-source tbody");
    for (const row of s.canonical_source) {
      const tr = document.createElement("tr");
      cell(tr, row.symbol);
      cell(tr, fmt(row.rows));
      cell(tr, pctCell(row.binance_pct));
      cell(tr, row.bybit_pct.toFixed(2) + "%");
      cell(tr, fmt(row.ffill_bars) + " (" + row.ffill_pct.toFixed(3) + "%)", row.ffill_bars > 0);
      cell(tr, fmt(row.zero_volume_bars));
      cell(tr, fmt(row.source_switches));
      cell(tr, row.max_abs_ret_at_switch === null ? "-" : (100 * row.max_abs_ret_at_switch).toFixed(2) + "%");
      cell(tr, fmt(row.ohlc_violations), row.ohlc_violations > 0);
      cell(tr, fmt(row.longest_flat_run_minutes));
      cell(tr, row.max_abs_ret_1m === null ? "-" : (100 * row.max_abs_ret_1m).toFixed(2) + "%");
      cell(tr, fmtDiv(row.div_mean));
      cell(tr, fmtDiv(row.div_p99));
      cell(tr, fmtDiv(row.div_max));
      ftbody.appendChild(tr);
    }
  })
  .catch((e) => {
    const meta = document.getElementById("meta");
    meta.textContent = "could not load status.json (" + e.message + ") — run `make status`";
    meta.className = "box err";
  });
