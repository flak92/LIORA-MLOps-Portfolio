"""Top-down gated strategy on the canonical research path.

    directional_probability_edge = p_long - p_short;  side = sign(edge)
    agreeing_trend_timeframe_count = #{timeframe : sign(trend_timeframe) == side}
    enter = |edge| >= entry_edge_threshold  AND  max(p_long, p_short) > p_neutral  AND  side != 0
            AND side == sign(trend_4h)  AND  agreeing_trend_timeframe_count >= 2
            AND entry_observable

The model picks the side, the hierarchy gates it. Two conditions that look
alike must not be confused:

    entry_observable = volume(entry_ts) > 0   known at t_0, MAY gate an entry
    label_valid      = event classifiable    known only afterwards, NEVER gates

A minute that printed no trade cannot be entered, and that is visible at the
time. Whether the event will resolve ambiguously is not, so label validity
governs training and scoring only — a signal whose event later turns out
ambiguous is still a trade, settled at the barrier adverse to the position.

The simulation applies USDT-perpetual PnL algebra to the canonical price path
at a fixed quantity, so PnL is linear in price:

    Q      = s * E0 / P0                       notional 1x current equity
    R      = s * (Px/P0 - 1) - c - c * (Px/P0)  entry fee c*E0, exit fee c*|Q|*Px
    E_next = E0 * (1 + R)
    E_t    = E0 * (1 - c + s * (Pt/P0 - 1))     mark-to-market while open

Compounding per-bar returns instead would misprice shorts: 100 -> 50 -> 100
gives 0% here and -100% under compounding.

Fills acknowledge that 1m OHLC hides the tick path: a take-profit fills at the
barrier, a stop fills at the worse of the barrier and the open of the minute
that touched it. The result is execution-cost-adjusted PnL, excluding funding.

The entry edge threshold is chosen on the validation folds only: the one
maximising the mean fold Sharpe among those giving at least
MINIMUM_TRADES_PER_VALIDATION_FOLD trades in every fold, ties resolved towards the
smaller threshold.
"""

from __future__ import annotations

import duckdb
import numpy as np

from . import config, dataset, validation

MILLISECONDS_PER_MINUTE = config.MILLISECONDS_PER_MINUTE
EQUITY_CURVE_SAMPLE_INTERVAL_MINUTES = 1440    # one equity point per day for the dashboard curve
BAR_CLOSE_OFFSET_MINUTES = 14          # a 15m bar closes on the 15th minute of its block


def load_inputs(ticker: str) -> dict:
    adir = config.artifact_dir(ticker)
    symbol = config.symbol(ticker)
    xy = dataset.load_xy(ticker)
    con = duckdb.connect(str(config.STORE_DB_PATH), read_only=True)
    close_1m = con.execute(
        f"""SELECT close FROM ohlcv_1m_canonical
            WHERE symbol = '{symbol}'
              AND timestamp_ms >= {config.RESEARCH_START_MS}
              AND timestamp_ms < {config.RESEARCH_END_MS}
            ORDER BY timestamp_ms"""
    ).fetchnumpy()["close"]
    con.close()
    c2 = duckdb.connect()
    preds = c2.execute(
        f"SELECT * FROM read_parquet('{config.oos_predictions_parquet(ticker)}') ORDER BY oos_fold_id, decision_ts"
    ).fetchnumpy()
    c2.close()

    trend = {timeframe: xy["x"][:, config.FEATURE_COLUMNS.index(f"{config.TREND_FAMILY}_{timeframe}")]
             for timeframe in config.HIERARCHY_TIMEFRAMES}
    return {"xy": xy, "close_1m": close_1m, "trend": trend, "preds": preds}


def signals_for_fold(inputs: dict, fold_id: int) -> dict:
    """Signal arrays for one fold, aligned to the label-event grid."""
    xy = inputs["xy"]
    in_fold = inputs["preds"]["oos_fold_id"] == fold_id
    ts = inputs["preds"]["decision_ts"][in_fold].astype(np.int64)
    pos = np.searchsorted(xy["decision_ts"], ts)
    assert np.array_equal(xy["decision_ts"][pos], ts)
    p_short, p_long = inputs["preds"]["p_short"][in_fold], inputs["preds"]["p_long"][in_fold]
    p_neutral = inputs["preds"]["p_neutral"][in_fold]
    directional_probability_edge = p_long - p_short
    side = np.sign(directional_probability_edge)
    agreeing_trend_timeframe_count = sum(
        (np.sign(inputs["trend"][timeframe][pos]) == side).astype(np.int64)
        for timeframe in config.HIERARCHY_TIMEFRAMES)
    gate = (
        (np.maximum(p_long, p_short) > p_neutral)
        & (side != 0)
        & (side == np.sign(inputs["trend"][config.TREND_GATE_TIMEFRAME][pos]))
        & (agreeing_trend_timeframe_count >= config.MINIMUM_AGREEING_TREND_TIMEFRAMES)
    )
    return {
        "directional_probability_edge": directional_probability_edge,
        "side": side, "gate": gate,
        "entry_observable": xy["entry_observable"][pos],
        "entry_ts": xy["entry_ts"][pos], "event_end_ts": xy["event_end_ts"][pos],
        "event_resolution": xy["event_resolution"][pos],
        "entry_price": xy["entry_price"][pos],
        "upper_barrier": xy["upper_barrier"][pos],
        "lower_barrier": xy["lower_barrier"][pos],
        "exit_reference_price": xy["exit_reference_price"][pos],
    }


def fill_price(side: float, event_resolution: int, upper_barrier: float,
               lower_barrier: float, exit_reference_price: float) -> float:
    """Take-profit at the barrier; stop (and the adverse side of an ambiguous
    minute) at the worse of the barrier and that minute's open. A vertical exit
    settles at the last event minute's close — a last-observed-price mark that,
    unlike a barrier touch, needs no trade in that minute (methodology_ml.md §5)."""
    if event_resolution == config.EVENT_RESOLUTION_VERTICAL:
        return exit_reference_price                      # mark: last event minute's close
    if event_resolution == side:
        return upper_barrier if side > 0 else lower_barrier   # target reached
    return (min(lower_barrier, exit_reference_price) if side > 0
            else max(upper_barrier, exit_reference_price))


def backtest(inputs: dict, signals: dict, entry_edge_threshold: float,
             fold_start_ms: int, fold_end_ms: int) -> dict:
    """Single-position state machine producing one continuous equity path."""
    c = config.EXECUTION_COST_RATE_PER_TRADE_SIDE
    fold_start_minute = (fold_start_ms - config.RESEARCH_START_MS) // MILLISECONDS_PER_MINUTE
    fold_minute_count = (fold_end_ms - fold_start_ms) // MILLISECONDS_PER_MINUTE
    close_1m = inputs["close_1m"]
    equity_1m = np.empty(fold_minute_count)

    enter = (signals["gate"] & signals["entry_observable"]
             & (np.abs(signals["directional_probability_edge"]) >= entry_edge_threshold))
    # A trade must be able to finish inside the fold, and that has to be decidable
    # at t_0: testing the REAL event_end_ts would let the future decide whether the
    # position was opened at all — a signal that happened to hit a barrier early
    # would fit where one that ran to the vertical barrier would not. The maximum
    # horizon is the only version of the question the entry moment can answer.
    fits = ((signals["entry_ts"] >= fold_start_ms)
            & (signals["entry_ts"] + config.LABEL_HORIZON_MS <= fold_end_ms))
    take = np.flatnonzero(enter & fits)

    equity, cursor, in_pos_ms = 1.0, 0, 0
    trades = []
    # the exit counts are counts by event_resolution, so they carry its names
    exits = {name: 0 for name in config.EVENT_RESOLUTION_NAME.values()}
    for k in take:
        i = int((signals["entry_ts"][k] - config.RESEARCH_START_MS)
                // MILLISECONDS_PER_MINUTE) - fold_start_minute
        j = int((signals["event_end_ts"][k] - config.RESEARCH_START_MS)
                // MILLISECONDS_PER_MINUTE) - fold_start_minute - 1
        if i < cursor:
            continue                                     # position still open
        s = float(signals["side"][k])
        entry_price = float(signals["entry_price"][k])
        resolution = int(signals["event_resolution"][k])
        px = fill_price(s, resolution, float(signals["upper_barrier"][k]),
                        float(signals["lower_barrier"][k]),
                        float(signals["exit_reference_price"][k]))
        equity_1m[cursor:i] = equity                     # flat while out of the market
        equity_1m[i:j] = equity * (1.0 - c + s * (
            close_1m[fold_start_minute + i:fold_start_minute + j] / entry_price - 1.0))
        r = s * (px / entry_price - 1.0) - c - c * (px / entry_price)
        equity *= 1.0 + r
        equity_1m[j] = equity
        cursor = j + 1
        in_pos_ms += int(signals["event_end_ts"][k] - signals["entry_ts"][k])
        trades.append(r)
        exits[config.EVENT_RESOLUTION_NAME[resolution]] += 1
    equity_1m[cursor:] = equity

    trade_returns = np.asarray(trades)
    # the same path sampled at bar closes, starting from the capital itself:
    # without E0 the first 15 minutes of the fold produce no return at all
    equity_15m = np.concatenate(([1.0], equity_1m[BAR_CLOSE_OFFSET_MINUTES::15]))
    returns_15m = np.diff(equity_15m) / equity_15m[:-1]
    return {
        "equity_1m": equity_1m,
        "sharpe": validation.sharpe_annualised(returns_15m),
        "max_drawdown": validation.max_drawdown(equity_1m),  # 1m path: intra-bar drawdown is real
        "trade_count": int(trade_returns.size),
        "hit_rate": float((trade_returns > 0).mean()) if trade_returns.size else None,
        "average_trade_return": float(trade_returns.mean()) if trade_returns.size else None,
        "exposure": in_pos_ms / (fold_end_ms - fold_start_ms),
        "exit_counts": exits,
        "final_equity": float(equity),
    }


def without_equity_path(result: dict) -> dict:
    """Everything but the 1m path, which is an intermediate, not a report."""
    return {k: v for k, v in result.items() if k != "equity_1m"}


def equity_curve(equity_1m: np.ndarray, fold_start_ms: int) -> dict:
    idx = np.arange(0, equity_1m.size, EQUITY_CURVE_SAMPLE_INTERVAL_MINUTES)
    return {
        "timestamp_ms": (fold_start_ms + idx * MILLISECONDS_PER_MINUTE).tolist(),
        "equity": np.round(equity_1m[idx], 6).tolist(),
    }


def main() -> int:
    args = config.ticker_parser(
        "entry edge threshold on the validation folds, final-holdout PnL"
    ).parse_args()

    for t in config.parse_tickers(args.tickers):
        inputs = load_inputs(t)
        validation_rows = {fold_id: signals_for_fold(inputs, fold_id)
                           for fold_id in config.VALIDATION_FOLD_IDS}
        validation_bounds = {fold_id: validation.fold_bounds(fold_id)
                             for fold_id in config.VALIDATION_FOLD_IDS}

        # the locals carry the names of the keys they end up as, so the selection
        # loop reads like the artifact it writes
        entry_edge_threshold, selection_score_mean_sharpe = None, -np.inf
        validation_by_fold, entry_edge_threshold_constraint_met = None, False
        for threshold in config.ENTRY_EDGE_THRESHOLD_GRID:
            results_by_fold = {fold_id: backtest(inputs, validation_rows[fold_id], threshold,
                                                 *validation_bounds[fold_id])
                               for fold_id in config.VALIDATION_FOLD_IDS}
            if any(r["trade_count"] < config.MINIMUM_TRADES_PER_VALIDATION_FOLD
                   for r in results_by_fold.values()):
                continue
            entry_edge_threshold_constraint_met = True
            score = float(np.mean([r["sharpe"] for r in results_by_fold.values()]))
            if score > selection_score_mean_sharpe:      # strict: ties keep the smaller threshold
                entry_edge_threshold, selection_score_mean_sharpe = threshold, score
                validation_by_fold = results_by_fold
        if not entry_edge_threshold_constraint_met:      # deterministic fallback, reported as such
            entry_edge_threshold = 0.0
            validation_by_fold = {fold_id: backtest(inputs, validation_rows[fold_id],
                                                    entry_edge_threshold, *validation_bounds[fold_id])
                                  for fold_id in config.VALIDATION_FOLD_IDS}
            selection_score_mean_sharpe = float(
                np.mean([r["sharpe"] for r in validation_by_fold.values()]))

        holdout_start, holdout_end = validation.fold_bounds(config.FINAL_HOLDOUT_FOLD_ID)
        final_holdout = backtest(inputs, signals_for_fold(inputs, config.FINAL_HOLDOUT_FOLD_ID),
                                 entry_edge_threshold, holdout_start, holdout_end)

        payload = {
            "entry_edge_threshold": entry_edge_threshold,
            "entry_edge_threshold_constraint_met": entry_edge_threshold_constraint_met,
            "selection_score_mean_sharpe": selection_score_mean_sharpe,
            "execution_cost_rate_per_trade_side": config.EXECUTION_COST_RATE_PER_TRADE_SIDE,
            "validation": {f"fold_{fold_id}": without_equity_path(r)
                           for fold_id, r in validation_by_fold.items()},
            "final_holdout": {**without_equity_path(final_holdout),
                              "equity_curve": equity_curve(final_holdout["equity_1m"],
                                                          holdout_start)},
        }
        out = config.strategy_evaluation_json(t)
        dataset.write_json(out, payload)
        print(f"{t} {out.name}: threshold={entry_edge_threshold} sharpe {final_holdout['sharpe']:.3f} "
              f"trades {final_holdout['trade_count']} maxDD {final_holdout['max_drawdown']:.3f} "
              f"final equity {final_holdout['final_equity']:.3f}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
