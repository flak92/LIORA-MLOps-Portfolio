"""Paths and defaults for the developer-experience picture — the only place this sub-module builds a path.

It imports nothing from module_data or module_ml. Those are the runtime pipeline
and pull duckdb, numpy and xgboost with them; this one is standard library plus
the git binary, so it runs on a bare clone with no virtual environment.

The defaults below are what the picture uses when visualisation_config.json says
nothing. Every one of them is overridable from that file, and the file wins: an
unknown key there is an error rather than a silent typo, so the JSON is the whole
configuration surface and Python is never edited to change the drawing.
"""

from __future__ import annotations

from pathlib import Path

# three hops, not two: this sub-module sits one level below the module that holds
# it, and a wrong root does not raise — it silently draws a subtree instead of the
# repository
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

SUB_MODULE_DX_DIR = Path(__file__).resolve().parent
VISUALISATION_CONFIG_JSON_PATH = SUB_MODULE_DX_DIR / "visualisation_config.json"
VISUALISATION_TEMPLATE_HTML_PATH = SUB_MODULE_DX_DIR / "files_and_folders_visualisation_template.html"
FILES_AND_FOLDERS_VISUALISATION_HTML_PATH = SUB_MODULE_DX_DIR / "files_and_folders_visualisation.html"

MAKE_TARGET = "monitoring-dx-update"

# the one region of the template this sub-module writes; everything outside it is
# hand-written rendering code and is never touched
STRUCTURE_BEGIN_MARKER = "/* VISUALISATION:STRUCTURE:BEGIN"
STRUCTURE_END_MARKER = "/* VISUALISATION:STRUCTURE:END */"

# camera knobs, named in the JSON in snake_case and in the template in the
# renderer's own vocabulary; the mapping is fixed so an unknown camera key can
# be reported instead of silently ignored
CAMERA_KEYS = {
    "start_rot_y": "START_ROT_Y",
    "start_rot_x": "START_ROT_X",
    "fit_width": "FIT_WIDTH",
}

# a role decides the glyph the renderer draws and the word the side panel shows;
# these are the fallbacks, and visualisation_config.json's "roles" overrides any of them
ROLE_BY_EXACT_NAME = {
    "Makefile": "entrypoint",
    "Dockerfile": "config",
    "docker-compose.yml": "config",
    "requirements.txt": "config",
}
ROLE_BY_SUFFIX = {
    ".md": "doc",
    ".py": "code",
    ".js": "code",
    ".css": "code",
    ".html": "code",
    ".json": "artifact",
    ".yml": "config",
    ".yaml": "config",
}
ROLE_FOR_FOLDER = "module"
ROLE_FOR_ROOT = "root"
ROLE_FALLBACK = "file"

CONFIG_DEFAULTS = {
    "default_story": None,
    "exclude": [],
    "story_map": {},
    "stories": {},
    "story_order": None,
    "core": {"name": "Repository root", "color": "#EDF2FF"},
    "aggregate": {},
    "descriptions": {},
    "roles": {},
    "place": {},
    "camera": {},
    "header": {},
}
STORY_IDS = {"S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"}   # the drawing gives an island one digit; a tenth story is a different picture
STORY_KEYS = {"name", "color", "hub"}
PLACE_KEYS = {"r", "da", "y", "jit"}
HEADER_KEYS = {"eyebrow_from_git", "title", "subtitle"}
CORE_KEYS = {"name", "color"}
