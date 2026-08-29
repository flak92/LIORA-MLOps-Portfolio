# Methodology — the research layer on the 1-minute series

Per asset, independently, and all of it on one market object — the canonical
research series: a fixed 15-column hierarchical feature matrix, a triple-barrier
label resolved on the canonical 1-minute path, a purged walk-forward protocol
with Optuna hyper-parameter search, a historical final out-of-sample fold, and a
top-down gated strategy evaluation. The experiment is described by its research
window and seed. The guards in the code are the mathematics' own — the seven
named in `AGENTS.md`; *The repository shows the destination, not the road*.

## 1. The nine rules the code implements

1. `X` is a function of **closed** historical OHLCV only.
2. The decision is taken at a 15m bar close; **execution happens one minute later**.
3. `Y` comes from the **canonical research series** only — the same object as `X`.
4. `Y` is a first-touch triple barrier on the 1m path; **ambiguity is not a class**.
5. Overlapping labels carry **average-uniqueness** weights, measured on the
   population that uses them.
6. A training event may **not cross the start of its OOS block**.
7. HPO and the entry edge threshold `τ` see **F2–F4 only**.
8. **F5 changes no decision** — not a feature, not a hyper-parameter, not the
   entry edge threshold, not a rule.
9. PnL is **linear fixed-quantity research PnL on canonical prices**, with an
   explicit cost and without funding.

Everything below is these nine rules written out.

Why this shape: the label is a **decision indication**, not a price forecast —
the triple barrier [4] asks "which barrier does the market touch first from
here: profit, stop, or neither within the horizon?", which is exactly the
question a rule-based exit answers. Tree ensembles are the strongest
general-purpose learner for tabular financial features [3][9], short-horizon
crypto predictability from technical features is documented in [1][2], and the
top-down multi-timeframe gate follows the classic triple-screen hierarchy
[10]. The protocol as a whole is built against backtest overfitting [8]:
parameters frozen before the first run, and selection statistics kept strictly
apart from the final report.

## 2. One series, one object

```
market source A ──┐
                  ├── canonical 1m series (M) ──┬── 15m / 1h / 4h bars ──► X   (M up to t)
market source B ──┘                             │
                                                └── triple barrier ─────► Y   (M after t)
X + Y ──► purged walk-forward ──► XGBoost
                                      │
                              class probabilities
                                      │
                             fixed strategy rules
                                      │
                            canonical research path
                                      │
                                 equity / PnL ──► monitoring
```

The providers end at the ingest boundary. What crosses it is one continuous
series whose every candle is a real observation of one of them (bar an explicit
forward fill), and the research layer studies that series and nothing else:

```
X_t = f(M_{<=t})        Y_t = g(M_{t+1 : t+H})        M = canonical series
```

Features and target therefore describe the same canonical research object by
construction, and nothing here simulates trading on a named exchange: it
simulates a strategy on a canonical market model, with the costs stated.
`methodology_data.md` §1 and §4 carry the construction rule and why verbatim candles
beat an average.

## 3. Time semantics

```
… ─┤ 12:45 ── 15M bar ── 13:00 ├─ 13:00 ── 15M bar ── 13:15 ├─ …
                                ▲ t_d = decision_ts = 13:00
features: bars with close_ts <= 13:00  (15M 12:45–13:00, 1H 12:00–13:00, 4H 08:00–12:00)
entry:    t_0 = 13:01, on the first observed trade of that minute — its OPEN
event:    [t_0, t_v) = [13:01, 17:01)  — the barrier examines minutes 13:01 … 17:00
```

`t_0 = t_d + 1 min` is the **one-minute decision-to-entry latency assumption**:
a signal computed at the close of a bar cannot be filled at that same close.

`t_0` names a one-minute bucket, not an instant. **Entry occurs on the first
observed trade of the minute beginning at `t_0`, and its price is that minute's
`open`** — which is what the open of a 1m bar is. If the minute contains no
trade there is no entry. The exact intra-minute execution time is unobserved at
1-minute resolution, and `volume(t_0) > 0` is not future knowledge used to buy
at an earlier price: it is the statement that the trade whose price is `open`
happened at all.
`event_end_ts` is the **exclusive** end of the event, which is what makes the
purge rule exactly `event_end_ts <= oos_start` — an event ending at the first
minute of the OOS block does not overlap it.

Higher-timeframe features come from the last **closed** bar of their timeframe
(`asof_index`: `searchsorted` on close times, causality asserted in code, not
assumed). Bars are exact UTC-aligned aggregations of the canonical 1m series
(O first, H max, L min, C last, V sum; `arg_min` / `arg_max` by timestamp for
determinism).

## 4. Features — fixed contract, 15 columns

| Family | Definition on the timeframe's own bars | Range | Ref. |
|---|---|---|---|
| `ema20_minus_ema50_over_atr14` | `(EMA20 − EMA50) / ATR14` | unbounded, dimensionless | [1][3] |
| `centered_rsi14` | `(RSI14 − 50) / 50` | [−1, 1] | [1][7] |
| `atr14_over_close` | `ATR14 / close` | > 0, dimensionless | [1][5] |
| `range_position_20` | `(close − min(low,20)) / (max(high,20) − min(low,20))` | [0, 1] | [2] |
| `log_volume_zscore_50` | z-score of `log1p(volume)` over 50 bars | dimensionless | [1][6] |

`log_volume_zscore_50` measures the activity of the **canonical observation process**, not
venue-independent market activity: the sources differ in liquidity level, so a
source switch may induce a volume-level discontinuity. Normalising per source
would push provider knowledge back below the ingest boundary, so the limitation
is stated rather than engineered away.

Five families on 15m / 1h / 4h — **15 columns**, identical for every asset,
**no per-asset selection** (a deliberate overfitting control). Cross-timeframe
trend agreement is **not** a feature: the count of timeframes whose trend sign
matches a given side is a deterministic function of columns the model already
has, so it can only add representation, never information; the 2-of-3
agreement lives where it is actually used, in the strategy gate. Five families
per timeframe exceeds the four-per-timeframe multi-timeframe guideline by one:
`log_volume_zscore_50` is volume information, not a fifth price-derived indicator.
`rel_divergence` is a data-quality signal, never a feature [11]. Warm-up: 200
top-timeframe bars (`WARMUP_4H_BARS`) — decision rows before `2021-02-03 08:00
UTC` are excluded everywhere. Recursions (EMA, Wilder) run as explicit loops;
rolling statistics use `sliding_window_view`; no NaN survives the warm-up
(asserted).

## 5. Labels

Triple barrier [4] on every 15m boundary after the warm-up. Entry
`P₀ = entry_price = canonical 1m open(t_0)`; horizontal barriers
`P₀ ± 2.0 × ATR14` of the last closed **canonical** 1h bar; vertical barrier
`LABEL_HORIZON_MINUTES` = 240 minutes (16 × 15m bars). Resolution walks
the canonical 1m path: the first minute whose high touches `upper_barrier`
gives `y = +1`, whose low touches `lower_barrier` gives `y = −1`, neither gives
`y = 0` with the exit at the close of the last event minute.

**A touch requires a trade.** `volume = 0` means no observed trade in that
minute, so both hit conditions are gated on `volume > 0`. Whether such a minute
is a provider candle that printed nothing or a synthesised continuity row is a
provenance question, answered in the canonical table and in `methodology_data.md`,
not here:

```
upper_hit = (volume > 0) & (high >= upper_barrier)
lower_hit = (volume > 0) & (low  <= lower_barrier)
```

If the vertical-barrier minute contains no trade, its canonical close is a
**last-observed-price mark** used by the research simulation, not an observed
execution fill: the volume gate applies to barrier touches and to the entry,
not to the mark that closes an unresolved event.

A minute touching **both** barriers leaves their order unknowable from OHLC, so
the row is `label_valid = false` — never relabelled `0`. Ambiguity is a missing
observation, not a third outcome.

**Two conditions that look alike and must not be merged:**

```
entry_observable = volume(entry_ts) > 0   known at t_0        MAY gate an entry
label_valid      = event classifiable     known afterwards    NEVER gates an entry
sample_valid     = entry_observable & label_valid             the supervised population
```

Whether the entry minute traded at all is visible at the time, so the strategy
may refuse it. Whether the event will resolve ambiguously is not, so using
`label_valid` as an entry condition would be look-ahead: a signal whose event
later turns out ambiguous **is a trade**, settled at the barrier adverse to the
position.

Supervision uses both. An unobservable entry gives `P₀ = open` of a minute that
printed no trade, so its barriers are anchored to a quote nothing traded at: not an executable decision and not a sound
measurement. `sample_valid` therefore governs the training rows, the HPO
objective and the classification metrics — and, through them, the populations
the uniqueness weights are measured on — while the strategy gates on
`entry_observable` alone.

Sample weight = **average uniqueness** [4, ch. 4]: the mean over the event's
minutes of `1 / (concurrently open events)`, exact via prefix sums. It is the
XGBoost sample weight, with no additional class re-weighting. Rows whose
vertical barrier would cross the research end are dropped.

**The weight is a property of a population, not of an event**, so it is
measured where it is used, in `validation.py`, and never stored in `Y`.
Concurrency is counted inside the population that carries the weights: the
**purged training rows** of a fold, and separately the **scored rows** of that
fold. Counting it once over the whole research window would let a purged
event — or an event inside the block being evaluated — raise the concurrency
of a training row, so the future would help decide how much that row counts.
The training weights therefore feed `model.fit` and the class prior, the
scoring weights feed the log-losses of that same fold, and neither can be
used in place of the other.

`<TICKER>_label_events_ss-15-hh-dd-MM.parquet` also carries the prices the backtest needs —
`entry_price`, `upper_barrier`, `lower_barrier`, `exit_reference_price` — so the
strategy replays exactly the event that produced the label instead of
recomputing it.

## 6. Folds — WARMUP | TRAIN | PURGE | OOS | final holdout

```
2021-01-01     warmup_end     2022-01-01     2023-01-01     2024-01-01     2025-01-01          2026-08-26
|-- WARMUP --|----- F1 -----|----- F2 -----|----- F3 -----|----- F4 -----|-------- F5 ---------|
                                                                         (final holdout fold)
Fold 2:  TRAIN = F1            | PURGE | OOS = F2
Fold 3:  TRAIN = F1–F2         | PURGE | OOS = F3
Fold 4:  TRAIN = F1–F3         | PURGE | OOS = F4
Holdout: TRAIN = F1–F4         | PURGE | F5   (frozen params, frozen threshold)
```

**Purge** keeps a training row only if `event_end_ts <= oos_start`. Because
`event_end_ts` is exclusive, that inequality *is* "no overlap" — no artificial
gap is added, since a gap wider than the event horizon removes information
without removing leakage. A classical embargo after the evaluated block
[4, ch. 7] is not required in forward chaining: no training observation lies
after the OOS block.

**Scoring** mirrors the purge at the other boundary: a fold scores only the
supervised rows whose maximum 240-minute horizon fits inside the block
(`entry_ts + LABEL_HORIZON_MS <= oos_end`), decided at t₀ — the real
`event_end_ts` is path-dependent, so admitting by it would let the future
choose the scored population.

**F5 is the historical final holdout fold.** The contract is a sentence, not a
guard, and it is about selection rather than counting: *F5 never participates
in feature definition, hyper-parameter selection, entry-edge-threshold
selection or strategy-rule selection.* F2–F4 carry the data-driven selection —
the hyper-parameters and the entry edge threshold; the barrier width, the
horizon, the cost and the feature set are frozen a priori. F5 is evaluated
against them. Recomputing F5 deterministically — after a refactor, on another
machine, in a later run — changes nothing, because nothing is chosen by
looking at it. What the contract forbids is the loop: read F5, change the
model, call the same fold out-of-sample again.

## 7. Hyper-parameter search

Optuna TPE (`seed = 42`), 50 sequential trials, in-memory study. Objective =
mean **uniqueness-weighted** multiclass log-loss over the three OOS validation
folds F2–F4. Space: `max_depth` 2–6, `eta` log 0.01–0.3, `min_child_weight`
1–50, `subsample` 0.5–1, `colsample_bytree` 0.5–1, `lambda` log 0.1–10,
`alpha` log 0.01–1, `num_boost_round` 100–800 step 50. Fixed:
`multi:softprob`, `num_class = 3`, `tree_method = hist`, `nthread = 1`,
`seed = 42`, no early stopping. Label parameters, costs and the entry-edge-threshold grid are **never** in the
space. The `hyperparameter_search_result` section of `<TICKER>_parameters.json` keeps the
chosen point, its log-loss and the trial count.

## 8. Classification metric — relative log-loss skill against the training prior

With `y = 0` dominant, a uniform `ln 3` baseline flatters any model that
merely learns the class frequencies. The baseline is therefore the
**uniqueness-weighted class prior of the fold's own training rows**,
`p_c = Σ wᵢ·1(yᵢ = c) / Σ wᵢ`, and the reported numbers are

```
prior_logloss · model_logloss · relative_logloss_skill = 1 − model/prior
```

`relative_logloss_skill` answers one question — does the model add information beyond knowing
how often each class occurs? — and is **a result, not a gate**. Metrics score the
supervised subset of a fold
whose maximum horizon fits inside it — the same t₀-decidable rule that governs
strategy eligibility (§9); predictions cover the full fold.

## 9. Strategy

```
edge = directional_probability_edge = p_long − p_short;  side = sign(edge)
agreeing_trend_timeframe_count =
    #{timeframe ∈ {15m, 1h, 4h} : sign(ema20_minus_ema50_over_atr14_<timeframe>) = side}
enter = |edge| ≥ τ ∧ max(p_long, p_short) > p_neutral ∧ side ≠ 0
        ∧ side = sign(ema20_minus_ema50_over_atr14_4h)
        ∧ agreeing_trend_timeframe_count ≥ 2
        ∧ entry_observable
```

The **model decides the side; the 4H hierarchy gates it**. One unit position
at a time, new signals ignored while in a position, and a signal is eligible
only where its whole 240-minute horizon fits inside the fold
(`entry_ts + LABEL_HORIZON_MS <= fold_end`) — decided at t₀, never by where the
trade actually ended.

**PnL — one formula.** The simulation applies USDT-perpetual PnL algebra to the
canonical price path: a position held at a fixed
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
minute that touched it (`long: min(lower_barrier, open)`, `short: max(upper_barrier, open)`),
which is also how the adverse side of an ambiguous minute is settled. Without
that rule a bar-based backtest silently assumes every gap fills at the barrier.

**The entry edge threshold `τ` is chosen on F2–F4 only**, by an explicit rule:

```
τ* = argmax_τ  mean( Sharpe_F2(τ), Sharpe_F3(τ), Sharpe_F4(τ) )
     subject to  trades_f(τ) ≥ MINIMUM_TRADES_PER_VALIDATION_FOLD = 30  for every f ∈ {F2, F3, F4}
     ties → the smaller τ
```

The trade floor is a **selection guardrail, not an acceptance gate**: without
it a threshold producing three or five trades with an accidentally high Sharpe
wins over a strategy that actually trades. If no threshold on the 0.00–0.60
grid meets it, the run falls back to `τ = 0` and reports
`entry_edge_threshold_constraint_met = false`.

**Sharpe and drawdown come from one equity process sampled two ways.** The
backtest writes a continuous 1-minute equity path starting at `E₀ = 1`; the
Sharpe is annualised (`×√(96·365)`) from that path sampled at **15m bar
closes**, starting from `E₀` itself so the first quarter-hour of a fold is not
silently dropped; the maximum drawdown is measured on the **1m** path, also
from `E₀` — a 15-minute sampling would report a 1.00 → 0.91 → 0.99 excursion as
−1 % instead of −9 %. `exposure` is
`Σ(exit − entry) / fold length`. The reported result is
**execution-cost-adjusted PnL, excluding funding**.

## 10. Artifacts and modules

Per asset in `store_assets_artifacts/<TICKER>/`, nine files, registered file by
file in `glossary.md` § Artifacts: three per-timeframe feature parquets, the
label-events and out-of-sample predictions parquets on the 15m decision grid,
two evaluation JSONs, the one parameters file and the README. Beside the
manifest, outside it, lies the asset's own database,
`<TICKER>_research_ohlcv.duckdb` — the market object every stage reads. The data
files are regenerable; `<TICKER>_parameters.json` and `<TICKER>_README.md` are
tracked, because they are what makes the rest readable without a run, and
neither carries a timestamp, so an unchanged experiment reproduces them byte
for byte. Every JSON is canonical (sorted keys, numpy scalars converted) and
carries **only what it computed** — no provenance envelope, no hashes. The
settings a run used are `module_ml/config.py` at the commit that ran it — the
commit is the record, and the parameters file carries only what the search
chose. The experiment is identified once, globally, in
`module_monitoring/ml_status.json`: research window and seed.
Library versions are pinned once, in `requirements.txt`. Runs are reproducible
by construction — fixed seed, `nthread = 1`, pinned versions — and that claim
is not backed by a hash gate, because a gate proves the metadata, not the
mathematics. No booster is persisted: nothing in this repo performs inference,
so the numbers are the product.

Module layout — three runtime modules, in the order the data moves, and
`module_skills`, which carries no dataflow: `module_data` (sources → normalised
raw 1m → one canonical DuckDB per asset) · `module_ml` (this document) ·
`module_monitoring` (presentation of what each module measured about itself,
and the server). Inside `module_ml`:
`module_ml/config` (frozen constants) · `module_ml/indicators`,
`module_ml/validation`, `module_ml/model` (pure numpy / xgboost kernels) ·
`module_ml/dataset` (artifact IO: X/Y loading, the one parquet writer, canonical
JSON) · `module_ml/bars` (the one writer, one file per asset) · `module_ml/features`,
`module_ml/labels`, `module_ml/hpo`, `module_ml/train`, `module_ml/strategy`,
`module_ml/status` (CLI stages, `python -m module_ml.<stage> [--tickers …]`).
Constant convention: **experiment-semantic constants live in
`module_ml/config.py`; implementation
constants** (chunk sizes, the equity-curve stride — daily in the artifact,
weekly on the page: seven daily points) **may stay local to their module**. The canonical series is gated where it is read:
`labels.load_research_1m` asserts the full 1m grid inside the research window,
per asset; the ingest stage rebuilds one asset's database at a time.

## 11. Running the layer: one asset per process

Every stage takes `--tickers`, so the chain parallelises the only way an
experiment with frozen thread caps may — **externally**, one asset per
process. `make ml-bars / ml-features / ml-labels / ml-hpo / ml-train / ml-strategy`
fan out `JOBS` assets at a time, where `JOBS = max(1, min(cores, available GiB))` is
measured at each invocation rather than written down (the machine this runs on
changes size); override with `make ml-hpo JOBS=2`. `ml-bars` fans out with
them — one file per process;
`data-ingest` alone stays sequential, because a memory ceiling is per process
and the sum of the concurrent ceilings is what has to fit the host.

Thread caps stay at one — `nthread = 1`, `OMP_NUM_THREADS = 1` — for the
reason `skill_determinism.md` states. The search is CPU-bound and one asset's
study is sequential by construction, so the wall-clock floor of `ml-hpo` is the
slowest single asset.

Rerun only what a change actually invalidates — the search is the expensive
stage, and most edits do not touch it:

| what changed | what to rerun |
|---|---|
| the canonical series (`make data-ingest`) | everything, from `ml-bars` |
| a feature definition | `ml-features ml-hpo ml-train ml-strategy ml-status` |
| a label or barrier parameter | `ml-labels ml-hpo ml-train ml-strategy ml-status` |
| the search space or the seed | `ml-hpo ml-train ml-strategy ml-status` |
| a strategy rule, the cost, the threshold grid | `ml-strategy ml-status` |
| the monitoring payload | `ml-status` |

## 12. What this is, and what it is not

This is a **bar-based research strategy simulation on the canonical market
series, with explicit execution-cost assumptions** — a canonical-market
research backtest. It is not a realistic simulation of trading on any exchange:
1m OHLCV contains no order book, no latency distribution, no partial fills, no
spread, no queue position and no funding payments. Every one of those would
move the result, and none of them is guessed at here.

One boundary belongs to the market model itself. The canonical series can
change provider between two minutes, and the two providers quote a real basis. A single barrier
touch can therefore come from a source switch rather than from the market
moving. That is a property of a constructed market object, not a defect hidden
by it: `source_switch_count` and `rel_divergence` are monitored per symbol
precisely so the effect is visible and countable.

Known limitations: no regime-conditional gating, no per-asset
feature selection, no CUSUM event sampling, no meta-labeling, no fractional
differentiation, fixed costs, unit position sizing. The class distribution is
dominated by `y = 0` (the 2×ATR barrier is rarely touched within one 4H
block) — reported per asset, not resampled.

## 13. References (DOIs resolve)

| Key | Reference |
|---|---|
| [1] | Jaquart, P., Dann, D., Weinhardt, C. (2021). Short-term bitcoin market prediction via machine learning. *The Journal of Finance and Data Science*, 7, 45–66. doi:10.1016/j.jfds.2021.03.001 |
| [2] | Sebastião, H., Godinho, P. (2021). Forecasting and trading cryptocurrencies with machine learning under changing market conditions. *Financial Innovation*, 7, 3. doi:10.1186/s40854-020-00217-x |
| [3] | Gu, S., Kelly, B., Xiu, D. (2020). Empirical asset pricing via machine learning. *The Review of Financial Studies*, 33(5), 2223–2273. doi:10.1093/rfs/hhaa009 |
| [4] | López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley — ch. 3 (triple barrier), ch. 4 (uniqueness), ch. 7 (purged CV, embargo) |
| [5] | Parkinson, M. (1980); Garman, M., Klass, M. (1980). *Journal of Business*, 53(1) — range-based volatility |
| [6] | Amihud, Y. (2002). Illiquidity and stock returns: cross-section and time-series effects. *Journal of Financial Markets*, 5(1), 31–56 |
| [7] | Wilder, J. W. (1978). *New Concepts in Technical Trading Systems* — RSI, ATR |
| [8] | Bailey, D., Borwein, J., López de Prado, M., Zhu, Q. (2014). Pseudo-mathematics and financial charlatanism: the effects of backtest overfitting on out-of-sample performance. *Notices of the AMS*, 61(5), 458–471. doi:10.1090/noti1105 |
| [9] | Chen, T., Guestrin, C. (2016). XGBoost: a scalable tree boosting system. *KDD 2016* |
| [10] | Elder, A. (1993). *Trading for a Living* — triple-screen multi-timeframe hierarchy |
| [11] | Makarov, I., Schoar, A. (2020). Trading and arbitrage in cryptocurrency markets. *Journal of Financial Economics*, 135(2), 293–319 — why `rel_divergence` stays a data-quality signal |
