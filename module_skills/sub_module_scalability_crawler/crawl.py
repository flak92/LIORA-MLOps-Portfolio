"""The crawl: every file to_crawl.txt lists goes, with crawlers_mission.md and the rules, to one fresh session of the
agent's command line, and the answer is appended verbatim to the file's report; then the snapshot. It reads, asks and
writes its reports — it edits no file it crawls and commits nothing. The first failure of the agent ends it.

    python3 -B -m module_skills.sub_module_scalability_crawler.crawl      (make skills-crawl)
"""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

from . import config, status


def load_rules_text() -> str:
    paths = [path for pattern in config.RULE_PATHS for path in sorted(map(str, Path().glob(pattern)))]
    return "\n".join(f"## {path}\n{Path(path).read_text(encoding='utf-8').rstrip(chr(10))}" for path in paths)


def build_message(mission: str, rules: str, path: str) -> str:
    text = Path(path).read_text(encoding="utf-8")
    return f"{mission.rstrip(chr(10))}\n\n# Rules\n{rules}\n\n# File under review: {path}\n{text}"


def write_report_entry(path: str, heading: str, answer: str) -> None:
    """A blank line, the heading, the answer as it came, a blank line — at the end of the report, never over it."""
    report = status.report_path(path)
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("a", encoding="utf-8") as handle:
        handle.write(f"\n{heading}\n{answer}" + ("\n" if answer.endswith("\n") else "\n\n"))


def main() -> int:
    paths, rules = status.load_crawl_paths(), load_rules_text()
    mission = config.CRAWLERS_MISSION_MD_PATH.read_text(encoding="utf-8")
    model = config.AGENT_COMMAND[config.AGENT_COMMAND.index("--model") + 1]
    commit = subprocess.run(("git", "rev-parse", "--short", "HEAD"), capture_output=True, text=True, check=True).stdout.strip()
    try:
        for number, path in enumerate(paths, start=1):
            print(f"{number}/{len(paths)}  {path}", flush=True)
            try:
                completed = subprocess.run(config.AGENT_COMMAND, input=build_message(mission, rules, path), capture_output=True,
                                           text=True, timeout=timedelta(minutes=config.AGENT_TIMEOUT_MINUTES).total_seconds())
            except subprocess.TimeoutExpired:
                print(f"{path}: the agent ran past {config.AGENT_TIMEOUT_MINUTES} minutes")
                return 1
            if completed.returncode != 0:
                print(f"{path}: the agent exited {completed.returncode}\n{completed.stderr or completed.stdout}")
                return 1
            stamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M")
            write_report_entry(path, f"{status.REPORT_HEADING_PREFIX}{stamp} UTC · {model} · {commit}", completed.stdout)
    finally:
        status.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
