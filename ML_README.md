# ML_README — Research layer on the 1-minute series

Per asset, independently: a fixed 15-column hierarchical feature matrix from
the canonical series, a triple-barrier label resolved on the executable
Binance 1-minute path, a purged walk-forward protocol with Optuna
hyper-parameter search, a historical final out-of-sample fold, and a top-down
gated strategy evaluation. The experiment is described by its research window
and seed; the git commit records which code produced a result.

## 1. The nine rules the code implements

1. `X` is a function of **closed** historical OHLCV only.
2. The decision is taken at a 15m bar close; **execution happens one minute later**.
3. `Y` comes from the **executable Binance USD-M path** only.
4. `Y` is a first-touch triple barrier on the 1m path; **ambiguity is not a class**.
5. Overlapping labels carry **average-uniqueness** weights.
6. A training event may **not cross the start of its OOS block**.
7. HPO and `τ` see **F2–F4 only**.
8. **F5 changes no decision** — not a feature, not a hyper-parameter, not `τ`, not a rule.
9. PnL is a **linear USDT-perpetual PnL for a fixed quantity**, with an explicit
   cost and without funding.

Everything below is these nine rules written out.

Why this shape: the label is a **decision indication**, not a price forecast —
the triple barrier [4] asks "which barrier does the market touch first from
here: profit, stop, or neither within the horizon?", which is exactly the
question a rule-based exit answers. Tree ensembles are the strongest
general-purpose learner for tabular financial features [3][10], short-horizon
crypto predictability from technical features is documented in [1][2], and the
top-down multi-timeframe gate follows the classic triple-screen hierarchy
[11]. The protocol as a whole is built against backtest overfitting [9]:
parameters frozen before the first run, selection statistics separated from
the final report, one read of the final fold.

## 2. Two series, two roles

```
BINANCE 1m ──┐
             ├── canonical OHLCV ──► 15m / 1h / 4h bars ──► X   (market observation)
BYBIT 1m ────┘

BINANCE 1m ──────────────────────────► triple barrier ─────► Y   (execution)
                                                              │
X + Y ──► purged walk-forward ──► XGBoost ────────────────────┘
                                      │
                              class probabilities
                                      │
                             fixed strategy rules
                                      │
                             Binance execution path
                                      │
                                 equity / PnL ──► dashboard
```

**Observation** may use the failover series: a continuous market picture is
what indicators need, and the canonical bar is always some venue's real
candle. **Execution may not.** A label and the PnL that replays it must
describe one instrument — a position cannot hop to another exchange because
the canonical source switched for a minute — so the barrier walk, the fills
and the equity path read `ohlcv_1m_binance` and nothing else. The `activity`
feature therefore follows the canonical source across a failover (Bybit
supplies 0.004–0.043 % of minutes); the traded path never does.

## 3. Time semantics

```
… ─┤ 12:45 ── 15M bar ── 13:00 ├─ 13:00 ── 15M bar ── 13:15 ├─ …
                                ▲ t_d = decision_ts = 13:00
features: bars with close_ts <= 13:00  (15M 12:45–13:00, 1H 12:00–13:00, 4H 08:00–12:00)
entry:    t_0 = entry_ts = 13:01, at the Binance 1m OPEN of that minute
event:    [t_0, t_v) = [13:01, 17:01)  — the barrier examines minutes 13:01 … 17:00
```

`t_0 = t_d + 1 min` is the **one-minute decision-to-entry latency assumption**:
a signal computed at the close of a bar cannot be filled at that same close.
`event_end_ts` is the **exclusive** end of the event, which is what makes the
purge rule exactly `event_end_ts <= oos_start` — an event ending at the first
minute of the OOS block does not overlap it.

Higher-level features come from the last **closed** bar of their level
(`asof_index`: `searchsorted` on close times, causality asserted in code, not
assumed). Bars are exact UTC-aligned aggregations of the canonical 1m series
(O first, H max, L min, C last, V sum; `arg_min` / `arg_max` by timestamp for
determinism). **Native-bar equivalence (one-off verification):** aggregating
raw Binance 1m to 1h for 2021-02 (672 bars, BTCUSDT) against native fapi 1h
klines gives **0 OHLC mismatches** and a maximum relative volume difference of
**7.1e-16** (float64 epsilon).

## 4. Features — fixed contract, 15 columns

| Family | Definition on the level's own bars | Range | Ref. |
|---|---|---|---|
| `trend` | `(EMA20 − EMA50) / ATR14` | unbounded, dimensionless | [1][3] |
| `momentum` | `(RSI14 − 50) / 50` | [−1, 1] | [1][7] |
| `volatility` | `ATR14 / close` | > 0, dimensionless | [1][5] |
| `structure` | `(close − min(low,20)) / (max(high,20) − min(low,20))` | [0, 1] | [2] |
| `activity` | z-score of `log1p(volume)` over 50 bars | dimensionless | [1][6] |

Five families on 15m / 1h / 4h — **15 columns**, identical for every asset,
**no per-asset selection** (a deliberate overfitting control). Cross-level
trend agreement is **not** a feature: `sign(trend_15m) + sign(trend_1h) +
sign(trend_4h)` is a deterministic function of three columns the model already
has, so it can only add representation, never information; the 2-of-3
agreement lives where it is actually used, in the strategy gate. Five families
per level exceeds the four-per-level multi-timeframe guideline by one:
`activity` is volume information, not a fifth price-derived indicator.
`rel_divergence` is a data-quality signal, never a feature [12]. Warm-up: 200
top-level bars (`WARMUP_4H_BARS`) — decision rows before `2021-02-03 08:00
UTC` are excluded everywhere. Recursions (EMA, Wilder) run as explicit loops;
rolling statistics use `sliding_window_view`; no NaN survives the warm-up
(asserted).

## 5. Labels

Triple barrier [4] on every 15m boundary after the warm-up. Entry
`P0 = Binance 1m open(t_0)`; horizontal barriers `P0 ± 2.0 × ATR14` of the
last closed **Binance** 1h bar; vertical barrier 240 minutes. Resolution walks
the Binance 1m path: the first minute whose high touches the upper barrier
gives `y = +1`, whose low touches the lower gives `y = −1`, neither gives
`y = 0` with the exit at the close of the last event minute.

**A touch requires a trade.** A zero-volume minute is a carried-forward price,
not an execution, so both hit conditions are gated on `volume > 0`:

```
upper_hit = (volume > 0) & (high >= upper)
lower_hit = (volume > 0) & (low  <= lower)
```

An entry minute with `volume = 0` has no executable entry, and a minute
touching **both** barriers leaves their order unknowable from OHLC — both are
`label_valid = false`, never relabelled `0`. Ambiguity is a missing
observation, not a third outcome.

**`label_valid` is not a trading eligibility flag:**

```
label_valid  governs ONLY : training · HPO scoring · classification metrics
label_valid  NEVER        : blocks an entry in the backtest
```

Validity is knowable only after the event resolves, so using it as an entry
condition would be look-ahead. A signal whose event later turns out ambiguous
**is a trade**, settled at the barrier adverse to the position.

Sample weight = **average uniqueness** [4, ch. 4]: the mean over the event's
minutes of `1 / (concurrently open events)`, exact via prefix sums, computed
over the **valid** events only so a masked row cannot dilute the weights of
the rows actually trained on. It is the XGBoost sample weight, with no
additional class re-weighting. Rows whose vertical barrier would cross the
research end are dropped.

`Y_<T>.parquet` also carries the prices the backtest needs — `p0`, `upper`,
`lower`, `exit_ref` — so the strategy replays exactly the event that produced
the label instead of recomputing it.

## 6. Split — WARMUP | TRAIN | PURGE | OOS | final OOS

```
2021-01-01     warmup_end     2022-01-01     2023-01-01     2024-01-01     2025-01-01          2026-08-26
|-- WARMUP --|----- F1 -----|----- F2 -----|----- F3 -----|----- F4 -----|-------- F5 ---------|
                                                                          (final OOS, read once)
Split 2: TRAIN = F1            | PURGE | OOS = F2
Split 3: TRAIN = F1–F2         | PURGE | OOS = F3
Split 4: TRAIN = F1–F3         | PURGE | OOS = F4
Test   : TRAIN = F1–F4         | PURGE | F5   (frozen params, frozen tau)
```

**Purge** keeps a training row only if `event_end_ts <= oos_start`. Because
`event_end_ts` is exclusive, that inequality *is* "no overlap" — no artificial
gap is added, since a gap wider than the event horizon removes information
without removing leakage. A classical post-test embargo [4, ch. 7] is not
required in forward chaining: no training observation lies after the OOS
block. Each segment builder asserts its own contract.

**F5 is a historical final OOS period, evaluated once.** The invariant is a
sentence, not a guard: *F5 never selects a feature, a hyper-parameter, `τ` or
a strategy rule.* A deterministic recomputation of the same numbers is not a
second look.

## 7. Hyper-parameter search

Optuna TPE (`seed = 42`), 50 sequential trials, in-memory study. Objective =
mean **uniqueness-weighted** multiclass log-loss over the three OOS validation
splits F2–F4. Space: `max_depth` 2–6, `eta` log 0.01–0.3, `min_child_weight`
1–50, `subsample` 0.5–1, `colsample_bytree` 0.5–1, `lambda` log 0.1–10,
`alpha` log 0.01–1, `num_boost_round` 100–800 step 50. Fixed:
`multi:softprob`, `num_class = 3`, `tree_method = hist`, `nthread = 1`, no
early stopping. Label parameters, costs and the `τ` grid are **never** in the
space. `hpo_<T>.json` keeps the winner and the trial count; the trajectory of
50 trials is a search diary, not a result.

## 8. Classification metric — skill against the training prior

With `y = 0` dominant, a uniform `ln 3` baseline flatters any model that
merely learns the class frequencies. The baseline is therefore the
**uniqueness-weighted class prior of the split's own training rows**,
`p_c = Σ wᵢ·1(yᵢ = c) / Σ wᵢ`, and the reported numbers are

```
prior_logloss · model_logloss · skill = 1 − model_logloss / prior_logloss · MCC
```

`skill` answers one question — does the model add information beyond knowing
how often each class occurs? — and is **a result, not a gate**. MCC [8] adds
the confusion-structure view in one number; balanced accuracy answers the same
question and is not reported. Metrics score the label-valid subset of a fold;
predictions cover the full fold.

## 9. Strategy

```
edge = p_long − p_short;  side = sign(edge)
n_agree = #{level ∈ {15m, 1h, 4h} : sign(trend_level) = side}
enter = |edge| ≥ τ ∧ max(p_long, p_short) > p_neutral
        ∧ side = sign(trend_4h) ∧ n_agree ≥ 2
```

The **model decides the side; the 4H hierarchy gates it**. One unit position
at a time, new signals ignored while in a position, and a trade must finish
inside its fold.

**PnL — one formula.** The position is a USDT perpetual held at a fixed
quantity `Q = s · E₀ / P₀` (notional 1× current equity), so PnL is linear in
price, with the cost `c = 0.0006` charged on entry notional and on exit
notional:

```
R      = s·(P_x/P₀ − 1) − c − c·(P_x/P₀)
E_next = E₀·(1 + R)
E_t    = E₀·(1 − c + s·(P_t/P₀ − 1))      mark-to-market while open
```

A short from 100 to 80 returns exactly +20 %, and the path 100 → 50 → 100
returns 0 %. Compounding per-bar returns instead — `Π(1 + s·r_t)` — returns
−100 % on that path; that is the arithmetic this formula replaces.

**Fills acknowledge that 1m OHLC hides the tick path.** A take-profit fills at
the barrier. A stop fills at the *worse* of the barrier and the open of the
minute that touched it (`long: min(lower, open)`, `short: max(upper, open)`),
which is also how the adverse side of an ambiguous minute is settled. Without
that rule a bar-based backtest silently assumes every gap fills at the barrier.

**`τ` is chosen on F2–F4 only**, by an explicit rule:

```
τ* = argmax_τ  mean( Sharpe_F2(τ), Sharpe_F3(τ), Sharpe_F4(τ) )
     subject to  trades_f(τ) ≥ TAU_MIN_TRADES = 30  for every f ∈ {F2, F3, F4}
     ties → the smaller τ
```

The trade floor is a **selection guardrail, not an acceptance gate**: without
it a `τ` producing three or five trades with an accidentally high Sharpe wins
over a strategy that actually trades. If no `τ` on the 0.00–0.60 grid meets
it, the run falls back to `τ = 0` and reports `tau_constraint_met = false`.

**Sharpe and drawdown come from one equity process sampled two ways.** The
backtest writes a continuous 1-minute equity path; the Sharpe is annualised
(`×√(96·365)`) from that path sampled at **15m bar closes**, the maximum
drawdown is measured on the **1m** path — a 15-minute sampling would report a
1.00 → 0.91 → 0.99 excursion as −1 % instead of −9 %. `exposure` is
`Σ(exit − entry) / fold length`. The reported result is
**execution-cost-adjusted PnL, excluding funding**.

## 10. Artifacts and modules

Per asset in `assets/Asset_<T>/` (gitignored, reconstructable):
`X_<T>.parquet`, `Y_<T>.parquet`, `hpo_<T>.json`, `predictions_<T>.parquet`,
`metrics_<T>.json`, `strategy_<T>.json`. Every JSON is canonical (sorted keys,
numpy scalars converted, written atomically) and carries **only what it
computed** — no provenance envelope, no hashes, no manifests. The experiment
is identified once, globally, in `dashboard/ml_status.json`: research window
and seed. Library versions live in `requirements.lock`, model parameters in
`hpo_<T>.json`. Runs are reproducible by construction — fixed seed,
`nthread = 1`, pinned versions — and that claim is not backed by a hash gate,
because such a gate proves the metadata, not the mathematics. No booster is
persisted: nothing in this repo performs inference, so the numbers are the
product.

Module layout: `ml/config` (frozen constants) · `ml/indicators`,
`ml/validation`, `ml/model` (pure numpy / xgboost kernels) · `ml/dataset`
(artifact IO: X/Y loading, the one parquet writer, canonical JSON) ·
`ml/bars` (single DB writer) · `ml/features`,
`ml/labels`, `ml/hpo`, `ml/train`, `ml/strategy`, `ml/status` (CLI stages,
`python -m ml.<stage> [--tickers …]`). Constant convention:
**experiment-semantic constants live in `ml/config.py`; implementation
constants** (chunk sizes, `MINUTE_MS`, equity-curve stride) **may stay local
to their module**. The export invariants of `pipeline/export.py` are the
canonical-series gate; the documented order runs `make ml-all` after
`make export`.

## 11. Running the layer: one asset per process

Every stage takes `--tickers`, so the chain parallelises the only way an
experiment with frozen thread caps may — **externally**, one asset per
process. `make ml-features / ml-labels / ml-hpo / ml-train / ml-strategy` fan
out `JOBS` assets at a time, where `JOBS = min(cores, available GiB)` is
measured at each invocation rather than written down (the machine this runs on
changes size); override with `make ml-hpo JOBS=2`. `ml-bars` stays sequential
because it is the only writer to the database.

Thread caps stay at one — `nthread = 1`, `OMP_NUM_THREADS = 1` — and are not
negotiable: multi-threaded float summation reorders, two runs of the same
experiment produce different models, and out-of-sample results stop being
comparable. Measured on 4 cores: the four per-asset stages take 1 min 29 s
instead of 4 min 13 s (2.8x) and every artifact is bit-identical either way.
The search itself is 88 % of the chain and is CPU-bound; one asset's Optuna
study is sequential by construction, so the wall-clock floor of `ml-hpo` is
the slowest single asset, not the total divided by the core count.

Rerun only what a change actually invalidates — the search is the expensive
stage, and most edits do not touch it:

| what changed | what to rerun |
|---|---|
| the canonical series (`make ingest`) | everything, from `ml-bars` |
| a feature definition | `ml-features ml-hpo ml-train ml-strategy ml-status` |
| a label or barrier parameter | `ml-labels ml-hpo ml-train ml-strategy ml-status` |
| the search space or the seed | `ml-hpo ml-train ml-strategy ml-status` |
| a strategy rule, the cost, the tau grid | `ml-strategy ml-status` |
| the dashboard payload | `ml-status` |

## 12. What this is, and what it is not

This is a **causally correct, internally consistent 1-minute bar-based
perpetual-futures research backtest with explicit execution-cost
assumptions**. It is not a realistic simulation of trading: 1m OHLCV contains
no order book, no latency distribution, no partial fills, no spread, no queue
position and no funding payments. Every one of those would move the result,
and none of them is guessed at here.

Known limitations of this version: no regime-conditional gating, no per-asset
feature selection, no CUSUM event sampling, no meta-labeling, no fractional
differentiation, fixed costs, unit position sizing. The class distribution is
dominated by `y = 0` (the `k = 2` barrier is rarely touched within one 4H
block) — reported per asset, not resampled.

## 13. References (verified online 2026-08-26; DOIs resolve)

| Key | Reference |
|---|---|
| [1] | Jaquart, P., Dann, D., Weinhardt, C. (2021). Short-term bitcoin market prediction via machine learning. *The Journal of Finance and Data Science*, 7, 45–66. doi:10.1016/j.jfds.2021.03.001 |
| [2] | Sebastião, H., Godinho, P. (2021). Forecasting and trading cryptocurrencies with machine learning under changing market conditions. *Financial Innovation*, 7, 3. doi:10.1186/s40854-020-00217-x |
| [3] | Gu, S., Kelly, B., Xiu, D. (2020). Empirical asset pricing via machine learning. *The Review of Financial Studies*, 33(5), 2223–2273. doi:10.1093/rfs/hhaa009 |
| [4] | López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley — ch. 3 (triple barrier), ch. 4 (uniqueness), ch. 7 (purged CV, embargo) |
| [5] | Parkinson, M. (1980); Garman, M., Klass, M. (1980). *Journal of Business*, 53(1) — range-based volatility |
| [6] | Amihud, Y. (2002). Illiquidity and stock returns: cross-section and time-series effects. *Journal of Financial Markets*, 5(1), 31–56 |
| [7] | Wilder, J. W. (1978). *New Concepts in Technical Trading Systems* — RSI, ATR |
| [8] | Gorodkin, J. (2004). Comparing two K-category assignments by a K-category correlation coefficient. *Computational Biology and Chemistry*, 28(5–6), 367–374. doi:10.1016/j.compbiolchem.2004.09.006 |
| [9] | Bailey, D., Borwein, J., López de Prado, M., Zhu, Q. (2014). Pseudo-mathematics and financial charlatanism: the effects of backtest overfitting on out-of-sample performance. *Notices of the AMS*, 61(5), 458–471. doi:10.1090/noti1105 |
| [10] | Chen, T., Guestrin, C. (2016). XGBoost: a scalable tree boosting system. *KDD 2016* |
| [11] | Elder, A. (1993). *Trading for a Living* — triple-screen multi-timeframe hierarchy |
| [12] | Makarov, I., Schoar, A. (2020). Trading and arbitrage in cryptocurrency markets. *Journal of Financial Economics*, 135(2), 293–319 — why `rel_divergence` stays a data-quality signal |
