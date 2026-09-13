"""The tree counted against its contract: store/status/skills_status.json — every metric of METRICS measured over the
tracked files of the checkout, a function of the tree it reads. The review record is one of those files, read here and
never written; the snapshot this stage writes is never read back.

    python3 -B -m module_skills.sub_module_scalability_crawler.status        (make skills-status)
"""

from __future__ import annotations

import ast
import fnmatch
import functools
import hashlib
import json
import posixpath
import re
import subprocess
from collections import Counter
from datetime import UTC, datetime

from . import config

NUMBER_WORDS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
FAMILY_NOUNS = {"snapshot": "snapshots", "tab": "tabs", "store": "stores", "module": "modules", "script": "section scripts"}
REFERENCE_SUFFIX_PATTERN = r"\.(py|md|js|html|css|json|yml|yaml|txt|parquet|duckdb|zip|sqlite3)$"
ENUMERATION_SEPARATOR_PATTERN = r"[\s`*,/+·()]*(?:\b(?:and|or)\b)?[\s`*,/+·()]*"
REVIEW_RULE = "module_skills/skill_scalability_crawler.md § The review record"


def git(*args: str, root=None) -> str:
    return subprocess.run(("git", *args), cwd=root or config.REPO_ROOT, capture_output=True, text=True, check=True).stdout


def tracked_paths(*pathspecs: str) -> list[str]:
    return sorted(path for path in git("ls-files", "-z", "--", *pathspecs).split("\0") if path)


@functools.cache
def load_file_text(path: str) -> str:
    return (config.REPO_ROOT / path).read_text(encoding="utf-8")


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def example(path: str, line: int, name: str) -> str:
    name = re.sub(r"\s+", " ", name)
    return f"{path}:{line} — {name}"


def word_pattern(word: str) -> re.Pattern:
    """A word bounded by anything but a word character, a space inside it matching any run of whitespace."""
    return re.compile(r"(?<!\w)" + r"\s+".join(map(re.escape, word.split())) + r"(?!\w)")


# ---- markdown: fences, headings, tables, code spans ------------------------------------------------------------------

def without_fences(text: str) -> str:
    """The text with every fenced block blanked, line count and offsets kept."""
    return re.sub(r"^```.*?^```", lambda match: re.sub(r"[^\n]", " ", match.group(0)), text, flags=re.M | re.S)


def section_spans(text: str) -> list[tuple[str, int, int]]:
    """Every heading as (title, start offset, end offset) — a section ends where a heading of its level or above begins."""
    headings = [(len(match.group(1)), match.group(2).strip(), match.start())
                for match in re.finditer(r"^(#{1,6})\s+(.*)$", without_fences(text), flags=re.M)]
    spans = []
    for index, (level, title, start) in enumerate(headings):
        end = next((later_start for later_level, _, later_start in headings[index + 1:] if later_level <= level), len(text))
        spans.append((title, start, end))
    return spans


def section_span(text: str, title: str | None) -> tuple[int, int] | None:
    if title is None:
        return 0, len(text)
    return next(((start, end) for heading, start, end in section_spans(text) if heading == title), None)


def table_cells(text: str):
    """Every body cell of every table as (header, row offset, cell start offset, cell end offset, cell text)."""
    header = None
    offset = 0
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith("|"):
            bounds = [match.start() for match in re.finditer(r"(?<!\\)\|", line)]
            cells = [(offset + left + 1, offset + right, line[left + 1:right]) for left, right in zip(bounds, bounds[1:])]
            if header is None:
                header = [cell.strip().lower() for _, _, cell in cells]
            elif not re.fullmatch(r"\|[\s:|-]+\|?", stripped):
                for column, (start, end, cell) in enumerate(cells):
                    yield (header[column] if column < len(header) else "", offset, start, end, cell)
        else:
            header = None
        offset += len(line)


def code_spans(text: str):
    return re.finditer(r"`([^`\n]+)`", without_fences(text))


def is_within(offset: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= offset < end for start, end in spans)


# ---- the tree ---------------------------------------------------------------------------------------------------------

@functools.cache
def all_paths() -> tuple[str, ...]:
    return tuple(tracked_paths())


@functools.cache
def scope_paths() -> tuple[str, ...]:
    return tuple(tracked_paths(*config.MEASURED_SCOPE_PATHSPECS))


@functools.cache
def crawl_paths() -> tuple[str, ...]:
    """The files the review pass may queue: the files in scope CRAWL_PATHSPECS names."""
    scope = set(scope_paths())
    return tuple(path for path in tracked_paths(*config.CRAWL_PATHSPECS) if path in scope)


@functools.cache
def tracked_directories() -> frozenset[str]:
    return frozenset(path[:match.start()] for path in all_paths() for match in re.finditer("/", path))


def python_paths() -> list[str]:
    return [path for path in scope_paths() if path.endswith(".py")]


@functools.cache
def python_tree(path: str) -> ast.Module:
    return ast.parse(load_file_text(path), filename=path)


def functions(tree: ast.Module) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    return [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]


def makefile_variable(name: str) -> list[str]:
    match = re.search(rf"^{name}\s*:?=\s*(.*)$", load_file_text(config.MAKEFILE_PATH), flags=re.M)
    return match.group(1).split() if match else []


def module_order() -> list[str]:
    """The chain as `all:` of the Makefile lists it, then the other modules in byte order."""
    modules = sorted({path.split("/")[0] for path in all_paths() if path.startswith("module_")})
    all_recipe = re.search(r"^all:.*\n\t(.*)$", load_file_text(config.MAKEFILE_PATH), flags=re.M)
    chain = [f"module_{token}" for token in re.findall(r"([a-z]+)-all\b", all_recipe.group(1) if all_recipe else "")]
    chain = [module for module in chain if module in modules]
    return chain + [module for module in modules if module not in chain]


def string_values(node) -> set[str]:
    if isinstance(node, dict):
        return set().union(*map(string_values, node.values()))
    if isinstance(node, list):
        return set().union(*map(string_values, node))
    return {node} if isinstance(node, str) else set()


def is_data_keyed(key: str, value, values: set[str]) -> bool:
    """A dictionary whose keys are data, not names: named `<what>_by_<dimension>`, or every key a datum — a digit in it,
    or a string value the same file carries."""
    return isinstance(value, dict) and ("_by_" in key or (len(value) >= 2 and all(
        re.search(r"\d", child) or child in values for child in value)))


def json_paths(patterns: tuple) -> list[str]:
    """The tracked JSON files a pattern names — never the snapshot this stage writes."""
    snapshot = str(config.SKILLS_STATUS_JSON_PATH.relative_to(config.REPO_ROOT))
    return [path for path in all_paths() if path != snapshot and any(fnmatch.fnmatch(path, pattern) for pattern in patterns)]


def json_entries(path: str):
    """Every key of a JSON file in document order, as (line, dotted key, key, value, is the key a datum, are the value's
    keys data)."""
    text = load_file_text(path)
    payload = json.loads(text)
    values = string_values(payload)
    cursor = 0

    def entries(node, dotted, keyed_by_data):
        nonlocal cursor
        if isinstance(node, dict):
            for key, value in node.items():
                found = text.find(json.dumps(key) + ":", cursor)
                cursor = found + 1 if found >= 0 else cursor
                holds_data_keys = is_data_keyed(key, value, values)
                yield line_of(text, max(found, 0)), f"{dotted}.{key}".lstrip("."), key, value, keyed_by_data, holds_data_keys
                yield from entries(value, f"{dotted}.{key}", holds_data_keys)
        elif isinstance(node, list):
            for value in node:
                yield from entries(value, dotted + "[]", False)

    yield from entries(payload, "", False)


# ---- the six measurement kinds ------------------------------------------------------------------------------------------

def path_segment_in(segments: tuple) -> list[str]:
    return [example(path, 1, segment) for path in all_paths() for segment in path.split("/") if segment in segments]


def python_name_prefix_in(names: list[tuple[str, str, int]], prefixes=(), suffixes=(), whole=(), standing=()) -> list[str]:
    """Names (path, name, line) whose bare form carries a forbidden prefix or suffix, or is a forbidden whole name."""
    return [example(path, line, name) for path, name, line in names if name not in standing
            and (name.lstrip("_").startswith(prefixes) or name.lstrip("_").endswith(suffixes) or name.lstrip("_") in whole)]


def json_key_in(names: tuple, string_suffixes: tuple) -> list[str]:
    return [example(path, line, dotted) for path in json_paths(("*.json",))
            for line, dotted, key, value, _, _ in json_entries(path)
            if key in names or (key.endswith(string_suffixes) and isinstance(value, str))]


def token_in_files(tokens: tuple, seats: tuple, standing_forms: tuple, category: str | None, paths) -> list[str]:
    """A token bounded by anything but a word character, outside its seats — (path, section), the section None for the
    whole file — and outside the standing forms it appears in; the category word stands in for a token that is itself
    the forbidden form."""
    hits = []
    for path in paths:
        text = load_file_text(path)
        spans = [span for span in (section_span(text, section) for seat, section in seats if seat == path) if span]
        for form in standing_forms:
            text = text.replace(form, " " * len(form))
        hits += [example(path, line_of(text, match.start()), category or token)
                 for token in tokens for match in word_pattern(token).finditer(text) if not is_within(match.start(), spans)]
    return hits


def regex_in_prose(pattern: str, excluded, paths) -> list[str]:
    """A pattern in the prose of Markdown — fences and inline code blanked — unless the excluded predicate keeps the word."""
    hits = []
    for path in paths:
        text = re.sub(r"`[^`\n]+`", lambda match: " " * len(match.group(0)), without_fences(load_file_text(path)))
        hits += [example(path, line_of(text, match.start()), match.group(0))
                 for match in re.finditer(pattern, text) if not excluded(match.group(0))]
    return hits


# ---- structural rules (ast_rule) ----------------------------------------------------------------------------------------

def cross_module_imports() -> list[str]:
    hits = []
    for path in python_paths():
        own = path.split("/")[0] if path.startswith("module_") else None
        for node in ast.walk(python_tree(path)):
            names = ([alias.name for alias in node.names] if isinstance(node, ast.Import)
                     else [node.module] if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module else [])
            hits += [example(path, node.lineno, name) for name in names
                     if name.split(".")[0].startswith("module_") and name.split(".")[0] != own]
    return hits


def store_literals_outside_config() -> list[str]:
    hits = []
    for path in python_paths():
        if posixpath.basename(path) == "config.py" or path == config.RECORDER_PATH:
            continue
        tree = python_tree(path)
        docstrings = {id(node.body[0].value) for node in ast.walk(tree)
                      if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body
                      and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)}
        hits += [example(path, node.lineno, node.value) for node in ast.walk(tree)
                 if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings
                 and node.value.startswith(config.STORE_LITERAL_PREFIXES)]
    return hits


def paths_from_file() -> list[str]:
    return [example(path, node.lineno, "__file__") for path in python_paths() if path not in config.PATH_FROM_FILE_STANDING
            for node in ast.walk(python_tree(path)) if isinstance(node, ast.Name) and node.id == "__file__"]


def root_python_outside_record() -> list[str]:
    return [example(path, 1, path) for path in python_paths() if not path.startswith("module_") and path != config.RECORDER_PATH]


def skills_outside_owner_directory() -> list[str]:
    return [example(path, 1, path) for path in all_paths()
            if re.fullmatch(r"(skill|methodology)_.*\.md", posixpath.basename(path))
            and not any(fnmatch.fnmatch(posixpath.dirname(path), pattern) for pattern in config.SKILL_DIRECTORY_PATTERNS)]


def launcher_file_copies() -> list[str]:
    return [example(path, 1, path) for path in all_paths() if path not in config.LAUNCHER_PATHS
            and any(fnmatch.fnmatch(posixpath.basename(path), pattern) for pattern in config.LAUNCHER_NAME_PATTERNS)]


def resident_execs() -> list[str]:
    """A command of the launcher that runs inside a resident rather than in a one-off container."""
    return [example(config.MAKEFILE_PATH, line_number, "exec")
            for line_number, line in enumerate(load_file_text(config.MAKEFILE_PATH).splitlines(), start=1)
            if not line.lstrip().startswith("#") and re.search(r"\bexec\b", line)]


def function_names() -> list[tuple[str, str, int]]:
    return [(path, node.name, node.lineno) for path in python_paths() for node in functions(python_tree(path))]


def boundary_names() -> list[tuple[str, str, int]]:
    """Every name that crosses a function boundary: the function's own and each of its parameters."""
    names = []
    for path in python_paths():
        for node in ast.walk(python_tree(path)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                if not isinstance(node, ast.Lambda):
                    names.append((path, node.name, node.lineno))
                arguments = node.args
                names += [(path, argument.arg, argument.lineno) for argument in
                          arguments.posonlyargs + arguments.args + arguments.kwonlyargs + [arguments.vararg, arguments.kwarg]
                          if argument is not None]
    return names


def numeric_constants_without_unit() -> list[str]:
    hits = []
    for path in python_paths():
        for node in python_tree(path).body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                value = node.value.operand if isinstance(node.value, ast.UnaryOp) else node.value
                name = node.targets[0].id
                if (re.fullmatch(r"[A-Z][A-Z0-9_]*", name) and isinstance(value, ast.Constant)
                        and isinstance(value.value, (int, float)) and not isinstance(value.value, bool)
                        and not name.endswith(config.CONSTANT_UNIT_SUFFIXES)
                        and not any(infix in name for infix in config.CONSTANT_UNIT_INFIXES)):
                    hits.append(example(path, node.lineno, name))
    return hits


def js_function_verbs() -> list[str]:
    pattern = (r"^(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\("
               r"|^(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>"
               r"|^(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s+)?function\b")
    hits = []
    for path in scope_paths():
        if path.endswith(".js"):
            text = load_file_text(path)
            for match in re.finditer(pattern, text, flags=re.M):
                name = match.group(1) or match.group(2) or match.group(3)
                if re.match(r"[a-z]*", name).group(0) in config.JS_FUNCTION_VERB_FORBIDDEN:
                    hits.append(example(path, line_of(text, match.start()), name))
    return hits


def css_classes_outside_bem() -> list[str]:
    """Every class a stylesheet selects, a page writes or a script sets, against BEM."""
    tokens = []
    for path in scope_paths():
        if path.endswith(".css"):
            text = load_file_text(path)
            bare = re.sub(r"/\*.*?\*/", lambda match: re.sub(r"[^\n]", " ", match.group(0)), text, flags=re.S)
            for prelude in re.finditer(r"(?:^|[{}])([^{}]*)\{", bare):
                tokens += [(path, line_of(text, prelude.start(1) + match.start()), match.group(1))
                           for match in re.finditer(r"\.([A-Za-z_-][\w-]*)", prelude.group(1))]
        elif path.endswith(".html"):
            text = load_file_text(path)
            tokens += [(path, line_of(text, match.start()), token)
                       for match in re.finditer(r'class="([^"]*)"', text) for token in match.group(1).split()]
        elif path.endswith(".js"):
            text = load_file_text(path)
            for match in re.finditer(r"classList\.(?:add|remove|toggle|contains)\(([^)]*)\)|className\s*=\s*(\"[^\"]*\"|'[^']*')", text):
                tokens += [(path, line_of(text, match.start()), token)
                           for literal in re.findall(r"[\"']([^\"']+)[\"']", match.group(1) or match.group(2)) for token in literal.split()]
    return [example(path, line, token) for path, line, token in tokens
            if not re.fullmatch(config.CSS_CLASS_GRAMMAR, token) or token in config.CSS_CLASS_FORBIDDEN]


def makefile_targets_outside_grammar() -> list[str]:
    module_tokens = {module.removeprefix("module_") for module in module_order()}
    tickers = {ticker.lower() for ticker in makefile_variable("TICKERS")}

    def is_admissible(target: str) -> bool:
        if target in config.MAKE_TARGET_BARE:
            return True
        if target.startswith("tmux-"):
            return target.removeprefix("tmux-") not in config.MAKE_TARGET_BARE and is_admissible(target.removeprefix("tmux-"))
        token, _, stage = target.partition("-")
        return ((token in module_tokens and re.fullmatch(r"[a-z][a-z0-9]*(-[a-z0-9]+)*", stage) is not None)
                or (token in tickers and stage in config.MAKE_TARGET_TICKER_ALIASES))

    hits = []
    for line_number, line in enumerate(load_file_text(config.MAKEFILE_PATH).splitlines(), start=1):
        match = re.match(r"([^\s:=#.][^:=#]*?)\s*:(?![=:])", line)
        if match:
            hits += [example(config.MAKEFILE_PATH, line_number, target) for target in match.group(1).split()
                     if not target.startswith("$(") and not is_admissible(target)]
    return hits


def glossary_enacted_words() -> set[str]:
    """The words the register enacts: every name in a backtick of a code cell, every word of a UI label cell."""
    words = set()
    for header, _, _, _, cell in table_cells(load_file_text(config.GLOSSARY_PATH)):
        if header == "code":
            words |= {word for span in re.findall(r"`([^`]+)`", cell) for word in re.findall(r"[A-Za-z][\w-]*", span)}
        elif header == "ui label":
            words |= set(re.findall(r"[A-Za-z][\w-]*", cell))
    return words


@functools.cache
def glossary_registered_names() -> frozenset[str]:
    """Every name the register writes in a backtick outside its never cells."""
    text = load_file_text(config.GLOSSARY_PATH)
    never_spans = [(start, end) for header, _, start, end, _ in table_cells(text) if header == "never"]
    return frozenset(name for span in code_spans(text) if not is_within(span.start(), never_spans)
                     for name in re.findall(r"\w+", span.group(1)))


def artifact_keys_without_glossary_row() -> list[str]:
    """A key of a published object with no row in the register; the keys of a dictionary keyed by data are data."""
    names = glossary_registered_names()
    return [example(path, line, dotted) for path in json_paths(config.ARTIFACT_JSON_PATH_PATTERNS)
            for line, dotted, key, _, keyed_by_data, _ in json_entries(path) if not keyed_by_data and key not in names]


def data_keyed_containers_outside_by_grammar() -> list[str]:
    return [example(path, line, dotted) for path in json_paths(config.ARTIFACT_JSON_PATH_PATTERNS)
            for line, dotted, key, _, _, holds_data_keys in json_entries(path) if holds_data_keys and "_by_" not in key]


def design_rationale_source(path: str) -> tuple[str, str] | None:
    for directory in sorted(config.DESIGN_RATIONALE_SOURCE_BY_DIRECTORY, key=len, reverse=True):
        if path.startswith(directory + "/"):
            return directory, config.DESIGN_RATIONALE_SOURCE_BY_DIRECTORY[directory]
    module = path.split("/")[0]
    if module.startswith("module_") and "/" in path:
        return module, config.module_orientation_path(module)
    return None


@functools.cache
def design_rationale_objects(source: str) -> tuple[str, ...]:
    """The objects a source argues, the source among them: every path the index links or names, or the object cells of
    a document's § Design rationale."""
    if source not in all_paths():
        return ()
    text = load_file_text(source)
    span = section_span(text, "Design rationale")
    if source == config.SKILLS_INDEX_PATH:
        tokens = re.findall(r"\]\(([^)]+)\)", text) + [match.group(1) for match in code_spans(text)]
    elif span:
        tokens = [match.group(1) for header, _, start, _, cell in table_cells(text)
                  if header == "object" and span[0] <= start < span[1] for match in re.finditer(r"`([^`]+)`", cell)]
    else:
        tokens = []
    return tuple(tokens + [posixpath.basename(source)])


def is_argued(path: str) -> bool:
    directory, source = design_rationale_source(path)
    relative = path.removeprefix(directory + "/")
    return any(token.rstrip("/") in (relative, path) or (token.endswith("/") and (relative.startswith(token) or path.startswith(token)))
               for token in design_rationale_objects(source))


def files_without_design_rationale_row() -> list[str]:
    return [example(path, 1, path) for path in scope_paths() if design_rationale_source(path) and not is_argued(path)]


@functools.cache
def is_ignored(path: str) -> bool:
    """Whether .gitignore keeps the path out of the tree — state a store holds and git never tracks."""
    return subprocess.run(("git", "check-ignore", "-q", "--no-index", "--", path), cwd=config.REPO_ROOT).returncode == 0


def is_reference_resolved(candidate: str, stores: list[str]) -> bool:
    pattern = re.sub(r"<[^>]*>", "*", candidate)
    bare = pattern.rstrip("/")
    if "*" in bare:
        tracked = (any(fnmatch.fnmatch(store, bare) for store in stores)
                   or any(fnmatch.fnmatch(path, bare) or fnmatch.fnmatch(path, bare + "/*") for path in all_paths()))
    else:
        tracked = bare in all_paths() or bare in tracked_directories()
    under_store = any(bare == store or bare.startswith(store + "/") for store in stores)
    return tracked or (under_store and is_ignored(bare + "/" if pattern.endswith("/") or bare in stores else bare))


def path_references_unresolved() -> list[str]:
    """A backticked path of a document that names nothing in the tree — the six rules of the skill."""
    tops = {path.split("/")[0] for path in all_paths()}
    stores = makefile_variable("STORES")
    hits = []
    for path in scope_paths():
        if not path.endswith(".md"):
            continue
        text = load_file_text(path)
        refused = ([(start, end) for header, _, start, end, _ in table_cells(text) if header in ("never", "what it forbids")]
                   + [(start, end) for title, start, end in section_spans(text)
                      if title in ("Rejected vocabulary", "Skills absent here, described")])
        directory = posixpath.dirname(path)
        module = path.split("/")[0] if "/" in path else ""
        for span in code_spans(text):
            token = re.sub(r":\d+(-\d+)?$", "", span.group(1))
            if re.search(r"\s", token) or "://" in token or token.startswith("/"):
                continue
            if "/" not in token and not re.search(REFERENCE_SUFFIX_PATTERN, token):
                continue
            first = token.split("/")[0]
            local = posixpath.join(directory, first)
            if not (first in tops or first == ".." or local in all_paths() or local in tracked_directories()):
                continue
            if is_within(span.start(), refused):
                continue
            candidates = {posixpath.normpath(posixpath.join(base, token)) for base in (directory, module, "")}
            if not any(is_reference_resolved(candidate, stores) for candidate in candidates):
                hits.append(example(path, line_of(text, span.start()), token))
    return hits


def skills_without_index_row() -> list[str]:
    index = config.SKILLS_INDEX_PATH
    named = {posixpath.normpath(posixpath.join(base, token)) for token in design_rationale_objects(index)
             for base in (posixpath.dirname(index), "")}
    return [example(path, 1, path) for path in all_paths()
            if re.fullmatch(r"(skill|methodology)_.*\.md", posixpath.basename(path)) and path not in named]


def filenames_outside_family_token() -> list[str]:
    hits = []
    for path in all_paths():
        directory, name = posixpath.split(path)
        for pattern_directory, patterns in config.FAMILY_NAME_PATTERNS_BY_DIRECTORY.items():
            if directory.count("/") == pattern_directory.count("/") and fnmatch.fnmatch(directory, pattern_directory):
                folder = posixpath.basename(directory)
                if not any(fnmatch.fnmatch(name, pattern.format(folder=folder)) for pattern in patterns):
                    hits.append(example(path, 1, name))
    return hits


def definition_forms(path: str, name: str) -> list[tuple[str, str, int]]:
    """How one owner defines a registered copy: a function as its syntax tree, a constant as its value when it is a
    literal, else as the tree of its expression."""
    text = load_file_text(path)
    if path.endswith(".js"):
        match = re.search(rf"^\s*const\s+{re.escape(name)}\s*=\s*([^;]+);", text, flags=re.M)
        if not match:
            return []
        try:
            return [("value", repr(ast.literal_eval(match.group(1).strip())), line_of(text, match.start()))]
        except (ValueError, SyntaxError):
            return [("expression", match.group(1).strip(), line_of(text, match.start()))]
    forms = []
    for node in python_tree(path).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            forms.append(("tree", ast.dump(node), node.lineno))
        elif isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            try:
                forms.append(("value", repr(ast.literal_eval(node.value)), node.lineno))
            except ValueError:
                forms.append(("expression", ast.dump(node.value), node.lineno))
    return forms


def twice_by_extraction_drift() -> list[str]:
    """A registered copy whose owners disagree — as syntax trees for a function, as values for a literal; an owner that
    derives by an expression what another owner writes as a literal is not compared with it."""
    text = load_file_text(config.GLOSSARY_PATH)
    span = section_span(text, "Twice by extraction")
    rows = {}
    for header, row, start, _, cell in table_cells(text):
        if span[0] <= start < span[1]:
            rows.setdefault(row, {})[header] = cell
    hits = []
    for cells in rows.values():
        objects = {name.removesuffix("()") for name in re.findall(r"`([A-Za-z_]\w*(?:\(\))?)`", cells.get("object", ""))}
        owners = [owner for owner in re.findall(r"`([^`]+\.(?:py|js))`", cells.get("owners", "")) if owner in all_paths()]
        for name in sorted(objects):
            forms = [(owner, form) for owner in owners for form in definition_forms(owner, name)]
            if len({kind for _, (kind, _, _) in forms}) > 1:
                forms = [(owner, form) for owner, form in forms if form[0] != "expression"]
            if len(forms) >= 2 and len({body for _, (_, body, _) in forms}) > 1:
                owner, (_, _, line) = forms[-1]
                hits.append(example(owner, line, name))
    return hits


def enumeration_families() -> dict[str, dict[str, re.Pattern]]:
    """The families whose enumerations are meant to be complete, each member with the pattern prose names it by."""
    index = next(path for path in all_paths() if path.endswith(".html") and 'id="tabs"' in load_file_text(path))
    html = load_file_text(index)
    nav = re.search(r'<nav id="tabs".*?</nav>', html, flags=re.S).group(0)

    def words(members):
        return {member: word_pattern(member) for member in members}

    return {
        "snapshots": words(posixpath.basename(path) for path in all_paths() if fnmatch.fnmatch(path, config.SNAPSHOT_PATH_PATTERN)),
        "tabs": words(label.strip() for label in re.findall(r"<button[^>]*>([^<]+)</button>", nav)),
        "stores": words(makefile_variable("STORES")),
        "modules": words(module_order()),
        "section scripts": words(src for src in re.findall(r'<script src="([^"]+)"', html) if src != "page.js"),
    }


def incomplete_enumerations() -> list[str]:
    """A list of two or more members of a family, members joined by nothing but separators, that misses one; or a number
    word before the family's noun that is not the family's size."""
    families = enumeration_families()
    hits = []
    for path in scope_paths():
        if not path.endswith((".md", ".html", ".py", ".js")):
            continue
        text = without_fences(load_file_text(path))
        for family, members in families.items():
            mentions = sorted((match.start(), match.end(), member) for member, pattern in members.items()
                              for match in pattern.finditer(text))
            run = []
            for mention in mentions + [None]:
                if run and (mention is None or not re.fullmatch(ENUMERATION_SEPARATOR_PATTERN, text[run[-1][1]:mention[0]])):
                    named = list(dict.fromkeys(member for _, _, member in run))
                    if 2 <= len(named) < len(members):
                        hits.append(example(path, line_of(text, run[0][0]), f"{family}: {', '.join(named)}"))
                    run = []
                if mention:
                    run.append(mention)
        for match in re.finditer(r"\b(two|three|four|five|six|seven|eight|nine|ten)\s+(?:[\w-]+\s+){0,2}?"
                                 r"(snapshot|tab|store|module|script)s\b", text, flags=re.I):
            if NUMBER_WORDS[match.group(1).lower()] != len(families[FAMILY_NOUNS[match.group(2).lower()]]):
                hits.append(example(path, line_of(text, match.start()), match.group(0)))
    return hits


def normative_documents_without_motto() -> list[str]:
    return [example(path, 1, path) for path in tracked_paths(*config.CANON_PATHSPECS) if path != config.CONTRACT_PATH
            and config.MOTTO not in re.sub(r"\s+", " ", load_file_text(path).replace("*", ""))]


# ---- the review record ----------------------------------------------------------------------------------------------------

@functools.cache
def blob_ids() -> dict[str, str]:
    return {line.split("\t", 1)[1]: line.split()[2] for line in git("ls-tree", "-r", "HEAD").splitlines()}


def canon_id(blobs: dict[str, str] | None = None) -> str:
    """The identity of the canon's content: its paths and blobs — of HEAD, or of the blobs a caller names."""
    blobs = blob_ids() if blobs is None else blobs
    lines = sorted(f"{path} {blobs.get(path, '')}" for path in tracked_paths(*config.CANON_PATHSPECS))
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


@functools.cache
def load_review_record() -> dict:
    return json.loads(config.SKILLS_REVIEW_JSON_PATH.read_text(encoding="utf-8"))


def current_review_rows() -> list[dict]:
    """The rows of the record whose file is still the blob they reviewed."""
    return [row for row in load_review_record()["files"]
            if row["path"] in crawl_paths() and blob_ids().get(row["path"]) == row["blob_id"]]


@functools.cache
def review_values() -> dict[str, tuple]:
    rows = current_review_rows()
    scope = crawl_paths()
    changed = [row for row in load_review_record()["files"] if row["path"] in scope and blob_ids().get(row["path"]) != row["blob_id"]]
    stale = [row for row in rows if row["canon_id"] != canon_id()]
    levels = [row["self_explaining_level"] for row in rows if row["self_explaining_level"] is not None]
    proposals = [proposal for proposal in load_review_record()["proposals"] if proposal["canon_id"] == canon_id()]

    def listed(selected):
        return [example(row["path"], 1, row["verdict"]) for row in selected]

    values = {
        "files_reviewed_pct": (config.rounded(100 * len(rows) / len(scope), config.PCT_DECIMAL_COUNT) if scope else None, listed(rows)),
        "changed_since_review_count": (len(changed), listed(changed)),
        "stale_count": (len(stale), listed(stale)),
        "finding_count": (sum(len(row["findings"]) for row in rows), [finding["example"] for row in rows for finding in row["findings"]]),
        "proposal_count": (len(proposals), [f"{proposal['occurrences'][0]} — {proposal['pattern']}" for proposal in proposals]),
        "self_explaining_level_mean": (config.rounded(sum(levels) / len(levels), config.LEVEL_MEAN_DECIMAL_COUNT) if levels else None,
                                       [row["evidence"] for row in rows if row["evidence"]]),
    }
    for verdict in ("conformant", "amended", "deferred"):
        selected = [row for row in rows if row["verdict"] == verdict]
        values[f"{verdict}_file_count"] = (len(selected), listed(selected))
    return values


# ---- the registry and the snapshot ------------------------------------------------------------------------------------------

def markdown_paths() -> list[str]:
    return [path for path in scope_paths() if path.endswith(".md")]


# every metric, named once: (metric, family, kind, rule, measure) — a kind is the register's (module_skills/glossary.md
# § Data quality); a measure returns the places it found, or (value, places)
METRICS = (
    ("cross_module_import_count", "modularity", "invariant", "AGENTS.md § Architecture shape, no module imports another",
     cross_module_imports),
    ("store_literal_outside_config_count", "modularity", "invariant",
     "AGENTS.md § Architecture shape, paths built only in a module's config.py", store_literals_outside_config),
    ("path_from_file_count", "modularity", "invariant", "AGENTS.md § Canonical vocabulary, the row store paths", paths_from_file),
    ("root_python_outside_record_count", "modularity", "invariant", "AGENTS.md § The shape, D01", root_python_outside_record),
    ("skill_outside_owner_directory_count", "modularity", "invariant", "AGENTS.md § The shape, D03",
     skills_outside_owner_directory),
    ("launcher_file_copy_count", "modularity", "invariant",
     "AGENTS.md § The shape, D05; § Rejected vocabulary, a second compose file, a second Makefile", launcher_file_copies),
    ("resident_exec_count", "modularity", "invariant", "AGENTS.md § The shape, D16", resident_execs),
    ("function_verb_outside_grammar_count", "naming", "invariant",
     "AGENTS.md § Canonical vocabulary, the function rows; skill_self_explaining_naming.md § The closed list absorbs its synonyms",
     lambda: python_name_prefix_in(function_names(), prefixes=config.FUNCTION_VERB_FORBIDDEN_PREFIXES,
                                   suffixes=config.FUNCTION_VERB_FORBIDDEN_SUFFIXES, whole=config.FUNCTION_NAME_FORBIDDEN,
                                   standing=config.FUNCTION_NAME_STANDING)),
    ("js_function_verb_outside_grammar_count", "naming", "invariant",
     "AGENTS.md § Canonical vocabulary, the row JavaScript functions at file scope", js_function_verbs),
    ("local_abbreviation_crossing_boundary_count", "naming", "invariant",
     "AGENTS.md § Canonical vocabulary, local abbreviations never cross a function boundary",
     lambda: python_name_prefix_in(boundary_names(), whole=config.LOCAL_ABBREVIATIONS)),
    ("css_class_outside_bem_count", "naming", "invariant", "AGENTS.md § Canonical vocabulary, the row CSS", css_classes_outside_bem),
    ("make_target_outside_grammar_count", "naming", "invariant", "AGENTS.md § Canonical vocabulary, the row Makefile targets",
     makefile_targets_outside_grammar),
    ("numeric_constant_without_unit_count", "naming", "observation",
     "AGENTS.md § Canonical vocabulary, unless the name already says what is counted", numeric_constants_without_unit),
    ("british_spelling_count", "naming", "observation", "AGENTS.md § Canonical vocabulary, British spelling throughout the prose",
     lambda: regex_in_prose(r"\b[A-Za-z]+iz(?:e|es|ed|ing|ation|ations)\b",
                            lambda word: re.match(r"(s|pr|se|caps)iz", word.lower()) is not None, markdown_paths())),
    ("debt_marker_count", "vocabulary", "invariant", "AGENTS.md § Values, no debt marker in a tracked file",
     lambda: token_in_files(config.DEBT_MARKERS, config.DEBT_MARKER_SEATS, (), "debt marker", scope_paths())),
    ("rejected_path_segment_count", "vocabulary", "invariant", "AGENTS.md § Rejected vocabulary, directories and path segments",
     lambda: path_segment_in(config.REJECTED_PATH_SEGMENTS)),
    ("rejected_key_name_count", "vocabulary", "invariant", "AGENTS.md § Rejected vocabulary, key names",
     lambda: json_key_in(config.REJECTED_KEY_NAMES, config.REJECTED_STRING_KEY_SUFFIXES)),
    ("cloud_noun_outside_seat_count", "vocabulary", "invariant",
     "AGENTS.md § Pre-AWS architectural direction, where a cloud proper noun is spoken",
     lambda: token_in_files(config.CLOUD_NOUNS, config.CLOUD_NOUN_SEATS, config.CLOUD_NOUN_STANDING_FORMS, "cloud noun",
                            scope_paths())),
    ("rejected_interface_word_count", "vocabulary", "observation", "AGENTS.md § Rejected vocabulary, interface words",
     lambda: token_in_files(tuple(word for word in config.REJECTED_INTERFACE_WORDS if word not in glossary_enacted_words()),
                            (), (), None, [path for path in scope_paths() if path.endswith((".html", ".js"))])),
    ("file_without_design_rationale_row_count", "self-explaining", "invariant",
     "AGENTS.md § Pre-AWS architectural direction, every placement is argued", files_without_design_rationale_row),
    ("artifact_key_without_glossary_row_count", "self-explaining", "invariant", "AGENTS.md § The shape, D09",
     artifact_keys_without_glossary_row),
    ("data_keyed_container_outside_by_grammar_count", "self-explaining", "observation",
     "module_skills/glossary.md § Data quality, one share per venue, keyed by it", data_keyed_containers_outside_by_grammar),
    ("path_reference_unresolved_count", "self-explaining", "invariant",
     "AGENTS.md § Architecture shape, a reference is a path in backticks", path_references_unresolved),
    ("skill_without_index_row_count", "self-explaining", "invariant", "AGENTS.md § The default choice, the index links every skill",
     skills_without_index_row),
    ("filename_outside_family_token_count", "sorting", "invariant",
     "module_skills/skill_sorting_files_naming_standard.md, taxonomic ordering", filenames_outside_family_token),
    ("twice_by_extraction_drift_count", "sorting", "invariant", "AGENTS.md § The shape, D14", twice_by_extraction_drift),
    ("enumeration_incomplete_count", "documents", "observation",
     "AGENTS.md § Canonical vocabulary, rule-derived structure over repeated project knowledge", incomplete_enumerations),
    ("normative_document_without_motto_count", "documents", "observation", "AGENTS.md § Values, destination, not road",
     normative_documents_without_motto),
    ("files_reviewed_pct", "review", "observation", REVIEW_RULE, lambda: review_values()["files_reviewed_pct"]),
    ("changed_since_review_count", "review", "observation", REVIEW_RULE, lambda: review_values()["changed_since_review_count"]),
    ("stale_count", "review", "observation", REVIEW_RULE, lambda: review_values()["stale_count"]),
    ("conformant_file_count", "review", "observation", REVIEW_RULE, lambda: review_values()["conformant_file_count"]),
    ("amended_file_count", "review", "observation", REVIEW_RULE, lambda: review_values()["amended_file_count"]),
    ("deferred_file_count", "review", "observation", REVIEW_RULE, lambda: review_values()["deferred_file_count"]),
    ("finding_count", "review", "observation", REVIEW_RULE, lambda: review_values()["finding_count"]),
    ("proposal_count", "review", "observation", REVIEW_RULE, lambda: review_values()["proposal_count"]),
    ("self_explaining_level_mean", "review", "observation", REVIEW_RULE, lambda: review_values()["self_explaining_level_mean"]),
)


def metric_block(metric: str, family: str, kind: str, rule: str, measure) -> dict:
    measured = measure()
    value, found = measured if isinstance(measured, tuple) else (len(measured), measured)
    return {"family": family, "metric": metric, "kind": kind, "value": value,
            "examples": sorted(found)[:config.EXAMPLES_PER_METRIC_COUNT], "rule": rule}


def module_block(module: str) -> dict:
    files = [path for path in scope_paths() if path.startswith(module + "/")]
    trees = [python_tree(path) for path in files if path.endswith(".py")]
    public = [node for tree in trees for node in functions(tree) if not node.name.startswith("_")]
    reviewed = {row["path"] for row in current_review_rows()}
    listed = [path for path in files if path in crawl_paths()]

    def pct(part: int, whole: int):
        return config.rounded(100 * part / whole, config.PCT_DECIMAL_COUNT) if whole else None

    return {
        "module": module,
        "file_count": len(files),
        "python_line_count": sum(len(load_file_text(path).splitlines()) for path in files if path.endswith(".py")),
        "function_count": sum(len(functions(tree)) for tree in trees),
        "class_count": sum(isinstance(node, ast.ClassDef) for tree in trees for node in ast.walk(tree)),
        "design_rationale_row_pct": pct(sum(is_argued(path) for path in files), len(files)),
        "module_docstring_pct": pct(sum(ast.get_docstring(tree) is not None for tree in trees), len(trees)),
        "public_function_docstring_pct": pct(sum(ast.get_docstring(node) is not None for node in public), len(public)),
        "files_reviewed_pct": pct(sum(path in reviewed for path in listed), len(listed)),
    }


def shape_block(metrics: list[dict]) -> list[dict]:
    """The rows of AGENTS.md § The shape at the measured commit, each with its evidence: a row holds when the invariant
    its evidence names reads zero; a row whose evidence is a target is proven by hand, and holds nothing here."""
    text = load_file_text(config.CONTRACT_PATH)
    span = section_span(text, config.SHAPE_SECTION_TITLE)
    values = {row["metric"]: row["value"] for row in metrics}
    conditions = [cell.strip() for header, _, start, _, cell in table_cells(text) if header == "#" and span[0] <= start < span[1]]
    return [{"condition": condition, "evidence": config.SHAPE_EVIDENCE_BY_CONDITION.get(condition),
             "holds": values[config.SHAPE_EVIDENCE_BY_CONDITION[condition]] == 0
             if config.SHAPE_EVIDENCE_BY_CONDITION.get(condition) in values else None}
            for condition in conditions]


def build_skills_status() -> dict:
    snapshot = config.SKILLS_STATUS_JSON_PATH.relative_to(config.REPO_ROOT)
    commit, committed_at = git("log", "-1", "--format=%H %ct", "--", ".", f":(exclude){snapshot}").split()
    metrics = [metric_block(*row) for row in METRICS]
    return {
        "measured_at_commit": commit,
        "measured_at_commit_utc": datetime.fromtimestamp(int(committed_at), tz=UTC).strftime("%Y-%m-%d %H:%M:%S"),
        "files_in_scope_count": len(scope_paths()),
        "python_line_count": sum(len(load_file_text(path).splitlines()) for path in python_paths()),
        "shape": shape_block(metrics),
        "metrics": metrics,
        "modules": [module_block(module) for module in module_order()],
    }


def main() -> int:
    payload = build_skills_status()
    config.SKILLS_STATUS_JSON_PATH.write_text(json.dumps(payload, sort_keys=True, indent=1) + "\n", encoding="utf-8")
    raised = [row["metric"] for row in payload["metrics"] if row["kind"] == "invariant" and row["value"]]
    print(f"wrote {config.SKILLS_STATUS_JSON_PATH}: {len(payload['metrics'])} metrics, "
          f"{len(raised)} invariant(s) above zero{': ' + ', '.join(raised) if raised else ''}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
