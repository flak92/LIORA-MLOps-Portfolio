"""The sheet read into a model — `skills_sheet.xlsx`, opened as the zip of XML parts it is, and nothing else.

The reader opens the package, reads every tab's cells as text — shared strings, inline strings and plain values, the
three forms Excel, LibreOffice and Google Sheets save — and finds every table by its header, wherever it lies: a table
is a run of non-blank rows, its first row is its header, and the header says what it holds. From them it builds the
model — the Skills of the skill register with their rules, the glossary, the closed list of rule types and the files
matrix — and refuses, in one line, a workbook that is not structurally whole. It reads the workbook alone: no other
file, no directory, and it writes nothing.
"""

import zipfile
from pathlib import Path, PurePosixPath
from typing import NamedTuple
from xml.etree import ElementTree

from . import config

MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RELATIONSHIPS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PACKAGE = "{http://schemas.openxmlformats.org/package/2006/relationships}"


class Rule(NamedTuple):
    rule_type_id: str
    rule_id: str
    description: str
    scope: str
    expected_form: str
    exception: str


class Skill(NamedTuple):
    sheet_tab: str     # the tab holding its rules, which is also its family: module_skills or module_<domain>
    skill_path: str    # relative to the root of the tree; its stem is the Skill's identifier
    summary: str
    rules: list[Rule]


class Mark(NamedTuple):
    path: str          # a file or a glob, relative to the root of the tree
    skill_ids: tuple[str, ...]


class Sheet(NamedTuple):
    skills: list[Skill]
    glossary: list[dict[str, str]]
    rule_type_ids: list[str]
    skill_ids: list[str]     # the files matrix's columns, in its order
    marks: list[Mark]


def _column_index(reference: str) -> int:
    index = 0
    for character in reference:
        if not character.isalpha():
            break
        index = index * 26 + ord(character.upper()) - ord("A") + 1
    return index - 1


def _shared_strings(package: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in package.namelist():
        return []
    return ["".join(node.text or "" for node in item.iter(f"{MAIN}t"))
            for item in ElementTree.fromstring(package.read("xl/sharedStrings.xml")).iter(f"{MAIN}si")]


def _sheet_parts(package: zipfile.ZipFile) -> list[tuple[str, str]]:
    """Every tab's name and the zip member that holds it, through the workbook's relationships."""
    targets = {}
    for relationship in ElementTree.fromstring(package.read("xl/_rels/workbook.xml.rels")).iter(f"{PACKAGE}Relationship"):
        target = relationship.get("Target", "")
        targets[relationship.get("Id")] = target.lstrip("/") if target.startswith("/") else f"xl/{target}"
    return [(tab.get("name"), targets[tab.get(f"{RELATIONSHIPS}id")])
            for tab in ElementTree.fromstring(package.read("xl/workbook.xml")).iter(f"{MAIN}sheet")]


def _cell_text(cell, shared: list[str]) -> str:
    kind = cell.get("t", "")
    if kind == "s":
        value = cell.find(f"{MAIN}v")
        text = shared[int(value.text)] if value is not None and value.text else ""
    elif kind == "inlineStr":
        text = "".join(node.text or "" for node in cell.iter(f"{MAIN}t"))
    else:
        value = cell.find(f"{MAIN}v")
        text = value.text or "" if value is not None else ""
    return " ".join(text.split())


def _grid(package: zipfile.ZipFile, member: str, shared: list[str]) -> list[list[str]]:
    """The tab as rows of text, a missing row or cell being empty."""
    rows: dict[int, dict[int, str]] = {}
    number = 0
    for row in ElementTree.fromstring(package.read(member)).iter(f"{MAIN}row"):
        number = int(row.get("r", number + 1))
        cells: dict[int, str] = {}
        column = -1
        for cell in row.iter(f"{MAIN}c"):
            column = _column_index(cell.get("r", "")) if cell.get("r") else column + 1
            cells[column] = _cell_text(cell, shared)
        rows[number] = cells
    grid = []
    for number in range(1, max(rows, default=0) + 1):
        cells = rows.get(number, {})
        grid.append([cells.get(column, "") for column in range(max(cells, default=-1) + 1)])
    return grid


def _tables(grid: list[list[str]]) -> list[tuple[list[str], list[list[str]]]]:
    """Every run of non-blank rows as (header, rows), each row as wide as its header; a header with a blank cell
    inside it, or a row wider than its header, ends the run in one line."""
    found, block = [], []
    for row in [*grid, []]:
        if any(cell for cell in row):
            block.append(row)
            continue
        if block:
            header = list(block[0])
            while header and not header[-1]:
                header.pop()
            if "" in header:
                _refuse(f"the table headed {' | '.join(header)} has a blank header cell")
            for line in block[1:]:
                if any(line[len(header):]):
                    _refuse(f"the table headed {' | '.join(header)} has a row wider than its header: {line[0]}")
            found.append((header, [[*line, *[""] * len(header)][:len(header)] for line in block[1:]]))
            block = []
    return found


def _refuse(message: str):
    raise SystemExit(f"skills_sheet.xlsx: {message}")


def _one_table(tabs: dict, is_wanted, headed: str) -> tuple[str, list[str], list[list[str]]]:
    """The one table of the workbook whose header is wanted, wherever it lies — none or two ends the run."""
    found = [(tab, header, rows) for tab, tables in tabs.items() for header, rows in tables if is_wanted(header)]
    if len(found) != 1:
        _refuse(f"{len(found)} tables are headed {headed}; exactly one must be")
    return found[0]


def _filled(cells: dict[str, str], where: str) -> None:
    empty = [column for column, value in cells.items() if not value]
    if empty:
        _refuse(f"{where} leaves {', '.join(empty)} empty")


def load_sheet() -> Sheet:
    try:
        with zipfile.ZipFile(config.SKILLS_SHEET_PATH) as package:
            shared = _shared_strings(package)
            tabs = {name: _tables(_grid(package, member, shared)) for name, member in _sheet_parts(package)}
    except (OSError, zipfile.BadZipFile, KeyError, ElementTree.ParseError, ValueError) as failure:
        raise SystemExit(f"{config.SKILLS_SHEET_PATH} cannot be read as a workbook: {failure}")
    rule_tables: dict[str, list[list[str]]] = {}
    for tab, tables in tabs.items():
        for header, rows in tables:
            if tuple(header) == config.RULE_HEADER:
                if tab in rule_tables:
                    _refuse(f"the tab {tab} holds two rule tables")
                rule_tables[tab] = rows
    if not rule_tables:
        _refuse(f"no tab holds a table headed {' | '.join(config.RULE_HEADER)}")
    _, _, glossary_rows = _one_table(tabs, lambda h: tuple(h) == config.GLOSSARY_HEADER, " | ".join(config.GLOSSARY_HEADER))
    _, _, type_rows = _one_table(tabs, lambda h: tuple(h) == config.RULE_TYPE_ID_HEADER, config.RULE_TYPE_ID_HEADER[0])
    _, _, register_rows = _one_table(tabs, lambda h: tuple(h) == config.SKILL_REGISTER_HEADER,
                                     " | ".join(config.SKILL_REGISTER_HEADER))
    _, matrix_header, matrix_rows = _one_table(tabs, lambda h: tuple(h[:1]) == config.FILES_MATRIX_HEADER,
                                               f"{' | '.join(config.FILES_MATRIX_HEADER)} | skill_*…")
    rule_type_ids = [row[0] for row in type_rows if row[0]]
    if len(set(rule_type_ids)) != len(rule_type_ids):
        _refuse("the rule_type_id list names a type twice")

    skills: dict[tuple[str, str], Skill] = {}
    stems: dict[str, tuple[str, str]] = {}
    for row in register_rows:
        cells = dict(zip(config.SKILL_REGISTER_HEADER, row))
        where = f"the skill register: {cells['sheet_tab']} | {cells['skill_path']}"
        _filled(cells, where)
        key = (cells["sheet_tab"], cells["skill_path"])
        if key in skills:
            _refuse(f"{where} is registered twice")
        if cells["sheet_tab"] not in rule_tables:
            _refuse(f"{where}: the tab {cells['sheet_tab']} holds no rule table")
        places = config.skill_places(cells["sheet_tab"])
        if not places:
            _refuse(f"{where}: the tab {cells['sheet_tab']} is no module_<domain>")
        if not any(PurePosixPath(cells["skill_path"]).match(place) and len(PurePosixPath(cells["skill_path"]).parts) == len(PurePosixPath(place).parts)
                   for place in places):
            _refuse(f"{where} lies outside the places a Skill of this tab may lie: {', '.join(places)}")
        stem = Path(cells["skill_path"]).stem
        if stem in stems:
            _refuse(f"{where} and {stems[stem][1]} share the stem {stem}")
        stems[stem] = key
        skills[key] = Skill(cells["sheet_tab"], cells["skill_path"], cells["summary"], [])

    seen: dict[str, str] = {}
    for tab, rows in rule_tables.items():
        for row in rows:
            cells = dict(zip(config.RULE_HEADER, row))
            where = f"{tab}: {cells['rule_id'] or cells['skill_path']}"
            _filled(cells, where)
            skill = skills.get((tab, cells["skill_path"]))
            if skill is None:
                _refuse(f"{where}: {cells['skill_path']} has no row of the skill register for the tab {tab}")
            if cells["rule_id"] in seen:
                _refuse(f"{cells['rule_id']} is written twice: in {seen[cells['rule_id']]} and {skill.skill_path}")
            seen[cells["rule_id"]] = skill.skill_path
            prefix = Path(skill.skill_path).stem.removeprefix("skill_").upper().replace("_", "-") + "-"
            if not cells["rule_id"].startswith(prefix):
                _refuse(f"{where} does not carry the prefix {prefix} of {skill.skill_path}")
            if cells["rule_type_id"] not in rule_type_ids:
                _refuse(f"{where} is typed {cells['rule_type_id']!r}, not one of the sheet's rule_type_id list")
            skill.rules.append(Rule(*(cells[column] for column in config.RULE_HEADER[1:])))
    for skill in skills.values():
        if not skill.rules:
            _refuse(f"the skill register: {skill.sheet_tab} | {skill.skill_path} has no rule")

    glossary = [dict(zip(config.GLOSSARY_HEADER, row)) for row in glossary_rows]
    concepts: set[str] = set()
    for entry in glossary:
        if entry["concept"] in concepts:
            _refuse(f"the glossary registers the concept twice: {entry['concept']}")
        concepts.add(entry["concept"])

    skill_ids = matrix_header[1:]
    if len(set(skill_ids)) != len(skill_ids):
        _refuse("the files matrix heads two columns with one Skill")
    for skill_id in skill_ids:
        if skill_id not in stems:
            _refuse(f"the files matrix: the column {skill_id} names no Skill of the register")
    for stem in stems:
        if stem not in skill_ids:
            _refuse(f"the files matrix has no column for the registered Skill {stem}")
    marked_columns: set[str] = set()
    marks: list[Mark] = []
    keys: set[str] = set()
    for row in matrix_rows:
        cells = dict(zip(config.FILES_MATRIX_HEADER, row[:1]))
        where = f"the files matrix: {cells['path']}"
        _filled(cells, where)
        if cells["path"] in keys:
            _refuse(f"{where} is listed twice; one row per path")
        keys.add(cells["path"])
        chosen = []
        for skill_id, cell in zip(skill_ids, row[1:]):
            if cell == config.SKILL_MARK:
                chosen.append(skill_id)
            elif cell:
                _refuse(f"{where} holds {cell!r} under {skill_id}, not {config.SKILL_MARK} or empty")
        if not chosen:
            _refuse(f"{where} marks no Skill")
        marked_columns.update(chosen)
        marks.append(Mark(cells["path"], tuple(chosen)))
    for skill_id in skill_ids:
        if skill_id not in marked_columns:
            _refuse(f"the files matrix: the column {skill_id} marks no file")
    return Sheet(list(skills.values()), glossary, rule_type_ids, skill_ids, marks)
