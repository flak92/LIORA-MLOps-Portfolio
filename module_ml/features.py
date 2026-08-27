"""Fixed hierarchical feature matrix X — 15 causal columns per asset.

Five families on three time scales, each named after what it computes
(ema20_minus_ema50_over_atr14, centered_rsi14, atr14_over_close,
range_position_20, log_volume_zscore_50, on 15m/1h/4h). Identical definition for every asset; no per-asset
selection. Cross-timeframe trend agreement is a strategy rule over these columns,
not a feature: it would carry no information the three trend columns lack.

Every value at decision_ts comes from the last CLOSED bar of its timeframe
(asof_index asserts causality); the 15m timeframe uses the bar closing exactly at
decision_ts.

Output: store_research_artifacts/<TICKER>/features.parquet with decision_ts + 15
feature columns, from the global research warm-up onward, no NaN (asserted).
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np

from . import config, dataset, indicators


def load_timeframe(con: duckdb.DuckDBPyConnection, sym: str, timeframe: str) -> dict[str, np.ndarray]:
    return con.execute(
        f"""SELECT timestamp_ms, open, high, low, close, volume
            FROM ohlcv_{timeframe}_canonical WHERE symbol = '{sym}' ORDER BY timestamp_ms"""
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


def build_x(con: duckdb.DuckDBPyConnection, ticker: str) -> tuple[np.ndarray, np.ndarray]:
    """Return (decision_ts, X matrix ordered as config.FEATURE_COLUMNS)."""
    sym = config.symbol(ticker)
    timeframes = {timeframe: load_timeframe(con, sym, timeframe) for timeframe in config.HIERARCHY_TIMEFRAMES}
    feats = {timeframe: timeframe_features(timeframes[timeframe])
             for timeframe in config.HIERARCHY_TIMEFRAMES}

    ts15 = timeframes["15m"]["timestamp_ms"].astype(np.int64)
    decision_ts = ts15[ts15 >= config.WARMUP_END_MS]

    cols: dict[str, np.ndarray] = {}
    for timeframe in config.HIERARCHY_TIMEFRAMES:
        idx = indicators.asof_index(decision_ts,
                                    timeframes[timeframe]["timestamp_ms"].astype(np.int64),
                                    config.TIMEFRAME_DURATION_MS[timeframe])
        for family in config.FAMILIES:
            cols[f"{family}_{timeframe}"] = feats[timeframe][family][idx]

    x = np.column_stack([cols[c] for c in config.FEATURE_COLUMNS])
    assert np.isfinite(x).all(), "NaN/inf in X after the research warm-up"
    return decision_ts, x


def write_x(ticker: str, decision_ts: np.ndarray, x: np.ndarray) -> Path:
    return dataset.write_parquet(
        config.artifact_dir(ticker) / "features.parquet",
        {"decision_ts": "BIGINT", **{c: "DOUBLE" for c in config.FEATURE_COLUMNS}},
        ([int(decision_ts[i])] + [repr(float(v)) for v in x[i]]
         for i in range(decision_ts.size)),
        order_by="decision_ts",
    )


def main() -> int:
    args = config.ticker_parser("hierarchical feature matrix X per asset").parse_args()
    con = duckdb.connect(str(config.DB_PATH), read_only=True)
    for t in config.parse_tickers(args.tickers):
        decision_ts, x = build_x(con, t)
        out = write_x(t, decision_ts, x)
        print(f"{t} {out.name}: {decision_ts.size} rows x {x.shape[1]} features", flush=True)
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
