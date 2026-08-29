/* Lifecycle tab: one recorded run read from /runs and /runs/<run_id> — the run header, the stage
   table and one shared timeline. Classic script; uses buildFrame, buildKeyValueBox and buildFootnote
   from asset.js, buildTable from ml.js, and buildMeter, formatBytes, formatCount, formatNumber,
   formatPercent and PILL_HOOKS from data.js. The page collects nothing: every number below was
   measured by the stage that produced it. */
"use strict";

const TIMELINE_WIDTH = 700;
const TIMELINE_HEIGHT = 100;
const SECONDS_PER_MINUTE = 60;
const BYTES_PER_SECOND_LABEL = "/s";

let RUN_RECORD = null;

/* the endpoint writes UTC as "YYYY-MM-DD HH:MM:SS" */
function secondsSinceEpoch(utcText) {
  const [day, clock] = utcText.split(" ");
  const [year, month, dayOfMonth] = day.split("-").map(Number);
  const [hour, minute, second] = clock.split(":").map(Number);
  return Date.UTC(year, month - 1, dayOfMonth, hour, minute, second) / 1000;
}

function formatSeconds(seconds) {
  if (seconds === null || seconds === undefined) return "-";
  if (seconds < SECONDS_PER_MINUTE) return seconds.toFixed(1) + "s";
  return Math.floor(seconds / SECONDS_PER_MINUTE) + "m " + Math.round(seconds % SECONDS_PER_MINUTE) + "s";
}

/* a counter series becomes a rate; a delta across a container change is not a rate, so it is dropped */
function buildRateSeries(samples, key) {
  const points = [];
  for (let i = 1; i < samples.length; i++) {
    const previous = samples[i - 1];
    const sample = samples[i];
    if (sample.docker_service !== previous.docker_service) continue;
    const span = secondsSinceEpoch(sample.timestamp_utc) - secondsSinceEpoch(previous.timestamp_utc);
    if (span <= 0) continue;
    const rise = key(sample) - key(previous);
    if (rise < 0) continue;
    points.push({ at: secondsSinceEpoch(sample.timestamp_utc), value: rise / span });
  }
  return points;
}

function buildLevelSeries(samples, key) {
  return samples.map((sample) => ({ at: secondsSinceEpoch(sample.timestamp_utc), value: key(sample) || 0 }));
}

/* one series on the run's shared time axis, with a dashed rule at every stage start */
function buildTimeline(points, boundaries, startAt, endAt) {
  const NS = "http://www.w3.org/2000/svg";
  const span = Math.max(1, endAt - startAt);
  const peak = Math.max(1e-9, ...points.map((point) => point.value));
  const x = (at) => (TIMELINE_WIDTH * (at - startAt)) / span;
  const y = (value) => TIMELINE_HEIGHT - (value / peak) * TIMELINE_HEIGHT;

  const svg = document.createElementNS(NS, "svg");
  svg.setAttribute("viewBox", "0 0 " + TIMELINE_WIDTH + " " + TIMELINE_HEIGHT);
  svg.setAttribute("preserveAspectRatio", "none");
  svg.setAttribute("class", "timeline");
  boundaries.forEach((boundary) => {
    const rule = document.createElementNS(NS, "line");
    rule.setAttribute("x1", x(boundary.at));
    rule.setAttribute("x2", x(boundary.at));
    rule.setAttribute("y1", 0);
    rule.setAttribute("y2", TIMELINE_HEIGHT);
    rule.setAttribute("class", "timeline__boundary");
    const tip = document.createElementNS(NS, "title");
    tip.textContent = boundary.stage;
    rule.appendChild(tip);
    svg.appendChild(rule);
  });
  const line = document.createElementNS(NS, "polyline");
  line.setAttribute("class", "timeline__series");
  line.setAttribute("points", points.map((point) => x(point.at).toFixed(1) + "," + y(point.value).toFixed(1)).join(" "));
  svg.appendChild(line);
  return svg;
}

function appendTimeline(body, caption, points, boundaries, startAt, endAt) {
  const label = document.createElement("p");
  label.className = "timeline__caption";
  const peak = points.length ? Math.max(...points.map((point) => point.value)) : 0;
  label.textContent = caption + "  ·  peak " + (points.length ? peak : "-");
  body.appendChild(label);
  body.appendChild(buildTimeline(points, boundaries, startAt, endAt));
}

function buildRunHeader(record) {
  const manifest = record.manifest;
  const summary = record.summary;
  return buildKeyValueBox([
    ["run", record.run_id],
    ["commit", (manifest.git_commit_short || "-") + (manifest.working_tree_clean ? "" : "  (working tree dirty)")],
    ["start / end", manifest.started_at_utc + "  ->  " + manifest.finished_at_utc + " UTC"],
    ["total time", formatSeconds(summary.total_wall_seconds) + "  (stages " + formatSeconds(summary.total_stage_seconds)
      + ", orchestration " + formatSeconds(summary.orchestration_seconds) + ")"],
    ["total CPU", formatSeconds(summary.total_cpu_seconds) + "  (" + summary.total_cpu_core_hours + " core-hours)"],
    ["peak RAM of a stage", formatBytes(summary.global_memory_peak_bytes)],
    ["bottleneck", summary.bottleneck_stage],
    ["exit code", manifest.exit_code + "  (" + summary.status + ")"
      + (summary.failed_stage ? "  failed at " + summary.failed_stage : "")],
    ["dashboard", "HTTP " + summary.dashboard_ready.status_code + "  " + summary.dashboard_ready.url],
    ["host", manifest.kernel + "  ·  " + manifest.cpu_count + " cpus  ·  sampled every "
      + manifest.sample_interval_seconds + "s"],
  ]);
}

function renderRunStages(body, summary) {
  body.appendChild(buildTable(
    ["stage", "container", "pid", "time", "CPU", "CPU share", "peak RAM", "read", "write",
     "net in (container)", "net out (container)", "samples", "exit"],
    summary.stages.map((stage) => {
      const share = document.createElement("span");
      share.appendChild(buildMeter(100 * (stage.cpu_share || 0)));
      share.appendChild(document.createTextNode(formatPercent(stage.cpu_share, 0)));
      return [
        stage.stage, stage.docker_service, stage.pid,
        formatSeconds(stage.wall_seconds), formatSeconds(stage.cpu_seconds), share,
        formatBytes(stage.memory_peak_bytes),
        formatBytes(stage.read_chars), formatBytes(stage.write_chars),
        formatBytes(stage.container_network_received_bytes_delta),
        formatBytes(stage.container_network_transmitted_bytes_delta),
        formatCount(stage.sample_count),
        [stage.exit_code, stage.exit_code !== 0],
      ];
    })));
}

function renderRunOutputs(body, summary) {
  const rows = [];
  summary.stages.forEach((stage) => {
    (stage.output || []).forEach((output) => {
      rows.push([stage.stage, stage.input || "-", output.path,
                 output.size_bytes === null ? "absent" : formatBytes(output.size_bytes)]);
    });
  });
  body.appendChild(buildTable(["stage", "input", "output", "size"], rows));
}

function renderRunTimelines(body, record) {
  const samples = record.samples;
  if (!samples.length) {
    body.appendChild(buildFootnote("no samples: every stage of this run was shorter than one sample interval."));
    return;
  }
  const startAt = secondsSinceEpoch(record.summary.first_stage_start_utc);
  const endAt = secondsSinceEpoch(record.summary.last_stage_end_utc);
  const boundaries = record.summary.stages.map((stage) => ({ stage: stage.stage, at: secondsSinceEpoch(stage.start_utc) }));
  appendTimeline(body, "CPU — container seconds per second",
    buildRateSeries(samples, (s) => s.container_cpu_usage_seconds), boundaries, startAt, endAt);
  appendTimeline(body, "RAM — resident set of the stage process (bytes)",
    buildLevelSeries(samples, (s) => s.process_memory_resident_bytes), boundaries, startAt, endAt);
  appendTimeline(body, "disk — container block bytes" + BYTES_PER_SECOND_LABEL,
    buildRateSeries(samples, (s) => s.container_disk_read_bytes + s.container_disk_write_bytes), boundaries, startAt, endAt);
  appendTimeline(body, "network — container bytes" + BYTES_PER_SECOND_LABEL,
    buildRateSeries(samples, (s) => s.container_network_received_bytes + s.container_network_transmitted_bytes),
    boundaries, startAt, endAt);
}

function renderRun(record) {
  RUN_RECORD = record;
  const host = document.getElementById("run-detail");
  host.textContent = "";
  if (!record.manifest || !record.summary) {
    host.appendChild(buildFootnote("run " + record.run_id + " has no summary — it was never finalized."));
    return;
  }
  const header = buildFrame("RUN — " + record.run_id);
  header.body.appendChild(buildRunHeader(record));
  const stages = buildFrame("STAGES — what ran, in which container, at what cost");
  renderRunStages(stages.body, record.summary);
  const outputs = buildFrame("INPUTS AND OUTPUTS — what each stage read and what it left behind");
  renderRunOutputs(outputs.body, record.summary);
  const timeline = buildFrame("TIMELINE — one axis, dashed rules at the stage boundaries");
  renderRunTimelines(timeline.body, record);
  [header, stages, outputs, timeline].forEach((frame) => host.appendChild(frame.frame));
}

function fetchRunRecord(runId) {
  return fetch("runs/" + runId, { cache: "no-store" })
    .then((response) => { if (!response.ok) throw new Error("HTTP " + response.status); return response.json(); });
}

function initRun() {
  const meta = document.getElementById("run-meta");
  fetch("runs", { cache: "no-store" })
    .then((response) => { if (!response.ok) throw new Error("HTTP " + response.status); return response.json(); })
    .then((runs) => {
      if (!runs.run_ids.length) {
        meta.textContent = "no recorded run yet — run `make docker-btc-lifecycle`";
        return;
      }
      meta.textContent = runs.run_ids.length + " recorded run(s) · newest " + runs.run_ids[0];
      return fetchRunRecord(runs.run_ids[0]).then((record) => {
        meta.textContent = runs.run_ids.length + " recorded run(s) · showing " + record.run_id
          + " · " + formatCount(record.sample_count) + " samples, stride " + record.sample_stride;
        renderRun(record);
      });
    })
    .catch((error) => {
      meta.textContent = "could not load /runs (" + error.message + ") — run `make docker-up`";
      meta.className = "box err";
    });
}

initRun();
