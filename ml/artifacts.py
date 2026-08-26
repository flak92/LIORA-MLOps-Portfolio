"""Canonical, deterministic artifact serialization.

Every JSON artifact of the ML layer goes through this module: numpy scalars
are converted to plain Python, keys are sorted, floats keep Python's
shortest-roundtrip repr, and the file is written atomically. The envelope
carries only reproducibility identifiers — no wall-clock time, no hostname,
no absolute paths — so byte-identical inputs produce byte-identical files.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np


def canon(obj):
    """Recursively convert numpy containers/scalars to canonical Python."""
    if isinstance(obj, dict):
        return {str(k): canon(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [canon(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return [canon(v) for v in obj.tolist()]
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, float) and not np.isfinite(obj):
        return None
    assert not isinstance(obj, set), "sets are order-unstable — forbidden in artifacts"
    return obj


def envelope(data_sha256: str, config_sha256: str, seed: int, versions: dict) -> dict:
    return {
        "data_sha256": data_sha256,
        "config_sha256": config_sha256,
        "seed": seed,
        "versions": dict(sorted(versions.items())),
    }


def write_json(path: Path, payload: dict) -> None:
    text = json.dumps(canon(payload), sort_keys=True, indent=1) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
