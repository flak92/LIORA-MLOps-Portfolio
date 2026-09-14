"""The crawler's one surface of configuration: the snapshot's path, the three files kept by hand, the rules sent with every
file and the agent's command line. A path of this sub-module is relative to the checkout's root, where make runs."""

from __future__ import annotations

import os
from pathlib import Path

STORE_STATUS_DIR = Path(os.environ["STORE_STATUS_DIR"])
SKILLS_STATUS_JSON_PATH = STORE_STATUS_DIR / "skills_status.json"   # the snapshot status.py writes; the page reads it
TO_CRAWL_TXT_PATH = Path("module_skills/sub_module_scalability_crawler/to_crawl.txt")                 # the list
CRAWLERS_MISSION_MD_PATH = Path("module_skills/sub_module_scalability_crawler/crawlers_mission.md")   # the prompt
REPORTS_AFTER_CRAWLED_FILES_DIR = Path("module_skills/sub_module_scalability_crawler/reports_after_crawled_files")
# the rules sent with every file: each pattern's matches in byte order, the patterns in this order
RULE_PATHS = ("AGENTS.md", "module_skills/glossary.md", "module_skills/skill_*.md")
# the agent's command line: its user's own CLI session, no tools, so the message carries everything and
# the answer is one turn of plain text; every flag is in `claude --help` of 2.1.270 but --max-turns, which it accepts
AGENT_COMMAND = ("claude", "-p", "--model", "claude-sonnet-5", "--output-format", "text", "--max-turns", "1", "--tools", "",
                 "--strict-mcp-config", "--no-session-persistence", "--setting-sources", "project")
AGENT_TIMEOUT_MINUTES = 30
