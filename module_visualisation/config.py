"""Paths and defaults for the visualisation generator — the only place this module builds a path.

The module deliberately imports nothing from module_data or module_ml. Those
modules are the runtime pipeline and pull duckdb, numpy and xgboost with them;
this one has to run on a bare CI runner with no virtual environment, so its
only dependencies are the standard library and the git binary. The repository
root is therefore derived here rather than re-exported from module_data.config.

The defaults below are what the generator does when visualisation_config.json says
nothing. Every one of them is overridable from that file, and the file wins:
an unknown key there is an error rather than a silent typo, so the JSON is the
whole configuration surface and Python is never edited to change the picture.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

MODULE_VISUALISATION_DIR = REPO_ROOT / "module_visualisation"
VISUALISATION_CONFIG_JSON_PATH = MODULE_VISUALISATION_DIR / "visualisation_config.json"
VISUALISATION_TEMPLATE_HTML_PATH = MODULE_VISUALISATION_DIR / "files_and_folders_visualisation_template.html"

MODULE_MONITORING_DIR = REPO_ROOT / "module_monitoring"
MODULE_MONITORING_FILES_AND_FOLDERS_VISUALISATION_HTML_PATH = MODULE_MONITORING_DIR / "files_and_folders_visualisation.html"

# the one region of the template the generator owns; everything outside it is
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
STORY_KEYS = {"name", "color", "hub"}
PLACE_KEYS = {"r", "da", "y", "jit"}
HEADER_KEYS = {"eyebrow_from_git", "title", "subtitle"}
CORE_KEYS = {"name", "color"}
