"""The parquet writer of the feature layer and the schema read off a written partition — twice by extraction, identical in
module_ml/dataset.py — the canonical JSON writer of the feature layer, and the readers a search of this layer needs:
the per-asset contract and the snapshot this module writes, and the state, the ledger and the answers the serpentine
search reads back."""

from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

import duckdb
import numpy as np

from . import config


# twice by extraction
def load_partition_schema(con: duckdb.DuckDBPyConnection, path: Path) -> list[dict[str, str]]:
    """The columns of a written partition, as data: `column` and DuckDB's `type` in the file's order — the schema of a
    homogeneous family, whose every partition carries the same; the partition keys stay out because the file is read
    as a file, not as a Hive tree."""
    return [{"column": name, "type": kind}
            for name, kind, *_ in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{path}', hive_partitioning=false)").fetchall()]


# twice by extraction
def write_parquet(path: Path, columns: dict[str, str], rows, order_by: str, family: str | None = None) -> Path:
    """zstd parquet from an iterable of rows via a CSV spool: numpy -> repr(float) -> read_csv round-trips float64 exactly.
    Named a homogeneous family's partition, it writes the family's `schema.json` beside the partitions too."""
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
        if family is not None:
            write_json(config.schema_json(family), load_partition_schema(con, path))
        con.close()
    finally:
        spool.unlink(missing_ok=True)
    return path


# twice by extraction
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


# twice by extraction
def write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_json_safe(payload), sort_keys=True, indent=1) + "\n", encoding="utf-8")


# twice by extraction
def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# twice by extraction
def load_jsonl(path: Path) -> list[dict]:
    """A ledger as it was written: one object a line, in the order they were appended."""
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def append_jsonl(path: Path, payloads: list[dict]) -> None:
    """A batch of objects, one a line, appended in the order given: a ledger grows by what it gains and is never
    rewritten. The batch is one open, because what a search learns from one answer it learns at once; a stop during
    the write leaves either whole lines, which read back and say which of them are there, or a last line cut short,
    which fails its read as a cut-short state file does."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as ledger:
        ledger.write("".join(json.dumps(to_json_safe(payload), sort_keys=True) + "\n" for payload in payloads))
