"""The one parquet writer of the pipeline: every layer that writes a parquet writes it here."""

from __future__ import annotations

import csv
import tempfile
from pathlib import Path

import duckdb

from . import config


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
