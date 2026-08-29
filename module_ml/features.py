"""X: 15 causal columns per asset — five families on 15m/1h/4h, every value from the last closed bar of its
timeframe; one parquet per timeframe, from the research warm-up onward."""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np

from . import config, dataset, indicators


def load_timeframe(con: duckdb.DuckDBPyConnection, symbol: str, timeframe: str) -> dict[str, np.ndarray]:
    return con.execute(
        f"""SELECT timestamp_ms, open, high, low, close, volume
            FROM ohlcv_{timeframe}_canonical WHERE symbol = '{symbol}' ORDER BY timestamp_ms"""
    ).fetchnumpy()


def timeframe_features(bars: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """The five family features on one timeframe's own bars."""
    close, high, low, vol = bars["close"], bars["high"], bars["low"], bars["volume"]
    atr14 = indicators.atr(high, low, close, config.ATR_WILDER_SMOOTHING_PERIOD_BARS)
    with np.errstate(divide="ignore", invalid="ignore"):
        ema_spread = (indicators.ema(close, config.EMA_FAST_SPAN_BARS)
                      - indicators.ema(close, config.EMA_SLOW_SPAN_BARS)) / atr14
    return {
        "ema20_minus_ema50_over_atr14": np.where(atr14 == 0.0, 0.0, ema_spread),
        "centered_rsi14": (indicators.rsi(close, config.RSI_WILDER_SMOOTHING_PERIOD_BARS) - 50.0) / 50.0,
        "atr14_over_close": atr14 / close,
        "range_position_20": indicators.range_position(close, high, low, config.RANGE_POSITION_LOOKBACK_BARS),
        "log_volume_zscore_50": indicators.rolling_zscore(
            np.log1p(vol), config.LOG_VOLUME_ZSCORE_LOOKBACK_BARS),
    }


def build_x(con: duckdb.DuckDBPyConnection, ticker: str) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Return (decision_ts, the named feature columns of config.FEATURE_COLUMNS);
    the stacked matrix is built only to assert finiteness across all of them."""
    symbol = config.symbol(ticker)
    timeframes = {timeframe: load_timeframe(con, symbol, timeframe) for timeframe in config.HIERARCHY_TIMEFRAMES}
    feats = {timeframe: timeframe_features(timeframes[timeframe])
             for timeframe in config.HIERARCHY_TIMEFRAMES}

    ts_15m = timeframes[config.DECISION_TIMEFRAME]["timestamp_ms"].astype(np.int64)
    decision_ts = ts_15m[ts_15m >= config.WARMUP_END_MS]

    cols: dict[str, np.ndarray] = {}
    for timeframe in config.HIERARCHY_TIMEFRAMES:
        idx = indicators.asof_index(decision_ts,
                                    timeframes[timeframe]["timestamp_ms"].astype(np.int64),
                                    config.TIMEFRAME_DURATION_MS[timeframe])
        for family in config.FEATURE_FAMILIES:
            cols[f"{family}_{timeframe}"] = feats[timeframe][family][idx]

    x = np.column_stack([cols[c] for c in config.FEATURE_COLUMNS])
    assert np.isfinite(x).all(), "NaN/inf in X after the research warm-up"
    return decision_ts, cols


def write_x(ticker: str, decision_ts: np.ndarray, cols: dict[str, np.ndarray]) -> list[Path]:
    """One parquet per timeframe: that timeframe's five family columns on the
    decision grid. The filename carries the timeframe, so the columns do not."""
    written = []
    for timeframe in config.HIERARCHY_TIMEFRAMES:
        written.append(dataset.write_parquet(
            config.features_parquet(ticker, timeframe),
            {"decision_ts": "BIGINT", **{family: "DOUBLE" for family in config.FEATURE_FAMILIES}},
            ([int(decision_ts[i])] + [repr(float(cols[f"{family}_{timeframe}"][i]))
                                      for family in config.FEATURE_FAMILIES]
             for i in range(decision_ts.size)),
            order_by="decision_ts",
        ))
    return written


def main() -> int:
    args = config.build_ticker_parser("hierarchical feature matrix X per asset").parse_args()
    for ticker in config.parse_tickers(args.tickers):
        con = duckdb.connect(str(config.research_ohlcv_duckdb(ticker)), read_only=True)
        decision_ts, cols = build_x(con, ticker)
        con.close()
        written = write_x(ticker, decision_ts, cols)
        print(f"{ticker} {', '.join(w.name for w in written)}: "
              f"{decision_ts.size} rows x {len(config.FEATURE_FAMILIES)} families each", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
