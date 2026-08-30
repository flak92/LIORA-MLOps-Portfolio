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
from pathlib import Path

from module_data import config as data_config
from module_ml import config as ml_config

from .serve import (CONTAINER_PORT, MICROSECONDS_PER_SECOND, load_cgroup_dir, load_host_memory_bytes,
                    load_text, to_int, to_utc_text)

SAMPLE_INTERVAL_SECONDS = 1.0
# /proc/<pid>/io is unreadable once the child is a zombie, so it is polled far faster than the
# samples are written: a stage shorter than one sample interval still leaves its byte counts
PROCESS_POLL_INTERVAL_SECONDS = 0.05
BYTES_PER_KIBIBYTE = data_config.BYTES_PER_KIBIBYTE
PIPE_READ_SIZE_BYTES = 65536
READINESS_TIMEOUT_SECONDS = 5
LOOPBACK_DASHBOARD_URL = f"http://127.0.0.1:{CONTAINER_PORT}/containers"
NETWORK_PROC_PATH = Path("/proc/net/dev")
LOOPBACK_INTERFACE_NAME = "lo"

# what each stage leaves behind, by the module that runs it; the paths are the descriptors the
# owning config already publishes, never assembled here
STAGE_OUTPUT_DESCRIPTORS = {
    "module_data.download_binance": lambda t: [data_config.raw_symbol_dir(t, "binance")],
    "module_data.download_bybit": lambda t: [data_config.raw_symbol_dir(t, "bybit")],
    "module_data.ingest": lambda t: [data_config.research_ohlcv_duckdb(t)],
    "module_data.status": lambda t: [data_config.MODULE_MONITORING_DATA_STATUS_JSON_PATH],
    "module_ml.bars": lambda t: [data_config.research_ohlcv_duckdb(t)],
    "module_ml.features": lambda t: [ml_config.features_parquet(t, tf) for tf in ml_config.HIERARCHY_TIMEFRAMES],
    "module_ml.labels": lambda t: [ml_config.label_events_parquet(t)],
    "module_ml.hpo": lambda t: [ml_config.parameters_json(t)],
    "module_ml.train": lambda t: [ml_config.oos_predictions_parquet(t), ml_config.model_evaluation_json(t)],
    "module_ml.strategy": lambda t: [ml_config.strategy_evaluation_json(t)],
    "module_ml.status": lambda t: [ml_config.MODULE_MONITORING_ML_STATUS_JSON_PATH, ml_config.asset_readme_md(t)],
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


def recorded_ticker() -> str:
    """The asset this container is, or the first of the basket for a basket-wide stage."""
    return os.environ.get("ASSET") or data_config.TICKERS[0]


def docker_service() -> str:
    """The compose service by its one distinguishing environment variable, as serve.py names it."""
    asset = os.environ.get("ASSET")
    return f"asset-{asset.lower()}" if asset else "pipeline"


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
        "container_cpu_usage_seconds": int(cpu_stat["usage_usec"]) / MICROSECONDS_PER_SECOND,
        "container_cpu_user_seconds": int(cpu_stat["user_usec"]) / MICROSECONDS_PER_SECOND,
        "container_cpu_system_seconds": int(cpu_stat["system_usec"]) / MICROSECONDS_PER_SECOND,
        # memory.current is anon + page cache + slab; the anonymous part is the only one a stage owns
        "container_memory_charged_bytes": to_int(load_text(own / "memory.current")),
        "container_memory_anonymous_bytes": int(memory_stat["anon"]),
        "container_memory_cache_bytes": int(memory_stat["file"]),
        "container_memory_limit_bytes": (load_host_memory_bytes() if memory_max == "max" else to_int(memory_max)),
        "container_pids_current": to_int(load_text(own / "pids.current")),
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


def output_block(module: str, ticker: str) -> list[dict]:
    """What the stage left on disk: the path, its size and its mtime — never a hash of a database."""
    descriptor = STAGE_OUTPUT_DESCRIPTORS.get(module)
    if descriptor is None:
        return []
    written = []
    for path in descriptor(ticker):
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
    ticker = recorded_ticker()
    run_directory = data_config.run_dir(ticker, run_id)
    (run_directory / "logs").mkdir(parents=True, exist_ok=True)
    log_path = run_directory / "logs" / f"{stage}.log"

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
    deadline = started_monotonic + SAMPLE_INTERVAL_SECONDS
    with log_path.open("wb") as log, os.fdopen(read_fd, "rb", buffering=0) as pipe:
        open_pipe = True
        while True:
            timeout = max(0.0, min(deadline - time.monotonic(), PROCESS_POLL_INTERVAL_SECONDS))
            readable = select.select([pipe], [], [], timeout)[0] if open_pipe else []
            process = process_counters(pid)
            if process is not None:
                last_process = process
            if readable:
                chunk = pipe.read(PIPE_READ_SIZE_BYTES)
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
                append_json_line(run_directory / "resources.jsonl", {
                    "timestamp_utc": to_utc_text(datetime.now(tz=UTC)),
                    "monotonic_seconds": round(time.monotonic() - started_monotonic, 3),
                    "run_id": run_id, "ticker": ticker, "stage": stage,
                    "docker_service": docker_service(), "pid": pid,
                    **sample, **(last_process or {}),
                })
                sample_count += 1
                deadline += SAMPLE_INTERVAL_SECONDS
            waited_pid, status, rusage = os.wait4(pid, os.WNOHANG)
            if waited_pid and not open_pipe:
                break

    exit_code = os.waitstatus_to_exitcode(status)
    counters_at_end = container_counters()
    ended_at = datetime.now(tz=UTC)
    record = {
        "run_id": run_id, "ticker": ticker, "stage": stage, "module": module,
        "docker_service": docker_service(), "container_id": platform.node(),
        "pid": pid, "command": " ".join(command), "exit_code": exit_code,
        "started_at_utc": to_utc_text(started_at), "ended_at_utc": to_utc_text(ended_at),
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
        "output": output_block(module, ticker),
    }
    append_json_line(run_directory / "events.jsonl", record)
    return exit_code


def load_stage_records(run_directory: Path) -> list[dict]:
    events = run_directory / "events.jsonl"
    if not events.exists():
        return []
    return [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines() if line.strip()]


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


def fetch_dashboard_ready(ticker: str) -> dict:
    """The readiness check that closes a run: the dashboard answering for the asset."""
    port = os.environ.get("PORT", str(CONTAINER_PORT))
    url = f"http://127.0.0.1:{port}/containers/{ticker}/status"
    started_at = datetime.now(tz=UTC)
    started_monotonic = time.monotonic()
    try:
        with urllib.request.urlopen(url, timeout=READINESS_TIMEOUT_SECONDS) as answer:
            status_code, body_bytes = answer.status, len(answer.read())
    except urllib.error.HTTPError as error:
        status_code, body_bytes = error.code, len(error.read())
    except OSError:
        status_code, body_bytes = 0, 0
    return {
        "stage": "dashboard-ready", "url": url, "status_code": status_code,
        "body_bytes": body_bytes, "exit_code": 0 if status_code == 200 else 1,
        "started_at_utc": to_utc_text(started_at),
        "ended_at_utc": to_utc_text(datetime.now(tz=UTC)),
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


def sample_coverage_block(run_directory: Path, rows: list[dict]) -> dict:
    """What the 1 s series does and does not cover, stated rather than assumed: a stage shorter than
    one interval cannot hold a sample, and its numbers come from rusage, which never sampled."""
    samples = [json.loads(line) for line in
               (run_directory / "resources.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()] \
        if (run_directory / "resources.jsonl").exists() else []
    moments = sorted(datetime.fromisoformat(sample["timestamp_utc"]).replace(tzinfo=UTC) for sample in samples)
    gaps = [(later - earlier).total_seconds() for earlier, later in zip(moments, moments[1:])]
    return {
        "sample_interval_seconds": SAMPLE_INTERVAL_SECONDS,
        "sample_count": len(samples),
        "first_sample_utc": to_utc_text(moments[0]) if moments else None,
        "last_sample_utc": to_utc_text(moments[-1]) if moments else None,
        "max_sample_gap_seconds": round(max(gaps), 3) if gaps else None,
        # a stage the series cannot reach; its cost is still exact, because rusage does not sample
        "stages_without_samples": [row["stage"] for row in rows if row["sample_count"] == 0],
    }


def write_summary(run_directory: Path, run_id: str, ticker: str, readiness: dict, status: str) -> dict:
    records = load_stage_records(run_directory)
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
        "run_id": run_id, "ticker": ticker, "status": status,
        "generated_at_utc": to_utc_text(datetime.now(tz=UTC)),
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
        "sample_coverage": sample_coverage_block(run_directory, rows),
        "measurement_notes": MEASUREMENT_NOTES,
        "stages": rows,
    }
    (run_directory / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n",
                                                encoding="utf-8")
    return summary


def write_manifest(run_directory: Path, run_id: str, ticker: str, summary: dict) -> None:
    manifest = {
        "run_id": run_id, "ticker": ticker,
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
        "asset_container": container_identity(f"asset-{ticker.lower()}"),
        "pipeline_container": container_identity("pipeline"),
        "research_start_utc": ml_config.RESEARCH_START_UTC,
        "research_end_utc": ml_config.RESEARCH_END_UTC,
        "data_window_start_utc": data_config.DATA_WINDOW_START_UTC,
        "sample_interval_seconds": SAMPLE_INTERVAL_SECONDS,
    }
    (run_directory / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n",
                                                 encoding="utf-8")


def finalize(run_id: str) -> int:
    ticker = data_config.TICKERS[0]
    run_directory = data_config.run_dir(ticker, run_id)
    records = load_stage_records(run_directory)
    readiness = fetch_dashboard_ready(ticker)
    failed = (not records or any(record["exit_code"] != 0 for record in records)
              or readiness["exit_code"] != 0)
    summary = write_summary(run_directory, run_id, ticker, readiness, "failed" if failed else "completed")
    write_manifest(run_directory, run_id, ticker, summary)
    print(f"run {run_id}: {summary['stage_count']} stages, "
          f"{summary['total_wall_seconds']}s wall, {summary['total_cpu_seconds']}s cpu "
          f"({summary['total_cpu_core_hours']} core-hours), bottleneck {summary['bottleneck_stage']}, "
          f"dashboard HTTP {readiness['status_code']} -> {summary['status']}", flush=True)
    print(f"wrote {(run_directory / 'summary.json').relative_to(data_config.REPO_ROOT)}", flush=True)
    return 0 if not failed else 1


def main() -> int:
    argv = sys.argv[1:]
    if not argv:
        raise SystemExit("usage: record <run_id> <command...>  |  record --finalize <run_id>")
    if argv[0] == "--finalize":
        return finalize(argv[1])
    return record_stage(argv[0], argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
