"""The crawler's one surface of configuration: the snapshot's path, the mission and the vendors kept by hand, the
reports directory in the status store — entirely generated: reset and written by every crawl, never committed — where
one controlled file's report lies in it, and the vendor's time limit. The root of the tree and the sheet are the package's
own, in `module_skills/config.py`."""

import os
from pathlib import Path

# twice by extraction
STORE_STATUS_DIR = Path(os.environ["STORE_STATUS_DIR"]).resolve()
SKILLS_STATUS_JSON_PATH = STORE_STATUS_DIR / "skills_status.json"   # the snapshot; the dashboard reads it
SUB_MODULE_DIR = Path(__file__).resolve().parent
CRAWLERS_MISSION_MD_PATH = SUB_MODULE_DIR / "crawlers_mission.md"
VENDORS_FOR_CRAWLING_TOML_PATH = SUB_MODULE_DIR / "vendors_for_crawling.toml"
REPORTS_DIR = STORE_STATUS_DIR / "reports_after_crawled_files"     # <path>.report.md, one current report per file
AGENT_TIMEOUT_SECONDS = 30 * 60


def report_path(key: str) -> Path:
    """The one current report of a controlled file, by its key — its path from the root of the tree."""
    return REPORTS_DIR / f"{key}.report.md"
