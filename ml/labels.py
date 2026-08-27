"""Triple-barrier labels resolved on the canonical 1m path, per asset.

For every 15m decision: entry P0 = canonical 1m open at decision_ts,
horizontal barriers P0 +- K * ATR14(last closed 1h bar), vertical barrier
240 minutes. The first 1m candle whose high touches the upper barrier gives
y = +1, whose low touches the lower gives y = -1; neither within the horizon
gives y = 0. A minute touching BOTH barriers before any other hit makes the
order unknowable from OHLC — the row is masked (exit_reason = 9), never
relabelled 0. A forward-filled minute anywhere in the horizon also masks the
row. Rows whose vertical barrier crosses the research end are dropped.

Sample weight = average uniqueness (Lopez de Prado, ch. 4): the mean over the
event's minutes of 1 / (number of concurrently open events), computed exactly
with prefix sums.

Output: assets/Asset_<T>/Y_<T>.parquet
(decision_ts, y, event_end_ts, mask_ok, weight, exit_reason).
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

CHUNK = 16384
MINUTE_MS = 60_000
W = config.HORIZON_MS // MINUTE_MS   # horizon in minutes (240)


def load_1m(con: duckdb.DuckDBPyConnection, sym: str) -> dict[str, np.ndarray]:
    """The only permitted 1m fetch outside SQL: five columns, one asset."""
    arrs = con.execute(
        f"""SELECT open, high, low, close, (source = 'ffill')::TINYINT AS ffill
            FROM ohlcv_1m_canonical
            WHERE symbol = '{sym}'
              AND timestamp_ms >= {config.RESEARCH_START_MS}
              AND timestamp_ms < {config.RESEARCH_END_MS}
            ORDER BY timestamp_ms"""
    ).fetchnumpy()
    n_expected = (config.RESEARCH_END_MS - config.RESEARCH_START_MS) // MINUTE_MS
    assert arrs["open"].size == n_expected, "1m grid incomplete inside the research window"
    return arrs


def triple_barrier(m1: dict[str, np.ndarray], decision_ts: np.ndarray, sigma: np.ndarray):
    """Vectorised in chunks; returns (y, t_resolve_minutes, exit_reason, ffill_in_path)."""
    idx = ((decision_ts - config.RESEARCH_START_MS) // MINUTE_MS).astype(np.int64)
    p0 = m1["open"][idx]
    up = p0 + config.K_BARRIER * sigma
    dn = p0 - config.K_BARRIER * sigma
    high, low = m1["high"], m1["low"]
    ffill_prefix = np.concatenate(([0], np.cumsum(m1["ffill"], dtype=np.int64)))

    n = idx.size
    y = np.zeros(n, dtype=np.int8)
    t_res = np.full(n, W, dtype=np.int32)
    reason = np.zeros(n, dtype=np.int8)
    offsets = np.arange(W)
    for a in range(0, n, CHUNK):
        b = min(a + CHUNK, n)
        win = idx[a:b, None] + offsets[None, :]
        hw, lw = high[win], low[win]
        up_hit = hw >= up[a:b, None]
        dn_hit = lw <= dn[a:b, None]
        t_up = np.where(up_hit.any(axis=1), up_hit.argmax(axis=1), W)
        t_dn = np.where(dn_hit.any(axis=1), dn_hit.argmax(axis=1), W)
        amb = (t_up == t_dn) & (t_up < W)
        y[a:b] = np.where(t_up < t_dn, 1, np.where(t_dn < t_up, -1, 0)).astype(np.int8)
        t_res[a:b] = np.minimum(t_up, t_dn)
        reason[a:b] = np.where(amb, 9, np.where(t_up < t_dn, 1, np.where(t_dn < t_up, -1, 0)))
        y[a:b][amb] = 0
    # the mask covers the RESOLVED path only: entry minute up to the resolving
    # minute (or the whole horizon when the vertical barrier ends the event)
    path_end = idx + np.minimum(t_res + 1, W)
    ffill_in_path = (ffill_prefix[path_end] - ffill_prefix[idx]) > 0
    return y, t_res, reason, ffill_in_path


def uniqueness_weights(decision_ts: np.ndarray, end_ts: np.ndarray) -> np.ndarray:
    """Average uniqueness over each event's minutes via exact prefix sums."""
    n_min = (config.RESEARCH_END_MS - config.RESEARCH_START_MS) // MINUTE_MS
    start = ((decision_ts - config.RESEARCH_START_MS) // MINUTE_MS).astype(np.int64)
    end = ((end_ts - config.RESEARCH_START_MS) // MINUTE_MS).astype(np.int64)
    delta = np.zeros(n_min + 1, dtype=np.int64)
    np.add.at(delta, start, 1)
    np.add.at(delta, end, -1)
    conc = np.cumsum(delta[:-1])
    inv = np.zeros(n_min + 1)
    covered = conc > 0
    inv[1:][covered] = 1.0 / conc[covered]
    s = np.cumsum(inv)
    w = (s[end] - s[start]) / (end - start)
    assert np.all((w > 0) & (w <= 1.0)), "uniqueness weights outside (0, 1]"
    return w


def main() -> int:
    ap = argparse.ArgumentParser(description="triple-barrier labels on the 1m path")
    ap.add_argument("--tickers", default=",".join(config.TICKERS), help="comma-separated subset")
    args = ap.parse_args()
    con = duckdb.connect(str(config.DB_PATH), read_only=True)
    for t in [x.strip().upper() for x in args.tickers.split(",") if x.strip()]:
        sym = config.symbol(t)
        bars_1h = con.execute(
            f"""SELECT timestamp_ms, high, low, close FROM ohlcv_1h_canonical
                WHERE symbol = '{sym}' ORDER BY timestamp_ms"""
        ).fetchnumpy()
        ts15 = con.execute(
            f"""SELECT timestamp_ms FROM ohlcv_15m_canonical
                WHERE symbol = '{sym}' ORDER BY timestamp_ms"""
        ).fetchnumpy()["timestamp_ms"].astype(np.int64)

        decision_ts = ts15[(ts15 >= config.WARMUP_END_MS)
                           & (ts15 + config.HORIZON_MS <= config.RESEARCH_END_MS)]
        atr_1h = indicators.atr(bars_1h["high"], bars_1h["low"], bars_1h["close"], config.ATR_N)
        idx_1h = indicators.asof_index(decision_ts, bars_1h["timestamp_ms"].astype(np.int64),
                                       config.TF_MS["1h"])
        sigma = atr_1h[idx_1h]
        assert np.isfinite(sigma).all() and (sigma >= 0).all()

        m1 = load_1m(con, sym)
        y, t_res, reason, ffill_in_path = triple_barrier(m1, decision_ts, sigma)
        event_end_ts = np.where(
            t_res < W,
            decision_ts + (t_res + 1) * MINUTE_MS,
            decision_ts + config.HORIZON_MS,
        ).astype(np.int64)
        mask_ok = (reason != 9) & ~ffill_in_path
        weight = uniqueness_weights(decision_ts, event_end_ts)
        assert np.all(event_end_ts > decision_ts)

        out = config.ASSETS_DIR / f"Asset_{t}" / f"Y_{t}.parquet"
        out.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="") as f:
            wcsv = csv.writer(f)
            for i in range(decision_ts.size):
                wcsv.writerow([int(decision_ts[i]), int(y[i]), int(event_end_ts[i]),
                               int(mask_ok[i]), repr(float(weight[i])), int(reason[i])])
            spool = Path(f.name)
        try:
            c2 = duckdb.connect()
            c2.execute(
                f"""COPY (SELECT * FROM read_csv('{spool}', header=false,
                          columns={{'decision_ts': 'BIGINT', 'y': 'TINYINT',
                                    'event_end_ts': 'BIGINT', 'mask_ok': 'BOOLEAN',
                                    'weight': 'DOUBLE', 'exit_reason': 'TINYINT'}})
                          ORDER BY decision_ts)
                    TO '{out}.tmp' (FORMAT PARQUET, COMPRESSION zstd)"""
            )
            c2.close()
            os.replace(f"{out}.tmp", out)
        finally:
            spool.unlink(missing_ok=True)
        n_amb = int((reason == 9).sum())
        n_masked = int((~mask_ok).sum())
        print(f"{out.name}: {decision_ts.size} rows  classes(-1/0/+1)="
              f"{int((y == -1).sum())}/{int((y == 0).sum())}/{int((y == 1).sum())}  "
              f"ambiguous={n_amb} masked={n_masked}", flush=True)
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
