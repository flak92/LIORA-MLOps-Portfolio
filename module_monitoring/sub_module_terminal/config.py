"""The monitoring terminal's one surface of configuration: the status store and the snapshots it shows, the one reader
of JSON, the targets its menu offers and whether its output is plain.

It runs on the host, on `python3` and gum, with no virtual environment: it imports the standard library and its own
package alone. The status store arrives as `STORE_STATUS_DIR`, which the Makefile exports; what is carried, twice by
extraction, is that store's variable, the one reader of JSON and the plain-output conditions every `tui.py` reads from
its own `config.py`; the names of the four snapshots the page reads are this terminal's own."""

import json
import os
import re
import sys
from pathlib import Path

# the status store the page reads beside it as status/ — the store contract, one variable per store
# twice by extraction
STORE_STATUS_DIR = Path(os.environ["STORE_STATUS_DIR"])
# the four snapshots the page reads, in the order of its tabs' writers
SNAPSHOT_FILE_NAMES = ("data_status.json", "features_status.json", "ml_status.json", "skills_status.json")


# twice by extraction
def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# plain output — state words in brackets, no colour, no symbol, no border: NO_COLOR set and not empty, TERM=dumb, or
# standard output not a terminal (module_skills/skill_tui_designer.md, TUI-DESIGNER-PLAIN-OUTPUT-FOLLOWS-THE-ENVIRONMENT)
# twice by extraction
OUTPUT_PLAIN = (bool(os.environ.get("NO_COLOR")) or os.environ.get("TERM") == "dumb"
                or not sys.stdout.isatty())

MENU_TARGET_PATTERN = re.compile(r"^(on|off)$")  # the presentation switch of `make help` (TUI-DESIGNER-ACTIONS-COME-FROM-MAKEFILE)
