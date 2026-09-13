/* Scalability tab: the tracked tree counted against its contract — /store_status/skills_status.json, the counts the
   canon's crawler measured, and /store_status/skills_review.json, its review record. Classic script over the page.js
   toolkit; the page computes nothing but presentation arithmetic: the findings summed by rule, and whether a proposal
   has reached its third occurrence. */
"use strict";

let SKILLS_STATUS = null;
let SKILLS_REVIEW = null;
/* skill_self_explaining_naming.md § Minting a new convention: a convention is minted at the third occurrence */
const MINTING_OCCURRENCE_COUNT = 3;

/* the places a metric or a finding names, one <code> per line */
function buildExampleList(examples) {
  const list = document.createElement("span");
  examples.forEach((text, index) => {
    if (index) list.appendChild(document.createElement("br"));
    const code = document.createElement("code");
    code.textContent = text;
    list.appendChild(code);
  });
  return list;
}

/* a share as a bar, a mean with two decimals, a count as a count */
function buildMetricValue(metric, value) {
  if (value === null || value === undefined) return "-";
  if (metric.endsWith("_pct")) return buildPercentageCell(value);
  return Number.isInteger(value) ? formatCount(value) : formatNumber(value, 2);
}

/* the cells of the named column in the rows of an invariant: the only correct value is zero */
function renderInvariantCells(table, header, metrics) {
  const column = Array.from(table.tHead.rows[0].cells).findIndex((cell) => cell.textContent === header);
  Array.from(table.tBodies[0].rows).forEach((row, index) => {
    if (metrics[index].kind === "invariant") row.cells[column].classList.add("invariant");
  });
}

function renderScalabilityMeta(meta, status) {
  const reviewed = status.metrics.find((row) => row.metric === "files_reviewed_pct");
  const level = status.metrics.find((row) => row.metric === "self_explaining_level_mean");
  const raised = status.metrics.filter((row) => row.kind === "invariant" && row.value);
  const box = buildKeyValueBox([
    ["measured at", status.measured_at_commit.slice(0, 12) + "  (" + status.measured_at_commit_utc + " UTC)"],
    ["files in scope", formatCount(status.files_in_scope_count) + "  ·  python lines " + formatCount(status.python_line_count)],
    ["invariants above zero", raised.length ? raised.map((row) => row.metric).join(", ") : "none"],
    ["self-explaining level", level.value === null ? "-" : formatNumber(level.value, 2)],
    ["reviewed", ""],
  ]);
  box.appendChild(buildPercentageCell(reviewed.value));
  meta.replaceWith(box);
  box.id = "scalability-meta";
}

/* the rows of AGENTS.md § The shape: a count that holds or not, or a target that proves the row by hand */
function renderShape(host, status) {
  const frame = buildFrame("SHAPE — what holds at every commit, AGENTS.md § The shape");
  const values = Object.fromEntries(status.metrics.map((row) => [row.metric, row.value]));
  frame.body.appendChild(buildTable(
    ["condition", "holds", "evidence"],
    status.shape.map((row) => [
      row.condition,
      row.holds === null ? "by hand" : [row.holds ? "yes" : "no", !row.holds],
      row.evidence === null ? "-"
        : buildExampleList([row.holds === null ? row.evidence : row.evidence + " = " + values[row.evidence]]),
    ])));
  host.appendChild(frame.frame);
}

function renderMetrics(host, status) {
  const frame = buildFrame("METRICS — the tree counted against the contract, by family");
  const table = buildTable(
    ["family", "metric", "value", "examples", "rule"],
    status.metrics.map((row) => [
      row.family, row.metric, [buildMetricValue(row.metric, row.value), row.kind === "invariant" && row.value > 0],
      buildExampleList(row.examples), row.rule,
    ]));
  renderInvariantCells(table, "value", status.metrics);
  frame.body.appendChild(table);
  host.appendChild(frame.frame);
}

function renderModules(host, status) {
  const frame = buildFrame("MODULES — size, argued placements and docstrings");
  frame.body.appendChild(buildTable(
    ["module", "files", "python lines", "functions", "classes", "rationale rows", "module docstrings",
     "function docstrings", "reviewed"],
    status.modules.map((module) => [
      module.module, formatCount(module.file_count), formatCount(module.python_line_count),
      formatCount(module.function_count), formatCount(module.class_count),
      buildMetricValue("design_rationale_row_pct", module.design_rationale_row_pct),
      buildMetricValue("module_docstring_pct", module.module_docstring_pct),
      buildMetricValue("public_function_docstring_pct", module.public_function_docstring_pct),
      buildMetricValue("files_reviewed_pct", module.files_reviewed_pct),
    ])));
  host.appendChild(frame.frame);
}

function renderReview(host, review) {
  const frame = buildFrame("REVIEW — what the review record holds");
  if (!review.files.length && !review.proposals.length) {
    frame.body.appendChild(buildFootnote("no file reviewed yet: store/status/skills_review.json holds no row."));
    host.appendChild(frame.frame);
    return;
  }
  const findingsByRule = {};
  review.files.forEach((file) => file.findings.forEach((finding) => {
    (findingsByRule[finding.rule] = findingsByRule[finding.rule] || []).push(finding.example);
  }));
  frame.body.appendChild(buildTable(
    ["rule", "findings", "examples"],
    Object.keys(findingsByRule).sort().map((rule) => [rule, formatCount(findingsByRule[rule].length),
                                                      buildExampleList(findingsByRule[rule])])));
  frame.body.appendChild(buildTable(
    ["pattern", "forbids", "scope", "occurrences", "state"],
    review.proposals.map((proposal) => [
      proposal.pattern, proposal.forbids, proposal.scope, buildExampleList(proposal.occurrences),
      proposal.occurrence_count >= MINTING_OCCURRENCE_COUNT ? "third occurrence — mint or reject" : "proposed",
    ])));
  frame.body.appendChild(buildTable(
    ["path", "finding", "example"],
    review.files.filter((file) => file.verdict === "deferred").flatMap((file) =>
      file.findings.map((finding) => [file.path, finding.finding, buildExampleList([finding.example])]))));
  host.appendChild(frame.frame);
}

function fetchSkillsObject(name) {
  return fetch("/store_status/" + name, { cache: "no-store" })
    .then((response) => { if (!response.ok) throw new Error(name + ": HTTP " + response.status); return response.json(); });
}

function initScalability() {
  const meta = document.getElementById("scalability-meta");
  Promise.all([fetchSkillsObject("skills_status.json"), fetchSkillsObject("skills_review.json")])
    .then(([status, review]) => {
      SKILLS_STATUS = status;
      SKILLS_REVIEW = review;
      const host = document.getElementById("scalability-detail");
      renderShape(host, status);
      renderMetrics(host, status);
      renderModules(host, status);
      renderReview(host, review);
      renderScalabilityMeta(meta, status);
    })
    .catch((error) => {
      meta.textContent = "could not fetch the crawler's objects (" + error.message + ") — run `make skills-status`";
      meta.className = "box err";
    });
}

initScalability();
