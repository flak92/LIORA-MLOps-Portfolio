"""Shared IO for the ML layer: load_xy, write_parquet, write_json and load_json."""

from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

import duckdb
import numpy as np

from . import config


def to_json_safe(obj):
    """numpy containers and scalars to canonical Python; a non-finite float becomes null."""
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
    path.write_text(json.dumps(to_json_safe(payload), sort_keys=True, indent=1) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_parquet(path: Path, columns: dict[str, str], rows, order_by: str) -> Path:
    """zstd parquet from an iterable of rows via a CSV spool: numpy -> repr(float) -> read_csv round-trips float64 exactly."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="") as f:
        csv.writer(f).writerows(rows)
        spool = Path(f.name)
    try:
        spec = ", ".join(f"'{name}': '{sqltype}'" for name, sqltype in columns.items())
        con = duckdb.connect()
        con.execute(f"SET memory_limit='{config.DUCKDB_MEMORY_LIMIT}'")
        con.execute("SET threads=1")   # float summation must not be reordered
        con.execute(
            f"""COPY (SELECT * FROM read_csv('{spool}', header=false, columns={{{spec}}})
                      ORDER BY {order_by})
                TO '{path}' (FORMAT PARQUET, COMPRESSION zstd)"""
        )
        con.close()
    finally:
        spool.unlink(missing_ok=True)
    return path


def load_xy(ticker: str) -> dict[str, np.ndarray]:
    """X and Y on Y's decision grid; X may carry tail rows Y had to drop."""
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{config.DUCKDB_MEMORY_LIMIT}'")
    con.execute("SET threads=1")   # float summation must not be reordered
    x, decision_grids = {}, []
    for timeframe in config.HIERARCHY_TIMEFRAMES:
        per_timeframe = con.execute(
            f"SELECT * FROM read_parquet('{config.features_parquet(ticker, timeframe)}') ORDER BY decision_ts"
        ).fetchnumpy()
        for family in config.FEATURE_FAMILIES:
            x[f"{family}_{timeframe}"] = per_timeframe[family]
        decision_grids.append(per_timeframe["decision_ts"].astype(np.int64))
    label_events = con.execute(f"SELECT * FROM read_parquet('{config.label_events_parquet(ticker)}') ORDER BY decision_ts").fetchnumpy()
    con.close()
    # the three files are joined by position, so they must share one decision grid
    x_ts = decision_grids[0]
    assert all(np.array_equal(x_ts, grid) for grid in decision_grids[1:]), "per-timeframe feature parquets disagree on the decision grid"
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
        # the supervised population: an observable entry and an unambiguous event
        "sample_valid": label_events["entry_observable"].astype(bool) & label_events["label_valid"].astype(bool),
        "event_resolution": label_events["event_resolution"].astype(np.int8),
        "entry_price": label_events["entry_price"].astype(np.float64),
        "upper_barrier": label_events["upper_barrier"].astype(np.float64),
        "lower_barrier": label_events["lower_barrier"].astype(np.float64),
        "exit_reference_price": label_events["exit_reference_price"].astype(np.float64),
    }
