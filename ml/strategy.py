"""Top-down gated strategy: the model decides the side, the hierarchy gates it.

enter = mask_ok  AND  |p_long - p_short| >= tau  AND  max(p_long, p_short) > p_neutral
        AND side == sign(trend_4h)
        AND n_agree >= 2,  where n_agree counts levels with sign(trend) == side

Entries additionally require the label to be valid (mask_ok).

One unit position at a time; new signals are ignored while a position is open.
Exits replay the label event: the same +-K*ATR14(1h) barriers on the same 1m
path (barrier price for horizontal exits, the 15m close of the final horizon
bar for vertical exits — identical values by construction, no 1m reads here).
Costs are charged per side on entry and exit. tau is chosen on the OOF
predictions of the validation splits only (max mean net Sharpe with a minimum
trade count per split, ties -> smaller tau); the locked test fold is evaluated
once with the frozen tau.
"""

from __future__ import annotations

import argparse

import duckdb
import numpy as np

from . import artifacts, config, dataset, indicators, validation

EQUITY_EVERY = 96   # one equity point per day of 15m bars


def load_inputs(ticker: str) -> dict:
    adir = config.ASSETS_DIR / f"Asset_{ticker}"
    sym = config.symbol(ticker)
    xy = dataset.load_xy(ticker)
    con = duckdb.connect(str(config.DB_PATH), read_only=True)
    bars15 = con.execute(
        f"""SELECT timestamp_ms, open, close FROM ohlcv_15m_canonical
            WHERE symbol = '{sym}' ORDER BY timestamp_ms"""
    ).fetchnumpy()
    bars1h = con.execute(
        f"""SELECT timestamp_ms, high, low, close FROM ohlcv_1h_canonical
            WHERE symbol = '{sym}' ORDER BY timestamp_ms"""
    ).fetchnumpy()
    con.close()
    c2 = duckdb.connect()
    preds = c2.execute(
        f"SELECT * FROM read_parquet('{adir}/predictions_{ticker}.parquet') ORDER BY split, decision_ts"
    ).fetchnumpy()
    c2.close()

    ts15 = bars15["timestamp_ms"].astype(np.int64)
    bar_of = np.searchsorted(ts15, xy["decision_ts"])
    assert np.array_equal(ts15[bar_of], xy["decision_ts"])
    atr_1h = indicators.atr(bars1h["high"], bars1h["low"], bars1h["close"], config.ATR_N)
    sigma = atr_1h[indicators.asof_index(xy["decision_ts"],
                                         bars1h["timestamp_ms"].astype(np.int64),
                                         config.TF_MS["1h"])]
    exit_bar = np.searchsorted(ts15, xy["event_end_ts"] - 60_000, side="right") - 1

    trend = {
        tf: xy["x"][:, config.FEATURE_COLUMNS.index(f"trend_{tf}")] for tf in config.LEVELS
    }
    return {
        "xy": xy, "ts15": ts15, "open15": bars15["open"], "close15": bars15["close"],
        "bar_of": bar_of, "exit_bar": exit_bar, "sigma": sigma,
        "trend": trend, "preds": preds, "x_ts": xy["decision_ts"],
    }


def rows_for_split(d: dict, split: int) -> dict:
    """Decision-row arrays for one split, aligned to the Y grid."""
    m = d["preds"]["split"] == split
    ts = d["preds"]["decision_ts"][m].astype(np.int64)
    pos = np.searchsorted(d["x_ts"], ts)
    assert np.array_equal(d["x_ts"][pos], ts)
    p_short = d["preds"]["p_short"][m]
    p_long = d["preds"]["p_long"][m]
    p_neutral = d["preds"]["p_neutral"][m]
    edge = p_long - p_short
    side = np.sign(edge)
    n_agree = sum(
        (np.sign(d["trend"][tf][pos]) == side).astype(np.int64) for tf in config.LEVELS
    )
    gate = (
        d["xy"]["mask_ok"][pos]
        & (np.maximum(p_long, p_short) > p_neutral)
        & (side != 0)
        & (side == np.sign(d["trend"]["4h"][pos]))
        & (n_agree >= config.AGREE_MIN)
    )
    return {
        "idx": pos, "edge": edge, "side": side, "gate": gate,
        "bar": d["bar_of"][pos], "exit_bar": d["exit_bar"][pos],
        "p0": d["open15"][d["bar_of"][pos]],
        "sigma": d["sigma"][pos],
        "reason": d["xy"]["exit_reason"][pos],
    }


def backtest(d: dict, rows: dict, tau: float) -> dict:
    """One pass of the single-position state machine over a split."""
    enter = rows["gate"] & (np.abs(rows["edge"]) >= tau)
    bar_lo, bar_hi = int(rows["bar"].min()), int(rows["exit_bar"].max()) + 1
    close15 = d["close15"]
    r = np.zeros(bar_hi - bar_lo)
    trades, busy, in_pos_bars = [], -1, 0
    exit_counts = {"upper": 0, "lower": 0, "vertical": 0}
    for k in range(rows["bar"].size):
        i = int(rows["bar"][k])
        if i <= busy or not enter[k]:
            continue
        s = float(rows["side"][k])
        p0 = float(rows["p0"][k])
        reason = int(rows["reason"][k])
        j = int(rows["exit_bar"][k])
        if reason == 1:
            px, key = p0 + config.K_BARRIER * float(rows["sigma"][k]), "upper"
        elif reason == -1:
            px, key = p0 - config.K_BARRIER * float(rows["sigma"][k]), "lower"
        else:
            px, key = float(close15[j]), "vertical"
        exit_counts[key] += 1
        if j == i:
            r[i - bar_lo] += s * (px / p0 - 1.0) - 2 * config.COST_PER_SIDE
        else:
            r[i - bar_lo] += s * (close15[i] / p0 - 1.0) - config.COST_PER_SIDE
            seg = s * (close15[i + 1:j] / close15[i:j - 1] - 1.0)
            r[i + 1 - bar_lo:j - bar_lo] += seg
            r[j - bar_lo] += s * (px / close15[j - 1] - 1.0) - config.COST_PER_SIDE
        trades.append(s * (px / p0 - 1.0) - 2 * config.COST_PER_SIDE)
        in_pos_bars += j - i + 1
        busy = j
    tr = np.asarray(trades)
    equity = np.cumprod(1.0 + r)
    return {
        "bar_returns": r, "equity": equity,
        "sharpe": validation.sharpe_annualised(r),
        "max_drawdown": validation.max_drawdown(equity),
        "n_trades": int(tr.size),
        "hit_rate": float((tr > 0).mean()) if tr.size else 0.0,
        "avg_trade_ret": float(tr.mean()) if tr.size else 0.0,
        "exposure": in_pos_bars / r.size,
        "turnover": 2.0 * tr.size / r.size,
        "exit_counts": exit_counts,
        "gate_share": float(rows["gate"].mean()),
        "bar_lo": bar_lo,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="tau selection on OOF splits, locked-test PnL")
    ap.add_argument("--tickers", default=",".join(config.TICKERS), help="comma-separated subset")
    args = ap.parse_args()

    con = duckdb.connect(str(config.DB_PATH), read_only=True)
    data_sha, config_sha = dataset.run_ids(con)
    con.close()

    for t in [x.strip().upper() for x in args.tickers.split(",") if x.strip()]:
        d = load_inputs(t)
        val_rows = {s: rows_for_split(d, s) for s in config.VALIDATION_SPLITS}

        best_tau, best_score, best_detail, constraint_met = None, -np.inf, None, False
        for tau in config.TAU_GRID:
            results = {s: backtest(d, val_rows[s], tau) for s in config.VALIDATION_SPLITS}
            if any(res["n_trades"] < config.MIN_TRADES_PER_SPLIT for res in results.values()):
                continue
            constraint_met = True
            score = float(np.mean([res["sharpe"] for res in results.values()]))
            if score > best_score:
                best_tau, best_score, best_detail = tau, score, results
        if not constraint_met:   # deterministic fallback, reported as such
            best_tau = 0.0
            best_detail = {s: backtest(d, val_rows[s], best_tau) for s in config.VALIDATION_SPLITS}
            best_score = float(np.mean([res["sharpe"] for res in best_detail.values()]))

        test_rows = rows_for_split(d, config.TEST_SPLIT)
        test = backtest(d, test_rows, best_tau)
        ts15 = d["ts15"]
        curve_idx = np.arange(0, test["equity"].size, EQUITY_EVERY)
        payload = artifacts.envelope(data_sha, config_sha, config.SEED, dataset.versions())
        payload.update(
            {
                "tau": best_tau,
                "tau_constraint_met": constraint_met,
                "selection_score_mean_sharpe": best_score,
                "validation": {
                    f"split_{s}": {k: v for k, v in res.items()
                                   if k not in ("bar_returns", "equity", "bar_lo")}
                    for s, res in best_detail.items()
                },
                "test_locked": {
                    **{k: v for k, v in test.items()
                       if k not in ("bar_returns", "equity", "bar_lo")},
                    "equity_curve": {
                        "timestamp_ms": ts15[test["bar_lo"] + curve_idx].tolist(),
                        "equity": np.round(test["equity"][curve_idx], 6).tolist(),
                    },
                },
                "costs_per_side": config.COST_PER_SIDE,
            }
        )
        out = config.ASSETS_DIR / f"Asset_{t}" / f"strategy_{t}.json"
        artifacts.write_json(out, payload)
        print(f"{out.name}: tau={best_tau} test sharpe {test['sharpe']:.3f} "
              f"trades {test['n_trades']} maxDD {test['max_drawdown']:.3f}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
