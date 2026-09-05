/* The toolkit every page of this dashboard shares: formatters, cells, tables, frames, pills,
   and the one fetch of the data snapshot. It writes into no page-specific element, so the
   status page and the DevOps panel both load it and neither inherits the other's markup. */
"use strict";

const BYTES_PER_KIBIBYTE = 1024;
const MILLISECONDS_PER_SECOND = 1000;
const SECONDS_PER_MINUTE = 60;

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

/* null-safe formatting: to_json_safe() writes null for non-finite floats */
function formatNumber(value, decimals) {
  return value === null || value === undefined ? "-" : value.toFixed(decimals);
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

function buildFrame(title) {
  const frame = document.createElement("div");
  frame.className = "frame";
  const head = document.createElement("div");
  head.className = "frame__head";
  head.textContent = title;
  const body = document.createElement("div");
  body.className = "frame__body";
  frame.append(head, body);
  return { frame: frame, body: body };
}

function buildKeyValueBox(pairs) {
  const box = document.createElement("div");
  box.className = "box";
  box.textContent = pairs.map((kv) => (kv[0] + ":").padEnd(26) + kv[1]).join("\n");
  return box;
}

function buildFootnote(text) {
  const paragraph = document.createElement("p");
  paragraph.className = "foot";
  paragraph.textContent = text;
  return paragraph;
}

/* a ticker as a link into a selector: selectAsset on the ML Assets tab, selectContainer on the panel */
function buildTickerLink(ticker, select) {
  const button = document.createElement("button");
  button.className = "ticker-link";
  button.textContent = ticker;
  button.addEventListener("click", () => select(ticker));
  return button;
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

initPills(document);

/* The data snapshot both pages read, fetched once. Root-relative, because the panel is served
   from a subdirectory. It resolves to the status or to the Error, never rejecting: a page that
   needs only the cadence must not fail on a snapshot another page renders. */
const DATA_STATUS_LOADED = fetch("/data_status.json", { cache: "no-store" })
  .then((response) => { if (!response.ok) throw new Error("HTTP " + response.status); return response.json(); })
  .then((status) => { DATA_STATUS = status; return status; })
  .catch((error) => error);
