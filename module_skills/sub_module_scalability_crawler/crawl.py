"""The crawler's menu: one action a hand chooses in gum — crawl, add a path or remove one — then it closes.

    python3 -B -m module_skills.sub_module_scalability_crawler.crawl      (make skills-crawl)
"""

from __future__ import annotations

import shutil
import subprocess
import tomllib
from datetime import UTC, datetime
from pathlib import Path

from . import config, status


def load_active_vendors() -> dict[str, dict]:
    """The tables of vendors_for_crawling.toml whose `active` is true, in the file's order; none ends the program."""
    tables = tomllib.loads(config.VENDORS_FOR_CRAWLING_TOML_PATH.read_text(encoding="utf-8"))
    vendors = {name: table for name, table in tables.items() if table["active"]}
    if not vendors:
        raise SystemExit("vendors_for_crawling.toml: no vendor is active")
    return vendors


def load_rules_text() -> str:
    """Every file RULE_PATHS names under the root, under its path: the patterns in order, each one's matches sorted."""
    root = config.REPO_ROOT
    paths = [str(found.relative_to(root)) for pattern in config.RULE_PATHS for found in sorted(root.glob(pattern))]
    return "\n".join(f"## {path}\n{(root / path).read_text(encoding='utf-8').rstrip('\n')}" for path in paths)


def build_message(mission: str, rules: str, path: str) -> str:
    """The mission, the rules, then the file under review: everything the agent reads, in one message."""
    text = (config.REPO_ROOT / path).read_text(encoding="utf-8")
    return f"{mission.rstrip('\n')}\n\n# Rules\n{rules}\n\n# File under review: {path}\n{text}"


def write_report_entry(path: str, fields: list[str], answer: str) -> None:
    """A blank line, `## crawled <UTC now> · <fields>`, the answer as it came and a blank line, at the report's end."""
    report = status.report_path(path)
    report.parent.mkdir(parents=True, exist_ok=True)
    heading = f"{status.REPORT_HEADING_PREFIX}{datetime.now(UTC):%Y-%m-%d %H:%M} UTC · {' · '.join(fields)}"
    with report.open("a", encoding="utf-8") as handle:
        handle.write(f"\n{heading}\n{answer}" + ("\n" if answer.endswith("\n") else "\n\n"))


def write_list(entries: list[str]) -> None:
    """to_crawl.txt as the menu leaves it: its entries in their order, each ending in a newline."""
    config.TO_CRAWL_TXT_PATH.write_text("".join(f"{entry}\n" for entry in entries), encoding="utf-8")


def _gum(*arguments: str) -> str | None:
    """A hand's answer in one gum prompt, off its stdout (gum draws on stderr); None for Esc, Ctrl-C or no answer."""
    answer = subprocess.run(("gum", *arguments), stdout=subprocess.PIPE, text=True)
    return (answer.stdout.strip() or None) if answer.returncode == 0 else None


def build_command(vendor: dict) -> tuple[list[str], list[str]] | None:
    """`command`, then the args of the option chosen in each form the vendor's table has (model, effort, permissions;
    the first option preselected), and the chosen labels. Its CLI off the PATH ends the program; no answer is None."""
    if not shutil.which(vendor["command"][0]):
        raise SystemExit(f"{vendor['command'][0]} is not on PATH — install it and log in")
    command, labels = list(vendor["command"]), []
    for form in filter(vendor.get, ("model", "effort", "permissions")):
        options = {option["label"]: option["args"] for option in vendor[form]}
        label = _gum("choose", "--header", form, "--selected", next(iter(options)), *options)
        if label is None:
            return None
        command, labels = command + options[label], labels + [label]
    return command, labels


def main() -> int:
    if not shutil.which("gum"):
        raise SystemExit("gum is not on PATH — the menu needs gum 2: https://github.com/charmbracelet/gum#installation")
    vendors = load_active_vendors()
    entries = [line.strip() for line in config.TO_CRAWL_TXT_PATH.read_text(encoding="utf-8").splitlines()]
    listed = [entry for entry in entries if entry]
    subprocess.run(("gum", "style", "--border", "normal", "--padding", "0 1", "Scalability crawler",
                    f"{len(listed)} path(s) listed"))
    action = _gum("choose", "--header", "action", "crawl", "add a path", "remove a path")
    if action is None:
        return 0
    if action == "add a path":
        entry = _gum("input", "--placeholder", "module_data/config.py  or  module_data")
        if entry is None or str(Path(entry)) in {str(Path(path)) for path in listed}:
            return 0
        status.load_entry_paths(entry)   # names something, or ends the program
        write_list(entries + [entry])
        return status.main()
    if action == "remove a path":
        entry = _gum("choose", "--header", "path to remove", *listed)
        if entry is None:
            return 0
        write_list([line for line in entries if line != entry])
        return status.main()
    name = _gum("choose", "--header", "vendor", *vendors)
    built = build_command(vendors[name]) if name else None
    if built is None:
        return 0
    rows = status.build_skills_status()["files"]
    chosen = _gum("choose", "--no-limit", "--header", "files to crawl", "--selected", "*",
                  *(f"{row['path']} · {row['last_crawled_utc'] or 'never'} · {row['crawl_count']}" for row in rows))
    if chosen is None:
        return 0
    command, labels = built
    mission, rules = config.CRAWLERS_MISSION_MD_PATH.read_text(encoding="utf-8"), load_rules_text()
    commit = subprocess.check_output(("git", "-C", config.REPO_ROOT, "rev-parse", "--short", "HEAD"), text=True).strip()
    try:
        for path in (line.partition(" · ")[0] for line in chosen.splitlines()):
            print(f"crawling {path} · {name}", flush=True)
            try:
                answer = subprocess.run(command, input=build_message(mission, rules, path), stdout=subprocess.PIPE,
                                        text=True, timeout=config.AGENT_TIMEOUT_MINUTES * config.SECONDS_PER_MINUTE)
            except subprocess.TimeoutExpired:
                raise SystemExit(f"{path}: the agent ran past {config.AGENT_TIMEOUT_MINUTES} minutes")
            if answer.returncode != 0 or not answer.stdout.strip():
                raise SystemExit(f"{path}: the agent gave no answer")
            write_report_entry(path, [name, *labels, commit], answer.stdout)
    finally:
        status.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
