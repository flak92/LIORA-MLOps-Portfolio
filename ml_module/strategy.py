"""Top-down gated strategy on the canonical research path.

    directional_probability_edge = p_long - p_short;  side = sign(edge)
    n_agree = #{level in {15m, 1h, 4h} : sign(trend_level) == side}
    enter = |edge| >= entry_edge_threshold  AND  max(p_long, p_short) > p_neutral
            AND side == sign(trend_4h)  AND  n_agree >= 2

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
MIN_TRADES_PER_VALIDATION_FOLD trades in every fold, ties resolved towards the
smaller threshold.
"""

from __future__ import annotations

import duckdb
import numpy as np

from . import config, dataset, validation

MINUTE_MS = 60_000
EQUITY_SAMPLE_MIN = 1440    # one equity point per day for the dashboard curve
BAR_CLOSE_MIN = 14          # a 15m bar closes on the 15th minute of its block


def load_inputs(ticker: str) -> dict:
    adir = config.artifact_dir(ticker)
    sym = config.symbol(ticker)
    xy = dataset.load_xy(ticker)
    con = duckdb.connect(str(config.DB_PATH), read_only=True)
    close1m = con.execute(
        f"""SELECT close FROM ohlcv_1m_canonical
            WHERE symbol = '{sym}'
              AND timestamp_ms >= {config.RESEARCH_START_MS}
              AND timestamp_ms < {config.RESEARCH_END_MS}
            ORDER BY timestamp_ms"""
    ).fetchnumpy()["close"]
    con.close()
    c2 = duckdb.connect()
    preds = c2.execute(
        f"SELECT * FROM read_parquet('{adir}/oos_predictions.parquet') ORDER BY oos_fold_id, decision_ts"
    ).fetchnumpy()
    c2.close()

    trend = {tf: xy["x"][:, config.FEATURE_COLUMNS.index(f"{config.TREND_FAMILY}_{tf}")] for tf in config.LEVELS}
    return {"xy": xy, "close1m": close1m, "trend": trend, "preds": preds}


def rows_for_fold(d: dict, fold_id: int) -> dict:
    """Signal arrays for one fold, aligned to the label-event grid."""
    xy = d["xy"]
    m = d["preds"]["oos_fold_id"] == fold_id
    ts = d["preds"]["decision_ts"][m].astype(np.int64)
    pos = np.searchsorted(xy["decision_ts"], ts)
    assert np.array_equal(xy["decision_ts"][pos], ts)
    p_short, p_long = d["preds"]["p_short"][m], d["preds"]["p_long"][m]
    p_neutral = d["preds"]["p_neutral"][m]
    directional_probability_edge = p_long - p_short
    side = np.sign(directional_probability_edge)
    n_agree = sum((np.sign(d["trend"][tf][pos]) == side).astype(np.int64) for tf in config.LEVELS)
    gate = (
        (np.maximum(p_long, p_short) > p_neutral)
        & (side != 0)
        & (side == np.sign(d["trend"]["4h"][pos]))
        & (n_agree >= config.AGREE_MIN)
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
    minute) at the worse of the barrier and that minute's open."""
    if event_resolution == config.EVENT_RESOLUTION_VERTICAL:
        return exit_reference_price                      # mark: last event minute's close
    if event_resolution == side:
        return upper_barrier if side > 0 else lower_barrier   # target reached
    return (min(lower_barrier, exit_reference_price) if side > 0
            else max(upper_barrier, exit_reference_price))


def backtest(d: dict, rows: dict, threshold: float, fold_start_ms: int, fold_end_ms: int) -> dict:
    """Single-position state machine producing one continuous equity path."""
    c = config.COST_PER_SIDE
    off = (fold_start_ms - config.RESEARCH_START_MS) // MINUTE_MS
    n_min = (fold_end_ms - fold_start_ms) // MINUTE_MS
    close1m = d["close1m"]
    eq = np.empty(n_min)

    enter = (rows["gate"] & rows["entry_observable"]
             & (np.abs(rows["directional_probability_edge"]) >= threshold))
    # A trade must be able to finish inside the fold, and that has to be decidable
    # at t_0: testing the REAL event_end_ts would let the future decide whether the
    # position was opened at all — a signal that happened to hit a barrier early
    # would fit where one that ran to the vertical barrier would not. The maximum
    # horizon is the only version of the question the entry moment can answer.
    fits = ((rows["entry_ts"] >= fold_start_ms)
            & (rows["entry_ts"] + config.HORIZON_MS <= fold_end_ms))
    take = np.flatnonzero(enter & fits)

    equity, cursor, in_pos_ms = 1.0, 0, 0
    trades = []
    # the exit counts are counts by event_resolution, so they carry its names
    exits = {name: 0 for name in config.EVENT_RESOLUTION_NAME.values()}
    for k in take:
        i = int((rows["entry_ts"][k] - config.RESEARCH_START_MS) // MINUTE_MS) - off
        j = int((rows["event_end_ts"][k] - config.RESEARCH_START_MS) // MINUTE_MS) - off - 1
        if i < cursor:
            continue                                     # position still open
        s = float(rows["side"][k])
        entry_price = float(rows["entry_price"][k])
        resolution = int(rows["event_resolution"][k])
        px = fill_price(s, resolution, float(rows["upper_barrier"][k]),
                        float(rows["lower_barrier"][k]),
                        float(rows["exit_reference_price"][k]))
        eq[cursor:i] = equity                            # flat while out of the market
        eq[i:j] = equity * (1.0 - c + s * (close1m[off + i:off + j] / entry_price - 1.0))
        r = s * (px / entry_price - 1.0) - c - c * (px / entry_price)
        equity *= 1.0 + r
        eq[j] = equity
        cursor = j + 1
        in_pos_ms += int(rows["event_end_ts"][k] - rows["entry_ts"][k])
        trades.append(r)
        exits[config.EVENT_RESOLUTION_NAME[resolution]] += 1
    eq[cursor:] = equity

    tr = np.asarray(trades)
    # the same path sampled at bar closes, starting from the capital itself:
    # without E0 the first 15 minutes of the fold produce no return at all
    eq15 = np.concatenate(([1.0], eq[BAR_CLOSE_MIN::15]))
    ret15 = np.diff(eq15) / eq15[:-1]
    return {
        "equity_1m": eq,
        "sharpe": validation.sharpe_annualised(ret15),
        "max_drawdown": validation.max_drawdown(eq),     # 1m path: intra-bar drawdown is real
        "n_trades": int(tr.size),
        "hit_rate": float((tr > 0).mean()) if tr.size else 0.0,
        "avg_trade_ret": float(tr.mean()) if tr.size else None,
        "exposure": in_pos_ms / (fold_end_ms - fold_start_ms),
        "exit_counts": exits,
        "final_equity": float(equity),
    }


def public(result: dict) -> dict:
    """Everything but the 1m path, which is an intermediate, not a report."""
    return {k: v for k, v in result.items() if k != "equity_1m"}


def equity_curve(eq: np.ndarray, fold_start_ms: int) -> dict:
    idx = np.arange(0, eq.size, EQUITY_SAMPLE_MIN)
    return {
        "timestamp_ms": (fold_start_ms + idx * MINUTE_MS).tolist(),
        "equity": np.round(eq[idx], 6).tolist(),
    }


def main() -> int:
    args = config.ticker_parser(
        "entry edge threshold on the validation folds, final-holdout PnL"
    ).parse_args()

    for t in config.parse_tickers(args.tickers):
        d = load_inputs(t)
        val_rows = {s: rows_for_fold(d, s) for s in config.VALIDATION_FOLD_IDS}
        val_bounds = {s: validation.fold_bounds(s)
                      for s in config.VALIDATION_FOLD_IDS}

        best_threshold, best_score, best_detail, constraint_met = None, -np.inf, None, False
        for threshold in config.ENTRY_EDGE_THRESHOLD_GRID:
            res = {s: backtest(d, val_rows[s], threshold, *val_bounds[s])
                   for s in config.VALIDATION_FOLD_IDS}
            if any(r["n_trades"] < config.MIN_TRADES_PER_VALIDATION_FOLD for r in res.values()):
                continue
            constraint_met = True
            score = float(np.mean([r["sharpe"] for r in res.values()]))
            if score > best_score:                       # strict: ties keep the smaller threshold
                best_threshold, best_score, best_detail = threshold, score, res
        if not constraint_met:                           # deterministic fallback, reported as such
            best_threshold = 0.0
            best_detail = {s: backtest(d, val_rows[s], best_threshold, *val_bounds[s])
                           for s in config.VALIDATION_FOLD_IDS}
            best_score = float(np.mean([r["sharpe"] for r in best_detail.values()]))

        holdout_start, holdout_end = validation.fold_bounds(config.FINAL_HOLDOUT_FOLD_ID)
        final_holdout = backtest(d, rows_for_fold(d, config.FINAL_HOLDOUT_FOLD_ID),
                                 best_threshold, holdout_start, holdout_end)

        payload = {
            "entry_edge_threshold": best_threshold,
            "entry_edge_threshold_constraint_met": constraint_met,
            "selection_score_mean_sharpe": best_score,
            "cost_per_side": config.COST_PER_SIDE,
            "validation": {f"fold_{s}": public(r) for s, r in best_detail.items()},
            "final_holdout": {**public(final_holdout),
                              "equity_curve": equity_curve(final_holdout["equity_1m"],
                                                          holdout_start)},
        }
        out = config.artifact_dir(t) / "strategy_evaluation.json"
        dataset.write_json(out, payload)
        print(f"{t} {out.name}: threshold={best_threshold} sharpe {final_holdout['sharpe']:.3f} "
              f"trades {final_holdout['n_trades']} maxDD {final_holdout['max_drawdown']:.3f} "
              f"final equity {final_holdout['final_equity']:.3f}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
