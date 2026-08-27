"""Triple-barrier labels on the canonical research series, per asset.

One market object, two directions in time: X reads the canonical series up to
the decision, Y reads the same series after it —

    X_t = f(M_{<=t})        Y_t = g(M_{t+1 : t+H})       M = canonical series

so the features and the target describe the same canonical research object.
The sources that built M end at the ingest boundary; nothing below that line
knows which of them printed a given minute.

Timing, once and for all:

    t_d = decision_ts          close of the 15m bar; all features are known
    t_0 = entry_ts = t_d + 1m  the first fully tradable minute after the signal
    event = [t_0, t_v),        t_v = t_0 + 240 min

The barrier examines minutes t_0 … t_0+239. Entry is the canonical 1m open at
t_0; the barriers are P0 ± 2·ATR14 of the last closed canonical 1h bar. The first
minute whose high touches `upper_barrier` gives y = +1, whose low touches
`lower_barrier` gives y = -1, neither gives y = 0 with the exit at the close of
the last event minute. `event_end_ts` is the EXCLUSIVE end of the event, which
makes the purge rule exactly `event_end_ts <= oos_start`.

A touch requires a trade: `volume = 0` means no observed trade in that minute,
so hits are gated on `volume > 0`. Whether the minute was a provider candle
that printed nothing or a synthesized continuity row is a provenance question,
answered in the canonical table, not here. Both barriers inside one minute
leave the order unknowable from OHLC, so the row is
`label_valid = false` — never relabelled 0. That flag answers exactly one
question, "can this event be classified?", and it is knowable only after the
event resolves.

`entry_observable` answers a different, present-tense question: did the entry
minute trade at all? Both travel in Y, because both are properties of the
event, and downstream they combine into one population:

    sample_valid = entry_observable & label_valid

An unobservable entry is not merely untradable — its `entry_price` is the open
of a minute that printed no trade, so the barriers around it are anchored to a
quote nothing traded at.
Such a row is neither an executable decision nor a sound measurement, so it
carries no weight and trains nothing. The strategy still gates on
`entry_observable` alone and never on `label_valid`.
Average uniqueness [Lopez de Prado, ch. 4] is computed over the supervised
events only, so an excluded row cannot dilute the weights of the rows actually
trained on.

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
HORIZON_MINUTES = config.HORIZON_MINUTES

Y_COLUMNS = {
    "decision_ts": "BIGINT", "entry_ts": "BIGINT", "y": "TINYINT",
    "event_end_ts": "BIGINT", "entry_observable": "BOOLEAN",
    "label_valid": "BOOLEAN", "weight": "DOUBLE",
    "event_resolution": "TINYINT", "entry_price": "DOUBLE",
    "upper_barrier": "DOUBLE", "lower_barrier": "DOUBLE",
    "exit_reference_price": "DOUBLE",
}


def load_research_1m(con: duckdb.DuckDBPyConnection, sym: str) -> dict[str, np.ndarray]:
    """The canonical 1m series over the research window — the market object."""
    arrs = con.execute(
        f"""SELECT open, high, low, close, volume FROM ohlcv_1m_canonical
            WHERE symbol = '{sym}'
              AND timestamp_ms >= {config.RESEARCH_START_MS}
              AND timestamp_ms < {config.RESEARCH_END_MS}
            ORDER BY timestamp_ms"""
    ).fetchnumpy()
    expected = (config.RESEARCH_END_MS - config.RESEARCH_START_MS) // MINUTE_MS
    assert arrs["open"].size == expected, "canonical 1m grid incomplete inside the research window"
    return arrs


def triple_barrier(m1: dict[str, np.ndarray], entry_ts: np.ndarray, sigma: np.ndarray):
    """Walk the 1m path in chunks.

    Returns (y, t_res, event_resolution, entry_price, upper_barrier,
    lower_barrier, exit_reference_price).
    """
    idx = ((entry_ts - config.RESEARCH_START_MS) // MINUTE_MS).astype(np.int64)
    entry_price = m1["open"][idx]
    upper_barrier = entry_price + config.K_BARRIER * sigma
    lower_barrier = entry_price - config.K_BARRIER * sigma
    high, low, vol, opn, close = m1["high"], m1["low"], m1["volume"], m1["open"], m1["close"]

    n = idx.size
    y = np.zeros(n, dtype=np.int8)
    t_res = np.full(n, HORIZON_MINUTES, dtype=np.int32)
    event_resolution = np.zeros(n, dtype=np.int8)
    offsets = np.arange(HORIZON_MINUTES)
    for a in range(0, n, CHUNK):
        b = min(a + CHUNK, n)
        win = idx[a:b, None] + offsets[None, :]
        traded = vol[win] > 0                       # volume = 0 means no observed trade
        up_hit = traded & (high[win] >= upper_barrier[a:b, None])
        dn_hit = traded & (low[win] <= lower_barrier[a:b, None])
        t_up = np.where(up_hit.any(axis=1), up_hit.argmax(axis=1), HORIZON_MINUTES)
        t_dn = np.where(dn_hit.any(axis=1), dn_hit.argmax(axis=1), HORIZON_MINUTES)
        amb = (t_up == t_dn) & (t_up < HORIZON_MINUTES)
        y[a:b] = np.where(t_up < t_dn, 1, np.where(t_dn < t_up, -1, 0)).astype(np.int8)
        y[a:b][amb] = 0
        t_res[a:b] = np.minimum(t_up, t_dn)
        event_resolution[a:b] = np.where(amb, config.EVENT_RESOLUTION_AMBIGUOUS, y[a:b])

    resolved = t_res < HORIZON_MINUTES
    # horizontal or ambiguous: the open of the resolving minute (the price the
    # market was actually at); vertical: the close of the last event minute
    exit_reference_price = np.where(
        resolved,
        opn[idx + np.minimum(t_res, HORIZON_MINUTES - 1)],
        close[idx + HORIZON_MINUTES - 1],
    )
    return y, t_res, event_resolution, entry_price, upper_barrier, lower_barrier, exit_reference_price


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
        config.artifact_dir(ticker) / "label_events.parquet",
        Y_COLUMNS,
        ([
            int(cols["decision_ts"][i]), int(cols["entry_ts"][i]), int(cols["y"][i]),
            int(cols["event_end_ts"][i]), int(cols["entry_observable"][i]),
            int(cols["label_valid"][i]),
            repr(float(cols["weight"][i])), int(cols["event_resolution"][i]),
            repr(float(cols["entry_price"][i])), repr(float(cols["upper_barrier"][i])),
            repr(float(cols["lower_barrier"][i])),
            repr(float(cols["exit_reference_price"][i])),
        ] for i in range(cols["decision_ts"].size)),
        order_by="decision_ts",
    )


def main() -> int:
    args = config.ticker_parser("triple-barrier labels on the canonical 1m path").parse_args()
    con = duckdb.connect(str(config.DB_PATH), read_only=True)
    for t in config.parse_tickers(args.tickers):
        sym = config.symbol(t)
        bars_1h = con.execute(
            f"""SELECT timestamp_ms, high, low, close FROM ohlcv_1h_canonical
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

        m1 = load_research_1m(con, sym)
        (y, t_res, event_resolution, entry_price, upper_barrier, lower_barrier,
         exit_reference_price) = triple_barrier(m1, entry_ts, sigma)
        event_end_ts = entry_ts + np.minimum(t_res + 1, HORIZON_MINUTES) * MINUTE_MS   # exclusive
        assert np.all(event_end_ts > entry_ts)

        entry_idx = ((entry_ts - config.RESEARCH_START_MS) // MINUTE_MS).astype(np.int64)
        entry_observable = m1["volume"][entry_idx] > 0
        label_valid = event_resolution != config.EVENT_RESOLUTION_AMBIGUOUS
        sample_valid = entry_observable & label_valid

        weight = np.zeros(decision_ts.size)
        v = np.flatnonzero(sample_valid)
        weight[v] = uniqueness_weights(entry_ts[v], event_end_ts[v])

        out = write_y(t, {
            "decision_ts": decision_ts, "entry_ts": entry_ts, "y": y,
            "event_end_ts": event_end_ts, "entry_observable": entry_observable,
            "label_valid": label_valid, "weight": weight,
            "event_resolution": event_resolution, "entry_price": entry_price,
            "upper_barrier": upper_barrier, "lower_barrier": lower_barrier,
            "exit_reference_price": exit_reference_price,
        })
        print(f"{t} {out.name}: {decision_ts.size} rows  classes(-1/0/+1)="
              f"{int((y == -1).sum())}/{int((y == 0).sum())}/{int((y == 1).sum())}  "
              f"ambiguous={int((~label_valid).sum())}  "
              f"unobservable={int((~entry_observable).sum())}  "
              f"trainable={int(sample_valid.sum())}  "
              f"vertical={int((t_res == HORIZON_MINUTES).sum())}", flush=True)
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
