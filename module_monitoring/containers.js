/* Containers tab: the registry (GET /containers), then one GET /containers/<TICKER>/status per asset every
   poll_interval_seconds while the tab is visible — each asset container as it reports itself. */
"use strict";

const MILLISECONDS_PER_MINUTE = 60000;
const MILLISECONDS_PER_SECOND = 1000;
const MINUTES_PER_HOUR = 60;
const HOURS_PER_DAY = 24;

/* the tab's two live globals beside the page's snapshot globals: the registry, and the latest answer per
   ticker — { status, payload, askedAt, cpuRate }; one poll at a time */
let CONTAINER_REGISTRY = null;
const CONTAINER_STATUS = {};
let CONTAINER_POLL_IN_FLIGHT = false;

/* the endpoint writes UTC as "YYYY-MM-DD HH:MM:SS" */
function minutesSince(utcText) {
  const [day, clock] = utcText.split(" ");
  const [year, month, dayOfMonth] = day.split("-").map(Number);
  const [hour, minute, second] = clock.split(":").map(Number);
  const then = Date.UTC(year, month - 1, dayOfMonth, hour, minute, second);
  return Math.max(0, Math.floor((Date.now() - then) / MILLISECONDS_PER_MINUTE));
}

function formatDuration(minutes) {
  if (minutes < MINUTES_PER_HOUR) return minutes + "m";
  const hours = Math.floor(minutes / MINUTES_PER_HOUR);
  if (hours < HOURS_PER_DAY) return hours + "h";
  return Math.floor(hours / HOURS_PER_DAY) + "d " + (hours % HOURS_PER_DAY) + "h";
}

function buildBadge(text, modifier) {
  const badge = document.createElement("span");
  badge.className = "badge" + (modifier ? " " + modifier : "");
  badge.textContent = text;
  return badge;
}

/* one badge per variable of the asset's state; --warn marks an observation or a measurement older than the download cadence */
function buildStateBadges(payload, cadence) {
  const warn = (minutes) => (minutes > cadence ? "badge--warn" : "");
  const footprint = payload.footprint;
  const badges = [buildBadge("up since " + payload.started_at_utc + " · " + formatDuration(minutesSince(payload.started_at_utc)), "")];
  if (payload.data) {
    badges.push(buildBadge("data " + payload.data.last_observation_utc + " · " + formatDuration(payload.data.observation_lag_minutes) + " behind",
                           warn(payload.data.observation_lag_minutes)));
    badges.push(buildBadge("rows " + formatCount(payload.data.row_count) + " · " + formatBytes(payload.data.db_bytes), ""));
    badges.push(buildBadge("window " + (payload.data.research_window_covered ? "covered" : "not covered"),
                           payload.data.research_window_covered ? "" : "badge--warn"));
  } else {
    badges.push(buildBadge("data no data yet", ""));
  }
  if (payload.artifacts) {
    badges.push(buildBadge("trained " + payload.artifacts.model_evaluation_modified_utc, ""));
    badges.push(buildBadge("threshold " + (payload.artifacts.entry_edge_threshold_constraint_met ? "met" : "fallback"),
                           payload.artifacts.entry_edge_threshold_constraint_met ? "" : "badge--warn"));
  } else {
    badges.push(buildBadge("artifacts no run yet", ""));
  }
  if (payload.data) {
    badges.push(buildBadge("measured " + formatDuration(payload.data.measurement_age_minutes) + " ago",
                           warn(payload.data.measurement_age_minutes)));
  }
  badges.push(buildBadge("memory " + formatBytes(footprint.memory_bytes) + " of " + formatBytes(footprint.memory_limit_bytes), ""));
  badges.push(buildBadge("peak " + formatBytes(footprint.memory_peak_bytes), ""));
  badges.push(buildBadge("cpu " + footprint.cpu_usage_seconds + "s on " + footprint.cpu_count + " cpus", ""));
  return badges;
}

function buildMemoryCell(footprint) {
  const wrap = document.createElement("span");
  wrap.appendChild(buildMeter((100 * footprint.memory_bytes) / footprint.memory_limit_bytes));
  wrap.appendChild(document.createTextNode(formatBytes(footprint.memory_bytes) + " of " + formatBytes(footprint.memory_limit_bytes)));
  return wrap;
}

/* the rate is presentation arithmetic: two readings of cpu_usage_seconds over the wall time between them, as a
   share of the host's cpus — a dash until the second poll */
function buildCpuCell(cpuRate, cpuCount) {
  if (cpuRate === null) return document.createTextNode("-");
  const wrap = document.createElement("span");
  wrap.appendChild(buildMeter(100 * cpuRate));
  wrap.appendChild(document.createTextNode(formatPercent(cpuRate, 1) + " of " + cpuCount + " cpus"));
  return wrap;
}

function renderContainerOverview() {
  const table = document.getElementById("container-overview");
  const cadence = DATA_STATUS.download_cadence_minutes;
  table.querySelector("thead").textContent = "";
  table.querySelector("tbody").textContent = "";
  appendHeaderRow(table, ["asset", "container", "up since", "memory", "peak", "CPU", "data", "measured"]);
  appendRows(table, CONTAINER_REGISTRY.tickers.map((ticker) => {
    const answer = CONTAINER_STATUS[ticker];
    const link = buildTickerLink(ticker, selectContainer);
    if (answer.status !== 200) return [link, buildBadge("down", "badge--down"), "-", "-", "-", "-", "-", "-"];
    const payload = answer.payload;
    return [
      link,
      buildBadge("up", ""),
      payload.started_at_utc + " · " + formatDuration(minutesSince(payload.started_at_utc)),
      buildMemoryCell(payload.footprint),
      formatBytes(payload.footprint.memory_peak_bytes),
      buildCpuCell(answer.cpuRate, payload.footprint.cpu_count),
      payload.data ? [formatDuration(payload.data.observation_lag_minutes) + " behind", payload.data.observation_lag_minutes > cadence]
                   : "no data yet",
      payload.data ? [formatDuration(payload.data.measurement_age_minutes) + " ago", payload.data.measurement_age_minutes > cadence] : "-",
    ];
  }));
  table.hidden = false;
}

/* the selected container's badge row and its answer verbatim; down, or not asked yet, is one badge and no body */
function renderContainer(ticker) {
  const host = document.getElementById("container-detail");
  const answer = CONTAINER_STATUS[ticker] || null;
  const payload = answer && answer.status === 200 ? answer.payload : null;
  host.textContent = "";
  const frame = buildFrame(ticker + " — the container, as it reports itself");
  const row = document.createElement("div");
  if (payload) buildStateBadges(payload, DATA_STATUS.download_cadence_minutes).forEach((badge) => row.appendChild(badge));
  else row.appendChild(buildBadge(answer ? "down" + (answer.status ? " · HTTP " + answer.status : "") : "not asked yet", "badge--down"));
  frame.body.appendChild(row);
  frame.body.appendChild(buildKeyValueBox([["/containers/" + ticker + "/status", payload ? JSON.stringify(payload) : "no body"]]));
  frame.body.appendChild(buildFootnote("a warning marks an observation or a measurement older than the download cadence; memory is what the kernel "
    + "charges the container, page cache included, against its ceiling; cpu is the container's total so far, and "
    + "the overview's rate is its share of the host's cpus over the last poll. A container that does not answer "
    + "is down and shows no previous numbers."));
  host.appendChild(frame.frame);
}

function selectContainer(ticker) {
  document.querySelector("#container-pills button[data-key='" + ticker + "']").click();
}

function buildContainerPills() {
  const group = document.getElementById("container-pills");
  CONTAINER_REGISTRY.tickers.forEach((ticker, i) => {
    const button = document.createElement("button");
    button.className = "pill" + (i === 0 ? " pill--active" : "");
    button.dataset.key = ticker;
    button.textContent = ticker;
    group.appendChild(button);
  });
  PILL_HOOKS.container = renderContainer;
}

function fetchContainerRegistry() {
  return fetch("containers", { cache: "no-store" })
    .then((response) => { if (!response.ok) throw new Error("HTTP " + response.status); return response.json(); });
}

/* one asset's endpoint through the proxy: any status but 200 is down, a failed exchange too */
function fetchContainerStatus(ticker) {
  const askedAt = Date.now();
  return fetch("containers/" + ticker + "/status", { cache: "no-store" })
    .then((response) => (response.ok
      ? response.json().then((payload) => ({ status: response.status, payload: payload }))
      : { status: response.status, payload: null }))
    .catch(() => ({ status: 0, payload: null }))
    .then((answer) => {
      const previous = CONTAINER_STATUS[ticker] || null;
      answer.askedAt = askedAt;
      answer.cpuRate = null;
      /* a rate needs two readings of one counter: the same container run, as its start time says */
      if (answer.payload && previous && previous.payload && previous.payload.started_at_utc === answer.payload.started_at_utc) {
        const cpuSeconds = answer.payload.footprint.cpu_usage_seconds - previous.payload.footprint.cpu_usage_seconds;
        const wallSeconds = (askedAt - previous.askedAt) / MILLISECONDS_PER_SECOND;
        answer.cpuRate = wallSeconds > 0 ? cpuSeconds / wallSeconds / answer.payload.footprint.cpu_count : null;
      }
      CONTAINER_STATUS[ticker] = answer;
      return answer;
    });
}

function fetchContainerStatuses() {
  return Promise.all(CONTAINER_REGISTRY.tickers.map((ticker) => fetchContainerStatus(ticker)));
}

/* one poll at a time: ask every container, then redraw the overview and the pill selected at that moment */
function renderContainers() {
  if (CONTAINER_POLL_IN_FLIGHT) return;
  CONTAINER_POLL_IN_FLIGHT = true;
  fetchContainerStatuses()
    .then(() => {
      renderContainerOverview();
      renderContainer(document.querySelector("#container-pills .pill--active").dataset.key);
    })
    .finally(() => { CONTAINER_POLL_IN_FLIGHT = false; });
}

/* the registry and the data snapshot first — the cadence the badges warn against — so the tab starts from one complete state */
function initContainers() {
  const meta = document.getElementById("container-meta");
  Promise.all([fetchContainerRegistry(), DATA_STATUS_LOADED])
    .then(([registry]) => {
      CONTAINER_REGISTRY = registry;
      meta.textContent = registry.tickers.length + " asset containers · polled every " + registry.poll_interval_seconds
        + "s while this tab is visible · registry " + registry.generated_at_utc + " UTC";
      buildContainerPills();
      PILL_HOOKS.tab = (key) => { if (key === "containers") renderContainers(); };
      setInterval(() => {
        if (document.visibilityState === "visible" && !document.getElementById("tab-containers").hidden) renderContainers();
      }, registry.poll_interval_seconds * MILLISECONDS_PER_SECOND);
      renderContainers();
    })
    .catch((error) => {
      meta.textContent = "could not load /containers (" + error.message + ") — run `make docker-up`";
      meta.className = "box err";
    });
}

initContainers();
