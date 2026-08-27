"""Fixed hierarchical feature matrix X — 15 causal columns per asset.

Five families on three time scales (trend, momentum, volatility, structure,
activity on 15m/1h/4h). Identical definition for every asset; no per-asset
selection. Cross-level trend agreement is a strategy rule over these columns,
not a feature: it would carry no information the three trend columns lack.

Every value at decision_ts comes from the last CLOSED bar of its level
(asof_index asserts causality); the 15m level uses the bar closing exactly at
decision_ts.

Output: assets/Asset_<T>/X_<T>.parquet with decision_ts + 15 float64 columns,
rows from the global research warm-up onward, no NaN (asserted).
"""

from __future__ import annotations

import argparse
import csv
import os
import tempfile
from pathlib import Path

import duckdb
import numpy as np

from . import config, indicators


def load_level(con: duckdb.DuckDBPyConnection, sym: str, tf: str) -> dict[str, np.ndarray]:
    return con.execute(
        f"""SELECT timestamp_ms, open, high, low, close, volume
            FROM ohlcv_{tf}_canonical WHERE symbol = '{sym}' ORDER BY timestamp_ms"""
    ).fetchnumpy()


def level_features(bars: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """The five family features on one level's own bars."""
    close, high, low, vol = bars["close"], bars["high"], bars["low"], bars["volume"]
    atr14 = indicators.atr(high, low, close, config.ATR_N)
    with np.errstate(divide="ignore", invalid="ignore"):
        trend = (indicators.ema(close, config.EMA_FAST) - indicators.ema(close, config.EMA_SLOW)) / atr14
    return {
        "trend": np.where(atr14 == 0.0, 0.0, trend),
        "momentum": (indicators.rsi(close, config.RSI_N) - 50.0) / 50.0,
        "volatility": atr14 / close,
        "structure": indicators.range_position(close, high, low, config.STRUCTURE_N),
        "activity": indicators.rolling_zscore(np.log1p(vol), config.ACTIVITY_N),
    }


def build_x(con: duckdb.DuckDBPyConnection, ticker: str) -> tuple[np.ndarray, np.ndarray]:
    """Return (decision_ts, X matrix ordered as config.FEATURE_COLUMNS)."""
    sym = config.symbol(ticker)
    levels = {tf: load_level(con, sym, tf) for tf in config.LEVELS}
    feats = {tf: level_features(levels[tf]) for tf in config.LEVELS}

    ts15 = levels["15m"]["timestamp_ms"].astype(np.int64)
    decision_ts = ts15[ts15 >= config.WARMUP_END_MS]

    cols: dict[str, np.ndarray] = {}
    for tf in config.LEVELS:
        idx = indicators.asof_index(decision_ts, levels[tf]["timestamp_ms"].astype(np.int64), config.TF_MS[tf])
        for fam in config.FAMILIES:
            cols[f"{fam}_{tf}"] = feats[tf][fam][idx]

    x = np.column_stack([cols[c] for c in config.FEATURE_COLUMNS])
    assert np.isfinite(x).all(), "NaN/inf in X after the research warm-up"
    return decision_ts, x


def write_x(ticker: str, decision_ts: np.ndarray, x: np.ndarray) -> Path:
    out = config.ASSETS_DIR / f"Asset_{ticker}" / f"X_{ticker}.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="") as f:
        w = csv.writer(f)
        for i in range(decision_ts.size):
            w.writerow([int(decision_ts[i])] + [repr(float(v)) for v in x[i]])
        spool = Path(f.name)
    try:
        cols = ", ".join(f"'{c}': 'DOUBLE'" for c in config.FEATURE_COLUMNS)
        con = duckdb.connect()
        con.execute(
            f"""COPY (SELECT * FROM read_csv('{spool}', header=false,
                       columns={{'decision_ts': 'BIGINT', {cols}}})
                     ORDER BY decision_ts)
                TO '{out}.tmp' (FORMAT PARQUET, COMPRESSION zstd)"""
        )
        con.close()
        os.replace(f"{out}.tmp", out)
    finally:
        spool.unlink(missing_ok=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="hierarchical feature matrix X per asset")
    ap.add_argument("--tickers", default=",".join(config.TICKERS), help="comma-separated subset")
    args = ap.parse_args()
    con = duckdb.connect(str(config.DB_PATH), read_only=True)
    for t in [x.strip().upper() for x in args.tickers.split(",") if x.strip()]:
        decision_ts, x = build_x(con, t)
        out = write_x(t, decision_ts, x)
        print(f"{out.name}: {decision_ts.size} rows x {x.shape[1]} features", flush=True)
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
