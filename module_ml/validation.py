"""The fold contract — the geometry of time `module_ml/skills/methodology_ml.md` draws — and the metrics. Pure numpy;
a population and its average-uniqueness weights are returned together, so a population is never used with somebody
else's weights."""

import numpy as np

from . import config


def fold_bounds(fold_id: int) -> tuple[int, int]:
    """The bounds of fold Fk, from the 1-based fold table — its OOS block is the whole fold."""
    return config.FOLD_BOUNDS_MS[fold_id - 1], config.FOLD_BOUNDS_MS[fold_id]


def fold_minutes(fold_id: int) -> int:
    """How long fold Fk lasts, in minutes — 2024 is a leap year, so F4 is longer than F2 and F3 and no
    fold is idealised to a round year."""
    fold_start_ms, fold_end_ms = fold_bounds(fold_id)
    return (fold_end_ms - fold_start_ms) // config.MILLISECONDS_PER_MINUTE


def average_uniqueness_weight(entry_ts: np.ndarray, event_end_ts: np.ndarray) -> np.ndarray:
    """Average uniqueness [Lopez de Prado, ch. 4] over exactly the events given: the mean over an event's minutes of
    1 / (events of this population open at that minute), exact via prefix sums."""
    research_minute_count = (config.RESEARCH_END_MS - config.RESEARCH_START_MS) // config.MILLISECONDS_PER_MINUTE
    start = ((entry_ts - config.RESEARCH_START_MS) // config.MILLISECONDS_PER_MINUTE).astype(np.int64)
    end = ((event_end_ts - config.RESEARCH_START_MS) // config.MILLISECONDS_PER_MINUTE).astype(np.int64)
    delta = np.zeros(research_minute_count + 1, dtype=np.int64)
    np.add.at(delta, start, 1)
    np.add.at(delta, end, -1)
    concurrent = np.cumsum(delta[:-1])
    inverse = np.zeros(research_minute_count + 1)
    covered = concurrent > 0
    inverse[1:][covered] = 1.0 / concurrent[covered]
    cumulative = np.cumsum(inverse)
    return (cumulative[end] - cumulative[start]) / (end - start)


def training_set(entry_ts: np.ndarray, event_end_ts: np.ndarray,
                 sample_valid: np.ndarray, fold_start_ms: int) -> tuple[np.ndarray, np.ndarray]:
    """Purged training rows — event_end_ts <= fold_start_ms is exactly no overlap, the end being exclusive — and
    their weights, measured after the purge."""
    keep = sample_valid & (event_end_ts <= fold_start_ms)
    idx = np.flatnonzero(keep)
    return idx, average_uniqueness_weight(entry_ts[idx], event_end_ts[idx])


def scoring_set(decision_ts: np.ndarray, entry_ts: np.ndarray, event_end_ts: np.ndarray,
                sample_valid: np.ndarray, fold_start_ms: int, fold_end_ms: int,
                maximum_label_horizon_minutes: int) -> tuple[np.ndarray, np.ndarray]:
    """Supervised rows of the OOS block that leave room for the maximum label horizon before its end — decidable at
    t_0 — and their weights, with concurrency counted among the scored events alone. The horizon is the
    experiment's, not the search state's, so two search states of one experiment score one population whatever label
    horizon each holds."""
    keep = (sample_valid & (decision_ts >= fold_start_ms)
            & (entry_ts + maximum_label_horizon_minutes * config.MILLISECONDS_PER_MINUTE <= fold_end_ms))
    idx = np.flatnonzero(keep)
    return idx, average_uniqueness_weight(entry_ts[idx], event_end_ts[idx])


def oos_block_rows(decision_ts: np.ndarray, fold_start_ms: int, fold_end_ms: int) -> np.ndarray:
    """Every decision row of the OOS block: label validity never decides which rows receive predictions."""
    return np.flatnonzero((decision_ts >= fold_start_ms) & (decision_ts < fold_end_ms))


# ---- metrics (weighted where it matters) ----------------------------------

def multiclass_logloss(y_cls: np.ndarray, proba: np.ndarray, weight: np.ndarray) -> float:
    p = np.clip(proba[np.arange(y_cls.size), y_cls], 1e-15, 1.0)
    return float(-(weight * np.log(p)).sum() / weight.sum())


def weighted_class_prior(y_cls: np.ndarray, weight: np.ndarray) -> np.ndarray:
    """Weight-normalised class frequencies — the baseline a model must beat."""
    prior = np.array([weight[y_cls == c].sum() for c in range(3)], dtype=np.float64)
    return prior / prior.sum()


def prior_logloss(prior: np.ndarray, y_cls: np.ndarray, weight: np.ndarray) -> float:
    """Log-loss of predicting the training prior everywhere, weighted by the same function."""
    return multiclass_logloss(y_cls, np.broadcast_to(prior, (y_cls.size, 3)), weight)


def sharpe_annualised(bar_returns: np.ndarray, decision_bars_per_year: float) -> float | None:
    """The mean decision-bar return over its standard deviation, annualised; None where the returns never varied —
    a fold that took no trade — the ratio having no denominator, as calmar() and profit_factor() are None."""
    sd = bar_returns.std(ddof=1)
    if sd == 0.0:
        return None
    return float(bar_returns.mean() / sd * np.sqrt(decision_bars_per_year))


def cagr(final_equity: float, minute_count: int) -> float:
    """Compound annual growth rate of an equity path that started at E0 = 1, over its own length in
    minutes — a calendar year of 365 days, the 24/7 convention the annualised Sharpe already uses."""
    return float(final_equity ** (config.MINUTES_PER_YEAR / minute_count) - 1.0)


def calmar(cagr_annual_rate: float, max_drawdown_fraction: float) -> float | None:
    """CAGR per unit of maximum drawdown; None where the path never drew down, the ratio having no denominator — as
    profit_factor() is None where nothing lost. It is reported and never selected on."""
    if max_drawdown_fraction == 0.0:
        return None
    return float(cagr_annual_rate / max_drawdown_fraction)


def profit_factor(trade_returns: np.ndarray) -> float | None:
    """Gross profit over gross loss of a population of trades; None where nothing lost, the ratio having
    no denominator — as hit_rate is None where nothing traded."""
    gross_loss = -trade_returns[trade_returns < 0.0].sum()
    if gross_loss == 0.0:
        return None
    return float(trade_returns[trade_returns > 0.0].sum() / gross_loss)


def max_drawdown(equity: np.ndarray) -> float:
    """Largest peak-to-trough fraction of an equity path that starts at E0 = 1, the starting capital included."""
    full = np.concatenate(([1.0], equity))
    peak = np.maximum.accumulate(full)
    return float(np.max((peak - full) / peak))
