"""Shared read-only loading of per-asset X/Y artifacts and run identifiers.

X may contain tail rows that the label stage dropped (vertical barrier past
the research end); the join keeps exactly Y's decision grid and asserts the
alignment instead of assuming it.
"""

from __future__ import annotations

import duckdb
import numpy as np

from . import config


def run_ids(con: duckdb.DuckDBPyConnection) -> tuple[str, str]:
    """(data_sha256 from _ml_meta, config_sha256) for artifact envelopes."""
    row = con.execute("SELECT value FROM _ml_meta WHERE key = 'data_sha256'").fetchone()
    assert row is not None, "run `make ml-bars` first (data_sha256 missing)"
    return row[0], config.config_sha256()


def versions() -> dict:
    import optuna
    import xgboost

    return {
        "duckdb": duckdb.__version__,
        "numpy": np.__version__,
        "optuna": optuna.__version__,
        "xgboost": xgboost.__version__,
    }


def load_xy(ticker: str) -> dict[str, np.ndarray]:
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
        "x": np.column_stack([x[c][pos] for c in config.FEATURE_COLUMNS]),
        "y": yy["y"].astype(np.int8),
        "event_end_ts": yy["event_end_ts"].astype(np.int64),
        "mask_ok": yy["mask_ok"].astype(bool),
        "weight": yy["weight"].astype(np.float64),
        "exit_reason": yy["exit_reason"].astype(np.int8),
    }
