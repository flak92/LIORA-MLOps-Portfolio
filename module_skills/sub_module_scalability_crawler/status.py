"""The crawler's snapshot, `skills_status.json`: the current state of every controlled file of the files matrix —
`pending` before the first file of a crawl, `running` while its crawl runs, `done` once its report is written,
`failed` otherwise, `interrupted` where Ctrl-C ended its crawl —
with the vendor, the time it finished and where its report is. Nothing historical: the snapshot is overwritten
whole, through a temporary file and `os.replace`, so the dashboard never reads a part of it."""

import json

from . import config
from .. import sync


def row(key: str, state: str = "pending", vendor: str | None = None, finished_at_utc: str | None = None,
        report: str | None = None) -> dict:
    """One file of the snapshot: `report` only once it is `done`, every missing value `null`."""
    return {"path": key, "state": state, "vendor": vendor, "finished_at_utc": finished_at_utc,
            "report": report}


def write_skills_status(rows: list[dict]) -> None:
    """The snapshot, whole, its rows sorted by path."""
    files = sorted(rows, key=lambda file_row: file_row["path"])
    sync.write_text(config.SKILLS_STATUS_JSON_PATH, json.dumps({"files": files}, sort_keys=True, indent=1) + "\n")
