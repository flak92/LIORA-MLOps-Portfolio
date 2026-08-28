"""Triple-barrier labels on the canonical research series, per asset.

One market object, two directions in time: X reads the canonical series up to
the decision, Y reads the same series after it —

    X_t = f(M_{<=t})        Y_t = g(M_{t+1 : t+H})       M = canonical series

so the features and the target describe the same canonical research object.
The sources that built M end at the ingest boundary; nothing below that line
knows which of them printed a given minute.

Timing, once and for all:

    t_d = decision_ts          close of the 15m bar; all features are known
    t_0 = entry_ts = t_d + 1m  the candidate entry minute after the decision
    event = [t_0, t_v),        t_v = t_0 + 240 min

The barrier examines minutes t_0 … t_0+239. Entry is the canonical 1m open at
t_0; the barriers are P0 ± 2·ATR14 of the last closed canonical 1h bar. The first
minute whose high touches `upper_barrier` gives y = +1, whose low touches
`lower_barrier` gives y = -1, neither gives y = 0 with the exit at the close of
the last event minute. `event_end_ts` is the EXCLUSIVE end of the event, which
makes the purge rule exactly `event_end_ts <= oos_start`.

A touch requires a trade: `volume = 0` means no observed trade in that minute,
so hits are gated on `volume > 0`. Whether the minute was a provider candle
that printed nothing or a synthesised continuity row is a provenance question,
answered in the canonical table, not here. The vertical exit mark is not gated:
the close of the last event minute is a last-observed-price mark, not a fill
(methodology_ml.md §5). Both barriers inside one minute
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
Sample weights are NOT computed here. Average uniqueness depends on which
events are open at the same time, and that population is a property of a
fold, not of the label: `validation.py` measures it over the purged training
rows and over the scored rows separately.

Y also carries the prices the strategy needs (entry, both barriers, and the
reference price of the resolving minute), so the backtest replays exactly the
event that produced the label instead of recomputing it.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np

from . import config, dataset, indicators

LABEL_PROCESSING_CHUNK_SIZE_ROWS = 16384
LABEL_HORIZON_MINUTES = config.LABEL_HORIZON_MINUTES

Y_COLUMNS = {
    "decision_ts": "BIGINT", "entry_ts": "BIGINT", "y": "TINYINT",
    "event_end_ts": "BIGINT", "entry_observable": "BOOLEAN",
    "label_valid": "BOOLEAN",
    "event_resolution": "TINYINT", "entry_price": "DOUBLE",
    "upper_barrier": "DOUBLE", "lower_barrier": "DOUBLE",
    "exit_reference_price": "DOUBLE",
}


def load_research_1m(con: duckdb.DuckDBPyConnection, symbol: str) -> dict[str, np.ndarray]:
    """The canonical 1m series over the research window — the market object."""
    bars_1m = con.execute(
        f"""SELECT open, high, low, close, volume FROM ohlcv_1m_canonical
            WHERE symbol = '{symbol}'
              AND timestamp_ms >= {config.RESEARCH_START_MS}
              AND timestamp_ms < {config.RESEARCH_END_MS}
            ORDER BY timestamp_ms"""
    ).fetchnumpy()
    expected = (config.RESEARCH_END_MS - config.RESEARCH_START_MS) // config.MILLISECONDS_PER_MINUTE
    assert bars_1m["open"].size == expected, "canonical 1m grid incomplete inside the research window"
    return bars_1m


def triple_barrier(bars_1m: dict[str, np.ndarray], entry_ts: np.ndarray, sigma: np.ndarray):
    """Walk the 1m path in chunks.

    Returns (y, t_res, event_resolution, entry_price, upper_barrier,
    lower_barrier, exit_reference_price).
    """
    idx = ((entry_ts - config.RESEARCH_START_MS) // config.MILLISECONDS_PER_MINUTE).astype(np.int64)
    entry_price = bars_1m["open"][idx]
    upper_barrier = entry_price + config.ATR_BARRIER_MULTIPLIER * sigma
    lower_barrier = entry_price - config.ATR_BARRIER_MULTIPLIER * sigma
    high, low, vol, opn, close = (bars_1m["high"], bars_1m["low"], bars_1m["volume"],
                                  bars_1m["open"], bars_1m["close"])

    event_count = idx.size
    y = np.zeros(event_count, dtype=np.int8)
    t_res = np.full(event_count, LABEL_HORIZON_MINUTES, dtype=np.int32)
    event_resolution = np.zeros(event_count, dtype=np.int8)
    offsets = np.arange(LABEL_HORIZON_MINUTES)
    for a in range(0, event_count, LABEL_PROCESSING_CHUNK_SIZE_ROWS):
        b = min(a + LABEL_PROCESSING_CHUNK_SIZE_ROWS, event_count)
        event_minutes = idx[a:b, None] + offsets[None, :]
        traded = vol[event_minutes] > 0             # volume = 0 means no observed trade
        up_hit = traded & (high[event_minutes] >= upper_barrier[a:b, None])
        dn_hit = traded & (low[event_minutes] <= lower_barrier[a:b, None])
        t_up = np.where(up_hit.any(axis=1), up_hit.argmax(axis=1), LABEL_HORIZON_MINUTES)
        t_dn = np.where(dn_hit.any(axis=1), dn_hit.argmax(axis=1), LABEL_HORIZON_MINUTES)
        ambiguous = (t_up == t_dn) & (t_up < LABEL_HORIZON_MINUTES)
        y[a:b] = np.where(t_up < t_dn, 1, np.where(t_dn < t_up, -1, 0)).astype(np.int8)
        t_res[a:b] = np.minimum(t_up, t_dn)
        event_resolution[a:b] = np.where(ambiguous, config.EVENT_RESOLUTION_AMBIGUOUS, y[a:b])

    resolved = t_res < LABEL_HORIZON_MINUTES
    # horizontal or ambiguous: the open of the resolving minute (the price the
    # market was actually at); vertical: the close of the last event minute
    exit_reference_price = np.where(
        resolved,
        opn[idx + np.minimum(t_res, LABEL_HORIZON_MINUTES - 1)],
        close[idx + LABEL_HORIZON_MINUTES - 1],
    )
    return y, t_res, event_resolution, entry_price, upper_barrier, lower_barrier, exit_reference_price


def write_y(ticker: str, cols: dict[str, np.ndarray]) -> Path:
    return dataset.write_parquet(
        config.label_events_parquet(ticker),
        Y_COLUMNS,
        ([
            int(cols["decision_ts"][i]), int(cols["entry_ts"][i]), int(cols["y"][i]),
            int(cols["event_end_ts"][i]), int(cols["entry_observable"][i]),
            int(cols["label_valid"][i]), int(cols["event_resolution"][i]),
            repr(float(cols["entry_price"][i])), repr(float(cols["upper_barrier"][i])),
            repr(float(cols["lower_barrier"][i])),
            repr(float(cols["exit_reference_price"][i])),
        ] for i in range(cols["decision_ts"].size)),
        order_by="decision_ts",
    )


def main() -> int:
    args = config.ticker_parser("triple-barrier labels on the canonical 1m path").parse_args()
    con = duckdb.connect(str(config.STORE_DB_PATH), read_only=True)
    for t in config.parse_tickers(args.tickers):
        symbol = config.symbol(t)
        bars_1h = con.execute(
            f"""SELECT timestamp_ms, high, low, close FROM ohlcv_1h_canonical
                WHERE symbol = '{symbol}' ORDER BY timestamp_ms"""
        ).fetchnumpy()
        ts_15m = con.execute(
            f"""SELECT timestamp_ms FROM ohlcv_15m_canonical
                WHERE symbol = '{symbol}' ORDER BY timestamp_ms"""
        ).fetchnumpy()["timestamp_ms"].astype(np.int64)

        decision_ts = ts_15m[ts_15m >= config.WARMUP_END_MS]
        entry_ts = decision_ts + config.MILLISECONDS_PER_MINUTE
        keep = entry_ts + config.LABEL_HORIZON_MS <= config.RESEARCH_END_MS
        decision_ts, entry_ts = decision_ts[keep], entry_ts[keep]

        atr_1h = indicators.atr(bars_1h["high"], bars_1h["low"], bars_1h["close"],
                                config.ATR_WILDER_SMOOTHING_PERIOD_BARS)
        sigma = atr_1h[indicators.asof_index(decision_ts,
                                             bars_1h["timestamp_ms"].astype(np.int64),
                                             config.TIMEFRAME_DURATION_MS["1h"])]
        assert np.isfinite(sigma).all() and (sigma > 0).all()

        bars_1m = load_research_1m(con, symbol)
        (y, t_res, event_resolution, entry_price, upper_barrier, lower_barrier,
         exit_reference_price) = triple_barrier(bars_1m, entry_ts, sigma)
        event_end_ts = (entry_ts + np.minimum(t_res + 1, LABEL_HORIZON_MINUTES)
                        * config.MILLISECONDS_PER_MINUTE)              # exclusive

        entry_idx = ((entry_ts - config.RESEARCH_START_MS) // config.MILLISECONDS_PER_MINUTE).astype(np.int64)
        entry_observable = bars_1m["volume"][entry_idx] > 0
        label_valid = event_resolution != config.EVENT_RESOLUTION_AMBIGUOUS
        sample_valid = entry_observable & label_valid

        out = write_y(t, {
            "decision_ts": decision_ts, "entry_ts": entry_ts, "y": y,
            "event_end_ts": event_end_ts, "entry_observable": entry_observable,
            "label_valid": label_valid,
            "event_resolution": event_resolution, "entry_price": entry_price,
            "upper_barrier": upper_barrier, "lower_barrier": lower_barrier,
            "exit_reference_price": exit_reference_price,
        })
        print(f"{t} {out.name}: {decision_ts.size} rows  classes(-1/0/+1)="
              f"{int((y == -1).sum())}/{int((y == 0).sum())}/{int((y == 1).sum())}  "
              f"ambiguous={int((~label_valid).sum())}  "
              f"unobservable={int((~entry_observable).sum())}  "
              f"trainable={int(sample_valid.sum())}  "
              f"vertical={int((t_res == LABEL_HORIZON_MINUTES).sum())}", flush=True)
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
