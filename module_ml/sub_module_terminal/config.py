"""The ML terminal's one surface of configuration: the reader of the contract it shows a hand, the targets its menu
offers and whether its output is plain.

It runs on the host, on `python3` and gum, with no virtual environment: it imports the standard library and its own
package alone. `module_ml/config.py` is standard library and is imported by terminal.py for the descriptors of every
file this terminal reads; `module_ml/dataset.py` is not — it imports duckdb and numpy — so the reader of JSON it shares
with that module is carried here, twice by extraction."""

import json
import os
import re
import sys
from pathlib import Path


# twice by extraction
def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# plain output — state words in brackets, no colour, no symbol, no border: NO_COLOR set and not empty, TERM=dumb,
# or standard output not a terminal (module_skills/skill_tui_designer.md, TUI-DESIGNER-PLAIN-OUTPUT-FOLLOWS-THE-ENVIRONMENT)
# twice by extraction
OUTPUT_PLAIN = (bool(os.environ.get("NO_COLOR")) or os.environ.get("TERM") == "dumb"
                or not sys.stdout.isatty())

MENU_TARGET_PATTERN = re.compile(r"^(tmux-)?ml-")  # this module's targets of `make help`, the terminal-menu row
