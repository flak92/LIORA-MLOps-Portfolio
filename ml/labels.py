"""Triple-barrier labels on the executable Binance USD-M path, per asset.

Market observation (X) comes from the canonical series; the label and the PnL
must describe the *same instrument*, so both come from Binance alone — one
position cannot hop between venues just because the canonical source switched.

Timing, once and for all:

    t_d = decision_ts          close of the 15m bar; all features are known
    t_0 = entry_ts = t_d + 1m  the first fully tradable minute after the signal
    event = [t_0, t_v),        t_v = t_0 + 240 min

The barrier examines minutes t_0 … t_0+239. Entry is the Binance 1m open at
t_0; the barriers are P0 ± 2·ATR14 of the last closed Binance 1h bar. The first
minute whose high touches the upper barrier gives y = +1, whose low touches the
lower gives y = -1, neither gives y = 0 with the exit at the close of the last
event minute. `event_end_ts` is the EXCLUSIVE end of the event, which makes the
purge rule exactly `event_end_ts <= oos_start`.

A touch requires a trade: a zero-volume minute is a carried-forward price, not
an execution, so hits are gated on `volume > 0` and an entry minute without
volume has no executable entry. Both barriers inside one minute leave the order
unknowable from OHLC, so the row is `label_valid = false` — never relabelled 0.
Average uniqueness [Lopez de Prado, ch. 4] is computed over the *valid* events
only, so a masked row cannot dilute the weights of the rows actually trained on.

Y also carries the prices the strategy needs (entry, both barriers, and the
reference price of the resolving minute), so the backtest replays exactly the
event that produced the label instead of recomputing it.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np

from . import config, dataset, indicators

CHUNK = 16384
MINUTE_MS = 60_000
W = config.HORIZON_MS // MINUTE_MS   # horizon in minutes (240)

Y_COLUMNS = {
    "decision_ts": "BIGINT", "entry_ts": "BIGINT", "y": "TINYINT",
    "event_end_ts": "BIGINT", "label_valid": "BOOLEAN", "weight": "DOUBLE",
    "exit_reason": "TINYINT", "p0": "DOUBLE", "upper": "DOUBLE",
    "lower": "DOUBLE", "exit_ref": "DOUBLE",
}


def load_venue_1m(con: duckdb.DuckDBPyConnection, sym: str) -> dict[str, np.ndarray]:
    """Binance 1m over the research window — the executable path."""
    arrs = con.execute(
        f"""SELECT open, high, low, close, volume FROM ohlcv_1m_binance
            WHERE symbol = '{sym}'
              AND timestamp_ms >= {config.RESEARCH_START_MS}
              AND timestamp_ms < {config.RESEARCH_END_MS}
            ORDER BY timestamp_ms"""
    ).fetchnumpy()
    expected = (config.RESEARCH_END_MS - config.RESEARCH_START_MS) // MINUTE_MS
    assert arrs["open"].size == expected, "Binance 1m grid incomplete inside the research window"
    return arrs


def triple_barrier(m1: dict[str, np.ndarray], entry_ts: np.ndarray, sigma: np.ndarray):
    """Walk the 1m path in chunks; return (y, t_res, reason, p0, upper, lower, exit_ref)."""
    idx = ((entry_ts - config.RESEARCH_START_MS) // MINUTE_MS).astype(np.int64)
    p0 = m1["open"][idx]
    upper = p0 + config.K_BARRIER * sigma
    lower = p0 - config.K_BARRIER * sigma
    high, low, vol, opn, close = m1["high"], m1["low"], m1["volume"], m1["open"], m1["close"]

    n = idx.size
    y = np.zeros(n, dtype=np.int8)
    t_res = np.full(n, W, dtype=np.int32)
    reason = np.zeros(n, dtype=np.int8)
    offsets = np.arange(W)
    for a in range(0, n, CHUNK):
        b = min(a + CHUNK, n)
        win = idx[a:b, None] + offsets[None, :]
        traded = vol[win] > 0                       # a carried-forward price is not a trade
        up_hit = traded & (high[win] >= upper[a:b, None])
        dn_hit = traded & (low[win] <= lower[a:b, None])
        t_up = np.where(up_hit.any(axis=1), up_hit.argmax(axis=1), W)
        t_dn = np.where(dn_hit.any(axis=1), dn_hit.argmax(axis=1), W)
        amb = (t_up == t_dn) & (t_up < W)
        y[a:b] = np.where(t_up < t_dn, 1, np.where(t_dn < t_up, -1, 0)).astype(np.int8)
        y[a:b][amb] = 0
        t_res[a:b] = np.minimum(t_up, t_dn)
        reason[a:b] = np.where(amb, 9, y[a:b])

    resolved = t_res < W
    # horizontal or ambiguous: the open of the resolving minute (the price the
    # market was actually at); vertical: the close of the last event minute
    exit_ref = np.where(resolved, opn[idx + np.minimum(t_res, W - 1)], close[idx + W - 1])
    return y, t_res, reason, p0, upper, lower, exit_ref


def uniqueness_weights(entry_ts: np.ndarray, end_ts: np.ndarray) -> np.ndarray:
    """Average uniqueness over each event's minutes, exact via prefix sums."""
    n_min = (config.RESEARCH_END_MS - config.RESEARCH_START_MS) // MINUTE_MS
    start = ((entry_ts - config.RESEARCH_START_MS) // MINUTE_MS).astype(np.int64)
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


def write_y(ticker: str, cols: dict[str, np.ndarray]) -> Path:
    return dataset.write_parquet(
        config.ASSETS_DIR / f"Asset_{ticker}" / f"Y_{ticker}.parquet",
        Y_COLUMNS,
        ([
            int(cols["decision_ts"][i]), int(cols["entry_ts"][i]), int(cols["y"][i]),
            int(cols["event_end_ts"][i]), int(cols["label_valid"][i]),
            repr(float(cols["weight"][i])), int(cols["exit_reason"][i]),
            repr(float(cols["p0"][i])), repr(float(cols["upper"][i])),
            repr(float(cols["lower"][i])), repr(float(cols["exit_ref"][i])),
        ] for i in range(cols["decision_ts"].size)),
        order_by="decision_ts",
    )


def main() -> int:
    args = config.ticker_parser("triple-barrier labels on the Binance 1m path").parse_args()
    con = duckdb.connect(str(config.DB_PATH), read_only=True)
    for t in config.parse_tickers(args.tickers):
        sym = config.symbol(t)
        bars_1h = con.execute(
            f"""SELECT timestamp_ms, high, low, close FROM ohlcv_1h_binance
                WHERE symbol = '{sym}' ORDER BY timestamp_ms"""
        ).fetchnumpy()
        ts15 = con.execute(
            f"""SELECT timestamp_ms FROM ohlcv_15m_canonical
                WHERE symbol = '{sym}' ORDER BY timestamp_ms"""
        ).fetchnumpy()["timestamp_ms"].astype(np.int64)

        decision_ts = ts15[ts15 >= config.WARMUP_END_MS]
        entry_ts = decision_ts + MINUTE_MS
        keep = entry_ts + config.HORIZON_MS <= config.RESEARCH_END_MS
        decision_ts, entry_ts = decision_ts[keep], entry_ts[keep]
        assert np.all(entry_ts > decision_ts)

        atr_1h = indicators.atr(bars_1h["high"], bars_1h["low"], bars_1h["close"], config.ATR_N)
        sigma = atr_1h[indicators.asof_index(decision_ts,
                                             bars_1h["timestamp_ms"].astype(np.int64),
                                             config.TF_MS["1h"])]
        assert np.isfinite(sigma).all() and (sigma > 0).all()

        m1 = load_venue_1m(con, sym)
        y, t_res, reason, p0, upper, lower, exit_ref = triple_barrier(m1, entry_ts, sigma)
        event_end_ts = entry_ts + np.minimum(t_res + 1, W) * MINUTE_MS   # exclusive
        assert np.all(event_end_ts > entry_ts)

        entry_idx = ((entry_ts - config.RESEARCH_START_MS) // MINUTE_MS).astype(np.int64)
        label_valid = (reason != 9) & (m1["volume"][entry_idx] > 0)

        weight = np.zeros(decision_ts.size)
        v = np.flatnonzero(label_valid)
        weight[v] = uniqueness_weights(entry_ts[v], event_end_ts[v])

        out = write_y(t, {
            "decision_ts": decision_ts, "entry_ts": entry_ts, "y": y,
            "event_end_ts": event_end_ts, "label_valid": label_valid, "weight": weight,
            "exit_reason": reason, "p0": p0, "upper": upper, "lower": lower,
            "exit_ref": exit_ref,
        })
        print(f"{out.name}: {decision_ts.size} rows  classes(-1/0/+1)="
              f"{int((y == -1).sum())}/{int((y == 0).sum())}/{int((y == 1).sum())}  "
              f"invalid={int((~label_valid).sum())} "
              f"(ambiguous {int((reason == 9).sum())}, no-trade entry "
              f"{int((m1['volume'][entry_idx] == 0).sum())})  "
              f"vertical={int((t_res == W).sum())}", flush=True)
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
