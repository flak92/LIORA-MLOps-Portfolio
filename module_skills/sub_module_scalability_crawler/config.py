"""The crawler's one surface of configuration: the snapshot's path, the files kept by hand, the reports' folder, the
rules sent with every file and the agent's timeout. The sub-module's own files are read from its folder, a listed path
and a rule from the root of the checkout."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

STORE_STATUS_DIR = Path(os.environ["STORE_STATUS_DIR"])
SKILLS_STATUS_JSON_PATH = STORE_STATUS_DIR / "skills_status.json"   # the snapshot status.py writes; the page reads it
SUB_MODULE_DIR = Path(__file__).resolve().parent                     # the sub-module's own files
# where a listed path and a rule are read from
REPO_ROOT = Path(subprocess.run(("git", "rev-parse", "--show-toplevel"), capture_output=True, text=True,
                                check=True).stdout.strip())
TO_CRAWL_TXT_PATH = SUB_MODULE_DIR / "to_crawl.txt"                                 # the list
CRAWLERS_MISSION_MD_PATH = SUB_MODULE_DIR / "crawlers_mission.md"                   # the prompt
VENDORS_FOR_CRAWLING_TOML_PATH = SUB_MODULE_DIR / "vendors_for_crawling.toml"       # the vendors and their forms
REPORTS_AFTER_CRAWLED_FILES_DIR = SUB_MODULE_DIR / "reports_after_crawled_files"    # the root's tree, <path>.md
RULE_PATHS = ("AGENTS.md", "module_skills/glossary.md", "module_skills/skill_*.md")   # the canon, sent with every file
MODULE_RULE_PATHS = ("{module}/README_{module}.md", "{module}/skills/*.md")  # {module}: the file's first path segment
AGENT_TIMEOUT_MINUTES = 30
# twice by extraction — the unit below (module_skills/glossary.md § Twice by extraction)
SECONDS_PER_MINUTE = 60
