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

# AGENTS.md § The shape, D03: where a skill lives — the canon, or the skills of the module it describes
SKILL_DIRECTORY_PATTERNS = ("module_skills", "module_*/skills")
# AGENTS.md § The shape, D05, and § Rejected vocabulary, a second compose file, a second Makefile
LAUNCHER_PATHS = ("Makefile", "docker-compose.yml")
LAUNCHER_NAME_PATTERNS = ("Makefile*", "*.mk", "docker-compose*.yml", "docker-compose*.yaml", "compose*.yml", "compose*.yaml")
# the section whose rows the shape table reads, and each row's evidence: a metric the row holds by when that invariant
# reads zero, or — where no count can say it — the target that proves it by hand
SHAPE_SECTION_TITLE = "The shape — what holds the project together"
SHAPE_EVIDENCE_BY_CONDITION = {
    "D01": "root_python_outside_record_count",
    "D02": "cross_module_import_count",
    "D03": "skill_outside_owner_directory_count",
    "D04": "make all, then make on, from a fresh clone",
    "D05": "launcher_file_copy_count",
    "D06": "git status --porcelain empty after make all",
    "D07": "docker compose config --services: one asset-<ticker> per ticker, no service per stage",
    "D08": "git ls-files ':(glob)module_*/sub_module_*/**'",
    "D09": "artifact_key_without_glossary_row_count",
    "D10": "README.md § Parity",
    "D11": "README.md § Parity",
    "D12": "requirements.txt, and trials_sqlite() in module_ml/config.py",
    "D13": "make features-status",
    "D14": "twice_by_extraction_drift_count",
    "D15": "git ls-files store/",
    "D16": "resident_exec_count",
    "D17": "make skills-status",
}

# the review pass: its branch and the worktree beside the checkout, never inside it
CRAWLER_DIR = "module_skills/sub_module_scalability_crawler"
BRIEF_TEMPLATE_PATH = "module_skills/sub_module_scalability_crawler/crawl_brief_template.md"
CRAWL_BRANCH = "scalability-crawler"
CRAWL_WORKTREE_DIR = REPO_ROOT.parent / f"{REPO_ROOT.name}_scalability_crawler"
# the bound of one pass: batches of one module, at most this many files each, at most this many batches, two attempts each
CRAWL_BATCH_FILE_COUNT = 6
CRAWL_PASS_BATCH_COUNT = 6
CRAWL_ATTEMPT_COUNT_PER_BATCH = 2
AGENT_TIMEOUT_SECONDS = 1800
# the checkout is quiet when nothing under it but these changed for this long; 0 turns the wait off
QUIET_PROBE_SECONDS = 300
PROBE_EXCLUDE = (".git", ".venv", "store/status/skills_status.json", "store/status/skills_review.json")
# module_skills/glossary.md § Scalability crawler, the verdict and level rows
VERDICTS = ("conformant", "amended", "deferred")
SELF_EXPLAINING_LEVELS = (1, 2, 3, 4, 5)
# the agent's command line — its own vocabulary inside this tuple: Claude Sonnet 5, one JSON envelope on stdout, the brief
# on stdin; only the tools a review needs, no tool that creates a file, nothing that would ask a question, and none of the
# user's settings, MCP servers or sessions
AGENT_COMMAND = ("claude", "-p", "--model", "claude-sonnet-5", "--output-format", "json", "--max-turns", "40",
                 "--tools", "Read,Edit,Glob,Grep,Bash",
                 "--allowedTools", "Read,Edit,Glob,Grep,Bash(git diff:*),Bash(git log:*),Bash(git show:*),Bash(git status:*),Bash(git grep:*)",
                 "--permission-mode", "acceptEdits", "--permission-prompts", "none",
                 "--setting-sources", "project", "--strict-mcp-config", "--no-session-persistence")

EXAMPLES_PER_METRIC_COUNT = 5
PCT_DECIMAL_COUNT = 1
LEVEL_MEAN_DECIMAL_COUNT = 2


# twice by extraction — identical in module_data/config.py and module_ml/config.py (module_skills/glossary.md
# § Twice by extraction)
def rounded(x, ndigits: int):
    """round() that tolerates None: the NULL a scan reports when no row qualifies, the None a fold without trades reports."""
    return None if x is None else round(float(x), ndigits)
