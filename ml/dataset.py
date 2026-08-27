"""Shared IO for the ML layer: per-asset artifacts in, canonical JSON out.

Loading X/Y and writing JSON are the only two things every stage needs from a
common place, so they live together here. There is no provenance envelope: the
git commit records which code produced a result, and ml_status.json carries the
research window and the seed once, not in every file.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import duckdb
import numpy as np

from . import config


def canon(obj):
    """Recursively convert numpy containers/scalars to canonical Python."""
    if isinstance(obj, dict):
        return {str(k): canon(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [canon(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return [canon(v) for v in obj.tolist()]
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, float) and not np.isfinite(obj):
        return None
    return obj


def write_json(path: Path, payload: dict) -> None:
    text = json.dumps(canon(payload), sort_keys=True, indent=1) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_xy(ticker: str) -> dict[str, np.ndarray]:
    """X and Y on Y's decision grid; X may carry tail rows Y had to drop."""
    adir = config.ASSETS_DIR / f"Asset_{ticker}"
    con = duckdb.connect()
    x = con.execute(f"SELECT * FROM read_parquet('{adir}/X_{ticker}.parquet') ORDER BY decision_ts").fetchnumpy()
    yy = con.execute(f"SELECT * FROM read_parquet('{adir}/Y_{ticker}.parquet') ORDER BY decision_ts").fetchnumpy()
    con.close()
    x_ts = x["decision_ts"].astype(np.int64)
    y_ts = yy["decision_ts"].astype(np.int64)
    pos = np.searchsorted(x_ts, y_ts)
    assert np.array_equal(x_ts[pos], y_ts), "X/Y decision grids do not align"
    return {
        "decision_ts": y_ts,
        "entry_ts": yy["entry_ts"].astype(np.int64),
        "x": np.column_stack([x[c][pos] for c in config.FEATURE_COLUMNS]),
        "y": yy["y"].astype(np.int8),
        "event_end_ts": yy["event_end_ts"].astype(np.int64),
        "label_valid": yy["label_valid"].astype(bool),
        "weight": yy["weight"].astype(np.float64),
        "exit_reason": yy["exit_reason"].astype(np.int8),
        "p0": yy["p0"].astype(np.float64),
        "upper": yy["upper"].astype(np.float64),
        "lower": yy["lower"].astype(np.float64),
        "exit_ref": yy["exit_ref"].astype(np.float64),
    }
