/* Render status.json on two tabs. Vanilla JS, no external resources. */
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

function bar(pctValue) {
  const track = document.createElement("span");
  track.className = "bar-track";
  const fill = document.createElement("span");
  fill.className = "bar-fill";
  fill.style.width = Math.max(0, Math.min(100, pctValue)) + "%";
  track.appendChild(fill);
  return track;
}

function pctCell(pctValue) {
  const wrap = document.createElement("span");
  wrap.appendChild(bar(pctValue));
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

/* tabs */
document.querySelectorAll("#tabs button").forEach((b) =>
  b.addEventListener("click", () => {
    document.querySelectorAll("#tabs button")
      .forEach((x) => x.classList.toggle("active", x === b));
    document.querySelectorAll("section[id^='tab-']")
      .forEach((s) => { s.hidden = s.id !== "tab-" + b.dataset.tab; });
  }));

function renderVenue(tableId, list) {
  const tbody = document.querySelector("#" + tableId + " tbody");
  for (const v of list) {
    const tr = document.createElement("tr");
    cell(tr, v.symbol);
    cell(tr, fmt(v.zip_count));
    cell(tr, fmt(v.rows));
    cell(tr, pctCell(v.coverage_pct));
    cell(tr, fmt(v.gaps));
    cell(tr, fmt(v.gaps_after_listing), v.gaps_after_listing > 0);
    cell(tr, fmt(v.duplicates), v.duplicates > 0);
    cell(tr, fmt(v.ohlc_violations), v.ohlc_violations > 0);
    cell(tr, fmt(v.zero_volume));
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
      "flow: " + fmt(f.zips_binance) + " binance zips + " + fmt(f.zips_bybit) + " bybit zips" +
      " -> " + fmt(f.rows_binance) + " + " + fmt(f.rows_bybit) + " venue rows" +
      " -> " + fmt(f.rows_canonical) + " canonical rows -> " + fmt(f.parquet_rows) + " parquet rows";

    const table = document.getElementById("symbols");
    const tbody = table.querySelector("tbody");
    for (const y of s.symbols) {
      const tr = document.createElement("tr");
      cell(tr, y.symbol);
      cell(tr, fmt(y.rows));
      cell(tr, pctCell(y.data_pct), y.data_pct < 99.9);
      cell(tr, fmt(y.ffill_bars), y.ffill_bars > 0);
      cell(tr, fmt(y.parquet_rows), y.parquet_rows !== y.rows);
      cell(tr, fmtBytes(y.parquet_bytes));
      tbody.appendChild(tr);
    }
    table.hidden = false;

    renderVenue("venue-binance", s.venues.binance);
    renderVenue("venue-bybit", s.venues.bybit);

    const ftbody = document.querySelector("#canonical-source tbody");
    for (const y of s.canonical_source) {
      const tr = document.createElement("tr");
      cell(tr, y.symbol);
      cell(tr, fmt(y.rows));
      cell(tr, pctCell(y.pct_binance));
      cell(tr, y.pct_bybit.toFixed(2) + "%");
      cell(tr, fmt(y.ffill_bars) + " (" + y.pct_ffill.toFixed(3) + "%)", y.pct_ffill > 0.1);
      cell(tr, fmt(y.zero_volume_bars));
      cell(tr, fmt(y.source_switches));
      cell(tr, y.max_abs_ret_at_switch === null ? "-" : (100 * y.max_abs_ret_at_switch).toFixed(2) + "%",
           y.max_abs_ret_at_switch !== null && y.max_abs_ret_at_switch > 0.01);
      cell(tr, fmt(y.ohlc_violations), y.ohlc_violations > 0);
      cell(tr, fmt(y.longest_flat_run_min));
      cell(tr, y.max_abs_ret_1m === null ? "-" : (100 * y.max_abs_ret_1m).toFixed(2) + "%");
      cell(tr, fmtDiv(y.div_mean));
      cell(tr, fmtDiv(y.div_p99), y.div_p99 !== null && y.div_p99 > 0.002);
      cell(tr, fmtDiv(y.div_max));
      ftbody.appendChild(tr);
    }
  })
  .catch((e) => {
    const meta = document.getElementById("meta");
    meta.textContent = "could not load status.json (" + e.message + ") — run `make status`";
    meta.className = "box err";
  });

/* ML Research tab */
fetch("ml_status.json", { cache: "no-store" })
  .then((r) => { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
  .then((s) => {
    document.getElementById("ml-meta").textContent =
      "research window: [" + s.research_window[0] + " .. " + s.research_window[1] + ") UTC\n" +
      "data_sha256:    " + (s.data_sha256 || "-") + "\n" +
      "config_sha256:  " + (s.config_sha256 || "-");
    const table = document.getElementById("ml-assets");
    const tbody = table.querySelector("tbody");
    for (const a of s.assets) {
      const tr = document.createElement("tr");
      const warn = a.warnings.test_logloss_above_uniform || a.warnings.too_few_trades;
      cell(tr, a.ticker, warn);
      cell(tr, fmt(a.rows));
      cell(tr, a.masked_pct.toFixed(3) + "%");
      cell(tr, fmt(a.class_counts.short) + "/" + fmt(a.class_counts.neutral) + "/" + fmt(a.class_counts.long));
      cell(tr, a.best_params.max_depth + " / " + a.best_params.eta.toFixed(3) + " / " + a.best_params.num_boost_round);
      cell(tr, a.hpo_best_logloss.toFixed(4));
      cell(tr, a.test.logloss.toFixed(4), a.warnings.test_logloss_above_uniform);
      cell(tr, a.test.balanced_accuracy.toFixed(3));
      cell(tr, a.test.mcc.toFixed(3));
      cell(tr, a.strategy.tau.toFixed(2) + (a.strategy.tau_constraint_met ? "" : " !"));
      cell(tr, a.strategy.sharpe.toFixed(2));
      cell(tr, (100 * a.strategy.max_drawdown).toFixed(1) + "%");
      cell(tr, fmt(a.strategy.n_trades), a.warnings.too_few_trades);
      cell(tr, (100 * a.strategy.hit_rate).toFixed(1) + "%");
      cell(tr, (100 * a.strategy.exposure).toFixed(1) + "%");
      tbody.appendChild(tr);
    }
    table.hidden = false;
  })
  .catch((e) => {
    const meta = document.getElementById("ml-meta");
    meta.textContent = "could not load ml_status.json (" + e.message + ") — run `make ml-status`";
    meta.className = "box err";
  });
