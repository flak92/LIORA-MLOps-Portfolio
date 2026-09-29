"""The features terminal's one surface of configuration: the targets its menu offers, the one target it opens its own
screen for, the store reads and the descriptors of the files it shows a hand, the files of the serpentine search it
drafts and reads back, the grid its draft offers, and whether its output is plain.

It runs on the host, on `python3` and gum, with no virtual environment: it imports the standard library and its own
package alone. It cannot import `module_features/config.py` — its thirteenth line imports `.indicators`, and numpy
with it — nor the serpentine search's `config.py`, which imports that one, so the store reads, the descriptors, the
readers and the writer of JSON and the values the draft pins a coordinate to are carried here as registered copies,
twice by extraction (module_skills/glossary.md § Twice by extraction), each the same as its owner's.
The store is read from `STORE_ASSETS_ARTIFACTS_DIR`, so a shell that lacks it fails here, at import, before a hand
chooses a stage."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# twice by extraction
STORE_ASSETS_ARTIFACTS_DIR = Path(os.environ["STORE_ASSETS_ARTIFACTS_DIR"])


# twice by extraction
def artifact_dir(ticker: str) -> Path:
    """The asset's folder of non-tabular files — the segment `ticker=<TICKER>/` a partition carries, at the root of the
    store; inside it one file per artifact, named for it."""
    return STORE_ASSETS_ARTIFACTS_DIR / f"ticker={ticker}"


# twice by extraction
def partition_dir(family: str, ticker: str, timeframe: str | None = None, store: Path = STORE_ASSETS_ARTIFACTS_DIR) -> Path:
    """One partition of a table family: `<store>/<family>/ticker=<TICKER>/[timeframe=<tf>/]` — Hive's `key=value`, the value
    the ticker in capitals and the compact token; the store the artifacts store unless the family lives in another."""
    partition = store / family / f"ticker={ticker}"
    return partition if timeframe is None else partition / f"timeframe={timeframe}"


# twice by extraction
def catalogue_json(ticker: str):
    """The asset's copy of the feature layer's contract — what the ML layer reads instead of the feature configuration."""
    return artifact_dir(ticker) / f"{ticker}_catalogue.json"


# twice by extraction
def serpentine_search_json(ticker: str) -> Path:
    """Where the serpentine search stands: its inputs, its beam, its champion, the path it took and its proposals."""
    return artifact_dir(ticker) / f"{ticker}_serpentine_search.json"


# twice by extraction
def serpentine_search_trials_jsonl(ticker: str) -> Path:
    """Every scored state of the serpentine search, one JSON object a line; a line's number is the trial's index."""
    return artifact_dir(ticker) / f"{ticker}_serpentine_search_trials.jsonl"


# twice by extraction
def serpentine_search_profile_json(ticker: str) -> Path:
    """What a hand asks the serpentine search to look at — the one file this terminal writes."""
    return artifact_dir(ticker) / f"{ticker}_serpentine_search_profile.json"


# the one target whose form a bare run cannot answer: the proposal it promotes is asked on this terminal's own screen —
# a record of the serpentine search's CONFIGURABLES
# twice by extraction
PROMOTE_TARGET = "features-serpentine-search-promote"


# twice by extraction
def feature_set_json(ticker: str) -> Path:
    """The asset's promoted feature set — what the promotion writes and the ML chain reads."""
    return artifact_dir(ticker) / f"{ticker}_feature_set.json"


# twice by extraction
def barriers_json(ticker: str) -> Path:
    """The asset's promoted barrier geometry — what the promotion writes and the ML chain reads."""
    return artifact_dir(ticker) / f"{ticker}_barriers.json"


# the loops of a round in the order a round runs them, and the geometry a coordinate stands at without a promotion —
# the point a draft pins an unsearched coordinate to
# twice by extraction
SERPENTINE_SEARCH_ROUND_LOOPS = ("barrier", "feature_set", "hpo")
# twice by extraction
START_BY_COORDINATE_DEFAULT = {
    "label_barrier_true_range_multiplier": 2.0,
    "label_horizon": "4h",
    "stop_loss_true_range_multiplier": 2.0,
    "take_profit_true_range_multiplier": 2.0,
}
# the grid each coordinate is searched over — the one preset the terminal offers, a record of the serpentine search's
# CONFIGURABLES; another grid is a hand's edit of the profile itself, which is what "drafted, never derived" permits
# twice by extraction
GRID_BY_COORDINATE_DEFAULT = {
    "label_barrier_true_range_multiplier": [1.75, 2.0, 2.25],
    "label_horizon": ["2h", "4h", "8h", "12h", "1d"],
    "stop_loss_true_range_multiplier": [1.5, 2.0, 2.5],
    "take_profit_true_range_multiplier": [1.5, 2.0, 2.5],
}


# twice by extraction
def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# twice by extraction
def load_jsonl(path: Path) -> list[dict]:
    """A ledger as it was written: one object a line, in the order they were appended."""
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


# twice by extraction
def write_json(path: Path, payload: dict) -> None:
    """The canonical JSON form of this tree, equal by value to module_features/dataset.py's — without to_json_safe(),
    which canonicalises numpy values this sub-module never holds. The same decisions write the same bytes, so a
    draft that changes nothing leaves git unmoved."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=1) + "\n", encoding="utf-8")


# plain output — state words in brackets, no colour, no symbol, no border: NO_COLOR set and not empty, TERM=dumb,
# or standard output not a terminal (module_skills/skill_tui_designer.md, TUI-DESIGNER-PLAIN-OUTPUT-FOLLOWS-THE-ENVIRONMENT)
# twice by extraction
OUTPUT_PLAIN = (bool(os.environ.get("NO_COLOR")) or os.environ.get("TERM") == "dumb"
                or not sys.stdout.isatty())

# the targets of the one Makefile this terminal offers: its module's, read off `make help` by name — `features-<stage>`,
# `features-all` and a stage's `tmux-` twin (AGENTS.md § Canonical vocabulary, the terminal-menu row)
MENU_TARGET_PATTERN = re.compile(r"^(tmux-)?features-")
