"""Settle the enacted names of the act against the tree, so a convention can fail.

`act_naming_conventions.md` records which names this project enacted and which it
rejected, and until now those decisions were prose: a reader could honour them or
not, and nothing said which. This file reads the act's `conventions-data` block
and settles the eight of them a byte comparison can settle. Every failure names
the act row it came from, so what a reader gets is a decision to take in the act,
never a rule hidden in Python.

It carries no list of its own. That is deliberate and load-bearing: the tokens it
hunts live in the act, so its own checks can scan this file without an exemption,
and the act is the one document the content scan skips — because its
rejected-forms column is the authority for exactly those tokens.

Some rejected forms are prose rather than names, and some are already settled by
a one-liner in `skill_self_explaining_naming.md`. Both sets stay in the block
with their reason and are counted on every run, so this file never looks more
complete than it is.

Standard library only, plus the git binary, so it runs on a bare runner with no
virtual environment — the visualisation generator's reason exactly.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

# module_skills is a documentation folder and has no config.py, so the one path
# this file needs is derived here as every module's config.py derives it. The
# name is REPO_ROOT, not a _DIR name: the _DIR grammar names a directory of the
# tree (STORE_RAW_1M_DIR -> store_raw_1m/) and the root is the anchor those names
# are built from, which is also why the `paths at point of use` grep stays empty.
REPO_ROOT = Path(__file__).resolve().parent.parent
ACT_RELATIVE_PATH = "module_skills/act_naming_conventions.md"
BLOCK_FENCE = "```conventions-data"
COMMENTED_CODE_SUFFIXES = (".py", ".js")

# a target is a name at line start followed by a colon that is not an assignment:
# := ?= += are variables and a leading dot is a special target, so the naive
# `^name:` reading reports PY, COMPOSE, .PHONY and .DEFAULT_GOAL as targets
MAKEFILE_TARGET_PATTERN = re.compile(r"^([A-Za-z0-9_%-][A-Za-z0-9_.%-]*) *:(?!=)", re.M)
COMMENTED_PYTHON_PATTERN = re.compile(
    r"^\s*#\s*(def |class |import |from \w+ import |return\b|elif\b|else:|try:|except\b"
    r"|print\(|[A-Za-z_][\w.\[\]\"']*\s*=[^=])")
COMMENTED_SCRIPT_PATTERN = re.compile(
    r"^\s*//\s*(function |var |let |const |return\b|if\s*\(|for\s*\("
    r"|[A-Za-z_$][\w.$\[\]\"']*\s*=[^=])")


def load_file_text(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8", errors="replace")


def load_tracked_paths() -> list[str]:
    # -z because git quotes unusual names, and a quoted path is a different file
    done = subprocess.run(("git", "ls-files", "-z"), cwd=REPO_ROOT,
                          capture_output=True, text=True, check=True)
    return sorted(p for p in done.stdout.split("\0") if p)


def load_conventions_data() -> dict[str, list[list[str]]]:
    """The act's conventions-data block, as key -> rows of pipe-separated cells."""
    body = load_file_text(ACT_RELATIVE_PATH).split(BLOCK_FENCE, 1)[-1].split("```", 1)[0]
    rows: dict[str, list[list[str]]] = {}
    for line in body.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            key, _, rest = line.partition(" ")
            rows.setdefault(key, []).append([cell.strip() for cell in rest.split("|")])
    return rows


def ticker_folders(paths: list[str]) -> list[str]:
    return sorted({p.split("/")[1] for p in paths
                   if p.startswith("store_assets_artifacts/") and p.count("/") == 2})


def directory_listings(paths: list[str]) -> dict[str, list[str]]:
    """Every directory of the tracked tree and the names `ls` would show in it.

    Rebuilt from the index rather than read with ls: a build artifact or a
    gitignored store absent from a fresh clone must not be able to move the
    answer, which is exactly why the shell one-liner this replaces was not
    reproducible across machines.
    """
    listings: dict[str, set[str]] = {}
    for path in paths:
        parts = path.split("/")
        for depth in range(len(parts)):
            listings.setdefault("/".join(parts[:depth]) or ".", set()).add(parts[depth])
    return {directory: sorted(names) for directory, names in listings.items()}


def load_tree_facts() -> dict:
    paths = load_tracked_paths()
    return {"paths": paths, "texts": {p: load_file_text(p) for p in paths},
            "tickers": ticker_folders(paths), "listings": directory_listings(paths)}


def collation_key(name: str) -> str:
    """What a UTF-8 locale compares and LC_COLLATE=C does not: letters and digits,
    case folded, punctuation ignored. Reproduces glibc en_US.UTF-8 on every
    directory of this tree, and needs no locale generated on the runner."""
    return re.sub(r"[^0-9a-z]", "", name.lower())


def expanded(token: str, tickers: list[str]) -> list[str]:
    return [token.replace("<TICKER>", t) for t in tickers] if "<TICKER>" in token else [token]


def stem_hits(stem: str, texts: dict[str, str], exempt: set[str]) -> list[str]:
    """Where a stem appears as a name component, as file:line.

    The tail guard is case sensitive while the stem is not, so a banned stem is
    found camel-cased, snake-cased and hyphenated alike. A plain re.IGNORECASE
    would fold the guard too — [a-z0-9] would quietly become [A-Za-z0-9] — and
    every camel-cased occurrence would pass while the check reported green.

    This paragraph used to name a banned stem as its example, and the check
    caught it on the first run. A file that hunts tokens may not spell them.
    """
    pattern = re.compile(r"(?<![A-Za-z0-9])(?i:" + re.escape(stem) + r")(?![a-z0-9])")
    return [f"{path}:{number}" for path, text in sorted(texts.items()) if path not in exempt
            for number, line in enumerate(text.splitlines(), 1) if pattern.search(line)]


def reference_forms(path: str, tickers: list[str], data: dict) -> set[str]:
    """Every spelling that counts as one tracked file naming another."""
    rules = {row[0] for row in data.get("reachability_rule", [])}
    name = path.rsplit("/", 1)[-1]
    forms = {path, name}
    if "python_import" in rules and path.endswith(".py"):
        forms |= {path[:-3], path[:-3].replace("/", ".")}
    if "ticker_placeholder" in rules:
        forms |= {"<TICKER>_" + name[len(t) + 1:] for t in tickers if name.startswith(t + "_")}
    for glob, _row, _why in data.get("reachability_glob", []):
        head, _, tail = glob.partition("*")
        if name.startswith(head) and name.endswith(tail):
            forms.add(glob)
    return forms


def _failure(offender: str, act_row: str, fix: str) -> str:
    return f"  {offender}\n    act row {act_row} — fix: {fix}"


def _content_exempt(data: dict) -> set[str]:
    return {row[0] for row in data.get("content_scan_exempt", [])}


def rejected_names_absent(data: dict, tree: dict) -> list[str]:
    """Act, rejected-forms column: a form is rejected in a role, and mode says which."""
    failures = []
    for token, mode, act_row, fix in data.get("rejected_name", []):
        if mode == "path_segment":
            found = [p for p in tree["paths"] if token in p.split("/")]
        elif mode == "path_exact":
            found = [p for p in tree["paths"] if p == token]
        else:
            continue
        if found:
            failures.append(_failure(f"{token} ({mode}) at {found[0]}", act_row, fix))
    return failures


def enacted_names_present(data: dict, tree: dict) -> list[str]:
    """Act, enacted column: the names exist, families carry their prefix, top levels their category."""
    known = set(tree["paths"]) | {d for d in tree["listings"] if d != "."}
    exempt = {row[0] for row in data.get("collation_exempt", [])}
    failures = []
    for token, act_row, fix in data.get("enacted_path", []):
        for name in expanded(token, tree["tickers"]):
            if name not in known and not any(p.endswith("/" + name) for p in tree["paths"]):
                failures.append(_failure(f"enacted path {name} is not in the tree", act_row, fix))
    for prefix, suffix, allowed, act_row, fix in data.get("enacted_family", []):
        for path in tree["paths"]:
            if path.startswith(prefix) and path.endswith(suffix) and \
                    not path.rsplit("/", 1)[-1].startswith(tuple(allowed.split())):
                failures.append(_failure(f"{path} is outside its enacted family", act_row, fix))
    categories = tuple(row[0] for row in data.get("top_level_category", []))
    for name in sorted({p.split("/")[0] for p in tree["paths"] if "/" in p}):
        if not name.startswith(categories) and name not in exempt:
            failures.append(_failure(f"top-level {name}/ carries no enacted category", "1",
                                     f"start it with one of {' '.join(categories)}: one category, one block"))
    return failures


def collation_invariance(data: dict, tree: dict) -> list[str]:
    """Act rows 14 and 16: one listing order under LC_COLLATE=C and under a UTF-8 locale."""
    exempt = {n for row in data.get("collation_exempt", [])
              for n in expanded(row[0], tree["tickers"])}
    failures = []
    for directory, names in sorted(tree["listings"].items()):
        bound = [n for n in names if n not in exempt]
        keys = [collation_key(n) for n in bound]
        if len(set(keys)) != len(keys):
            failures.append(_failure(
                f"{directory}/ holds two names differing only by case or punctuation", "16",
                "rename one — an order that depends on case survives no filesystem"))
        elif sorted(bound, key=lambda n: n.encode()) != sorted(bound, key=collation_key):
            failures.append(_failure(
                f"{directory}/ lists as {bound} by byte and as "
                f"{sorted(bound, key=collation_key)} by locale", "16",
                "rename the offender, or record the exemption in the act and in its block"))
    return failures


def ticker_manifest(data: dict, tree: dict) -> list[str]:
    """Act row 8: an asset folder tracks the manifest files, each carrying its ticker."""
    root, act_row, fix = data["ticker_store"][0]
    wanted = [row[0] for row in data.get("ticker_tracked_file", [])]
    failures = []
    for ticker in tree["tickers"]:
        held = sorted(p.rsplit("/", 1)[-1] for p in tree["paths"]
                      if p.startswith(root + ticker + "/"))
        failures += [_failure(f"{root}{ticker}/{n} does not carry the {ticker}_ prefix",
                              act_row, fix) for n in held if not n.startswith(ticker + "_")]
        if held != sorted(w.replace("<TICKER>", ticker) for w in wanted):
            failures.append(_failure(f"{root}{ticker}/ tracks {held}", act_row, fix))
    return failures


def single_vocabulary(data: dict, tree: dict) -> list[str]:
    """One concept, one name: a banned stem is spelled nowhere at all."""
    failures = []
    for stem, act_row, fix in data.get("banned_stem", []):
        found = stem_hits(stem, tree["texts"], _content_exempt(data))
        if found:
            failures.append(_failure(f"{stem} at {found[0]} and {len(found) - 1} more",
                                     act_row, fix))
    return failures


def target_prefixes(data: dict, tree: dict) -> list[str]:
    """Act rows 13, 19 and 22: a make target is lifecycle, or it carries its module."""
    lifecycle = {row[0] for row in data.get("make_lifecycle_target", [])}
    prefixes = tuple(row[0] for row in data.get("make_stage_prefix", []))
    return [_failure(f"make target {target!r}", "13",
                     "name it <module>-<stage>, or enact it in the act as lifecycle")
            for target in MAKEFILE_TARGET_PATTERN.findall(tree["texts"]["Makefile"])
            if target not in lifecycle and not target.startswith(prefixes)]


def no_debt_markers(data: dict, tree: dict) -> list[str]:
    """Act row 24: no debt marker, and no code left inside a comment."""
    generated = {row[0] for row in data.get("generated_path", [])}
    exempt = _content_exempt(data) | generated
    failures = []
    for marker, act_row, fix in data.get("debt_marker", []):
        failures += [_failure(f"{marker} at {hit}", act_row, fix)
                     for hit in stem_hits(marker, tree["texts"], exempt)]
    for path, text in sorted(tree["texts"].items()):
        if path in generated or not path.endswith(COMMENTED_CODE_SUFFIXES):
            continue
        pattern = COMMENTED_PYTHON_PATTERN if path.endswith(".py") else COMMENTED_SCRIPT_PATTERN
        failures += [_failure(f"commented-out code at {path}:{number}", "24",
                              "delete it — git remembers the line, the comment only hides it")
                     for number, line in enumerate(text.splitlines(), 1) if pattern.match(line)]
    return failures


def file_reachability(data: dict, tree: dict) -> list[str]:
    """AGENTS.md, first value: a file whose purpose cannot be named goes.

    The generated page is not a source — it embeds every tracked path, so counting
    it would make this pass on any tree at all. Inside the picture's config the
    `exclude` array is not a source either: naming a path there keeps it OUT of
    the picture, which is the opposite of a reference.
    """
    generated = {row[0] for row in data.get("generated_path", [])}
    owned = {row[0] for row in data.get("reachability_ecosystem_owned", [])}
    sources = {p: t for p, t in tree["texts"].items() if p not in generated}
    for path, key, _row, _why in data.get("reachability_ignored_region", []):
        if path in sources:
            sources[path] = re.sub(rf'"{key}"\s*:\s*\[[^\]]*\]', "", sources[path])
    failures = []
    for path in tree["paths"]:
        if path in owned or path in generated:
            continue
        patterns = [re.compile(r"(?<![A-Za-z0-9_])" + re.escape(form) + r"(?![A-Za-z0-9_])")
                    for form in reference_forms(path, tree["tickers"], data)]
        if not any(p.search(text) for source, text in sources.items() if source != path
                   for p in patterns):
            failures.append(_failure(f"{path} is named by no other tracked file", "1",
                                     "name it where it is used, or delete it"))
    return failures


CHECKS = (rejected_names_absent, enacted_names_present, collation_invariance, ticker_manifest,
          single_vocabulary, target_prefixes, no_debt_markers, file_reachability)


def main() -> int:
    data = load_conventions_data()
    tree = load_tree_facts()
    failures = []
    for check in CHECKS:
        found = check(data, tree)
        print(f"{'FAIL' if found else 'pass'}  {check.__name__}")
        for line in found:
            print(line)
        failures += found
    # the coverage the act records but this file does not settle, printed every
    # run: a verifier that hides its own gaps is worse than no verifier
    owned = [row for row in data.get("rejected_name", []) if row[1] == "owned"]
    print(f"\n{len(tree['paths'])} tracked files · {len(owned)} rejected forms settled by another "
          f"check · {len(data.get('unenforceable', []))} recorded as prose no grep can settle")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
