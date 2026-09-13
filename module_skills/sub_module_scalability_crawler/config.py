"""The crawler's one surface of configuration: where it writes, what it measures and the closed lists it measures with —
each list read off the section of AGENTS.md or of a skill its comment names, and moved in the commit that moves that
section. The checkout is git's answer, never a path derived from this file."""

from __future__ import annotations

import os
import subprocess

from pathlib import Path

REPO_ROOT = Path(subprocess.run(("git", "rev-parse", "--show-toplevel"), capture_output=True, text=True,
                                check=True).stdout.strip())
STORE_STATUS_DIR = Path(os.environ["STORE_STATUS_DIR"])
SKILLS_STATUS_JSON_PATH = STORE_STATUS_DIR / "skills_status.json"   # the snapshot status.py writes and never reads back
SKILLS_REVIEW_JSON_PATH = STORE_STATUS_DIR / "skills_review.json"   # the review record; status.py reads it
# the tracked files the measurement reads by name, relative to the checkout
CONTRACT_PATH = "AGENTS.md"
GLOSSARY_PATH = "module_skills/glossary.md"
SKILLS_INDEX_PATH = "module_skills/README.md"
MAKEFILE_PATH = "Makefile"
RECORDER_PATH = "record.py"
SNAPSHOT_PATH_PATTERN = "store/status/*_status.json"
ARTIFACT_JSON_PATH_PATTERNS = ("store/status/*.json", "store/assets_artifacts/*/*.json")

# the files in scope: the tracked tree but the stores (derived, D09 guards their keys) and the dated reviews
MEASURED_SCOPE_PATHSPECS = (".", ":(exclude)store", ":(exclude,glob)REPORT_*.md")
# the canon (AGENTS.md § The default choice): the contract, the register, the index and every skill
CANON_PATHSPECS = (":(glob)AGENTS.md", ":(glob)module_skills/*.md", ":(glob)module_*/skills/*.md")
# how a store is addressed (AGENTS.md § Canonical vocabulary, the row store paths): on the host, inside a container
STORE_LITERAL_PREFIXES = ("store/", "/store/")
# the one exception to the path grammar that stands in the tree: the web root the dashboard serves
# (module_monitoring/README_module_monitoring.md § Design rationale, the config.py row)
PATH_FROM_FILE_STANDING = ("module_monitoring/config.py",)
# where a directory's objects are argued (AGENTS.md § Pre-AWS architectural direction, every placement is argued): a
# runtime module's orientation unless a longer prefix names another document
DESIGN_RATIONALE_SOURCE_BY_DIRECTORY = {
    "module_skills": "module_skills/README.md",
    "module_skills/sub_module_scalability_crawler": "module_skills/skill_scalability_crawler.md",
}


def module_orientation_path(module: str) -> str:
    """A runtime module's orientation (AGENTS.md § Canonical vocabulary, the row a module's orientation)."""
    return f"{module}/README_module_{module.removeprefix('module_')}.md"


# AGENTS.md § Canonical vocabulary, the rows external I/O functions, conversions, composite constructors, functions that
# are a quantity, booleans; § Rejected vocabulary, function verbs; skill_self_explaining_naming.md § The closed list
# absorbs its synonyms
FUNCTION_VERB_FORBIDDEN_PREFIXES = ("get_", "process_", "handle_", "make_", "calculate_", "compute_", "convert_",
                                    "generate_", "aggregate_", "read_", "probe_", "spool_", "iter_", "run_", "save_",
                                    "publish_", "download_", "train_", "evaluate_", "execute_", "manage_", "check_",
                                    "should_", "needs_")
FUNCTION_VERB_FORBIDDEN_SUFFIXES = ("_factory",)
# AGENTS.md § Canonical vocabulary, the rows CLI entry and booleans; skill_self_explaining_naming.md § The closed list
FUNCTION_NAME_FORBIDDEN = ("run", "cli", "entrypoint", "process", "handle", "execute", "manage", "do_work", "convert",
                           "check", "flag", "ok", "trigger")
# AGENTS.md § Rejected vocabulary, function verbs: a domain noun the register carries is not a verb
FUNCTION_NAME_STANDING = ("run_dir", "run_payload", "write_venue_spool")
# AGENTS.md § Canonical vocabulary, the row JavaScript functions at file scope, and § Rejected vocabulary, function verbs
JS_FUNCTION_VERB_FORBIDDEN = ("make", "load", "poll", "get", "process", "handle", "compute", "calculate")
# AGENTS.md § Canonical vocabulary: local abbreviations never cross a function boundary
LOCAL_ABBREVIATIONS = ("N", "W", "TF", "MIN", "MAX", "K", "XGB")
# AGENTS.md § Canonical vocabulary, the paragraph on constants and the rows conversion factors and artifact keys
CONSTANT_UNIT_SUFFIXES = ("_BARS", "_MINUTES", "_MS", "_SECONDS", "_DAYS", "_ROWS", "_FOLD_ID", "_RATE", "_COUNT", "_PCT",
                          "_BYTES")
CONSTANT_UNIT_INFIXES = ("_PER_",)
# AGENTS.md § Canonical vocabulary, the row CSS: BEM, and the forms it forbids
CSS_CLASS_GRAMMAR = r"[a-z][a-z0-9]*(-[a-z0-9]+)*(__[a-z0-9]+(-[a-z0-9]+)*)?(--[a-z0-9]+(-[a-z0-9]+)*)?"
CSS_CLASS_FORBIDDEN = ("red", "diag", "badge--off", "status--red")
# AGENTS.md § Canonical vocabulary, the row Makefile targets: the lifecycle targets that go bare, the ticker aliases
MAKE_TARGET_BARE = ("all", "build", "help", "on", "off", "all-record")
MAKE_TARGET_TICKER_ALIASES = ("all", "lifecycle")

# AGENTS.md § Rejected vocabulary, directories and path segments
REJECTED_PATH_SEGMENTS = ("src", "core", "lib", "common", "utils", "helpers", "manager", "service", "assets", "artifacts",
                          "data", "db", "database", "raw_data")
# AGENTS.md § Rejected vocabulary, key names; `_ts` only on a UTC string
REJECTED_KEY_NAMES = ("lag", "age", "usage", "mem", "cpu_pct", "hash", "weight")
REJECTED_STRING_KEY_SUFFIXES = ("_ts",)
# AGENTS.md § Rejected vocabulary, interface words — a word the register enacts in a code or UI label cell is read there
REJECTED_INTERFACE_WORDS = ("online", "offline", "alive", "healthy", "running", "RAM", "RSS", "load", "utilisation",
                            "freshness", "boot", "pill", "chip", "tile", "stat", "badge--off", "status--red", "mobile",
                            "tablet", "phone", "responsive", "breakpoint")
# AGENTS.md § Values: no debt marker in a tracked file — this file and the contract name the forbidden form
DEBT_MARKERS = ("TODO", "FIXME", "XXX", "HACK")
DEBT_MARKER_SEATS = (("AGENTS.md", None), ("module_skills/sub_module_scalability_crawler/config.py", None))
# AGENTS.md § Pre-AWS architectural direction: the closed list of where a cloud proper noun is spoken — (path, section),
# the section None for a whole document; this file lists the nouns for the count and is a seat for that alone
CLOUD_NOUNS = ("AWS", "Amazon", "S3", "ECS", "EC2", "ECR", "EBS", "EFS", "EKS", "RDS", "EventBridge", "CloudWatch",
               "CloudFront", "CodeBuild", "Fargate", "Step Functions", "Secrets Manager")
CLOUD_NOUN_SEATS = (("AGENTS.md", "Pre-AWS architectural direction"), ("AGENTS.md", "Skills absent here, described"),
                    ("README.md", "Architectural direction"), ("module_skills/skill_pre_aws_solution.md", None),
                    ("module_skills/skill_asset_containers.md", "The topology"), ("module_skills/skill_determinism.md", None),
                    ("module_data/skills/skill_candle_canonicalisation.md", "15. Docker does not own the database"),
                    ("module_monitoring/skills/skill_devops_panel.md", "The one socket, and what containment means"),
                    ("module_skills/sub_module_scalability_crawler/config.py", None))
# the forms a cloud noun stands in: the repository's own word (AGENTS.md § Pre-AWS architectural direction) and the
# rejected form § Rejected vocabulary spells to refuse it
CLOUD_NOUN_STANDING_FORMS = ("Pre-AWS", "AWS-ready")
# AGENTS.md § Values, the first bullet: the motto every normative document carries
MOTTO = "The repository shows the destination, not the road"
# skill_sorting_files_naming_standard.md, a file keeps its family token inside its folder, and module_skills/glossary.md
# § Stores, the status store row — `*` one directory level, `{folder}` the name of the file's own folder
FAMILY_NAME_PATTERNS_BY_DIRECTORY = {
    "module_*/skills": ("skill_*.md", "methodology_*.md"),
    "store/status": ("*_status.json", "skills_review.json"),
    "store/assets_artifacts/*": ("{folder}_*",),
}

EXAMPLES_PER_METRIC_COUNT = 5
PCT_DECIMAL_COUNT = 1
LEVEL_MEAN_DECIMAL_COUNT = 2


# twice by extraction — identical in module_data/config.py and module_ml/config.py (module_skills/glossary.md
# § Twice by extraction)
def rounded(x, ndigits: int):
    """round() that tolerates None: the NULL a scan reports when no row qualifies, the None a fold without trades reports."""
    return None if x is None else round(float(x), ndigits)
