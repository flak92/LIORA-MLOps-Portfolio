"""The sync: every Skill and the register rendered from the sheet beside what each governs — `make skills-sync`.

The sheet is read once — `sheet.load_sheet()` refuses, in one line, a workbook that is not whole — and every document
is rendered in memory, written through a temporary file and `os.replace`, and only after the last of them is written
are the generated files the sheet no longer names deleted: in every place a Skill may lie, and only where the first
line carries the marker, so a hand-written document is never touched. The sync knows nothing of
the crawler: it reads no store, clears no report and writes no snapshot.
"""

import os
import tempfile
from pathlib import Path

from . import config, sheet


def to_markdown(skill: sheet.Skill, rule_type_ids: list[str], glossary: list[dict[str, str]]) -> str:
    """A Skill as its file: the marker, the stem as its heading, the summary, one section per rule_type_id in the sheet's order with
    a list item per rule; the glossary adds one section per register section, an item per concept. An empty cell
    writes no sub-bullet; `none` is a value and stays."""
    lines = [config.GENERATED_MARKER, f"# {Path(skill.skill_path).stem}", "", skill.summary]
    for kind in rule_type_ids:
        rules = [rule for rule in skill.rules if rule.rule_type_id == kind]
        if rules:
            lines += ["", f"## {kind}", ""]
            for rule in rules:
                lines.append(f"- `{rule.rule_id}`")
                for label, value in (("Description", rule.description), ("Scope", rule.scope),
                                     ("Expected", rule.expected_form), ("Exception", rule.exception)):
                    if value:
                        lines.append(f"  - {label}: {value}")
    if skill.skill_path == config.GLOSSARY_SKILL_PATH:
        section = None
        for entry in glossary:
            if entry["section"] != section:
                section = entry["section"]
                lines += ["", f"## {section}", ""]
            lines.append(f"- {entry['concept']}")
            for column in config.GLOSSARY_HEADER[2:]:
                if entry[column]:
                    lines.append(f"  - {column.replace('_', ' ').capitalize()}: {entry[column]}")
    return "\n".join(lines) + "\n"


def build_documents(loaded: sheet.Sheet) -> dict[Path, str]:
    """Every generated file by its absolute path, rendered before anything is written."""
    return {config.skill_document_path(skill.skill_path): to_markdown(skill, loaded.rule_type_ids, loaded.glossary)
            for skill in loaded.skills}


def write_text(path: Path, text: str) -> None:
    """A file written whole: through a temporary file beside it and `os.replace`, so no reader sees a part."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
    os.replace(temporary, path)


def delete_stale(documents: dict[Path, str]) -> None:
    """Every generated file the sheet no longer names is deleted: in every place a Skill of any family may lie — only
    a file whose first line is the marker."""
    places = {place for family in ("module_skills", "module_*") for place in config.skill_places(family)}
    for place in sorted(places):
        for path in sorted(config.TREE_ROOT_DIR.glob(place)):
            if path not in documents and path.is_file():
                with path.open(encoding="utf-8") as stream:
                    generated = stream.readline().rstrip("\n") == config.GENERATED_MARKER
                if generated:
                    path.unlink()


def main() -> int:
    loaded = sheet.load_sheet()
    documents = build_documents(loaded)
    for path, text in documents.items():
        write_text(path, text)
    delete_stale(documents)
    print("skills synchronized", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
