"""The skills terminal's one surface of configuration: the targets its menu offers and whether its output is plain.

The actions it offers are not listed here: they are the targets of the Makefile that carry a `##` and that
`MENU_TARGET_PATTERN` gives the canon, read from `make help` where the menu is drawn, so this file holds no second list
of them. What it shows of the canon — the root of the tree and the sheet — is the package's own, in
`module_skills/config.py`.

It runs on the host, on `python3` and gum, with no virtual environment: it imports the standard library and its own
package alone, and every action it starts, it starts through `make`, the Makefile being where the canon's stages
are named."""

import os
import re
import sys

# plain output — state words in brackets, no colour, no symbol, no border: NO_COLOR set and not empty, TERM=dumb, or
# standard output not a terminal (module_skills/skill_tui_designer.md, TUI-DESIGNER-PLAIN-OUTPUT-FOLLOWS-THE-ENVIRONMENT)
# twice by extraction
OUTPUT_PLAIN = (bool(os.environ.get("NO_COLOR")) or os.environ.get("TERM") == "dumb"
                or not sys.stdout.isatty())

MENU_TARGET_PATTERN = re.compile(r"^skills-")  # the canon's targets of `make help`, the terminal-menu row
