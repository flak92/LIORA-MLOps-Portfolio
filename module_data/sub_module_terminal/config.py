"""The data terminal's one surface of configuration: the targets its menu offers and whether its output is plain.

It runs on the host, on `python3` and gum, with no virtual environment: it imports the standard library and its own
package alone. `module_data/config.py` is standard library and is imported by terminal.py for the venues and the
descriptors of every path this terminal reads — each venue's raw leaf and the asset's canonical partition — so no descriptor
is carried here; what is carried, twice by extraction, is the plain-output conditions every `tui.py` reads from its
own `config.py`."""

import os
import re
import sys

# plain output — state words in brackets, no colour, no symbol, no border: NO_COLOR set and not empty, TERM=dumb,
# or standard output not a terminal (module_skills/skill_tui_designer.md, TUI-DESIGNER-PLAIN-OUTPUT-FOLLOWS-THE-ENVIRONMENT)
# twice by extraction
OUTPUT_PLAIN = (bool(os.environ.get("NO_COLOR")) or os.environ.get("TERM") == "dumb"
                or not sys.stdout.isatty())

MENU_TARGET_PATTERN = re.compile(r"^(tmux-)?data-")  # this module's targets of `make help`, the terminal-menu row
