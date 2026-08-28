"""Shared IO for the ML layer: per-asset artifacts in, canonical JSON out.

Loading X/Y and writing JSON are the only two things every stage needs from a
common place, so they live together here. No artifact carries a provenance
envelope: the git commit records which code produced a result, and
ml_status.json carries the research window and the seed once, not in every
file. The per-asset experiment configuration written by status.py is a
different thing — the configuration a run used, read from config.py, not a
statement about the file it sits next to.
"""

from __future__ import annotations

import csv
import json
import os
import tempfile
from pathlib import Path

import duckdb
import numpy as np

from . import config


def to_json_safe(obj):
    """Recursively convert numpy containers/scalars to canonical Python.

    Type conversion comes first and the finiteness check second: a numpy NaN
    that returned as a float on the way past would reach json.dumps, which
    writes the literal NaN — valid Python, invalid JSON, and unreadable by any
    strict parser.
    """
    if isinstance(obj, dict):
        return {str(k): to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_json_safe(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return [to_json_safe(v) for v in obj.tolist()]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.floating):
        obj = float(obj)
    if isinstance(obj, float) and not np.isfinite(obj):
        return None
    return obj


def write_json(path: Path, payload: dict) -> None:
    text = json.dumps(to_json_safe(payload), sort_keys=True, indent=1) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_parquet(path: Path, columns: dict[str, str], rows, order_by: str) -> Path:
    """Atomic zstd parquet from an iterable of rows, via a CSV spool.

    numpy -> repr(float) -> read_csv round-trips float64 exactly, and DuckDB
    sorts and compresses; os.replace makes the artifact appear whole or not at
    all. Every per-asset artifact writer is this function with its own rows.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="") as f:
        csv.writer(f).writerows(rows)
        spool = Path(f.name)
    try:
        spec = ", ".join(f"'{name}': '{sqltype}'" for name, sqltype in columns.items())
        con = duckdb.connect()
        con.execute(
            f"""COPY (SELECT * FROM read_csv('{spool}', header=false, columns={{{spec}}})
                      ORDER BY {order_by})
                TO '{path}.tmp' (FORMAT PARQUET, COMPRESSION zstd)"""
        )
        con.close()
        os.replace(f"{path}.tmp", path)
    finally:
        spool.unlink(missing_ok=True)
    return path


def load_xy(ticker: str) -> dict[str, np.ndarray]:
    """X and Y on Y's decision grid; X may carry tail rows Y had to drop."""
    adir = config.artifact_dir(ticker)
    con = duckdb.connect()
    x = {}
    for timeframe in config.HIERARCHY_TIMEFRAMES:
        per_timeframe = con.execute(
            f"SELECT * FROM read_parquet('{config.features_parquet(ticker, timeframe)}') ORDER BY decision_ts"
        ).fetchnumpy()
        for family in config.FAMILIES:
            x[f"{family}_{timeframe}"] = per_timeframe[family]
        x["decision_ts"] = per_timeframe["decision_ts"]
    label_events = con.execute(f"SELECT * FROM read_parquet('{config.label_events_parquet(ticker)}') ORDER BY decision_ts").fetchnumpy()
    con.close()
    x_ts = x["decision_ts"].astype(np.int64)
    y_ts = label_events["decision_ts"].astype(np.int64)
    pos = np.searchsorted(x_ts, y_ts)
    assert np.array_equal(x_ts[pos], y_ts), "X/Y decision grids do not align"
    return {
        "decision_ts": y_ts,
        "entry_ts": label_events["entry_ts"].astype(np.int64),
        "x": np.column_stack([x[c][pos] for c in config.FEATURE_COLUMNS]),
        "y": label_events["y"].astype(np.int8),
        "event_end_ts": label_events["event_end_ts"].astype(np.int64),
        "entry_observable": label_events["entry_observable"].astype(bool),
        "label_valid": label_events["label_valid"].astype(bool),
        # the supervised population: an entry that could be observed and an
        # event that resolves unambiguously
        "sample_valid": label_events["entry_observable"].astype(bool) & label_events["label_valid"].astype(bool),
        "event_resolution": label_events["event_resolution"].astype(np.int8),
        "entry_price": label_events["entry_price"].astype(np.float64),
        "upper_barrier": label_events["upper_barrier"].astype(np.float64),
        "lower_barrier": label_events["lower_barrier"].astype(np.float64),
        "exit_reference_price": label_events["exit_reference_price"].astype(np.float64),
    }
