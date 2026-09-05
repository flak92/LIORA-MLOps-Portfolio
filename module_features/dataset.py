"""The parquet writer of the feature layer — twice by extraction, identical in module_ml/dataset.py — and the canonical JSON
writer of the feature layer: the per-asset contract and the snapshot this module writes."""

from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

import duckdb
import numpy as np

from . import config


# twice by extraction — identical in module_ml/dataset.py (module_skills/glossary.md § Twice by extraction)
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


# twice by extraction — identical in module_ml/dataset.py (module_skills/glossary.md § Twice by extraction)
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
