"""One stage of a run, recorded as it executes — the stage reporting itself.

The Makefile wraps every stage command with this module, inside whatever container that stage
already runs in:

    python -m module_monitoring.record <run_id> python -m module_ml.hpo --tickers BTC

The wrapped process is the measured object, and its cost comes from `wait4`'s rusage: exact
CPU and an exact peak resident set, neither of them charged the page cache the cgroup counts.
Its data volume comes from /proc/<pid>/io read while the child is still alive, because a
zombie's io file is unreadable. The cgroup counters sampled beside it describe the CONTAINER
over the same window and never the stage — every one of those keys carries the `container_`
prefix, and the summary repeats why.

    --finalize <run_id>   the run's own role, on the host: the readiness check, the manifest
                          and the summary, from the stage records the stages left behind
"""

from __future__ import annotations

import json
import os
import platform
import select
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from http import HTTPStatus
from pathlib import Path

from module_data import config as data_config
from module_ml import config as ml_config

from . import config
from .serve import load_cgroup_dir, load_host_memory_bytes, load_jsonl, load_text

BYTES_PER_KIBIBYTE = data_config.BYTES_PER_KIBIBYTE
NETWORK_PROC_PATH = Path("/proc/net/dev")
LOOPBACK_INTERFACE_NAME = "lo"

# what each stage leaves behind, by the module that runs it; the paths are the descriptors the
# owning config already publishes, never assembled here
STAGE_OUTPUT_DESCRIPTORS = {
    "module_data.download_binance": lambda ticker: [data_config.raw_symbol_dir(ticker, "binance")],
    "module_data.download_bybit": lambda ticker: [data_config.raw_symbol_dir(ticker, "bybit")],
    "module_data.ingest": lambda ticker: [data_config.research_ohlcv_duckdb(ticker)],
    "module_data.status": lambda ticker: [data_config.MODULE_MONITORING_DATA_STATUS_JSON_PATH],
    "module_ml.bars": lambda ticker: [data_config.research_ohlcv_duckdb(ticker)],
    "module_ml.features": lambda ticker: [ml_config.features_parquet(ticker, tf) for tf in ml_config.HIERARCHY_TIMEFRAMES],
    "module_ml.labels": lambda ticker: [ml_config.label_events_parquet(ticker)],
    "module_ml.hpo": lambda ticker: [ml_config.parameters_json(ticker)],
    "module_ml.train": lambda ticker: [ml_config.oos_predictions_parquet(ticker), ml_config.model_evaluation_json(ticker)],
    "module_ml.strategy": lambda ticker: [ml_config.strategy_evaluation_json(ticker)],
    "module_ml.status": lambda ticker: [ml_config.MODULE_MONITORING_ML_STATUS_JSON_PATH, ml_config.asset_readme_md(ticker)],
}

STAGE_INPUT_NOTES = {
    "module_data.download_binance": "Binance USDS-M public HTTP API",
    "module_data.download_bybit": "Bybit Linear public HTTP API",
    "module_data.ingest": "both venue ZIP trees",
    "module_data.status": "the asset databases",
    "module_ml.bars": "ohlcv_1m_canonical",
    "module_ml.features": "ohlcv_15m/1h/4h_canonical",
    "module_ml.labels": "canonical 1m path + ohlcv_1h_canonical",
    "module_ml.hpo": "X + Y",
    "module_ml.train": "X + Y + the search result",
    "module_ml.strategy": "out-of-sample predictions + the canonical 1m path",
    "module_ml.status": "every per-asset research artifact",
}


def module_of(command: list[str]) -> str:
    """The `-m` argument of the wrapped command — the module that is the stage."""
    return command[command.index("-m") + 1]


def stage_of(module: str) -> str:
    """`module_data.download_binance` -> `data-download-binance`, the Makefile's target grammar."""
    package, _, name = module.partition(".")
    return f"{package.removeprefix('module_')}-{name.replace('_', '-')}"


def recorded_tickers(command: list[str]) -> list[str]:
    """The assets this stage covered: what its command was told, else the one its container is,
    else the whole basket for a basket-wide stage in the one-off container."""
    if "--tickers" in command:
        return data_config.parse_tickers(command[command.index("--tickers") + 1])
    asset = os.environ.get("ASSET")
    return [asset] if asset else list(data_config.TICKERS)


def docker_service() -> str:
    """The compose service by its one distinguishing environment variable, as the config names it."""
    asset = os.environ.get("ASSET")
    return config.asset_service(asset) if asset else config.PIPELINE_SERVICE


def load_network_bytes() -> tuple[int, int]:
    """Received and transmitted bytes over every interface of this container but loopback."""
    received = transmitted = 0
    for line in NETWORK_PROC_PATH.read_text(encoding="utf-8").splitlines()[2:]:
        name, _, counters = line.partition(":")
        if name.strip() == LOOPBACK_INTERFACE_NAME:
            continue
        fields = counters.split()
        received += int(fields[0])
        transmitted += int(fields[8])
    return received, transmitted


def container_counters() -> dict:
    """The container's own cgroup and interfaces — the whole container, never one stage."""
    own = load_cgroup_dir()
    memory_max = load_text(own / "memory.max")
    cpu_stat = dict(line.split() for line in load_text(own / "cpu.stat").splitlines())
    memory_stat = dict(line.split()[:2] for line in load_text(own / "memory.stat").splitlines())
    disk_read_bytes = disk_write_bytes = 0
    io_stat = load_text(own / "io.stat") or ""
    for line in io_stat.splitlines():
        fields = dict(field.split("=") for field in line.split()[1:])
        disk_read_bytes += int(fields.get("rbytes", 0))
        disk_write_bytes += int(fields.get("wbytes", 0))
    received, transmitted = load_network_bytes()
    return {
        "container_cpu_usage_seconds": int(cpu_stat["usage_usec"]) / config.MICROSECONDS_PER_SECOND,
        "container_cpu_user_seconds": int(cpu_stat["user_usec"]) / config.MICROSECONDS_PER_SECOND,
        "container_cpu_system_seconds": int(cpu_stat["system_usec"]) / config.MICROSECONDS_PER_SECOND,
        # memory.current is anon + page cache + slab; the anonymous part is the only one a stage owns
        "container_memory_charged_bytes": config.to_int(load_text(own / "memory.current")),
        "container_memory_anonymous_bytes": int(memory_stat["anon"]),
        "container_memory_cache_bytes": int(memory_stat["file"]),
        "container_memory_limit_bytes": (load_host_memory_bytes() if memory_max == "max" else config.to_int(memory_max)),
        "container_pids_current": config.to_int(load_text(own / "pids.current")),
        "container_disk_read_bytes": disk_read_bytes,
        "container_disk_write_bytes": disk_write_bytes,
        "container_network_received_bytes": received,
        "container_network_transmitted_bytes": transmitted,
    }


def process_counters(pid: int) -> dict | None:
    """The wrapped process while it still lives; None once it is a zombie or gone."""
    try:
        io = dict(line.split(": ") for line in Path(f"/proc/{pid}/io").read_text().splitlines())
        status = Path(f"/proc/{pid}/status").read_text()
    except (OSError, ValueError):
        return None
    fields = {line.split(":")[0]: line.split(":", 1)[1].strip() for line in status.splitlines() if ":" in line}
    return {
        "process_read_chars": int(io["rchar"]),
        "process_write_chars": int(io["wchar"]),
        "process_read_bytes": int(io["read_bytes"]),
        "process_write_bytes": int(io["write_bytes"]),
        "process_memory_resident_bytes": int(fields["VmRSS"].split()[0]) * BYTES_PER_KIBIBYTE,
        "process_thread_count": int(fields["Threads"]),
        "process_ppid": int(fields["PPid"]),
    }


def output_block(module: str, tickers: list[str]) -> list[dict]:
    """What the stage left on disk for every asset it covered: the path, its size and its mtime —
    never a hash of a database."""
    descriptor = STAGE_OUTPUT_DESCRIPTORS.get(module)
    if descriptor is None:
        return []
    written = []
    for path in [path for ticker in tickers for path in descriptor(ticker)]:
        if path.is_dir():
            files = sorted(path.glob("*"))
            written.append({"path": str(path.relative_to(data_config.REPO_ROOT)),
                            "file_count": len(files),
                            "size_bytes": sum(f.stat().st_size for f in files),
                            "mtime_ns": max((f.stat().st_mtime_ns for f in files), default=None)})
        elif path.exists():
            stat = path.stat()
            written.append({"path": str(path.relative_to(data_config.REPO_ROOT)),
                            "size_bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns})
        else:
            written.append({"path": str(path.relative_to(data_config.REPO_ROOT)),
                            "size_bytes": None, "mtime_ns": None})
    return written


def append_json_line(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def record_stage(run_id: str, command: list[str]) -> int:
    """Run the stage, sample the container beside it, and leave one record. Returns its exit code."""
    module = module_of(command)
    stage = stage_of(module)
    tickers = recorded_tickers(command)
    log_path = config.stage_log(run_id, stage, docker_service())
    log_path.parent.mkdir(parents=True, exist_ok=True)

    started_at = datetime.now(tz=UTC)
    started_monotonic = time.monotonic()
    counters_at_start = container_counters()

    read_fd, write_fd = os.pipe()
    pid = os.posix_spawnp(
        command[0], command, os.environ,
        file_actions=[(os.POSIX_SPAWN_DUP2, write_fd, 1), (os.POSIX_SPAWN_DUP2, write_fd, 2)],
    )
    os.close(write_fd)

    sample_count = 0
    last_process = None
    memory_charged_peak_bytes = counters_at_start["container_memory_charged_bytes"]
    deadline = started_monotonic + config.SAMPLE_INTERVAL_SECONDS
    with log_path.open("wb") as log, os.fdopen(read_fd, "rb", buffering=0) as pipe:
        open_pipe = True
        while open_pipe:
            timeout = max(0.0, min(deadline - time.monotonic(), config.PROCESS_POLL_INTERVAL_SECONDS))
            readable = select.select([pipe], [], [], timeout)[0]
            process = process_counters(pid)
            if process is not None:
                last_process = process
            if readable:
                chunk = pipe.read(config.PIPE_READ_SIZE_BYTES)
                if chunk:
                    log.write(chunk)
                    log.flush()
                    sys.stdout.buffer.write(chunk)
                    sys.stdout.flush()
                else:
                    open_pipe = False
            if time.monotonic() >= deadline:
                sample = container_counters()
                memory_charged_peak_bytes = max(memory_charged_peak_bytes,
                                                sample["container_memory_charged_bytes"])
                append_json_line(config.resources_jsonl(run_id), {
                    "timestamp_utc": config.to_utc_text(datetime.now(tz=UTC)),
                    "monotonic_seconds": round(time.monotonic() - started_monotonic, 3),
                    "run_id": run_id, "stage": stage,
                    "docker_service": docker_service(), "pid": pid,
                    **sample, **(last_process or {}),
                })
                sample_count += 1
                deadline += config.SAMPLE_INTERVAL_SECONDS

    # EOF on the pipe means every write end is closed, so the child is exiting: one blocking reap,
    # and its rusage is the kernel's own accounting of the process that call took
    _, status, rusage = os.wait4(pid, 0)
    exit_code = os.waitstatus_to_exitcode(status)
    counters_at_end = container_counters()
    ended_at = datetime.now(tz=UTC)
    record = {
        "run_id": run_id, "tickers": tickers, "stage": stage, "module": module,
        "docker_service": docker_service(), "container_id": platform.node(),
        "pid": pid, "command": " ".join(command), "exit_code": exit_code,
        "started_at_utc": config.to_utc_text(started_at), "ended_at_utc": config.to_utc_text(ended_at),
        "duration_seconds": round(time.monotonic() - started_monotonic, 3),
        # the stage itself, from the kernel's own accounting of the process it reaped
        "process_cpu_seconds": round(rusage.ru_utime + rusage.ru_stime, 3),
        "process_user_cpu_seconds": round(rusage.ru_utime, 3),
        "process_system_cpu_seconds": round(rusage.ru_stime, 3),
        "process_memory_peak_bytes": rusage.ru_maxrss * BYTES_PER_KIBIBYTE,
        "process_major_fault_count": rusage.ru_majflt,
        "process_disk_read_bytes": rusage.ru_inblock * 512,
        "process_disk_write_bytes": rusage.ru_oublock * 512,
        **(last_process or {}),
        # the container over the same window — every reader is told which is which
        "container_cpu_seconds_delta": round(counters_at_end["container_cpu_usage_seconds"]
                                             - counters_at_start["container_cpu_usage_seconds"], 3),
        "container_memory_charged_peak_bytes": memory_charged_peak_bytes,
        "container_disk_read_bytes_delta": (counters_at_end["container_disk_read_bytes"]
                                            - counters_at_start["container_disk_read_bytes"]),
        "container_disk_write_bytes_delta": (counters_at_end["container_disk_write_bytes"]
                                             - counters_at_start["container_disk_write_bytes"]),
        "container_network_received_bytes_delta": (counters_at_end["container_network_received_bytes"]
                                                   - counters_at_start["container_network_received_bytes"]),
        "container_network_transmitted_bytes_delta": (counters_at_end["container_network_transmitted_bytes"]
                                                      - counters_at_start["container_network_transmitted_bytes"]),
        "sample_count": sample_count,
        "input": STAGE_INPUT_NOTES.get(module),
        "output": output_block(module, tickers),
    }
    append_json_line(config.events_jsonl(run_id), record)
    return exit_code


def load_stage_records(run_id: str) -> list[dict]:
    """Every stage of the run in start order. The file holds arrival order, and with one container
    per asset appending to it, arrival order is not the order the stages started."""
    return sorted(load_jsonl(config.events_jsonl(run_id)), key=lambda record: record["started_at_utc"])


def shell_output(command: list[str]) -> str | None:
    answer = subprocess.run(command, capture_output=True, text=True)
    return answer.stdout.strip() if answer.returncode == 0 else None


def container_identity(service: str) -> dict:
    """What the host knows about the container a stage ran in; None for a one-off already gone."""
    container_id = shell_output(["docker", "compose", "ps", "-q", service])
    if not container_id:
        return {"docker_service": service, "container_id": None, "docker_image": None,
                "docker_image_id": None, "memory_limit_bytes": None, "cpu_max": None}
    inspected = shell_output(["docker", "inspect", container_id, "--format",
                              "{{.Config.Image}}\t{{.Image}}\t{{.HostConfig.Memory}}\t{{.HostConfig.NanoCpus}}"])
    image, image_id, memory, nano_cpus = (inspected or "\t\t\t").split("\t")
    return {
        "docker_service": service, "container_id": container_id[:12],
        "docker_image": image or None, "docker_image_id": image_id or None,
        "memory_limit_bytes": int(memory) if memory and memory != "0" else None,
        "cpu_max": "max" if nano_cpus in ("", "0") else nano_cpus,
    }


def fetch_dashboard_route(url: str) -> dict:
    """One route of the dashboard as url, status code and body size; status 0 when nothing answered."""
    try:
        with urllib.request.urlopen(url, timeout=config.DASHBOARD_READY_FETCH_TIMEOUT_SECONDS) as answer:
            return {"url": url, "status_code": answer.status, "body_bytes": len(answer.read())}
    except urllib.error.HTTPError as error:
        return {"url": url, "status_code": error.code, "body_bytes": len(error.read())}
    except OSError:
        return {"url": url, "status_code": 0, "body_bytes": 0}


def fetch_dashboard_ready() -> dict:
    """The readiness check that closes a run: the dashboard's own registry, then one question per
    asset through its proxy. The run is ready only when the registry and every asset answered 200;
    url and status_code stay at this level because they are what the Lifecycle tab prints."""
    port = os.environ.get("PORT", str(config.CONTAINER_PORT))
    started_at = datetime.now(tz=UTC)
    started_monotonic = time.monotonic()
    registry = fetch_dashboard_route(config.dashboard_registry_url(port))
    assets = [fetch_dashboard_route(config.dashboard_asset_status_url(port, ticker))
              for ticker in data_config.TICKERS]
    return {
        "stage": "dashboard-ready",
        "url": registry["url"], "status_code": registry["status_code"], "body_bytes": registry["body_bytes"],
        "assets": assets,
        "exit_code": 0 if all(answer["status_code"] == HTTPStatus.OK for answer in (registry, *assets)) else 1,
        "started_at_utc": config.to_utc_text(started_at),
        "ended_at_utc": config.to_utc_text(datetime.now(tz=UTC)),
        "duration_seconds": round(time.monotonic() - started_monotonic, 3),
    }


def summary_row(record: dict) -> dict:
    """One stage as the table reads it: the process columns are the stage, the container columns are not."""
    cpu_seconds = record["process_cpu_seconds"]
    wall_seconds = record["duration_seconds"]
    return {
        "stage": record["stage"],
        "docker_service": record["docker_service"],
        "start_utc": record["started_at_utc"], "end_utc": record["ended_at_utc"],
        "wall_seconds": wall_seconds,
        "cpu_seconds": cpu_seconds,
        "cpu_core_hours": round(cpu_seconds / 3600.0, 6),
        "cpu_share": round(cpu_seconds / wall_seconds, 3) if wall_seconds else None,
        "memory_peak_bytes": record["process_memory_peak_bytes"],
        "read_chars": record.get("process_read_chars"),
        "write_chars": record.get("process_write_chars"),
        "disk_read_bytes": record["process_disk_read_bytes"],
        "disk_write_bytes": record["process_disk_write_bytes"],
        "container_network_received_bytes_delta": record["container_network_received_bytes_delta"],
        "container_network_transmitted_bytes_delta": record["container_network_transmitted_bytes_delta"],
        "container_memory_charged_peak_bytes": record["container_memory_charged_peak_bytes"],
        "sample_count": record["sample_count"],
        "pid": record["pid"], "command": record["command"],
        "exit_code": record["exit_code"],
        "input": record.get("input"), "output": record.get("output", []),
    }


# what each published number is, and is not — the summary states it so a reader is never misled
MEASUREMENT_NOTES = {
    "cpu_seconds": "the stage process and every descendant it reaped, from wait4 rusage — exact, not sampled",
    "memory_peak_bytes": "peak resident set of the stage process, from wait4 ru_maxrss; the page cache the "
                         "container is charged is NOT counted against the stage",
    "container_memory_charged_peak_bytes": "the whole container, page cache included, and it only ever grows "
                                           "while the 5 GiB ceiling is far away — a run high-water mark, "
                                           "never a stage cost",
    "read_chars/write_chars": "bytes the stage moved through read()/write(), independent of the page cache; "
                              "disk_read_bytes/disk_write_bytes are the physical blocks and are both "
                              "cache-dependent and delayed by writeback (up to 30 s on this host)",
    "container_network_*": "container-wide, so it also carries the dashboard's polls of /status; network "
                           "cannot be attributed to a stage from /proc, and is not claimed to be",
    "orchestration_seconds": "wall time between stages: docker exec setup and teardown, measured, not hidden",
    "sample_coverage": "the 1 s series cannot reach a stage shorter than one interval; sample_coverage names "
                       "those stages, and their cpu_seconds and memory_peak_bytes are exact anyway, because "
                       "rusage is the kernel's accounting of the reaped process and never a sample",
}


def sample_coverage_block(run_id: str, rows: list[dict]) -> dict:
    """What the 1 s series does and does not cover, stated rather than assumed: a stage shorter than
    one interval cannot hold a sample, and its numbers come from rusage, which never sampled."""
    samples = load_jsonl(config.resources_jsonl(run_id))
    moments = sorted(config.to_utc_datetime(sample["timestamp_utc"]) for sample in samples)
    # the gap is measured inside one container's own series: two containers sampling in parallel
    # would otherwise fill each other's gaps and the number would stop meaning anything
    by_service = {}
    for sample in samples:
        by_service.setdefault(sample["docker_service"], []).append(config.to_utc_datetime(sample["timestamp_utc"]))
    gaps = [(later - earlier).total_seconds()
            for moments_of_service in by_service.values()
            for earlier, later in zip(sorted(moments_of_service), sorted(moments_of_service)[1:])]
    return {
        "sample_interval_seconds": config.SAMPLE_INTERVAL_SECONDS,
        "sample_count": len(samples),
        "first_sample_utc": config.to_utc_text(moments[0]) if moments else None,
        "last_sample_utc": config.to_utc_text(moments[-1]) if moments else None,
        "max_sample_gap_seconds": round(max(gaps), 3) if gaps else None,
        # a stage the series cannot reach; its cost is still exact, because rusage does not sample
        "stages_without_samples": [row["stage"] for row in rows if row["sample_count"] == 0],
    }


def write_summary(run_id: str, readiness: dict, status: str) -> dict:
    records = load_stage_records(run_id)
    rows = [summary_row(record) for record in records]
    total_cpu_seconds = round(sum(row["cpu_seconds"] for row in rows), 3)
    total_stage_seconds = round(sum(row["wall_seconds"] for row in rows), 3)
    first_start = min((row["start_utc"] for row in rows), default=None)
    last_end = max((row["end_utc"] for row in rows), default=None)
    total_wall_seconds = None
    if first_start and last_end:
        total_wall_seconds = round(
            (datetime.fromisoformat(last_end).replace(tzinfo=UTC)
             - datetime.fromisoformat(first_start).replace(tzinfo=UTC)).total_seconds(), 3)
    bottleneck = max(rows, key=lambda row: row["wall_seconds"], default=None)
    summary = {
        "run_id": run_id, "status": status,
        "generated_at_utc": config.to_utc_text(datetime.now(tz=UTC)),
        "stage_count": len(rows),
        "first_stage_start_utc": first_start, "last_stage_end_utc": last_end,
        "total_wall_seconds": total_wall_seconds,
        "total_stage_seconds": total_stage_seconds,
        "orchestration_seconds": (round(total_wall_seconds - total_stage_seconds, 3)
                                  if total_wall_seconds is not None else None),
        "total_cpu_seconds": total_cpu_seconds,
        "total_cpu_core_hours": round(total_cpu_seconds / 3600.0, 6),
        "global_memory_peak_bytes": max((row["memory_peak_bytes"] for row in rows), default=None),
        "bottleneck_stage": bottleneck["stage"] if bottleneck else None,
        "failed_stage": next((row["stage"] for row in rows if row["exit_code"] != 0), None),
        "dashboard_ready": readiness,
        "sample_coverage": sample_coverage_block(run_id, rows),
        "measurement_notes": MEASUREMENT_NOTES,
        "stages": rows,
    }
    config.summary_json(run_id).write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n",
                                           encoding="utf-8")
    return summary


def write_manifest(run_id: str, summary: dict) -> None:
    manifest = {
        "run_id": run_id, "tickers": list(data_config.TICKERS),
        "git_commit": shell_output(["git", "rev-parse", "HEAD"]),
        "git_commit_short": shell_output(["git", "rev-parse", "--short", "HEAD"]),
        "working_tree_clean": shell_output(["git", "status", "--porcelain"]) == "",
        "started_at_utc": summary["first_stage_start_utc"],
        "finished_at_utc": summary["last_stage_end_utc"],
        "duration_seconds": summary["total_wall_seconds"],
        "status": summary["status"],
        "exit_code": 0 if summary["status"] == "completed" else 1,
        "failed_stage": summary["failed_stage"],
        "kernel": platform.release(),
        "cpu_count": os.cpu_count(),
        "host_load_average": os.getloadavg(),
        "asset_containers": [container_identity(config.asset_service(ticker))
                             for ticker in data_config.TICKERS],
        "pipeline_container": container_identity(config.PIPELINE_SERVICE),
        "research_start_utc": ml_config.RESEARCH_START_UTC,
        "research_end_utc": ml_config.RESEARCH_END_UTC,
        "data_window_start_utc": data_config.DATA_WINDOW_START_UTC,
        "sample_interval_seconds": config.SAMPLE_INTERVAL_SECONDS,
    }
    config.manifest_json(run_id).write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n",
                                            encoding="utf-8")


def finalize(run_id: str) -> int:
    records = load_stage_records(run_id)
    readiness = fetch_dashboard_ready()
    failed = (not records or any(record["exit_code"] != 0 for record in records)
              or readiness["exit_code"] != 0)
    summary = write_summary(run_id, readiness, "failed" if failed else "completed")
    write_manifest(run_id, summary)
    print(f"run {run_id}: {summary['stage_count']} stages, "
          f"{summary['total_wall_seconds']}s wall, {summary['total_cpu_seconds']}s cpu "
          f"({summary['total_cpu_core_hours']} core-hours), bottleneck {summary['bottleneck_stage']}, "
          f"dashboard HTTP {readiness['status_code']} -> {summary['status']}", flush=True)
    print(f"wrote {config.summary_json(run_id).relative_to(data_config.REPO_ROOT)}", flush=True)
    return 0 if not failed else 1


def main() -> int:
    argv = sys.argv[1:]
    if argv[0] == "--finalize":
        return finalize(argv[1])
    return record_stage(argv[0], argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
