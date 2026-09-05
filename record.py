"""Measure one stage of a run from outside: the four stores before, the command, the four stores after — one record.

    python3 record.py <stage> <command…>

The recorder knows no module. It lists the four stores the launcher names (STORE_RAW_1M_DIR, STORE_ASSETS_ARTIFACTS_DIR,
STORE_RUN_RECORDS_DIR, STORE_STATUS_DIR — path, size and mtime of every file), runs the command with its output passed
through, lists them again, and writes store_run_records/<RUN_ID>/<stage>.json: when the stage started and ended, how it
exited, and what it added, changed and removed in the stores. Its exit code is the command's. This is what a task scheduler
records about a task — what it wrote — and nothing a stage could say about itself."""

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
    "run_records": "STORE_RUN_RECORDS_DIR",
    "status": "STORE_STATUS_DIR",
}


def listing(root: Path) -> dict[str, tuple[int, int]]:
    """Every file under a store as path relative to it -> (size_bytes, mtime_ns); an absent store is empty, and a file that
    vanishes between the walk and its stat (a database's temporary file) is simply not there."""
    if not root.exists():
        return {}
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


def to_utc_text(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%d %H:%M:%S")


def main() -> int:
    if len(sys.argv) < 3:
        raise SystemExit("usage: python3 record.py <stage> <command…>")
    stage, command = sys.argv[1], sys.argv[2:]
    run_id = os.environ["RUN_ID"]
    roots = {store: Path(os.environ[variable]) for store, variable in STORES.items()}
    before = {store: listing(root) for store, root in roots.items()}
    started_at, started_monotonic = datetime.now(tz=UTC), time.monotonic()
    try:
        exit_code = subprocess.run(command).returncode
    except OSError as error:                      # the command itself could not start — recorded, like any failure
        print(error, file=sys.stderr, flush=True)
        exit_code = 127
    ended_at, duration_seconds = datetime.now(tz=UTC), round(time.monotonic() - started_monotonic, 3)
    after = {store: listing(root) for store, root in roots.items()}
    diffs = [store_diff(store, before[store], after[store]) for store in STORES]
    record = {
        "run_id": run_id,
        "stage": stage,
        "command": " ".join(command),
        "exit_code": exit_code,
        "started_at_utc": to_utc_text(started_at),
        "ended_at_utc": to_utc_text(ended_at),
        "duration_seconds": duration_seconds,
        "store_diff": {state: [row for diff in diffs for row in diff[state]] for state in ("added", "changed", "removed")},
    }
    out = roots["run_records"] / run_id / f"{stage}.json"   # written after the second listing, so it is never in its own diff
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, sort_keys=True, indent=1) + "\n", encoding="utf-8")
    print(f"{stage}: exit {exit_code} in {duration_seconds}s — "
          f"+{len(record['store_diff']['added'])} ~{len(record['store_diff']['changed'])} -{len(record['store_diff']['removed'])} files -> {out}",
          flush=True)
    return exit_code if exit_code >= 0 else 128 - exit_code   # a signal, in the shell's own convention


if __name__ == "__main__":
    raise SystemExit(main())
