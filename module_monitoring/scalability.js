/* Scalability tab: where the crawler's files stand — status/skills_status.json, every controlled file of the
   files matrix with its state (pending, running, done, failed, interrupted), the vendor, when it finished and where its current
   report is. Classic script over the page.js toolkit; this view derives nothing. */
"use strict";

let SKILLS_STATUS = null;

function renderCrawlState(host, status) {
  const frame = buildFrame("CRAWL STATE — every controlled file of the files matrix, and its current report");
  frame.body.appendChild(buildTable(
    ["file", "state", "vendor", "finished_at_utc", "report"],
    status.files.map((file) => [
      file.path,
      file.state,
      file.vendor === null ? "—" : file.vendor,
      file.finished_at_utc === null ? "—" : file.finished_at_utc,
      file.report === null ? "—" : file.report,
    ])));
  host.appendChild(frame.frame);
}

function initScalability() {
  const meta = document.getElementById("scalability-meta");
  fetch("status/skills_status.json", { cache: "no-store" })
    .then((response) => { if (!response.ok) throw new Error("HTTP " + response.status); return response.json(); })
    .then((status) => {
      SKILLS_STATUS = status;
      renderCrawlState(document.getElementById("scalability-detail"), status);
      meta.hidden = true;
    })
    .catch((error) => {
      meta.textContent = "could not fetch skills_status.json (" + error.message + ") — run `make skills-crawl`";
      meta.className = "box err";
    });
}

initScalability();
