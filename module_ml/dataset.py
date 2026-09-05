"""Shared IO for the ML layer: load_xy with the asset's feature set, load_feature_columns, build_x, write_json and
load_json; the parquet writer is module_features' and is re-exported here for the label and prediction writers."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import numpy as np

from module_features.dataset import write_parquet  # re-exported

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


def load_feature_columns(ticker: str) -> dict[str, tuple[str, ...]]:
    """The asset's feature set by timeframe: the promoted file's columns, in catalogue order, else the default set."""
    path = config.feature_set_json(ticker)
    if not path.exists():
        return dict(config.DEFAULT_FEATURE_COLUMNS_BY_TIMEFRAME)
    promoted = load_json(path)["columns_by_timeframe"]
    return {timeframe: tuple(sorted(promoted[timeframe], key=config.catalogue_columns(timeframe).index))
            for timeframe in config.HIERARCHY_TIMEFRAMES}


def build_x(catalogue_values: dict[str, np.ndarray],
            columns_by_timeframe: dict[str, tuple[str, ...]]) -> tuple[np.ndarray, tuple[str, ...]]:
    """The model's matrix from the catalogue's values: the set's features, timeframe-major and catalogue-order
    within — the order is what the model samples by position. Returns (x, its feature ids)."""
    feature_columns = tuple(config.feature_id(name, timeframe)
                            for timeframe in config.HIERARCHY_TIMEFRAMES for name in columns_by_timeframe[timeframe])
    return np.column_stack([catalogue_values[c] for c in feature_columns]), feature_columns


def load_xy(ticker: str) -> dict:
    """X and Y on Y's decision grid, with the values of every catalogue column beside X; X may carry tail rows Y
    had to drop."""
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{config.DUCKDB_MEMORY_LIMIT}'")
    con.execute("SET threads=1")   # float summation must not be reordered
    catalogue_values, decision_grids = {}, []
    for timeframe in config.HIERARCHY_TIMEFRAMES:
        per_timeframe = con.execute(
            f"SELECT * FROM read_parquet('{config.features_parquet(ticker, timeframe)}') ORDER BY decision_ts"
        ).fetchnumpy()
        for name in config.catalogue_columns(timeframe):
            catalogue_values[config.feature_id(name, timeframe)] = per_timeframe[name]
        decision_grids.append(per_timeframe["decision_ts"].astype(np.int64))
    label_events = con.execute(f"SELECT * FROM read_parquet('{config.label_events_parquet(ticker)}') ORDER BY decision_ts").fetchnumpy()
    con.close()
    # the files are joined by position, so they must share one decision grid
    x_ts = decision_grids[0]
    assert all(np.array_equal(x_ts, grid) for grid in decision_grids[1:]), "per-timeframe feature parquets disagree on the decision grid"
    y_ts = label_events["decision_ts"].astype(np.int64)
    pos = np.searchsorted(x_ts, y_ts)
    assert np.array_equal(x_ts[pos], y_ts), "X/Y decision grids do not align"
    catalogue_values = {c: catalogue_values[c][pos] for c in config.CATALOGUE_COLUMNS}
    x, feature_columns = build_x(catalogue_values, load_feature_columns(ticker))
    return {
        "decision_ts": y_ts,
        "entry_ts": label_events["entry_ts"].astype(np.int64),
        "x": x,
        "feature_columns": feature_columns,
        "catalogue_values": catalogue_values,
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
