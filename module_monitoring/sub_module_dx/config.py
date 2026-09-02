"""Paths and defaults for the developer-experience picture — the only place this sub-module builds a path.

It imports nothing from module_data or module_ml. Those are the runtime pipeline
and pull duckdb, numpy and xgboost with them; this one is standard library plus
the git binary, so it runs on a bare clone with no virtual environment.

The defaults below are what the picture uses when visualisation_config.json says
nothing. Every one of them is overridable from that file, and the file wins: an
unknown key there is an error rather than a silent typo, so the JSON is the whole
configuration surface and Python is never edited to change the drawing.

The optional `deployment` block restates the placement keys for a second view of
the same tree; a key it leaves out is the top level's, and its roles, descriptions
and camera layer over the top level's entry by entry. A view may also declare
primitives — what it seats the tree beside, one icon each — and the flows between
them; a primitive exists in the view that declares it.
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
    "fit_zoom": "FIT_ZOOM",
}

# a role decides the glyph the renderer draws and the word the side panel shows;
# these are the fallbacks, and a view's "roles" in visualisation_config.json retypes any of them
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
    "primitives": {},   # id -> {role, name, absent}: what a view seats the tree beside, one icon each
    "flows": [],        # {from, to} over two primitive ids of the view, drawn as a dashed arrow
    "place": {},
    "camera": {},
    "header": {},
    "deployment": None,   # the second view of the same tree; None means one view and no view control
}
STORY_IDS = {"S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"}   # the drawing gives an island one digit; a tenth story is a different picture
STORY_KEYS = {"name", "color", "hub"}
PLACE_KEYS = {"r", "da", "y", "jit"}
HEADER_KEYS = {"eyebrow_from_git", "title", "subtitle"}
CORE_KEYS = {"name", "color"}
PRIMITIVE_KEYS = {"role", "name", "absent"}
# the roles that are icons, one each in the template's drawPrimitiveIcon — closed, because a
# primitive is nothing but its icon and a role outside this set has no icon to call
PRIMITIVE_ROLES = {"registry", "instance", "container", "store", "database", "state_machine",
                   "event_rule", "log_streams", "front", "secret"}
FLOW_KEYS = {"from", "to"}

# what a second view of the same tree restates; exclude, aggregate and header define the
# tree and are shared by every view
VIEW_KEYS = {"default_story", "story_map", "stories", "story_order", "core", "place", "roles",
             "descriptions", "camera", "primitives", "flows"}
LAYERED_VIEW_KEYS = {"roles", "descriptions", "camera"}   # laid over the top level's entry by entry; every other view key replaces it whole
DEVELOPMENT_VIEW = "development"   # the top level of the JSON: the tree as tracked
DEPLOYMENT_VIEW = "deployment"     # the block of that name: the same tree on the primitives the mapping table names
