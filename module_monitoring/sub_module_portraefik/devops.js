/* The DevOps panel: the Docker Engine views, proxied through the dashboard at /devops/api/*.
   Classic script using the formatters, cells and tables of page.js. The asset-container view
   beside it is containers.js, which reads the assets' own endpoints instead of the engine. */
"use strict";

let PANEL_MACHINES = null;
const MACHINE_SAMPLES = {};
let PANEL_POLL_IN_FLIGHT = false;
let MACHINE_ACTION_IN_FLIGHT = false;

/* the engine writes RFC 3339 with nanoseconds; the page shows the minute, like every other time here */
function formatEngineTime(text) {
  return text && text.length >= 16 ? text.slice(0, 10) + " " + text.slice(11, 16) : "-";
}

function formatPorts(ports) {
  return ports.length ? ports.join(" ") : "-";
}

/* the engine pins an image by digest, and names an untagged one by its bare hash; a reader
   recognises the tag, so the digest is dropped and a bare hash is cut to the length docker prints */
function formatImage(image) {
  if (!image) return "-";
  const tagged = image.split("@")[0];
  return tagged.startsWith("sha256:") ? tagged.slice("sha256:".length, "sha256:".length + 12) : tagged;
}

/* a compose container name repeats its project; the project has its own column */
function formatMachineName(machine) {
  return machine.compose_project && machine.name.startsWith(machine.compose_project + "-")
    ? machine.name.slice(machine.compose_project.length + 1)
    : machine.name;
}

function fetchPanelRoute(route) {
  return fetch("/devops/api/" + route, { cache: "no-store" })
    .then((response) => { if (!response.ok) throw new Error("HTTP " + response.status); return response.json(); });
}

function fetchMachineAction(containerId, action) {
  return fetch("/devops/api/machines/" + containerId + "/" + action, { method: "POST", cache: "no-store" })
    .then((response) => response.json().catch(() => ({})).then((body) => ({ status: response.status, body: body })));
}

/* the action's answer is never optimistic: the panel re-reads every view and renders what the engine now reports */
function selectMachineAction(containerId, action) {
  if (MACHINE_ACTION_IN_FLIGHT) return;
  MACHINE_ACTION_IN_FLIGHT = true;
  const meta = document.getElementById("panel-meta");
  meta.textContent = action + " " + containerId + "…";
  fetchMachineAction(containerId, action)
    .then((answer) => {
      meta.className = answer.status < 300 ? "box" : "box err";
      meta.textContent = answer.status < 300
        ? action + " " + containerId + " accepted (HTTP " + answer.status + ")"
        : action + " " + containerId + " refused (HTTP " + answer.status + "): " + (answer.body.reason || "no reason given");
    })
    .catch((error) => {
      meta.className = "box err";
      meta.textContent = action + " " + containerId + " failed: " + error.message;
    })
    .finally(() => { MACHINE_ACTION_IN_FLIGHT = false; renderPanel(); });
}

function buildActionCell(machine) {
  const wrap = document.createElement("span");
  PANEL_MACHINES.actions.forEach((action) => {
    const button = document.createElement("button");
    button.className = "ticker-link";
    button.textContent = action;
    button.disabled = !machine.own_project || MACHINE_ACTION_IN_FLIGHT;
    button.addEventListener("click", () => selectMachineAction(machine.container_id, action));
    wrap.appendChild(button);
  });
  return wrap;
}

function buildMachineMemoryCell(machine) {
  if (machine.memory_bytes === null || machine.memory_bytes === undefined) return "-";
  const wrap = document.createElement("span");
  if (machine.memory_limit_bytes) wrap.appendChild(buildMeter(100 * machine.memory_bytes / machine.memory_limit_bytes));
  wrap.appendChild(document.createTextNode(formatBytes(machine.memory_bytes)
    + (machine.memory_limit_bytes ? " of " + formatBytes(machine.memory_limit_bytes) : "")));
  return wrap;
}

/* the engine reports a counter, not a rate; the rate is this page's arithmetic over two polls, as for an asset */
function buildMachineCpuCell(machine) {
  const sample = MACHINE_SAMPLES[machine.container_id];
  if (!sample || sample.cpuRate === null || sample.cpuRate === undefined) return "-";
  const wrap = document.createElement("span");
  wrap.appendChild(buildMeter(100 * sample.cpuRate));
  wrap.appendChild(document.createTextNode(formatPercent(sample.cpuRate, 1) + " of " + machine.cpu_count));
  return wrap;
}

function renderMachines() {
  const table = document.getElementById("machines");
  table.querySelector("thead").textContent = "";
  table.querySelector("tbody").textContent = "";
  appendHeaderRow(table, ["container", "project", "service", "state", "up since", "image", "ports", "restarts",
                          "memory", "CPU", "actions"]);
  appendRows(table, PANEL_MACHINES.machines.map((machine) => [
    formatMachineName(machine),
    [machine.own_project ? "own" : machine.compose_project || "-", !machine.own_project],
    machine.compose_service || "-",
    machine.state,
    formatEngineTime(machine.started_at_utc),
    formatImage(machine.image),
    formatPorts(machine.ports),
    formatCount(machine.restart_count),
    buildMachineMemoryCell(machine),
    buildMachineCpuCell(machine),
    buildActionCell(machine),
  ]));
}

function renderNetworks(payload) {
  const table = document.getElementById("networks");
  table.querySelector("thead").textContent = "";
  table.querySelector("tbody").textContent = "";
  appendHeaderRow(table, ["network", "driver", "scope", "project", "attached"]);
  appendRows(table, payload.networks.map((network) => [
    network.name, network.driver, network.scope,
    [network.own_project ? "own" : network.compose_project || "-", !network.own_project],
    network.attached.length ? network.attached.join(" ") : "-",
  ]));
}

function renderVolumes(payload) {
  const volumes = document.getElementById("volumes");
  volumes.querySelector("thead").textContent = "";
  volumes.querySelector("tbody").textContent = "";
  appendHeaderRow(volumes, ["volume", "driver", "project", "size", "used by"]);
  appendRows(volumes, payload.volumes.map((volume) => [
    volume.name, volume.driver,
    [volume.own_project ? "own" : volume.compose_project || "-", !volume.own_project],
    formatBytes(volume.size_bytes), formatCount(volume.reference_count),
  ]));

  const binds = document.getElementById("bind-mounts");
  binds.querySelector("thead").textContent = "";
  binds.querySelector("tbody").textContent = "";
  appendHeaderRow(binds, ["source on the host", "destination in the container", "writable", "containers"]);
  appendRows(binds, payload.bind_mounts.map((mount) => [
    mount.source, mount.destination, mount.writable ? "yes" : "read-only", mount.containers.join(" "),
  ]));
}

function renderImage(payload) {
  document.getElementById("image").textContent = payload.image
    ? ["image", "id", "size", "created", "tags"].map((label, i) => (label + ":").padEnd(12) + [
        payload.image, payload.image_id || "-", formatBytes(payload.size_bytes),
        formatEngineTime(payload.created_utc), payload.repo_tags.join(" ") || "-",
      ][i]).join("\n")
    : "the engine reported no image for this container";
}

function renderEvents(payload) {
  const table = document.getElementById("events");
  table.querySelector("thead").textContent = "";
  table.querySelector("tbody").textContent = "";
  appendHeaderRow(table, ["time (UTC)", "type", "service", "action", "container"]);
  appendRows(table, payload.events.map((event) => [
    event.time_utc, event.type, event.compose_service || "-", event.action, event.name || "-",
  ]));
}

/* a view the engine did not answer holds no rows: an empty table is what this page knows, and an
   empty host is a measurement, so the outage clears them rather than leaving the last ones up */
function clearPanelViews() {
  ["machines", "networks", "volumes", "bind-mounts", "events"].forEach((id) => {
    const table = document.getElementById(id);
    table.querySelector("thead").textContent = "";
    table.querySelector("tbody").textContent = "";
  });
  document.getElementById("image").textContent = "-";
  PANEL_MACHINES = null;
  Object.keys(MACHINE_SAMPLES).forEach((containerId) => delete MACHINE_SAMPLES[containerId]);
}

/* one poll of every engine view; the CPU rate needs the previous sample, so it is kept per container */
function renderPanel() {
  if (PANEL_POLL_IN_FLIGHT) return;
  PANEL_POLL_IN_FLIGHT = true;
  const meta = document.getElementById("panel-meta");
  Promise.all([fetchPanelRoute("machines"), fetchPanelRoute("networks"), fetchPanelRoute("volumes"),
               fetchPanelRoute("image"), fetchPanelRoute("events")])
    .then(([machines, networks, volumes, image, events]) => {
      const askedAt = Date.now();
      machines.machines.forEach((machine) => {
        const previous = MACHINE_SAMPLES[machine.container_id];
        const wallSeconds = previous ? (askedAt - previous.askedAt) / MILLISECONDS_PER_SECOND : 0;
        /* a counter that went backwards is a container that restarted, not a negative rate */
        const cpuSeconds = machine.cpu_usage_seconds;
        const cpuRate = previous && wallSeconds > 0 && cpuSeconds !== null && machine.cpu_count
                        && cpuSeconds >= previous.cpuSeconds
          ? (cpuSeconds - previous.cpuSeconds) / wallSeconds / machine.cpu_count
          : null;
        MACHINE_SAMPLES[machine.container_id] = { cpuSeconds: machine.cpu_usage_seconds, askedAt: askedAt, cpuRate: cpuRate };
      });
      PANEL_MACHINES = machines;
      if (!MACHINE_ACTION_IN_FLIGHT) {
        meta.className = "box";
        meta.textContent = machines.machines.length + " containers on this host · "
          + machines.machines.filter((machine) => machine.own_project).length + " of "
          + (machines.compose_project || "no compose project") + " · polled every "
          + machines.poll_interval_seconds + "s while this panel is open · engine read "
          + machines.generated_at_utc + " UTC";
      }
      renderMachines();
      renderNetworks(networks);
      renderVolumes(volumes);
      renderImage(image);
      renderEvents(events);
    })
    .catch((error) => {
      clearPanelViews();
      meta.className = "box err";
      meta.textContent = "could not load /devops/api (" + error.message + ") — run `make docker-up`";
    })
    .finally(() => { PANEL_POLL_IN_FLIGHT = false; });
}

function initPanel() {
  fetchPanelRoute("machines")
    .then((machines) => {
      setInterval(() => {
        if (document.visibilityState === "visible") renderPanel();
      }, machines.poll_interval_seconds * MILLISECONDS_PER_SECOND);
      renderPanel();
    })
    .catch((error) => {
      clearPanelViews();
      const meta = document.getElementById("panel-meta");
      meta.className = "box err";
      meta.textContent = "could not load /devops/api/machines (" + error.message + ") — run `make docker-up`";
      /* the cadence is the server's to publish, so a panel that never reached it has no interval to
         install; it retries when the tab is next looked at rather than staying dead until a reload */
      document.addEventListener("visibilitychange", function retryPanel() {
        if (document.visibilityState !== "visible") return;
        document.removeEventListener("visibilitychange", retryPanel);
        initPanel();
      });
    });
}

initPanel();
