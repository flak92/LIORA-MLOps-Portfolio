"""The crawler: every controlled file of the files matrix, read by the active vendor against the Skills marked for
it — `make skills-crawl`, after `make skills-sync` has rendered the Skills it sends.

The crawl reads the sheet and resolves the files matrix: every glob under the root of the tree, the marks of two rows
that reach one file joined, the whole sorted by key; each Skill's text is the document the sync rendered. One vendor is
active in `vendors_for_crawling.toml`; its `argv` is the whole command line, run with `shell=False` at the root of the tree,
the message on its stdin, the answer its stdout. Once the matrix is resolved the reports are reset and every controlled
file is `pending` in the snapshot; then the files go one after another: `running` while the vendor works, `done` once
the report is written, `failed` on a non-zero exit, an empty answer, the time limit, a command that cannot start or
text that cannot be decoded — then the next file; the process ends non-zero if any file failed. Ctrl-C leaves the
current file `interrupted`, the rest `pending`, and ends with 130. `done` says the report was written, not that the
file conforms: the report holds what the vendor answered, as it came.

The crawl asks nothing and prints one line per file on stdout, after its result, in one form —
`<current>/<total> | <controlled file> | <vendor> | <state>` — then one closing line `<processed>/<total> | crawl | <vendor> |
<state>`, the files processed being those that reached `done` or `failed`; a refusal, and the reason a file failed, are one line each on stderr.
"""

import shutil
import subprocess
import sys
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import NamedTuple

from . import config, status
from .. import config as skills_config, sheet, sync


class ControlledFile(NamedTuple):
    key: str                      # its path from the root of the tree, the one name a file has in the reports and the snapshot
    path: Path
    skill_ids: tuple[str, ...]


def load_vendor() -> tuple[str, list[str]]:
    """The one active vendor and its command line; a file that cannot be read, zero or two active ends the crawl in one line."""
    try:
        with config.VENDORS_FOR_CRAWLING_TOML_PATH.open("rb") as stream:
            vendors = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as failure:
        raise SystemExit(f"{config.VENDORS_FOR_CRAWLING_TOML_PATH.name}: {failure}")
    active = [name for name, vendor in vendors.items() if vendor.get("active")]
    if len(active) != 1:
        raise SystemExit(f"vendors_for_crawling.toml: {len(active)} vendors are active; exactly one must be")
    argv = vendors[active[0]].get("argv")
    if not isinstance(argv, list) or not argv:
        raise SystemExit(f"vendors_for_crawling.toml: [{active[0]}] has no argv")
    return active[0], [str(argument) for argument in argv]


def build_controlled_files(loaded: sheet.Sheet) -> list[ControlledFile]:
    """Every file the files matrix reaches, with the marks of every row that reaches it joined, in the matrix's column
    order, the files sorted by key; a row that reaches no file, or a generated one — a rendered Skill, the snapshot —
    ends the crawl in one line."""
    generated = {skills_config.skill_document_path(skill.skill_path) for skill in loaded.skills}
    found: dict[str, ControlledFile] = {}
    for mark in loaded.marks:
        paths = sorted(path for path in skills_config.TREE_ROOT_DIR.glob(mark.path) if path.is_file())
        if not paths:
            raise SystemExit(f"the files matrix: {mark.path} matches no file")
        for path in paths:
            if path in generated or path == config.SKILLS_STATUS_JSON_PATH:
                raise SystemExit(f"the files matrix: {mark.path} reaches {path.name}, a generated file")
            key = path.relative_to(skills_config.TREE_ROOT_DIR).as_posix()
            earlier = found.get(key)
            marked = set(mark.skill_ids) | set(earlier.skill_ids if earlier else ())
            found[key] = ControlledFile(key, path, tuple(skill_id for skill_id in loaded.skill_ids if skill_id in marked))
    return [found[key] for key in sorted(found)]


def load_skill_texts(loaded: sheet.Sheet) -> dict[str, str]:
    """Every Skill's rendered document by its identifier, read from where the sync wrote it."""
    texts = {}
    for skill in loaded.skills:
        path = skills_config.skill_document_path(skill.skill_path)
        try:
            texts[Path(skill.skill_path).stem] = path.read_text(encoding="utf-8")
        except OSError:
            raise SystemExit(f"{path}: not rendered — run make skills-sync first")
    return texts


def build_message(skill_texts: dict[str, str], controlled_file: ControlledFile, mission: str) -> str:
    """The Skills marked for the file, the file with every line after its number, then the mission."""
    skills = "\n".join(skill_texts[skill_id] for skill_id in controlled_file.skill_ids)
    lines = controlled_file.path.read_text(encoding="utf-8").splitlines()
    numbered = "\n".join(f"{number:>4}  {line}" for number, line in enumerate(lines, 1))
    return f"{skills}\n# File under review: {controlled_file.key}\n\n{numbered}\n\n# Mission\n\n{mission.strip()}\n"


def main() -> int:
    loaded = sheet.load_sheet()
    vendor, argv = load_vendor()
    try:
        mission = config.CRAWLERS_MISSION_MD_PATH.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as failure:
        raise SystemExit(f"{config.CRAWLERS_MISSION_MD_PATH.name}: {failure}")
    controlled_files = build_controlled_files(loaded)
    skill_texts = load_skill_texts(loaded)
    # the reset and the pending snapshot together, after the last refusal, so the snapshot never names a report that is gone
    shutil.rmtree(config.REPORTS_DIR, ignore_errors=True)
    rows = {controlled_file.key: status.row(controlled_file.key) for controlled_file in controlled_files}
    status.write_skills_status(list(rows.values()))
    total, processed, failed_file_count = len(controlled_files), 0, 0
    for number, controlled_file in enumerate(controlled_files, 1):
        rows[controlled_file.key] = status.row(controlled_file.key, "running", vendor)
        status.write_skills_status(list(rows.values()))
        why = None
        try:
            vendor_process = subprocess.run(argv, shell=False, cwd=skills_config.TREE_ROOT_DIR,
                                            input=build_message(skill_texts, controlled_file, mission), text=True,
                                            encoding="utf-8", capture_output=True,
                                            timeout=config.AGENT_TIMEOUT_SECONDS)
            answer = vendor_process.stdout.strip()
            if vendor_process.returncode != 0:
                # the vendor's last line, wherever it wrote it — a CLI out of its usage limit says so on stdout
                vendor_last_line = (vendor_process.stderr.strip() or answer or "no message").splitlines()[-1]
                why = f"exit {vendor_process.returncode}: {vendor_last_line}"[:200]
            elif not answer:
                why = "empty answer"
        except subprocess.TimeoutExpired:
            why = f"no answer within {config.AGENT_TIMEOUT_SECONDS // config.SECONDS_PER_MINUTE} minutes"
        except (OSError, UnicodeError) as failure:
            why = f"{type(failure).__name__}: {failure}"[:200]
        except KeyboardInterrupt:
            rows[controlled_file.key] = status.row(controlled_file.key, "interrupted", vendor)
            status.write_skills_status(list(rows.values()))
            print(f"{number}/{total} | {controlled_file.key} | {vendor} | interrupted", flush=True)
            print(f"{processed}/{total} | crawl | {vendor} | interrupted", flush=True)
            return 130
        finished_at_utc = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        if why is None:
            report = config.report_path(controlled_file.key)
            sync.write_text(report, f"{controlled_file.key} · {vendor} · {finished_at_utc}\n\n{answer}\n")
            rows[controlled_file.key] = status.row(controlled_file.key, "done", vendor, finished_at_utc,
                                                   report.relative_to(config.REPORTS_DIR).as_posix())
            print(f"{number}/{total} | {controlled_file.key} | {vendor} | done", flush=True)
        else:
            failed_file_count += 1
            rows[controlled_file.key] = status.row(controlled_file.key, "failed", vendor, finished_at_utc)
            print(f"{controlled_file.key}: {why}", file=sys.stderr, flush=True)
            print(f"{number}/{total} | {controlled_file.key} | {vendor} | failed", flush=True)
        processed += 1
        status.write_skills_status(list(rows.values()))
    print(f"{processed}/{total} | crawl | {vendor} | {'failed' if failed_file_count else 'done'}", flush=True)
    return 1 if failed_file_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
