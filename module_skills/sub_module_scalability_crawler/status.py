"""The crawler's snapshot, `skills_status.json`: the current state of every controlled file of the files matrix —
`pending` before the first file of a crawl, `running` while its crawl runs, `done` once its report is written,
`failed` otherwise, `interrupted` where Ctrl-C ended its crawl —
with the vendor, the time it finished and where its report is. Nothing historical: the snapshot is overwritten
whole, through a temporary file and `os.replace`, so the dashboard never reads a part of it."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from . import config


def row(key: str, state: str = "pending", vendor: str | None = None, finished_at_utc: str | None = None,
        report: str | None = None) -> dict:
    """One file of the snapshot: `report` only once it is `done`, every missing value `null`."""
    return {"path": key, "state": state, "vendor": vendor, "finished_at_utc": finished_at_utc,
            "report": report if state == "done" else None}


def write_atomically(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
    os.replace(temporary, path)


def write_skills_status(rows: list[dict]) -> None:
    write_atomically(config.SKILLS_STATUS_JSON_PATH, json.dumps({"files": rows}, sort_keys=True, indent=1) + "\n")
