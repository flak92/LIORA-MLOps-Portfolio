"""Pure assembly of the dashboard snapshot payload — no IO, no argparse.

Turns the three per-asset artifacts into the ml_status.json v2 contract. The
blocks follow the experiment flow (sample -> segments -> search -> validation
-> locked test -> attribution -> strategy); the file itself is written with
sorted keys, so reading order lives in the dashboard and in ML_README, never
in key names.

SCHEMA_VERSION, LN3 and EQUITY_STRIDE are implementation constants and stay
local: ml/config.py collects every UPPERCASE name into config_sha256, so
adding them there would invalidate the envelope of every existing artifact.
"""

from __future__ import annotations

import json

from . import config

SCHEMA_VERSION = 2
LN3 = 1.0986122886681098   # uniform 3-class baseline log-loss
EQUITY_STRIDE = 7          # daily equity grid -> weekly points for the sparkline


def _r(x, n):
    """round() that tolerates the nulls canon() produces for non-finite floats."""
    return None if x is None else round(x, n)


def experiment_config() -> dict:
    """The frozen constants the dashboard needs to describe itself."""
    return {
        "seed": config.SEED,
        "feature_columns": list(config.FEATURE_COLUMNS),
        "fold_bounds_utc": list(config.FOLD_BOUNDS_UTC),
        "validation_splits": list(config.VALIDATION_SPLITS),
        "test_split": config.TEST_SPLIT,
        "n_trials": config.N_TRIALS,
        "min_trades_per_split": config.MIN_TRADES_PER_SPLIT,
        "costs_per_side": config.COST_PER_SIDE,
        "k_barrier": config.K_BARRIER,
        "horizon_bars": config.HORIZON_BARS,
        "warmup_4h_bars": config.WARMUP_4H_BARS,
        "agree_min": config.AGREE_MIN,
        "pretest_gap_bars": config.PRETEST_GAP_BARS,
    }


def envelope(docs: list[dict]) -> dict:
    """One (data_sha256, config_sha256, versions) across every artifact."""
    pairs = {
        (d["data_sha256"], d["config_sha256"], json.dumps(d["versions"], sort_keys=True))
        for d in docs
    }
    assert len(pairs) == 1, f"inconsistent artifact envelopes: {len(pairs)} distinct"
    data_sha, config_sha, versions = next(iter(pairs))
    return {
        "data_sha256": data_sha,
        "config_sha256": config_sha,
        "versions": json.loads(versions),
    }


def sample_block(metrics: dict) -> dict:
    mask = metrics["mask"]
    return {
        "rows": mask["rows"],
        "masked": mask["masked"],
        "ambiguous": mask["ambiguous"],
        "masked_pct": round(100.0 * mask["masked"] / mask["rows"], 4),
        "n_warmup_excluded": metrics["segments"]["n_warmup_excluded"],
        "uniqueness_weight_mean": round(metrics["uniqueness_weight_mean"], 4),
        "class_counts": dict(metrics["class_counts"]),
    }


def hpo_block(hpo: dict) -> dict:
    """Objective trajectory in TPE order plus the winning point."""
    trials = sorted(hpo["trials"], key=lambda t: t["number"])
    assert all(t["value"] is not None for t in trials), "an HPO trial has no objective value"
    assert len(trials) == hpo["n_trials"], "trial count does not match n_trials"
    values = [round(t["value"], 6) for t in trials]
    best = min(range(len(values)), key=lambda i: values[i])
    return {
        "n_trials": hpo["n_trials"],
        "best_trial": trials[best]["number"],
        "best_logloss": round(hpo["best_value"], 6),
        "best_params": dict(sorted(hpo["best_params"].items())),
        "trial_values": values,
    }


def classification_block(metrics: dict) -> tuple[dict, dict]:
    """(validation per split, locked test) — confusion rows are true classes."""
    validation = {
        k: {
            "logloss": round(v["logloss_weighted"], 6),
            "balanced_accuracy": round(v["balanced_accuracy"], 4),
            "mcc": round(v["mcc"], 4),
            "n": v["n"],
        }
        for k, v in sorted(metrics["validation"].items())
    }
    t = metrics["test_locked"]
    confusion = t["confusion"]
    assert sum(sum(row) for row in confusion) == t["n"], "confusion does not sum to scored rows"
    test = {
        "n": t["n"],
        "logloss": round(t["logloss_weighted"], 6),
        "balanced_accuracy": round(t["balanced_accuracy"], 4),
        "mcc": round(t["mcc"], 4),
        "confusion": confusion,
    }
    return validation, test


def thin_curve(curve: dict, stride: int = EQUITY_STRIDE) -> dict:
    """Drop the timestamp array: the grid is regular, so origin + step rebuild it.

    The last grid point rarely coincides with the end of the curve, so the true
    final equity travels as a scalar instead of an off-grid point.
    """
    ts, equity = curve["timestamp_ms"], curve["equity"]
    steps = {ts[i + 1] - ts[i] for i in range(len(ts) - 1)}
    assert len(steps) == 1, f"irregular equity grid: {sorted(steps)[:3]}"
    return {
        "t0_ms": ts[0],
        "step_ms": steps.pop() * stride,
        "stride": stride,
        "n_source": len(equity),
        "equity": [round(v, 4) for v in equity[::stride]],
        "equity_final": round(equity[-1], 4),
    }


def _pnl(block: dict) -> dict:
    return {
        "sharpe": _r(block["sharpe"], 3),
        "max_drawdown": _r(block["max_drawdown"], 4),
        "n_trades": block["n_trades"],
        "hit_rate": _r(block["hit_rate"], 4),
        "avg_trade_ret": _r(block["avg_trade_ret"], 6),
        "exposure": _r(block["exposure"], 4),
        "turnover": _r(block["turnover"], 6),
        "gate_share": _r(block["gate_share"], 4),
        "exit_counts": dict(block["exit_counts"]),
    }


def strategy_block(strategy: dict) -> dict:
    test = strategy["test_locked"]
    return {
        "tau": strategy["tau"],
        "tau_constraint_met": strategy["tau_constraint_met"],
        "selection_score_mean_sharpe": _r(strategy["selection_score_mean_sharpe"], 3),
        "costs_per_side": strategy["costs_per_side"],
        "validation": {k: _pnl(v) for k, v in sorted(strategy["validation"].items())},
        "test": _pnl(test),
        "equity_curve": thin_curve(test["equity_curve"]),
    }


def warnings_block(test: dict, strategy: dict) -> dict:
    """Protocol conditions only — never an unfavourable result."""
    return {
        "test_logloss_above_uniform": test["logloss"] >= LN3,
        "too_few_trades": strategy["test"]["n_trades"] < config.MIN_TRADES_PER_SPLIT,
        "tau_fallback": not strategy["tau_constraint_met"],
    }


def asset_report(ticker: str, hpo: dict, metrics: dict, strategy: dict,
                 artifact_sha256: dict) -> dict:
    validation, test = classification_block(metrics)
    strat = strategy_block(strategy)
    gain = {k: round(v, 1) for k, v in sorted(metrics["gain_importance"].items())}
    assert len(gain) == len(config.FEATURE_COLUMNS), "gain importance misses the feature contract"
    segments = {k: v for k, v in sorted(metrics["segments"].items()) if k.startswith("split_")}
    expected = {f"split_{s}" for s in (*config.VALIDATION_SPLITS, config.TEST_SPLIT)}
    assert set(segments) == expected, f"segments {sorted(segments)} != {sorted(expected)}"
    return {
        "ticker": ticker,
        "sample": sample_block(metrics),
        "segments": segments,
        "hpo": hpo_block(hpo),
        "validation": validation,
        "test": test,
        "gain_importance": gain,
        "strategy": strat,
        "warnings": warnings_block(test, strat),
        "artifact_sha256": artifact_sha256,
    }


def payload(assets: list[dict], env: dict) -> dict:
    """Everything except generated_at_utc, which only the CLI may stamp."""
    return {
        "schema_version": SCHEMA_VERSION,
        "research_window": [config.RESEARCH_START_UTC, config.RESEARCH_END_UTC],
        "baseline_logloss_uniform": round(LN3, 6),
        "config": experiment_config(),
        **env,
        "assets": assets,
    }
