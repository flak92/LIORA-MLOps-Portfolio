"""Stage: the table of every CONFIGURABLES record the project holds, on stdout — `make skills-configurables`.

The files are the files matrix's own: every controlled `config.py` whose module level assigns the block, in path
order. A file is read as text and its block evaluated as a literal, never imported, so no stage of any module
runs here and nothing is installed for it; the records are printed in the block's order, one row each, the file they
live in first. The table is rendered from the records and written nowhere, so it is never a second place a value is
written; the same records print the same bytes.
"""

import ast
import json

from . import config, sheet
from .sub_module_scalability_crawler import crawl


def load_records(path) -> tuple | None:
    """The file's CONFIGURABLES block as the literal it is written as, or None where the file assigns none."""
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == config.CONFIGURABLES_NAME
                                                for target in node.targets):
            return ast.literal_eval(node.value)
    return None


def to_cell(value) -> str:
    """A field as a table cell: text as it is, a yes or no for a flag, anything else as the JSON it travels as."""
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "yes" if value else "no"
    return json.dumps(value, ensure_ascii=False)


def main() -> int:
    rows = []
    for controlled_file in crawl.build_controlled_files(sheet.load_sheet()):
        if controlled_file.path.name != "config.py":
            continue
        records = load_records(controlled_file.path)
        for record in records or ():
            rows.append([controlled_file.key, *(to_cell(record[field]) for field in config.CONFIGURABLE_FIELDS)])
    header = ("file", *config.CONFIGURABLE_FIELDS)
    print("| " + " | ".join(header) + " |")
    print("|" + "---|" * len(header))
    for row in rows:
        print("| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
