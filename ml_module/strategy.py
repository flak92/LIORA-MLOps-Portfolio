"""Top-down gated strategy on the canonical research path.

    edge = p_long - p_short;  side = sign(edge)
    n_agree = #{level in {15m, 1h, 4h} : sign(trend_level) == side}
    enter = |edge| >= tau  AND  max(p_long, p_short) > p_neutral
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

tau is chosen on the validation folds only: the tau maximising the mean fold
Sharpe among those giving at least TAU_MIN_TRADES trades in every fold, ties
resolved towards the smaller tau.
"""

from __future__ import annotations

import duckdb
import numpy as np

from . import config, dataset, validation

MINUTE_MS = 60_000
EQUITY_SAMPLE_MIN = 1440    # one equity point per day for the dashboard curve
BAR_CLOSE_MIN = 14          # a 15m bar closes on the 15th minute of its block


def load_inputs(ticker: str) -> dict:
    adir = config.ASSETS_DIR / f"Asset_{ticker}"
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
        f"SELECT * FROM read_parquet('{adir}/predictions_{ticker}.parquet') ORDER BY split, decision_ts"
    ).fetchnumpy()
    c2.close()

    trend = {tf: xy["x"][:, config.FEATURE_COLUMNS.index(f"trend_{tf}")] for tf in config.LEVELS}
    return {"xy": xy, "close1m": close1m, "trend": trend, "preds": preds}


def rows_for_split(d: dict, split: int) -> dict:
    """Signal arrays for one split, aligned to the Y grid."""
    xy = d["xy"]
    m = d["preds"]["split"] == split
    ts = d["preds"]["decision_ts"][m].astype(np.int64)
    pos = np.searchsorted(xy["decision_ts"], ts)
    assert np.array_equal(xy["decision_ts"][pos], ts)
    p_short, p_long = d["preds"]["p_short"][m], d["preds"]["p_long"][m]
    p_neutral = d["preds"]["p_neutral"][m]
    edge = p_long - p_short
    side = np.sign(edge)
    n_agree = sum((np.sign(d["trend"][tf][pos]) == side).astype(np.int64) for tf in config.LEVELS)
    gate = (
        (np.maximum(p_long, p_short) > p_neutral)
        & (side != 0)
        & (side == np.sign(d["trend"]["4h"][pos]))
        & (n_agree >= config.AGREE_MIN)
    )
    return {
        "edge": edge, "side": side, "gate": gate,
        "entry_observable": xy["entry_observable"][pos],
        "entry_ts": xy["entry_ts"][pos], "event_end_ts": xy["event_end_ts"][pos],
        "reason": xy["exit_reason"][pos], "p0": xy["p0"][pos],
        "upper": xy["upper"][pos], "lower": xy["lower"][pos], "exit_ref": xy["exit_ref"][pos],
    }


def fill_price(side: float, reason: int, upper: float, lower: float, exit_ref: float) -> float:
    """Take-profit at the barrier; stop (and the adverse side of an ambiguous
    minute) at the worse of the barrier and that minute's open."""
    if reason == 0:
        return exit_ref                                  # vertical: last event minute's close
    if reason == side:
        return upper if side > 0 else lower              # target reached
    return min(lower, exit_ref) if side > 0 else max(upper, exit_ref)


EXIT_NAME = {0: "vertical", 9: "adverse"}


def backtest(d: dict, rows: dict, tau: float, fold_start_ms: int, fold_end_ms: int) -> dict:
    """Single-position state machine producing one continuous equity path."""
    c = config.COST_PER_SIDE
    off = (fold_start_ms - config.RESEARCH_START_MS) // MINUTE_MS
    n_min = (fold_end_ms - fold_start_ms) // MINUTE_MS
    close1m = d["close1m"]
    eq = np.empty(n_min)

    enter = rows["gate"] & (np.abs(rows["edge"]) >= tau) & rows["entry_observable"]
    # A trade must be able to finish inside the fold, and that has to be decidable
    # at t_0: testing the REAL event_end_ts would let the future decide whether the
    # position was opened at all — a signal that happened to hit a barrier early
    # would fit where one that ran to the vertical barrier would not. The maximum
    # horizon is the only version of the question the entry moment can answer.
    fits = (rows["entry_ts"] >= fold_start_ms) & (rows["entry_ts"] + config.HORIZON_MS <= fold_end_ms)
    take = np.flatnonzero(enter & fits)

    equity, cursor, in_pos_ms = 1.0, 0, 0
    trades = []
    exits = {"upper": 0, "lower": 0, "vertical": 0, "adverse": 0}
    for k in take:
        i = int((rows["entry_ts"][k] - config.RESEARCH_START_MS) // MINUTE_MS) - off
        j = int((rows["event_end_ts"][k] - config.RESEARCH_START_MS) // MINUTE_MS) - off - 1
        if i < cursor:
            continue                                     # position still open
        s = float(rows["side"][k])
        p0 = float(rows["p0"][k])
        reason = int(rows["reason"][k])
        px = fill_price(s, reason, float(rows["upper"][k]), float(rows["lower"][k]),
                        float(rows["exit_ref"][k]))
        eq[cursor:i] = equity                            # flat while out of the market
        eq[i:j] = equity * (1.0 - c + s * (close1m[off + i:off + j] / p0 - 1.0))
        r = s * (px / p0 - 1.0) - c - c * (px / p0)
        equity *= 1.0 + r
        eq[j] = equity
        cursor = j + 1
        in_pos_ms += int(rows["event_end_ts"][k] - rows["entry_ts"][k])
        trades.append(r)
        exits[EXIT_NAME.get(reason, "upper" if reason == 1 else "lower")] += 1
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
    args = config.ticker_parser("tau selection on validation folds, final-OOS PnL").parse_args()

    for t in config.parse_tickers(args.tickers):
        d = load_inputs(t)
        val_rows = {s: rows_for_split(d, s) for s in config.VALIDATION_SPLITS}
        val_bounds = {s: validation.split_bounds(s) for s in config.VALIDATION_SPLITS}

        best_tau, best_score, best_detail, constraint_met = None, -np.inf, None, False
        for tau in config.TAU_GRID:
            res = {s: backtest(d, val_rows[s], tau, *val_bounds[s]) for s in config.VALIDATION_SPLITS}
            if any(r["n_trades"] < config.TAU_MIN_TRADES for r in res.values()):
                continue
            constraint_met = True
            score = float(np.mean([r["sharpe"] for r in res.values()]))
            if score > best_score:                       # strict: ties keep the smaller tau
                best_tau, best_score, best_detail = tau, score, res
        if not constraint_met:                           # deterministic fallback, reported as such
            best_tau = 0.0
            best_detail = {s: backtest(d, val_rows[s], best_tau, *val_bounds[s])
                           for s in config.VALIDATION_SPLITS}
            best_score = float(np.mean([r["sharpe"] for r in best_detail.values()]))

        test_start, test_end = validation.split_bounds(config.TEST_SPLIT)
        test = backtest(d, rows_for_split(d, config.TEST_SPLIT), best_tau, test_start, test_end)

        payload = {
            "tau": best_tau,
            "tau_constraint_met": constraint_met,
            "selection_score_mean_sharpe": best_score,
            "costs_per_side": config.COST_PER_SIDE,
            "validation": {f"split_{s}": public(r) for s, r in best_detail.items()},
            "test": {**public(test), "equity_curve": equity_curve(test["equity_1m"], test_start)},
        }
        out = config.ASSETS_DIR / f"Asset_{t}" / f"strategy_{t}.json"
        dataset.write_json(out, payload)
        print(f"{out.name}: tau={best_tau} sharpe {test['sharpe']:.3f} "
              f"trades {test['n_trades']} maxDD {test['max_drawdown']:.3f} "
              f"final equity {test['final_equity']:.3f}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
