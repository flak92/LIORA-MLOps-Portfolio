"""Measure one stage of a run from outside: the three pipeline stores before, the command, the three after — one record.

    RUN_ID=<run_id> python3 record.py <stage> <command…>

The recorder knows no module. Given the execution name RUN_ID, it lists the three pipeline stores named below
(STORE_RAW_1M_DIR, STORE_ASSETS_ARTIFACTS_DIR, STORE_STATUS_DIR — path, size and mtime of every file), runs the command
with its output passed through, lists them again, and writes store/run_records/<RUN_ID>/<stage>.json: when the stage
started and ended, how it exited, and what it added, changed and removed in the stores. Its exit code is the command's.
This is what a task scheduler records about a task — what it wrote — and nothing a stage could say about itself.
STORE_TRIALS_DIR is deliberately absent: a trial ledger is the stage's own account of its search, which is the one thing
this recorder never reads. STORE_RUN_RECORDS_DIR is where the record goes, and no stage writes it.

Then it writes store/run_records/index.json again from the store's listing — every run with a record, newest first, each
with its records — the one file the page reads to find a run. Both files are written whole: beside their place, then
moved onto it, so a reader finds the old file or the new one and never half of one. It takes no lock: no second
recorder writes the index at once (PRE-AWS-SOLUTION-ONE-OPERATION-WRITES-AT-A-TIME-AND-NOTHING-LOCKS)."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

STORES = {
    "raw_1m": "STORE_RAW_1M_DIR",
    "assets_artifacts": "STORE_ASSETS_ARTIFACTS_DIR",
    "status": "STORE_STATUS_DIR",
}


def listing(root: Path) -> dict[str, tuple[int, int]]:
    """Every file under a store as path relative to it -> (size_bytes, mtime_ns); a file that vanishes between the walk
    and its stat — a temporary file a process beside the run moves onto its place, a search in its tmux session or a
    crawl — is simply not there."""
    out = {}
    for path in root.rglob("*"):
        try:
            info = path.stat()
        except OSError:
            continue
        if stat.S_ISREG(info.st_mode):
            out[str(path.relative_to(root))] = (info.st_size, info.st_mtime_ns)
    return out


def store_diff(store: str, before: dict, after: dict) -> dict[str, list]:
    """What the stage did to one store: added, changed (size or mtime moved), removed — each sorted by path."""
    def row(path):
        size_bytes, mtime_ns = after[path]
        return {"store": store, "path": path, "size_bytes": size_bytes, "mtime_ns": mtime_ns}
    return {
        "added": [row(path) for path in sorted(after.keys() - before.keys())],
        "changed": [row(path) for path in sorted(after.keys() & before.keys()) if after[path] != before[path]],
        "removed": [{"store": store, "path": path} for path in sorted(before.keys() - after.keys())],
    }


def write_json(path: Path, payload: dict) -> None:
    """The file whole or not at all: written beside its place, then moved onto it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f".{path.name}.partial")
    partial.write_text(json.dumps(payload, sort_keys=True, indent=1) + "\n", encoding="utf-8")
    os.replace(partial, path)


def build_run_index(run_records: Path) -> dict:
    """Every run of the store that holds a record, newest first — a run id sorts by its time — each with the paths of
    its records, relative to its directory, in path order."""
    records: dict[str, list[str]] = {}
    for path in run_records.glob("*/*.json"):
        records.setdefault(path.parent.name, []).append(path.name)
    return {"generated_at_utc": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S"),
            "runs": [{"run_id": run_id, "records": sorted(records[run_id])} for run_id in sorted(records, reverse=True)]}


def main() -> int:
    stage, command = sys.argv[1], sys.argv[2:]
    run_id = os.environ["RUN_ID"]
    roots = {store: Path(os.environ[variable]) for store, variable in STORES.items()}
    run_records = Path(os.environ["STORE_RUN_RECORDS_DIR"])
    before = {store: listing(root) for store, root in roots.items()}
    started_at, started_monotonic = datetime.now(tz=UTC), time.monotonic()
    exit_code = subprocess.run(command).returncode
    ended_at, duration_seconds = datetime.now(tz=UTC), round(time.monotonic() - started_monotonic, 3)
    after = {store: listing(root) for store, root in roots.items()}
    diffs = [store_diff(store, before[store], after[store]) for store in STORES]
    record = {
        "run_id": run_id,
        "stage": stage,
        "command": " ".join(command),
        "exit_code": exit_code,
        "started_at_utc": started_at.strftime("%Y-%m-%d %H:%M:%S"),
        "ended_at_utc": ended_at.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_seconds": duration_seconds,
        "store_diff": {state: [row for diff in diffs for row in diff[state]] for state in ("added", "changed", "removed")},
    }
    out = run_records / run_id / f"{stage}.json"
    write_json(out, record)
    write_json(run_records / "index.json", build_run_index(run_records))
    print(f"{stage}: exit {exit_code} in {duration_seconds}s — "
          f"+{len(record['store_diff']['added'])} ~{len(record['store_diff']['changed'])} -{len(record['store_diff']['removed'])} files -> {out}",
          flush=True)
    return exit_code if exit_code >= 0 else 128 - exit_code   # a signal, in the shell's own convention


if __name__ == "__main__":
    raise SystemExit(main())
