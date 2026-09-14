"""The crawler's menu: a hand chooses one action in gum — crawl chosen listed files with an active vendor, add a path to
to_crawl.txt or remove one — and the program closes after it. A crawl sends each chosen file, with crawlers_mission.md and
the rules, to one fresh session of the vendor's command line and appends the answer verbatim to the file's report. It
edits no file but its list and commits nothing; no answer in the menu or its prompt ends it with nothing written, and the
first failure of the agent ends it.

    python3 -B -m module_skills.sub_module_scalability_crawler.crawl      (make skills-crawl)
"""

from __future__ import annotations

import shutil
import subprocess
import tomllib
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


def load_active_vendors() -> dict[str, dict]:
    """The tables of vendors_for_crawling.toml whose `active` is true, in the file's order."""
    vendors = tomllib.loads(config.VENDORS_FOR_CRAWLING_TOML_PATH.read_text(encoding="utf-8"))
    return {name: vendor for name, vendor in vendors.items() if vendor["active"]}


def write_list(lines: list[str]) -> None:
    """to_crawl.txt as the menu leaves it: its lines in their order, each ending in a newline."""
    config.TO_CRAWL_TXT_PATH.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")


def _gum(*arguments: str) -> str | None:
    """A hand's answer in one gum prompt, off its stdout (gum draws on stderr); None when there is none — Esc, Ctrl-C, no
    terminal, or nothing chosen or typed."""
    answer = subprocess.run(("gum", *arguments), stdout=subprocess.PIPE, text=True)
    return (answer.stdout.strip() or None) if answer.returncode == 0 else None


def main() -> int:
    if not shutil.which("gum"):
        raise SystemExit("gum is not on PATH — the crawler's menu needs gum 2: https://github.com/charmbracelet/gum#installation")
    vendors = load_active_vendors()
    rows = status.build_skills_status()["files"]
    subprocess.run(("gum", "style", "--border", "normal", "--padding", "0 1", "Scalability crawler",
                    f"{len(rows)} file(s) listed"))
    action = _gum("choose", "--header", "action", *(f"crawl · {name}" for name in vendors), "add a path", "remove a path")
    if action is None:
        return 0
    if action in ("add a path", "remove a path"):
        lines = config.TO_CRAWL_TXT_PATH.read_text(encoding="utf-8").splitlines()
        entries = [line.strip() for line in lines]
        if action == "add a path":
            entry = _gum("input", "--placeholder", "module_data/config.py  or  module_data")
            if entry is None:
                return 0
            status.load_entry_paths(entry)
            if str(Path(entry)) in {str(Path(listed)) for listed in entries if listed}:
                return 0
            write_list(lines + [entry])
        else:
            entry = _gum("choose", "--header", "path to remove", *filter(None, entries))
            if entry is None:
                return 0
            del lines[entries.index(entry)]
            write_list(lines)
        return status.main()
    vendor = vendors[action.removeprefix("crawl · ")]
    command = [*vendor["command"], "--model", vendor["model"], *vendor["permissions"]]
    if not shutil.which(command[0]):
        raise SystemExit(f"{command[0]} is not on PATH — install it and log in")
    chosen = _gum("choose", "--no-limit", "--header", "files to crawl", "--selected", "*",
                  *(f"{row['path']} · {row['last_crawled_utc'] or 'never'} · {row['crawl_count']}" for row in rows))
    if chosen is None:
        return 0
    paths, rules = [line.partition(" · ")[0] for line in chosen.splitlines()], load_rules_text()
    mission = config.CRAWLERS_MISSION_MD_PATH.read_text(encoding="utf-8")
    commit = subprocess.run(("git", "rev-parse", "--short", "HEAD"), capture_output=True, text=True, check=True).stdout.strip()
    try:
        for path in paths:
            print(f"crawling {path}", flush=True)
            try:
                completed = subprocess.run(command, input=build_message(mission, rules, path), capture_output=True,
                                           text=True, timeout=timedelta(minutes=config.AGENT_TIMEOUT_MINUTES).total_seconds())
            except subprocess.TimeoutExpired:
                print(f"{path}: the agent ran past {config.AGENT_TIMEOUT_MINUTES} minutes")
                return 1
            if completed.returncode != 0:
                print(f"{path}: the agent exited {completed.returncode}\n{completed.stderr or completed.stdout}")
                return 1
            stamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M")
            write_report_entry(path, f"{status.REPORT_HEADING_PREFIX}{stamp} UTC · {vendor['model']} · {commit}", completed.stdout)
    finally:
        status.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
