# ML_README — Research layer on the canonical 1m series

Per asset, independently: a fixed 16-column hierarchical feature matrix, a
triple-barrier label resolved on the 1-minute path, a purged walk-forward
protocol with Optuna hyper-parameter search, a locked out-of-sample test read
exactly once, and a top-down gated strategy evaluation. Every run is a pure
function of `(data_sha256, config_sha256, seed)`.

## 1. Methodology

The label is a **decision indication**, not a price forecast: the triple
barrier [4] asks "which barrier does the market touch first from here —
profit, stop, or neither within the horizon?", which is exactly the question a
rule-based exit answers in trading. Tree ensembles are the strongest
general-purpose learner for tabular financial features [3][10]; short-horizon
crypto predictability from technical features is documented in [1][2]. The
whole protocol is built against backtest overfitting [9]: parameters frozen
before the first run, selection statistics separated from the final report,
one locked test read.

## 2. Time semantics

```
… ─┤ 12:45 ── 15M bar ── 13:00 ├─ 13:00 ── 15M bar ── 13:15 ├─ …
                                ▲ decision_ts = 13:00
features: bars with close_ts <= 13:00  (15M 12:45–13:00, 1H 12:00–13:00, 4H 08:00–12:00)
entry:    canonical 1m open at 13:00 (equals the 15M bar open)
label:    canonical 1m path over (13:00 .. 17:00] — first barrier touch wins
```

Higher-level features come from the last **closed** bar of their level
(`asof_index`: `searchsorted` on close times, causality asserted in code, not
assumed). Bars are exact UTC-aligned aggregations of the canonical 1m series
(O first, H max, L min, C last, V sum; `arg_min`/`arg_max` by timestamp for
determinism). **Native-bar equivalence (one-off verification):** aggregating
raw Binance 1m to 1h for 2021-02 (672 bars, BTCUSDT) against native fapi 1h
klines gives **0 OHLC mismatches** and a maximum relative volume difference of
**7.1e-16** (float64 epsilon).

## 3. Features — fixed contract, 16 columns

| Family | Definition on the level's own bars | Range | Ref. |
|---|---|---|---|
| `trend` | `(EMA20 − EMA50) / ATR14` | unbounded, dimensionless | [1][3] |
| `momentum` | `(RSI14 − 50) / 50` | [−1, 1] | [1][7] |
| `volatility` | `ATR14 / close` | > 0, dimensionless | [1][5] |
| `structure` | `(close − min(low,20)) / (max(high,20) − min(low,20))` | [0, 1] | [2] |
| `activity` | z-score of `log1p(volume)` over 50 bars | dimensionless | [1][6] |
| `alignment` | `sign(trend_15m) + sign(trend_1h) + sign(trend_4h)` | {−3 … +3} | [8] |

Columns: the five families on 15m / 1h / 4h plus `alignment` — 16 total,
identical for every asset, **no per-asset selection** (a deliberate
overfitting control; nested per-asset selection is a WO-ML-002 candidate).
Five families per level exceeds the four-per-level multi-timeframe guideline
by one: `activity` is volume information, not a fifth price-derived
indicator. `rel_divergence` is a data-quality signal, never a feature.
Warm-up: 200 top-level bars (`WARMUP_4H_BARS`) — decision rows before
`2021-02-03 08:00 UTC` are excluded everywhere. Recursions (EMA, Wilder) run
as explicit loops; rolling statistics use `sliding_window_view`; no NaN
survives the warm-up (asserted).

## 4. Labels

Triple barrier [4] on every 15m boundary after the warm-up: entry
`P0 = canonical 1m open(decision_ts)`; horizontal barriers
`P0 ± 2.0 × ATR14(last closed 1h bar)`; vertical barrier 240 minutes.
Resolution walks the **1-minute path**: first minute whose high touches the
upper barrier → `y = +1`; whose low touches the lower → `y = −1`; neither →
`y = 0`. A minute touching both barriers before any other hit makes the order
unknowable from OHLC — the row is **masked** (`exit_reason = 9`), never
relabelled `0`. A forward-filled minute anywhere in the horizon also masks the
row; rows whose vertical barrier crosses the research end are dropped.
Sample weight = **average uniqueness** [4, ch. 4]: the mean over the event's
minutes of `1 / (concurrently open events)`, exact via prefix sums; used as
the XGBoost sample weight with no additional class re-weighting.

## 5. Split — WARMUP | TRAIN | PURGE + GAP | OOS | locked TEST

```
2021-01-01     warmup_end     2022-01-01     2023-01-01     2024-01-01     2025-01-01          2026-08-26
|-- WARMUP --|----- F1 -----|----- F2 -----|----- F3 -----|----- F4 -----|-------- F5 ---------|
                                                                            (locked TEST, read once)
Split 2: TRAIN = F1            | PURGE+GAP | OOS = F2
Split 3: TRAIN = F1–F2         | PURGE+GAP | OOS = F3
Split 4: TRAIN = F1–F3         | PURGE+GAP | OOS = F4
Test   : TRAIN = F1–F4         | PURGE+GAP | TEST = F5   (frozen params, frozen tau)
Deploy : TRAIN = F1–F5         | —         | —           (no unbiased estimate; labelled as such)
```

**Purge** removes training events whose real `event_end_ts` reaches the
pre-test cutoff (`oos_start − 16 × 15m`); the extra 16 bars are a conservative
gap. Classical post-test embargo [4, ch. 7] is not required in forward
chaining because no training observation lies after the OOS block. Each
segment builder asserts its own contract (`train.decision_ts.max() <
oos_start`, `train.event_end_ts.max() < cutoff`, warm-up excluded).

## 6. Hyper-parameter search

Optuna TPE (`seed = 42`), 50 sequential trials, in-memory study. Objective =
mean **uniqueness-weighted** multiclass log-loss over the three OOS validation
splits. Space: `max_depth` 2–6, `eta` log 0.01–0.3, `min_child_weight` 1–50,
`subsample` 0.5–1, `colsample_bytree` 0.5–1, `lambda` log 0.1–10, `alpha` log
0.01–1, `num_boost_round` 100–800 step 50. Fixed: `multi:softprob`,
`num_class = 3`, `tree_method = hist`, `nthread = 1`, no early stopping.
Label parameters, costs and the tau grid are **never** in the space. The full
trial history is stored in `hpo_<T>.json`.

## 7. Locked test vs deployment model

With frozen parameters the expanding splits are refitted and their
out-of-fold probabilities stored (`predictions_<T>.parquet`) — the only input
the strategy layer may use for threshold selection. The locked test fold is
then evaluated **once** (fit on F1–F4, predict F5) and its classification
numbers frozen in `metrics_<T>.json`; that model is not persisted — the
numbers are. Only afterwards `--finalize` fits F1–F5 and persists
`model_<T>.json` with `role = deployment, unbiased_estimate = false`.

## 8. Strategy

```
edge = p_long − p_short;  side = sign(edge)
enter = mask_ok ∧ |edge| ≥ τ ∧ max(p_long, p_short) > p_neutral
        ∧ side = sign(trend_4h) ∧ |alignment| ≥ 2 ∧ sign(alignment) = side
```

The **model decides the side; the 4H hierarchy gates it**. One unit position
at a time, new signals ignored while in a position. Exits replay the label
event: the same barriers on the same 1m path (barrier price for horizontal
exits, the 15m close of the final horizon bar for vertical exits — equal to
the 1m values by construction). Costs `0.0006` per side on entry and exit.
τ is chosen on the OOF predictions of the validation splits only (max mean
net Sharpe, ≥ 30 trades per split, ties → smaller τ; a deterministic
`τ = 0` fallback is reported when no τ meets the constraint). The locked test
PnL — net Sharpe (annualised × √35040), max drawdown, trades, hit rate,
exposure, turnover, exit-reason distribution, gate share — is computed once.
"Neutral is a valid state, not a defect."

## 9. Artifacts and determinism

Per asset in `assets/Asset_<T>/` (gitignored, reconstructable):
`X_<T>.parquet`, `Y_<T>.parquet`, `hpo_<T>.json`, `predictions_<T>.parquet`,
`metrics_<T>.json`, `strategy_<T>.json`, `model_<T>.json`. Every JSON carries
the envelope `{data_sha256, config_sha256, seed, versions}` — canonical JSON
(sorted keys, numpy→python scalars), written atomically, with **no wall-clock
time, hostname or absolute path**. `data_sha256` = SHA-256 over the canonical
rows of the frozen research window (symbols in basket order, rows ascending,
little-endian int64/float64 bytes). Determinism is proven, not assumed: two
full runs must produce identical SHA-256 for X/Y/hpo/predictions/metrics/
strategy artifacts (`nthread = 1`, parallelism across assets only, pinned
`requirements.lock`).

Module layout: `ml/config` (frozen constants) · `ml/artifacts` (canonical
serialization) · `ml/indicators`, `ml/validation`, `ml/model` (pure numpy /
xgboost kernels) · `ml/dataset` (artifact loading) · `ml/bars` (single DB
writer) · `ml/features`, `ml/labels`, `ml/hpo`, `ml/train`, `ml/strategy`,
`ml/status` (CLI stages, `python -m ml.<stage> [--tickers …]`).

## 10. Limitations (v1 of the ML layer)

No regime-conditional gating, no per-asset feature selection, no CUSUM event
sampling, no meta-labeling, no fractional differentiation, fixed costs, unit
position sizing. The class distribution is dominated by `y = 0` (the k = 2
barrier is rarely hit within one 4H block) — reported per asset, not
resampled. Candidates for WO-ML-002 are listed in the work order.

## 11. References (verified online 2026-08-26; DOIs resolve)

| Key | Reference |
|---|---|
| [1] | Jaquart, P., Dann, D., Weinhardt, C. (2021). Short-term bitcoin market prediction via machine learning. *The Journal of Finance and Data Science*, 7, 45–66. doi:10.1016/j.jfds.2021.03.001 |
| [2] | Sebastião, H., Godinho, P. (2021). Forecasting and trading cryptocurrencies with machine learning under changing market conditions. *Financial Innovation*, 7, 3. doi:10.1186/s40854-020-00217-x |
| [3] | Gu, S., Kelly, B., Xiu, D. (2020). Empirical asset pricing via machine learning. *The Review of Financial Studies*, 33(5), 2223–2273. doi:10.1093/rfs/hhaa009 |
| [4] | López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley — ch. 3 (triple barrier), ch. 4 (uniqueness), ch. 7 (purged CV, embargo) |
| [5] | Parkinson, M. (1980); Garman, M., Klass, M. (1980). *Journal of Business*, 53(1) — range-based volatility |
| [6] | Amihud, Y. (2002). Illiquidity and stock returns: cross-section and time-series effects. *Journal of Financial Markets*, 5(1), 31–56 |
| [7] | Wilder, J. W. (1978). *New Concepts in Technical Trading Systems* — RSI, ATR |
| [8] | Elder, A. (1993). *Trading for a Living* — triple-screen multi-timeframe hierarchy; Grimes, A. (2012). *The Art and Science of Technical Analysis* |
| [9] | Bailey, D., Borwein, J., López de Prado, M., Zhu, Q. (2014). Pseudo-mathematics and financial charlatanism: the effects of backtest overfitting on out-of-sample performance. *Notices of the AMS*, 61(5), 458–471. doi:10.1090/noti1105 |
| [10] | Chen, T., Guestrin, C. (2016). XGBoost: a scalable tree boosting system. *KDD 2016* |
| [11] | Makarov, I., Schoar, A. (2020). Trading and arbitrage in cryptocurrency markets. *Journal of Financial Economics*, 135(2), 293–319 — why `rel_divergence` stays a data-quality signal |
