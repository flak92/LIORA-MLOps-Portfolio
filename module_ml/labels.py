"""Triple-barrier labels on the canonical 1m path, per asset.

    t_d = decision_ts          close of the 15m bar; all features are known
    t_0 = entry_ts = t_d + 1m  the candidate entry minute after the decision
    event = [t_0, t_v),        t_v = t_0 + 240 min

Entry is the canonical 1m open at t_0; the barriers are P0 ± 2·ATR14 of the last closed 1h bar; a touch requires
volume > 0; event_end_ts is the exclusive end of the event, so the purge rule is event_end_ts <= oos_start. Both
barriers inside one minute leave the order unknowable: label_valid = false, never relabelled 0. entry_observable
(the entry minute traded) may gate an entry; label_valid never does. Y also carries the prices the backtest replays.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np

from . import config, dataset, indicators

LABEL_PROCESSING_CHUNK_SIZE_ROWS = 16384

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
    """Walk the 1m path in chunks; returns (y, t_res, event_resolution, entry_price, upper_barrier, lower_barrier, exit_reference_price)."""
    idx = ((entry_ts - config.RESEARCH_START_MS) // config.MILLISECONDS_PER_MINUTE).astype(np.int64)
    entry_price = bars_1m["open"][idx]
    upper_barrier = entry_price + config.ATR_BARRIER_MULTIPLIER * sigma
    lower_barrier = entry_price - config.ATR_BARRIER_MULTIPLIER * sigma
    high, low, vol, opn, close = (bars_1m["high"], bars_1m["low"], bars_1m["volume"],
                                  bars_1m["open"], bars_1m["close"])

    event_count = idx.size
    y = np.zeros(event_count, dtype=np.int8)
    t_res = np.full(event_count, config.LABEL_HORIZON_MINUTES, dtype=np.int32)
    event_resolution = np.zeros(event_count, dtype=np.int8)
    offsets = np.arange(config.LABEL_HORIZON_MINUTES)
    for a in range(0, event_count, LABEL_PROCESSING_CHUNK_SIZE_ROWS):
        b = min(a + LABEL_PROCESSING_CHUNK_SIZE_ROWS, event_count)
        event_minutes = idx[a:b, None] + offsets[None, :]
        traded = vol[event_minutes] > 0             # volume = 0 means no observed trade
        up_hit = traded & (high[event_minutes] >= upper_barrier[a:b, None])
        dn_hit = traded & (low[event_minutes] <= lower_barrier[a:b, None])
        t_up = np.where(up_hit.any(axis=1), up_hit.argmax(axis=1), config.LABEL_HORIZON_MINUTES)
        t_dn = np.where(dn_hit.any(axis=1), dn_hit.argmax(axis=1), config.LABEL_HORIZON_MINUTES)
        ambiguous = (t_up == t_dn) & (t_up < config.LABEL_HORIZON_MINUTES)
        y[a:b] = np.where(t_up < t_dn, config.EVENT_RESOLUTION_UPPER_BARRIER,
                          np.where(t_dn < t_up, config.EVENT_RESOLUTION_LOWER_BARRIER,
                                   config.EVENT_RESOLUTION_VERTICAL)).astype(np.int8)
        t_res[a:b] = np.minimum(t_up, t_dn)
        event_resolution[a:b] = np.where(ambiguous, config.EVENT_RESOLUTION_AMBIGUOUS, y[a:b])

    resolved = t_res < config.LABEL_HORIZON_MINUTES
    # horizontal or ambiguous: the open of the resolving minute (the price the
    # market was actually at); vertical: the close of the last event minute
    exit_reference_price = np.where(
        resolved,
        opn[idx + np.minimum(t_res, config.LABEL_HORIZON_MINUTES - 1)],
        close[idx + config.LABEL_HORIZON_MINUTES - 1],
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
    args = config.build_ticker_parser("triple-barrier labels on the canonical 1m path").parse_args()
    for ticker in config.parse_tickers(args.tickers):
        symbol = config.symbol(ticker)
        con = duckdb.connect(str(config.research_ohlcv_duckdb(ticker)), read_only=True)
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
        assert np.isfinite(sigma).all() and (sigma > 0).all(), "ATR14 of the last closed 1h bar is not finite and positive at every decision"

        bars_1m = load_research_1m(con, symbol)
        con.close()
        (y, t_res, event_resolution, entry_price, upper_barrier, lower_barrier,
         exit_reference_price) = triple_barrier(bars_1m, entry_ts, sigma)
        event_end_ts = (entry_ts + np.minimum(t_res + 1, config.LABEL_HORIZON_MINUTES)
                        * config.MILLISECONDS_PER_MINUTE)              # exclusive

        entry_idx = ((entry_ts - config.RESEARCH_START_MS) // config.MILLISECONDS_PER_MINUTE).astype(np.int64)
        entry_observable = bars_1m["volume"][entry_idx] > 0
        label_valid = event_resolution != config.EVENT_RESOLUTION_AMBIGUOUS
        sample_valid = entry_observable & label_valid

        out = write_y(ticker, {
            "decision_ts": decision_ts, "entry_ts": entry_ts, "y": y,
            "event_end_ts": event_end_ts, "entry_observable": entry_observable,
            "label_valid": label_valid,
            "event_resolution": event_resolution, "entry_price": entry_price,
            "upper_barrier": upper_barrier, "lower_barrier": lower_barrier,
            "exit_reference_price": exit_reference_price,
        })
        print(f"{ticker} {out.name}: {decision_ts.size} rows  classes(-1/0/+1)="
              f"{int((y == -1).sum())}/{int((y == 0).sum())}/{int((y == 1).sum())}  "
              f"ambiguous={int((~label_valid).sum())}  "
              f"unobservable={int((~entry_observable).sum())}  "
              f"trainable={int(sample_valid.sum())}  "
              f"vertical={int((t_res == config.LABEL_HORIZON_MINUTES).sum())}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
