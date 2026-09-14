"""The crawler's snapshot, store/status/skills_status.json: every file to_crawl.txt lists, how often it was crawled and
when last — a function of the list and the reports, read off the reports' headings and never a clock.

    python3 -B -m module_skills.sub_module_scalability_crawler.status      (make skills-status)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import config

REPORT_HEADING_PATTERN = re.compile(r"^## (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC · \S+ · [0-9a-f]+$", re.M)


def load_crawl_paths() -> list[str]:
    """The files to_crawl.txt names, in its order: a line ending in / stands for every file under it, in byte order, but
    the bytecode of __pycache__ and the reports this crawler wrote. An entry that names nothing, or a file that is not
    UTF-8, ends the program in one line."""
    paths = []
    for entry in filter(None, map(str.strip, config.TO_CRAWL_TXT_PATH.read_text(encoding="utf-8").splitlines())):
        if not (Path(entry).is_dir() if entry.endswith("/") else Path(entry).is_file()):
            raise SystemExit(f"to_crawl.txt: {entry} names nothing")
        found = sorted(str(path) for path in Path(entry).rglob("*") if path.is_file() and "__pycache__" not in path.parts
                       and config.REPORTS_AFTER_CRAWLED_FILES_DIR not in path.parents) if entry.endswith("/") else [entry]
        for path in found:
            try:
                Path(path).read_text(encoding="utf-8")
            except UnicodeDecodeError:
                raise SystemExit(f"to_crawl.txt: {entry} — {path} is not UTF-8")
        paths += found
    return list(dict.fromkeys(paths))


def report_path(path: str) -> Path:
    return config.REPORTS_AFTER_CRAWLED_FILES_DIR / f"{path}.md"


def build_skills_status() -> dict:
    rows = []
    for path in sorted(load_crawl_paths()):
        report = report_path(path)
        stamps = REPORT_HEADING_PATTERN.findall(report.read_text(encoding="utf-8")) if report.is_file() else []
        rows.append({"path": path, "report": str(report.relative_to(config.REPORTS_AFTER_CRAWLED_FILES_DIR.parent)),
                     "crawl_count": len(stamps), "last_crawled_utc": stamps[-1] if stamps else None})
    return {"files": rows}


def main() -> int:
    config.SKILLS_STATUS_JSON_PATH.write_text(json.dumps(build_skills_status(), sort_keys=True, indent=1) + "\n",
                                              encoding="utf-8")
    print(f"wrote {config.SKILLS_STATUS_JSON_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
