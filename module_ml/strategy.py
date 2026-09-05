"""Top-down gated strategy on the canonical research path.

    directional_probability_edge = p_long - p_short;  side = sign(edge)
    agreeing_trend_timeframe_count = #{timeframe : sign(TREND_GATE_FEATURE_DEFINITION_<timeframe>) == side}
    enter = |edge| >= entry_edge_threshold  AND  max(p_long, p_short) > p_neutral  AND  side != 0
            AND side == sign(TREND_GATE_FEATURE_DEFINITION_<TREND_GATE_TIMEFRAME>)
            AND agreeing_trend_timeframe_count >= 2
            AND entry_observable

USDT-perpetual PnL at a fixed quantity, linear in price (compounding per-bar returns would misprice shorts):

    Q      = s * E0 / P0                       notional 1x current equity
    R      = s * (Px/P0 - 1) - c - c * (Px/P0)  entry fee c*E0, exit fee c*|Q|*Px
    E_next = E0 * (1 + R)
    E_t    = E0 * (1 - c + s * (Pt/P0 - 1))     mark-to-market while open

A take-profit fills at the barrier, a stop at the worse of the barrier and the open of the touching minute. The
entry edge threshold is the grid point maximising the mean validation-fold Sharpe among those with at least
MINIMUM_TRADES_PER_VALIDATION_FOLD trades in every fold, ties to the smaller threshold.
"""

from __future__ import annotations

import duckdb
import numpy as np

from . import config, dataset, validation

EQUITY_CURVE_SAMPLE_INTERVAL_MINUTES = 1440    # one equity point per day for the dashboard curve


def load_close_1m(ticker: str) -> np.ndarray:
    """The canonical 1m closes over the research window — the path the backtest replays."""
    con = duckdb.connect(str(config.research_ohlcv_duckdb(ticker)), read_only=True)
    con.execute(f"SET memory_limit='{config.DUCKDB_MEMORY_LIMIT}'")
    con.execute("SET threads=1")   # float summation must not be reordered
    close_1m = con.execute(
        f"""SELECT close FROM ohlcv_1m_canonical
            WHERE timestamp_ms >= {config.RESEARCH_START_MS}
              AND timestamp_ms < {config.RESEARCH_END_MS}
            ORDER BY timestamp_ms"""
    ).fetchnumpy()["close"]
    con.close()
    return close_1m


def load_oos_predictions(ticker: str, cat: dict) -> dict[str, np.ndarray]:
    """The out-of-sample windows as train.py wrote them, fold-major and by decision."""
    parquet_con = duckdb.connect()
    parquet_con.execute(f"SET memory_limit='{config.DUCKDB_MEMORY_LIMIT}'")
    parquet_con.execute("SET threads=1")   # float summation must not be reordered
    oos_predictions = parquet_con.execute(
        f"SELECT * FROM read_parquet('{config.oos_predictions_parquet(ticker, cat)}') ORDER BY oos_fold_id, decision_ts"
    ).fetchnumpy()
    parquet_con.close()
    return oos_predictions


def build_simulation_inputs(xy: dict, close_1m: np.ndarray, oos_predictions: dict[str, np.ndarray]) -> dict:
    """The strategy's inputs: X and Y, the 1m path, the predictions, and the trend definition on every timeframe,
    read from the catalogue by name — whatever the feature set holds."""
    trend = {timeframe: xy["catalogue_values"][config.feature_id(config.TREND_GATE_FEATURE_DEFINITION, timeframe)]
             for timeframe in xy["timeframes"]}
    return {"xy": xy, "close_1m": close_1m, "trend": trend, "oos_predictions": oos_predictions}


def load_simulation_inputs(ticker: str) -> dict:
    xy = dataset.load_xy(ticker)
    return build_simulation_inputs(xy, load_close_1m(ticker), load_oos_predictions(ticker, xy["catalogue"]))


def signals_for_fold(simulation_inputs: dict, fold_id: int) -> dict:
    """Signal arrays for one fold, aligned to the label-event grid."""
    xy = simulation_inputs["xy"]
    oos_predictions = simulation_inputs["oos_predictions"]
    in_fold = oos_predictions["oos_fold_id"] == fold_id
    ts = oos_predictions["decision_ts"][in_fold].astype(np.int64)
    pos = np.searchsorted(xy["decision_ts"], ts)
    p_short, p_long = oos_predictions["p_short"][in_fold], oos_predictions["p_long"][in_fold]
    p_neutral = oos_predictions["p_neutral"][in_fold]
    directional_probability_edge = p_long - p_short
    side = np.sign(directional_probability_edge)
    agreeing_trend_timeframe_count = sum(
        (np.sign(simulation_inputs["trend"][timeframe][pos]) == side).astype(np.int64)
        for timeframe in xy["timeframes"])
    gate_open = (
        (np.maximum(p_long, p_short) > p_neutral)
        & (side != 0)
        & (side == np.sign(simulation_inputs["trend"][config.trend_gate_timeframe(xy["catalogue"])][pos]))
        & (agreeing_trend_timeframe_count >= config.MINIMUM_AGREEING_TREND_TIMEFRAMES)
    )
    return {
        "directional_probability_edge": directional_probability_edge,
        "side": side, "gate_open": gate_open,
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
    """Take-profit at the barrier; a stop at the worse of the barrier and the touching minute's open; a vertical exit at the last event minute's close."""
    if event_resolution == config.EVENT_RESOLUTION_VERTICAL:
        return exit_reference_price                      # mark: last event minute's close
    if event_resolution == side:
        return upper_barrier if side > 0 else lower_barrier   # target reached
    return (min(lower_barrier, exit_reference_price) if side > 0
            else max(upper_barrier, exit_reference_price))


def backtest(simulation_inputs: dict, signals: dict, entry_edge_threshold: float,
             fold_start_ms: int, fold_end_ms: int) -> dict:
    """Single-position state machine producing one continuous equity path."""
    cat = simulation_inputs["xy"]["catalogue"]
    decision_bar_minutes = config.timeframe_entry(cat, cat["decision_timeframe"])["duration_ms"] // config.MILLISECONDS_PER_MINUTE
    bar_close_offset_minutes = decision_bar_minutes - 1   # a decision bar closes on the last minute of its block
    c = config.EXECUTION_COST_RATE_PER_TRADE_SIDE
    fold_start_minute = (fold_start_ms - config.RESEARCH_START_MS) // config.MILLISECONDS_PER_MINUTE
    fold_minute_count = (fold_end_ms - fold_start_ms) // config.MILLISECONDS_PER_MINUTE
    close_1m = simulation_inputs["close_1m"]
    equity_1m = np.empty(fold_minute_count)

    enter = (signals["gate_open"] & signals["entry_observable"]
             & (np.abs(signals["directional_probability_edge"]) >= entry_edge_threshold))
    # eligibility must be decidable at t_0, so the maximum horizon is tested, not the real event_end_ts
    fits = ((signals["entry_ts"] >= fold_start_ms)
            & (signals["entry_ts"] + config.LABEL_HORIZON_MS <= fold_end_ms))
    take = np.flatnonzero(enter & fits)

    equity, cursor, in_pos_ms = 1.0, 0, 0
    trades = []
    # the exit counts are counts by event_resolution, so they carry its names
    exits = {name: 0 for name in config.EVENT_RESOLUTION_NAMES.values()}
    for k in take:
        i = int((signals["entry_ts"][k] - config.RESEARCH_START_MS)
                // config.MILLISECONDS_PER_MINUTE) - fold_start_minute
        j = int((signals["event_end_ts"][k] - config.RESEARCH_START_MS)
                // config.MILLISECONDS_PER_MINUTE) - fold_start_minute - 1
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
        exits[config.EVENT_RESOLUTION_NAMES[resolution]] += 1
    equity_1m[cursor:] = equity

    trade_returns = np.asarray(trades)
    # the same path sampled at bar closes, starting from the capital itself:
    # without E0 the first 15 minutes of the fold produce no return at all
    equity_15m = np.concatenate(([1.0], equity_1m[bar_close_offset_minutes::decision_bar_minutes]))
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


def pnl_block(result: dict) -> dict:
    """Everything but the 1m path, which is an intermediate, not a report."""
    return {k: v for k, v in result.items() if k != "equity_1m"}


def equity_curve(equity_1m: np.ndarray) -> dict:
    idx = np.arange(0, equity_1m.size, EQUITY_CURVE_SAMPLE_INTERVAL_MINUTES)
    return {"equity": np.round(equity_1m[idx], 6).tolist()}


def entry_edge_threshold_selection(simulation_inputs: dict) -> dict:
    """The entry edge threshold chosen on the validation folds — the grid point maximising the mean fold Sharpe
    among those clearing the trade floor, ties to the smaller threshold, the grid floor when none clears it — with
    the fold results at that point. The one selection the stage and the feature-set search both run."""
    validation_rows = {fold_id: signals_for_fold(simulation_inputs, fold_id)
                       for fold_id in config.VALIDATION_FOLD_IDS}
    validation_bounds = {fold_id: validation.fold_bounds(fold_id)
                         for fold_id in config.VALIDATION_FOLD_IDS}

    # the locals carry the names of the keys they end up as
    entry_edge_threshold, selection_score_mean_sharpe = None, -np.inf
    validation_by_fold, entry_edge_threshold_constraint_met = None, False
    results_at_grid_floor = None                     # kept for the fallback below
    for threshold in config.ENTRY_EDGE_THRESHOLD_GRID:
        results_by_fold = {fold_id: backtest(simulation_inputs, validation_rows[fold_id], threshold,
                                             *validation_bounds[fold_id])
                           for fold_id in config.VALIDATION_FOLD_IDS}
        if threshold == config.ENTRY_EDGE_THRESHOLD_GRID[0]:
            results_at_grid_floor = results_by_fold
        if any(r["trade_count"] < config.MINIMUM_TRADES_PER_VALIDATION_FOLD
               for r in results_by_fold.values()):
            continue
        entry_edge_threshold_constraint_met = True
        score = float(np.mean([r["sharpe"] for r in results_by_fold.values()]))
        if score > selection_score_mean_sharpe:      # strict: ties keep the smaller threshold
            entry_edge_threshold, selection_score_mean_sharpe = threshold, score
            validation_by_fold = results_by_fold
    if not entry_edge_threshold_constraint_met:      # deterministic fallback, reported as such
        entry_edge_threshold = config.ENTRY_EDGE_THRESHOLD_GRID[0]
        validation_by_fold = results_at_grid_floor
        selection_score_mean_sharpe = float(
            np.mean([r["sharpe"] for r in validation_by_fold.values()]))
    return {
        "entry_edge_threshold": entry_edge_threshold,
        "entry_edge_threshold_constraint_met": entry_edge_threshold_constraint_met,
        "selection_score_mean_sharpe": selection_score_mean_sharpe,
        "validation_by_fold": validation_by_fold,
    }


def main() -> int:
    args = config.build_ticker_parser(
        "entry edge threshold on the validation folds, final-holdout PnL"
    ).parse_args()

    for ticker in config.parse_tickers(args.tickers):
        simulation_inputs = load_simulation_inputs(ticker)
        selection = entry_edge_threshold_selection(simulation_inputs)
        entry_edge_threshold = selection["entry_edge_threshold"]

        holdout_start, holdout_end = validation.fold_bounds(config.FINAL_HOLDOUT_FOLD_ID)
        final_holdout = backtest(simulation_inputs, signals_for_fold(simulation_inputs, config.FINAL_HOLDOUT_FOLD_ID),
                                 entry_edge_threshold, holdout_start, holdout_end)

        payload = {
            "entry_edge_threshold": entry_edge_threshold,
            "entry_edge_threshold_constraint_met": selection["entry_edge_threshold_constraint_met"],
            "selection_score_mean_sharpe": selection["selection_score_mean_sharpe"],
            "execution_cost_rate_per_trade_side": config.EXECUTION_COST_RATE_PER_TRADE_SIDE,
            "validation": {f"fold_{fold_id}": pnl_block(r)
                           for fold_id, r in selection["validation_by_fold"].items()},
            "final_holdout": {**pnl_block(final_holdout),
                              "equity_curve": equity_curve(final_holdout["equity_1m"])},
        }
        out = config.strategy_evaluation_json(ticker)
        dataset.write_json(out, payload)
        print(f"{ticker} {out.name}: threshold={entry_edge_threshold} sharpe {final_holdout['sharpe']:.3f} "
              f"trades {final_holdout['trade_count']} maxDD {final_holdout['max_drawdown']:.3f} "
              f"final equity {final_holdout['final_equity']:.3f}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
