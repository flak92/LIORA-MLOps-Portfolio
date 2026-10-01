/* Lifecycle tab: the newest run of run_records/index.json, its records read by the relative paths the index lists —
   the run header, the stage table and what each stage wrote to the three pipeline stores. Classic script; uses the
   shared toolkit from page.js, buildTable among them. The page collects nothing: every number below was measured from
   outside the stage by record.py — when it started, how it exited, what it added, changed and removed; a record is
   one stage's for the whole basket, `<stage>.json`. */
"use strict";

function formatSeconds(seconds) {
  if (seconds < SECONDS_PER_MINUTE) return seconds.toFixed(1) + "s";
  return Math.floor(seconds / SECONDS_PER_MINUTE) + "m " + Math.round(seconds % SECONDS_PER_MINUTE) + "s";
}

/* what a stage wrote: the bytes of every file it added or changed */
function bytesWritten(stage) {
  return stage.store_diff.added.concat(stage.store_diff.changed)
    .reduce((total, entry) => total + entry.size_bytes, 0);
}

function buildRunHeader(record) {
  const stages = record.stages;
  const first = stages[0];
  const last = stages[stages.length - 1];
  const failed = stages.filter((stage) => stage.exit_code !== 0);
  const totalSeconds = (millisecondsSinceEpoch(last.ended_at_utc) - millisecondsSinceEpoch(first.started_at_utc))
    / MILLISECONDS_PER_SECOND;
  const stageSeconds = stages.reduce((total, stage) => total + stage.duration_seconds, 0);
  return buildKeyValueBox([
    ["run", record.run_id],
    ["start / end", first.started_at_utc + "  ->  " + last.ended_at_utc + " UTC"],
    ["total time", formatSeconds(totalSeconds) + "  (stages " + formatSeconds(stageSeconds) + ")"],
    ["stages", stages.length + (failed.length
      ? "  ·  failed at " + failed.map((stage) => stage.stage).join(", ")
      : "  ·  every exit code 0")],
    ["written", formatBytes(stages.reduce((total, stage) => total + bytesWritten(stage), 0)) + " across the three pipeline stores"],
  ]);
}

function renderRunStages(body, stages) {
  body.appendChild(buildTable(
    ["stage", "start", "time", "exit", "added", "changed", "removed", "bytes written"],
    stages.map((stage) => [
      stage.stage, stage.started_at_utc, formatSeconds(stage.duration_seconds),
      [stage.exit_code, stage.exit_code !== 0],
      formatCount(stage.store_diff.added.length), formatCount(stage.store_diff.changed.length),
      formatCount(stage.store_diff.removed.length), formatBytes(bytesWritten(stage)),
    ])));
}

/* every file a stage touched, by store: the record of what the run left behind */
function renderRunStores(body, stages) {
  const rows = [];
  stages.forEach((stage) => {
    ["added", "changed", "removed"].forEach((change) => {
      stage.store_diff[change].forEach((entry) => {
        rows.push([stage.stage, entry.store, entry.path, change,
                   change === "removed" ? "-" : formatBytes(entry.size_bytes)]);
      });
    });
  });
  if (!rows.length) {
    body.appendChild(buildFootnote("no stage of this run wrote a file."));
    return;
  }
  body.appendChild(buildTable(["stage", "store", "path", "change", "size"], rows));
}

function renderRun(record) {
  const host = document.getElementById("run-detail");
  host.textContent = "";
  const header = buildFrame("RUN — " + record.run_id);
  header.body.appendChild(buildRunHeader(record));
  const stages = buildFrame("STAGES — what ran, how long, how it ended, what it wrote");
  renderRunStages(stages.body, record.stages);
  const stores = buildFrame("STORES — every file a stage added, changed or removed in the pipeline stores");
  renderRunStores(stores.body, record.stages);
  [header, stages, stores].forEach((frame) => host.appendChild(frame.frame));
}

function fetchJson(path) {
  return fetch(path, { cache: "no-store" })
    .then((response) => { if (!response.ok) throw new Error("HTTP " + response.status); return response.json(); });
}

/* one run as the tab reads it: every record the index lists for it, in the order the stages started */
function fetchRunRecord(run) {
  return Promise.all(run.records.map((path) => fetchJson("run_records/" + run.run_id + "/" + path)))
    .then((stages) => ({
      run_id: run.run_id,
      stages: stages.sort((one, other) => one.started_at_utc.localeCompare(other.started_at_utc)),
    }));
}

function initRun() {
  const meta = document.getElementById("run-meta");
  fetchJson("run_records/index.json")
    .then((index) => {
      meta.textContent = index.runs.length + " recorded run(s) · newest " + index.runs[0].run_id;
      return fetchRunRecord(index.runs[0]).then((record) => {
        meta.textContent = index.runs.length + " recorded run(s) · showing " + record.run_id
          + " · " + record.stages.length + " records";
        renderRun(record);
      });
    })
    .catch((error) => {
      meta.textContent = "could not load run_records/index.json (" + error.message + ") — run `make all-record`";
      meta.className = "box err";
    });
}

initRun();
