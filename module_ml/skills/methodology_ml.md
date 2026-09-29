# Methodology — the research layer on the 1-minute series

Per asset, independently, and all of it on one market object — the canonical
research series: the feature catalogue of `module_features` as X — the fifteen
columns of the default set until a promotion — a triple-barrier label resolved
on the canonical 1-minute path, a purged walk-forward protocol
with Optuna hyper-parameter search, a historical final out-of-sample fold, and a
top-down gated strategy evaluation. The experiment is described by its research
window and seed. What an operator may set is a record of `CONFIGURABLES` in
`module_ml/config.py`; this document names a record and never restates its
value, which stands in that file and in `ml_status.json`'s `configurables`. The
guards in the code are the mathematics' own — the ones `AGENTS.md` § Values
names; *The repository shows the destination, not the road*.

## 1. The nine rules the code implements

1. `X` is a function of **closed** historical OHLCV only.
2. The decision is taken at a bar close of the decision timeframe; **execution
   happens one minute later**.
3. `Y` comes from the **canonical research series** only — the same object as `X`.
4. `Y` is a first-touch triple barrier on the 1m path; **ambiguity is not a class**.
5. Overlapping labels carry **average-uniqueness** weights, measured on the
   population that uses them.
6. A training event may **not cross the start of its OOS block**.
7. HPO, the entry edge threshold `τ` and, once a promotion writes them, the
   feature set and the barrier geometry see **F2–F4 only**.
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
                  ├── canonical 1m series (M) ──┬── the bars of the register ──► X   (M up to t)
market source B ──┘                             │
                                                └── triple barrier ───────────► Y   (M after t)
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
`CANDLE-CANONICALISATION-A-CANDLE-IS-CHOSEN-WHOLE` and `CANDLE-CANONICALISATION-PRIMARY-FAILOVER-IS-A-TABLE`
(`module_data/skills/skill_candle_canonicalisation.md`) carry the construction rule, and
`module_data/skills/methodology_data.md` why verbatim candles beat an average.

## 3. Time semantics

```
… ─┤ decision bar ├─┤ decision bar ├─ …
                    ▲ t_d = decision_ts, a bar close of the decision timeframe
features: on every timeframe of the register, the last bar with close_ts <= t_d — never one still open
entry:    t_0 = t_d + 1 min, on the first observed trade of that minute — its OPEN
event:    [t_0, t_v),  t_v = t_0 + H, H the asset's horizon — the barrier examines minutes t_0 … t_v − 1 min
```

The decision timeframe and the hierarchy are the feature layer's register, read
per asset from the contract `<TICKER>_catalogue.json`; this layer names none of
them. `t_0 = t_d + 1 min` is the **one-minute decision-to-entry latency
assumption**: a signal computed at the close of a bar cannot be filled at that
same close.

`t_0` names a one-minute interval, not an instant. **Entry occurs on the first
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

## 4. Features — the catalogue, and the feature set per asset

The features are `module_features`': the names are
`module_features/skills/skill_feature_taxonomy.md`, the definitions, their
histories and their warm-ups `module_features/skills/methodology_features.md`,
and neither is repeated here. The catalogue holds every definition on the
timeframes it is offered on, and `features_status.json` publishes how many;
every asset's catalogue partitions carry all of them, and this layer reads each
feature by the id `feature_id()` composes from a definition name and a timeframe
the contract lists — no alias and no naming of its own.

What the model sees is the asset's **feature set**: the definitions marked as
the default set on every timeframe they are offered on — the fifteen columns of
the frozen experiment, in the order it stacks them — until a promotion writes
`<TICKER>_feature_set.json` (`dataset.load_feature_columns()`); `build_x()`
stacks the set timeframe-major and catalogue-order within, because the model
samples its columns by position. The set is chosen per asset, on F2–F4 only, by
the serpentine search; F5 is evaluated under it and never chooses it. Every
feature column is evaluated only after the warm-up the contract carries:
decision rows before its `warmup_end_ms` are excluded everywhere, and no NaN
survives it (asserted, in `catalogue.build_catalogue`).

**The serpentine search asks; this layer answers.** The search is
`module_features`' — its rounds and families, its beam, its profile, its resume,
its ledger and its promotion are `module_features/skills/methodology_features.md`
— and it computes no metric of a state: every number it reads is an answer of
`ml-score`, `module_ml/score.py`. A turn of the search leaves its question as
`<TICKER>_score_request.json` — the kind of scoring, the round and the states —
and `ml-score` answers in `<TICKER>_score_response.json`, in the order the
request named the states, written only once every one of them has an answer;
`make features-serpentine-search` alternates a turn and `ml-score`, a one-off
container each, while the turn leaves a question. A state Θ is the whole of what
is evaluated (`score.theta()`): the set's columns by timeframe, the barrier
geometry — the multiplier the label's barriers stand at, the horizon they stand
for, and the take-profit and the stop a **trade** leaves at — and the
hyper-parameter point, `best_params`. Its key is its own canonical JSON text,
compared by equality (`score.state_key()`).

**What one evaluation computes.** For the kind `score`, one trial row per state
(`score.score_results()`): X and Y for the state — the asset's own Y where the
label's geometry is the asset's, else Y walked again down the 1m path in process
(`score.xy_for_state()`) — three boosters fitted before F2, F3 and F4 as § 6
fits them under the state's `best_params`, scored as § 8 scores them, then the
threshold selection of § 9 on their out-of-fold predictions
(`score.trial_result()`), which gives each validation fold's realised CAGR,
maximum drawdown, Calmar ratio, profit factor, Sharpe ratio and trade count, and
the path the three chain into. States of one request that differ only where a
trade leaves share one fit identity (`score.fit_identity()`): the first of them
pays for the three fits and the rest inherit its predictions, because neither a
fit nor a prediction reads a trade's exit, and only the backtest is replayed. For
the kind `hpo`, the request names beam parents, and each gets one study of § 7 on
its own X and Y, its gate reading that parent's folds; the study's best
admissible point that beats the parent's path, scored as a state, is the
candidate it offers, or `null` — which is an answer (`score.hpo_results()`).
Every point of every study goes to the asset's partition of `score_trials` once
the last study has ended, and the response after them. No booster is kept:
nothing here performs inference, so the numbers are the product.

**One row, one schema.** A trial's row carries the whole of Θ and every quantity
measured on it — each fold's skill, Sharpe ratio, CAGR, drawdown, Calmar ratio,
profit factor and trade count, the mean skill, the chained path, the chosen
threshold, whether it met the trade floor and what it was chosen out of — under
one set of key names, and the selection reads some of them. The model's own
skill is among the measured and the reported; nothing selects on it.

**The goal is the validation path, the unit of robustness is the fold.** The
three out-of-fold equity curves are chained into one walk-forward path — each
fold's 1-minute equity scaled by what the folds before it settled at
(`validation_path_block`, `module_ml/strategy.py:257–279`) — and the path's
growth rate, `validation_path.cagr` (`validation_path_cagr`,
`module_ml/strategy.py:238–246`), is what a move has to raise. A position never
crosses a fold boundary (§ 9's eligibility requires the whole horizon inside the
fold), so the chaining is exact, and a drawdown that begins in one fold and ends
in the next is counted as it happened. The ranking maximises `state_objective`
(`module_features/sub_module_serpentine_search/serpentine_search.py:64–70`): the
path's CAGR, then its Calmar ratio, then its profit factor, a path that never
lost having none and sorting as +∞; `ranking_key` (`serpentine_search.py:164–168`)
breaks what is left by the smaller column count, then by the earlier trial.

**Two states are compared under the same conditions.** Everything but the state
is held fixed: the same data — the asset's catalogue, bars and canonical series,
read once per request (`score.build_asset()`) — the same folds and the same cost,
`EXECUTION_COST_RATE_PER_TRADE_SIDE` per side (`module_ml/strategy.py:166`); the
Sharpe ratio annualised by the periods per year of the decision bar
(`module_ml/strategy.py:211–215`) and every CAGR over a 24/7 year of minutes
(`validation.cagr`); causality by construction, a higher-timeframe
value read from the last closed bar alone (`indicators.asof_index`,
`module_features/indicators.py:200`); the fold contract WARMUP | TRAIN | PURGE |
OOS | final holdout of § 6 (`module_ml/validation.py`, its bounds
`module_ml/config.py:211–217`); and every label inside the research window — the
1m path read inside it alone, and a decision kept only where its whole horizon
ends by the window's end (`module_ml/labels.py:71–72`, `module_ml/labels.py:186`).
A move of the label's horizon changes the supervised population itself — a longer
horizon drops more of each fold's tail and moves the purge — so parent and child
are scored on row sets that differ at the edges; the difference is bounded by the
horizon and the purge width, the comparison is still made on the same calendar
window and the same capital, and that is a property of the coordinate rather than
an accident of the code.

**The gate says which children may be ranked at all** (`is_gate_cleared`,
`serpentine_search.py:73–102`). A child whose threshold fell back to the grid
floor — the entry-edge-threshold constraint of § 9, the trade floor in every
fold, unmet — is refused before it is compared, because its numbers stand at a
threshold nothing qualified for. Otherwise it needs a Calmar ratio strictly above
its parent's on **every** validation fold, F2, F3 and F4, and a path CAGR above
its parent's by more than k(n)·σ: n the candidates of its pass — the states its
family offers, or every point the pass's studies drew — and σ the asset's noise,
`path_cagr_noise_standard_deviation` of its profile. A calibration run, whose
profile has no σ yet, asks for strictly better on the objective and on every
fold, and for no worse (`≥`) on a move that shrinks the state. The folds alone
would admit a child better on all three fold measures while the path's CAGR
falls — a state worse at the thing searched for because it is better at the
thing guarding it — so the gate asks for both.

What the fold condition guarantees is a higher Calmar ratio on each validation
fold, and no more. Where a fold's CAGR is positive that is less drawdown per unit
of growth; where it is negative, a deeper drawdown at the same loss raises the
ratio toward zero, so on a losing fold a higher Calmar ratio is not a shallower
drawdown relative to growth — and on no fold does it bound the drawdown in
absolute terms.

**The proposal** is the champion alone (`proposals_block`,
`serpentine_search.py:190–210`), proposed only where its threshold constraint is
met, where it is not the start, where no validation fold scores it below the
start, and where its path CAGR beats the start's by more than k(N)·σ, N the
search's whole exposure —
`trial_count_by_loop` summed, the states its families scored and the points its
studies drew. A calibration run proposes nothing. These thresholds are the
method's own assumptions, its baseline, and not conditions of correctness that
every optimiser would have to meet: a search without them is another method, not
a wrong one.

**Progress and stopping.** Each family leaves the beam its best
`SERPENTINE_SEARCH_BEAM_WIDTH` distinct states by the ranking key among its
gate-cleared children **and the parents they came from**
(`serpentine_search.py:498–499`), so the best-ranked state — the champion, which
moves at the round's end — never ranks worse than it did. A round in which no
family changed the beam ends the search: `search_converged = not round_accepted`
(`serpentine_search.py:512`). That is a statement about the schedule the round
executed — every child it scored either failed the gate or ranked below the
states already there — and not a global optimum, which is not claimed: every
move is one coordinate, so an improvement that needs several coordinates changed
at once is out of its reach.

**k(n)·σ is a heuristic, not a guarantee.** `false_exceedance_rate`
(`serpentine_search.py:112–116`) is

```
1 − E_Z[ Φ(k + Z)ⁿ ],   Z standard normal, the expectation by Gauss–Hermite quadrature
```

the chance that the best of n candidates beats a parent by k noise standard
deviations when every score is its state's worth plus independent normal noise of
standard deviation σ and no candidate is truly better; `gate_threshold_multiple`
(`serpentine_search.py:119–130`) finds by bisection the k at which that chance is
`GATE_THRESHOLD_FALSE_EXCEEDANCE_RATE`, one in twenty. σ
(`path_cagr_noise_standard_deviation`, `serpentine_search.py:143–161`) is read off
the ledgers of calibration runs and drafted into the profile by a hand: the
path-CAGR differences between a child and its parent, both meeting the threshold
constraint and the child fitted on its own, each pair of states once, reduced to
one evaluation's standard deviation as the median absolute deviation × 1.4826 / √2.
Those pairs are **different** states, so σ holds the effect of each change as well
as the variability of one evaluation — which, seeded and single-threaded, gives
one state one number. And the candidates of an adaptive search are not
independent normal draws around a common worth: they are correlated neighbours,
and each pass is seeded by what the one before it kept. The one-in-twenty rate is
the model's, under its assumptions; no 95 % bound on a false move of the search
follows from it.

Selection overfitting is bounded and exposed, never absent: a move is accepted
only by every one of the three validation folds and above the noise margin of its
pass, under a trade floor that keeps a fold's CAGR and Calmar ratio from standing
on a handful of trades, and the trial count — in all and per loop — is published
beside every proposal in `features_status.json`. The objective is a strategy
number measured on `MINIMUM_TRADES_PER_VALIDATION_FOLD` to a few hundred trades a
fold, where the model's own skill stands on some 10⁴ decisions, so it is the
noisier quantity; the per-fold gate and the floor are what hold that in check,
and the skill is reported beside it so a state that wins on CAGR while losing
skill is visible by eye.

**A promotion** (`make features-serpentine-search-promote ASSET=<TICKER>
PROPOSAL=<n>`, one asset at a time, never fanned out) copies the proposal's
columns into `<TICKER>_feature_set.json` and its barrier geometry into
`<TICKER>_barriers.json` — those and nothing else; the commit history is the
record of every promotion — and reruns `ml-all` for the asset, `ml-hpo` included,
which tunes the hyper-parameters anew: the promoted state is evaluated again on
F2–F4 under the point that study chooses, and F5 is read after it and steers no
parameter. What is promoted is a state's columns and geometry, not the exactly
evaluated model, so the realised result differs from the search's. A search that
proposes nothing has returned a correct result.

## 5. Labels

Triple barrier [4] on every bar close of the decision timeframe after the
warm-up. Entry `P₀ = entry_price = canonical 1m open(t_0)`; horizontal barriers
`P₀ ± m × σ_t`, σ_t the recursive mean of the true range over
`LABEL_BARRIER_TRUE_RANGE_SMOOTHING_PERIOD_BARS` bars of
`LABEL_BARRIER_TRUE_RANGE_TIMEFRAME`, read off its last closed **canonical** bar
at t_d and asserted finite and positive at every decision
(`labels.label_events()`); vertical barrier the asset's horizon H. m and H are
coordinates of the serpentine search and are promoted into
`<TICKER>_barriers.json`; until one is, an asset holds the geometry of
`START_BY_COORDINATE_DEFAULT`. Resolution walks the canonical 1m path: the first
minute whose high touches `upper_barrier` gives `y = +1`, whose low touches
`lower_barrier` gives `y = −1`, neither gives `y = 0` with the exit at the close
of the last event minute.

**A touch requires a trade.** `volume = 0` means no observed trade in that
minute, so both hit conditions are gated on `volume > 0`. Whether such a minute
is a provider candle that printed nothing or a synthesised continuity row is a
provenance question, answered in the canonical family and in
`module_data/skills/skill_candle_canonicalisation.md`,
not here:

```
upper_hit = (volume > 0) & (high >= upper_barrier)
lower_hit = (volume > 0) & (low  <= lower_barrier)
```

**The horizon travels as a duration token and becomes a number once.**
`HORIZON_TOKEN_MINUTES` maps the tokens of the timeframe grammar to minutes, and
`dataset.barriers_from()` resolves a geometry's token there and nowhere else —
the promoted file's through `dataset.load_barriers()`, a state's of the search in
`score.py` — so a search that moves the coordinate moves one number. Four places
compute with that number, and each is handed it:

| reader | what it decides with the horizon |
|---|---|
| `labels.label_events()` | which decisions are labelled at all — the grid keeps only those whose whole horizon fits inside the research window |
| `labels.triple_barrier()` | how far down the 1m path a walk goes, and where a vertical exit is marked |
| `validation.scoring_set()` | which supervised rows a fold scores — those whose maximum horizon fits the block, decided at t₀ |
| `strategy.signals_for_fold()` | which entries are eligible in a fold — the same test, on the trade's side |

`validation.training_set()` is **not** among them: the purge is
`event_end_ts <= oos_start`, and `event_end_ts` is a column of Y that already
carries the horizon the labels were written with. A fifth reader is prose —
`status.py` states the horizon and the tail it costs in `<TICKER>_README.md`.

If the vertical-barrier minute contains no trade, its canonical close is a
**last-observed-price mark** used by the research simulation, not an observed
execution fill: the volume gate applies to barrier touches and to the entry,
not to the mark that closes an unresolved event.

A minute touching **both** barriers leaves their order unknowable from OHLC, so
the row is `label_valid = false` — never relabelled `0`; the `y` column carries 0 for such a row because no barrier ordered the touch, and `label_valid` is what removes it from every population — `y` is never read without it. Ambiguity is a missing
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

The asset's `labels` partition also carries the prices the backtest needs —
`entry_price`, `upper_barrier`, `lower_barrier`, `exit_reference_price` — so the
strategy replays exactly the event that produced the label instead of
recomputing it.

## 6. Folds — WARMUP | TRAIN | PURGE | OOS | final holdout

```
b₀           warmup_end     b₁             b₂             b₃             b₄                   b₅
|-- WARMUP --|----- F1 -----|----- F2 -----|----- F3 -----|----- F4 -----|-------- F5 ---------|
                                                                         (final holdout fold)
Fold 2:  TRAIN = F1            | PURGE | OOS = F2
Fold 3:  TRAIN = F1–F2         | PURGE | OOS = F3
Fold 4:  TRAIN = F1–F3         | PURGE | OOS = F4
Holdout: TRAIN = F1–F4         | PURGE | F5   (frozen params, frozen threshold)
```

b₀ … b₅ are `FOLD_BOUNDS_UTC`, b₀ and b₅ the research window, the first
inclusive and the last exclusive; `warmup_end` is the contract's
`warmup_end_ms`, before which no decision row exists.

**Purge** keeps a training row only if `event_end_ts <= oos_start`. Because
`event_end_ts` is exclusive, that inequality *is* "no overlap" — no artificial
gap is added, since a gap wider than the event horizon removes information
without removing leakage. A classical embargo after the evaluated block
[4, ch. 7] is not required in forward chaining: no training observation lies
after the OOS block.

**Scoring** mirrors the purge at the other boundary: a fold scores only the
supervised rows whose maximum horizon fits inside the block
(`entry_ts + the horizon <= oos_end`), decided at t₀ — the real
`event_end_ts` is path-dependent, so admitting by it would let the future
choose the scored population.

**F5 is the historical final holdout fold.** The contract is a sentence, not a
guard, and it is about selection rather than counting: *F5 never participates
in feature definition, hyper-parameter selection, entry-edge-threshold
selection or strategy-rule selection.* F2–F4 carry the data-driven selection —
the hyper-parameters, the entry edge threshold and, once a promotion writes them,
the feature set and the barrier geometry; until one does, the geometry is
`START_BY_COORDINATE_DEFAULT`, and the cost is frozen a priori.
F5 is evaluated against them — a promotion is decided on F2–F4 before F5 is
seen under the new state, and F5 is report-only. Recomputing F5 deterministically — after a refactor, on another
machine, in a later run — changes nothing, because nothing is chosen by
looking at it. What the contract forbids is the loop: read F5, change the
model, call the same fold out-of-sample again.

## 7. Hyper-parameter search

Optuna TPE seeded with `SEED`, `HYPERPARAMETER_SEARCH_TRIAL_COUNT` sequential
trials, in-memory study — sequential because a parallel study draws its trials in
nondeterministic order, and single-threaded because multi-threaded float
summation reorders and two runs diverge. The objective is the quantity the
serpentine search selects on: the CAGR of the validation path at the threshold
§ 9's rule would pick, maximised (`hpo.sweep_selection()`).

**The first `HYPERPARAMETER_SEARCH_STARTUP_TRIAL_COUNT` trials are the sampler's
random start.** TPE fits its two densities only once it holds `n_startup_trials`
trials — completed and pruned alike, in this Optuna — and draws at random until
then, so a study whose trial count is at or below the startup count is a random
search under the sampler's name and reports as a TPE one. The startup count is a
record of `CONFIGURABLES` rather than a default inherited from the library: a
number that decides how the experiment searches is the experiment's, and a
default that moves with a version bump is not a frozen method. The modelled
trials are the ones past the startup count, by construction and not by luck.

**The two counts are activation values, not calibration.** They are the smallest
counts at which every part of the method runs on every study: the sampler models,
the gate is evaluated fold by fold and its counts are written, and a study's
offer of its best admissible point has more than one point to choose among. They
say nothing about how many trials the research needs, and they are held until the
method is calibrated; a count that would be is a new experiment.

**The sampler's remaining internals are Optuna's, and are pinned as such.** The
quantile that splits good from bad, the number of candidates the acquisition
draws, the prior and its weight, the clipping, the endpoints, `multivariate`,
`group`, `constant_liar` — none of them is written here, and one of them is a
function rather than a number, so copying them into `config.py` would fork the
library's internals into this repo and let the fork drift. They are pinned
instead by `==` in `requirements.txt`. A version bump therefore changes the
method — it is never a silent drift, which is the property that was wanted.

**The trials families are files of this repository, and they are
byte-deterministic.** Every point every study drew is one JSON object on one line
of the asset's partition of a trials family, appended by `hpo.log_trials()`
through `dataset.append_jsonl` and never rewritten: the studies of `ml-hpo` in
`store/trials/hpo_trials/ticker=<TICKER>/hpo_trials.jsonl`, written by that stage
alone, and the studies `ml-score` runs for the serpentine search in
`store/trials/score_trials/ticker=<TICKER>/score_trials.jsonl`, written by that
stage alone. Both families carry one row, `TRIAL_COLUMNS`, and each family's
`schema.json` beside its partitions is written from that one constant. A line
carries where it was drawn — `origin`, `hpo` for the stage and
`serpentine_search` for the search's studies — the round when the search drew it,
the study's place in its partition (`search_index`), the trial's place in the
study, its state, the point the sampler drew and what the trial left. It carries
**no run id, no timestamp and no host name**, which is the property that matters:
two studies over an empty store leave the same bytes, so two runs over an asset's
emptied partition are a comparison and not an anecdote. A record that cannot be
compared is a note; this one is evidence.

**A partition counts every study that ran.** A request answered twice — `ml-score`
stopped after its studies' lines and before its response, then run again — leaves
its studies twice, under a later `search_index`. That is what a partition is for,
a record of the work done, and it is why it is not the exposure a proposal is read
against: that number is the search's own `trial_count_by_loop` (§ 4). A study's
`search_index` is read off its partition before its lines are appended, so a
partition takes one writer at a time: each family is written by its own stage
alone, one process per asset.

**A pruned trial and a completed one do not share a meaning.** Every key stands on
every line, `null` where it does not apply, so the file reads as one table. A
completed trial carries `cagr_validation_path`, the chained path's growth rate at
the threshold the rule chose, and `admissible`, whether that threshold beats the
champion on every fold — `null` for the stage, which has no champion. A pruned one
carries `null` in both and the fold it stopped at, `pruned_at_fold`. Both carry two
counts, one per fold the trial reached — what the gate saw, written down rather
than inferred from the fact that the trial survived:
`floor_clearing_threshold_count_by_fold`, the thresholds at which every fold so
far clears the trade floor, asked in both modes; and
`admissible_threshold_count_by_fold`, those of them that also beat the champion's
Calmar, `null` for the stage. One key answering whichever of the two questions its
writer had in mind would be a key the register could not define. The count the
gate stops on is zero on a pruned trial's last fold and on no completed trial's —
the floor's for the stage, the champion's for the search — which is the whole of
the gate's story on one line. The state is read from `trial.state` and never
inferred from the value: Optuna records the last reported intermediate value as a
pruned trial's value.

**The stage draws no point to start from.** It is a function of X, Y and the
frozen constants, so `<TICKER>_parameters.json` is a function of the raw store
and this code and never of its own last value: a derived artifact that read
itself would make the chain a fixed-point iteration, and two runs of `ml-all`
would not have to agree until it settled. What a study is compared against
belongs to the serpentine search's hyper-parameter family below, where a beam
parent is an input the search itself holds. Space: `HYPERPARAMETER_SEARCH_SPACE`,
one entry per hyper-parameter in xgboost's own spelling, with the kind of its
draw and its bounds. Fixed: `multi:softprob`, `num_class = 3`,
`tree_method = hist`, `nthread = 1`, the seed `SEED`, no early stopping — which is
why `num_boost_round` is itself a coordinate of the space, and why its ceiling has
to be high: at the bottom of the `eta` range a short run of rounds cannot
converge, so a low ceiling would leave the low end of `eta` unreachable rather
than merely unchosen. The barrier geometry, the costs and the entry-edge-threshold grid are
**never** in the space: the geometry is a coordinate of the serpentine search and
is promoted, not tuned. The `hyperparameter_search_result` section of
`<TICKER>_parameters.json` keeps the chosen point, its value under the frozen
objective and the trial count.

Inside the serpentine search the study is itself a coordinate — one candidate per
beam member, drawn on that member's own X and Y by `score.hpo_results()`. It
cannot answer worse than the member it ran on because a candidate has to beat it:
the guarantee is the gate's. The study is handed no point: the member's own
parameters as a first trial would be stopped by the gate after one fold —
equality does not beat a strict inequality — a fit spent on a point that could not
be a candidate, and a trial pruned before it reports anything tells the sampler
nothing. **One** gate stops a trial early, and it is the state gate's own
condition read one fold at a time (`hpo.admissible_thresholds()`): after each
validation fold, the thresholds at which every fold so far clears the trade floor
**and** beats the champion's Calmar there. The set only shrinks as folds are
added, and the child the search would keep needs one threshold inside it over all
three folds, so a trial whose set has gone empty cannot produce one however the
folds it has not run land. Nothing admissible is discarded. The count after each
fold is written into the ledger whether or not the gate is armed, so what the
gate saw is readable and not inferred.

Two bounds — the best Calmar ratio and the best growth rate a fold could still
reach over the whole grid, each read fold by fold and never jointly — would not
do: each is true of *some* threshold, and together they say nothing about *one*
threshold admissible on every fold, which is what the state gate needs. The set is
that quantity, so the gate stops a trial exactly when it can no longer produce a
child the search would keep.

Optuna's median pruner is not a gate here either: it compares a trial's best
intermediate value across all of its steps with the median of other trials at one
step, and with folds as successive stretches of calendar time that is not a
comparison of like with like. When every trial of a study is stopped, the study
offers nothing that round — which is an answer, not a failure.

**The study offers the best admissible point, not the best point**
(`hpo.admissible_point()`). A study's best trial by value may be one whose chosen
threshold does not beat the champion on every fold; the state gate refuses that
child. Offering it would mean the study answered nothing while holding, further
down its own list, a point the gate would have kept — so the trials are read by
value, descending, and the first admissible one that beats the champion's own path
is offered; where that point is the parent's own parameters, it is no move and
nothing is offered. Whether a trial's chosen threshold was admissible is decided
where the sweeps already are, and carried on its ledger line as `admissible`, so
the question is asked without refitting anything.

## 8. Classification metric — relative log-loss skill against the training prior

With `y = 0` dominant, a uniform `ln 3` baseline flatters any model that
merely learns the class frequencies. The baseline is therefore the
**uniqueness-weighted class prior of the fold's own training rows**,
`p_c = Σ wᵢ·1(yᵢ = c) / Σ wᵢ`, and the reported numbers are

```
prior_logloss · model_logloss · relative_logloss_skill = 1 − model/prior
```

`relative_logloss_skill` answers one question — does the model add information beyond knowing
how often each class occurs? — and is reported beside every state and selects nothing: the
hyper-parameter search maximises the validation path's CAGR (§ 7), and the serpentine search
gates a move on each fold's Calmar ratio and ranks it by that same CAGR (§ 4). Metrics score the
supervised subset of a fold
whose maximum horizon fits inside it — the same t₀-decidable rule that governs
strategy eligibility (§ 9); predictions cover the full fold.

**Two importances per validation fold**, each of that fold's own booster, none
of the final holdout's: `gain_importance`, XGBoost's total gain per column;
`mean_abs_shap_importance`, the mean absolute SHAP value [12] per column over
the fold's scoring rows and the three classes, in margin space and unweighted,
because it is a property of the fitted function rather than of a population.
They are results, not gates: the page shows their means over the validation
folds, and nothing selects on them.

## 9. Strategy

```
edge = directional_probability_edge = p_long − p_short;  side = sign(edge)
agreeing_trend_timeframe_count =
    #{timeframe of the register : sign(TREND_GATE_FEATURE_DEFINITION_<timeframe>) = side}
enter = |edge| ≥ τ ∧ max(p_long, p_short) > p_neutral ∧ side ≠ 0
        ∧ side = sign(TREND_GATE_FEATURE_DEFINITION_<top timeframe>)
        ∧ agreeing_trend_timeframe_count ≥ MINIMUM_AGREEING_TREND_TIMEFRAMES
        ∧ entry_observable
```

`TREND_GATE_FEATURE_DEFINITION` is
`exponential_smoothing20_minus_exponential_smoothing50_over_true_range_recursive_mean14`
— the spread of two exponential smoothings over the recursive mean of the true
range — read by its feature id on every timeframe from the catalogue, in the
feature set or not; the top timeframe is the coarsest of the hierarchy the
contract lists. The **model decides the side; the top timeframe gates it**. One
unit position at a time, new signals ignored while in a position, and a signal is
eligible only where its whole horizon fits inside the fold
(`entry_ts + the horizon <= fold_end`) — decided at t₀, never by where the
trade actually ended.

**PnL — one formula.** The simulation applies USDT-perpetual PnL algebra to the
canonical price path: a position held at a fixed
quantity `Q = s · E₀ / P₀` (notional 1× current equity), so PnL is linear in
price, with the cost `c = EXECUTION_COST_RATE_PER_TRADE_SIDE` charged on entry
notional and on exit notional:

```
R      = s·(P_x/P₀ − 1) − c − c·(P_x/P₀)
E_next = E₀·(1 + R)
E_t    = E₀·(1 − c + s·(P_t/P₀ − 1))      mark-to-market while open
```

Before the cost, a short from 100 to 80 returns exactly +20 %, and a short
through 100 → 50 → 100 returns 0 %. Compounding per-bar returns instead —
`Π(1 + s·r_t)` — returns −100 % on that path; that is the arithmetic this formula
replaces.

**A trade leaves where it chooses, not where the label did.** The label stays
symmetric — `entry ± m·σ`, the same on both sides — because that is how a
direction is learned. A trade has its own exit: for a long the take-profit at
`tp·σ` above the entry and the stop at `sl·σ` below it, mirrored for a short,
with the same vertical barrier. Both are found by the same walk down the 1m path
that wrote Y (§ 5), for the entries the gate admits, so "the first barrier
touched" has one definition in this repository and one guard on `volume > 0`. In
code the trade's barriers are the **label's own half-widths rescaled** —
`entry + (tp/m)·(upper − entry)` and `entry − (sl/m)·(entry − lower)` — and not a
σ recovered from one of them: at `tp = sl = m` the scale is exactly one and the
trade's barriers are the label's to the bit, for every `m`, whereas one recovered
σ reproduces the upper barrier and misses the lower by a unit in the last place
on about 2 % of BTC's rows. A position's occupancy runs to the end of the
**trade's** event, so a tighter stop frees the capital sooner, which is the point
of searching the two multipliers at all.

**Fills acknowledge that 1m OHLC hides the tick path.** A take-profit fills at
the barrier. A stop fills at the *worse* of the barrier and the open of the
minute that touched it (`long: min(lower_barrier, open)`, `short: max(upper_barrier, open)`),
which is also how a minute that touched both is settled — the order inside a
minute is unknowable, so the trade takes the adverse side. Without
that rule a bar-based backtest silently assumes every gap fills at the barrier.

**The entry edge threshold `τ` is chosen on F2–F4 only**, by an explicit rule:

```
τ* = argmax_τ  CAGR( E_F2(τ) ⌢ E_F3(τ) ⌢ E_F4(τ) ),   τ ∈ ENTRY_EDGE_THRESHOLD_GRID
     subject to  trades_f(τ) ≥ MINIMUM_TRADES_PER_VALIDATION_FOLD  for every f ∈ {F2, F3, F4}
     ties → the smaller τ
```

where `⌢` is the chaining of § 4: each fold's 1-minute equity scaled by what the
folds before it settled at, so the validation folds are one walk-forward path and
its CAGR is the growth of one capital through them. It is the **same function**
the stage and `ml-score` both call (`strategy.entry_edge_threshold_selection()`) —
the latter for every state the serpentine search asks about — so the chain and
the search can never choose a different threshold for the same predictions. The
rule reads what each fold settled at and nothing else: the path's drawdown and its
profit factor need the folds' curves chained, its growth rate does not, and a
selection walks every point of the grid.

The trade floor keeps a threshold from winning on three or five trades with an
accidentally high number. If no point of the grid meets it, the run falls back to
the grid's first point and reports `entry_edge_threshold_constraint_met = false`;
the serpentine search refuses such a state before it compares it (§ 4), because
its numbers stand at a threshold nothing qualified for.

**A fold's own numbers, and the path they chain into.** From the same 1-minute
equity a fold reports its CAGR — `final_equity ** (MINUTES_PER_YEAR / minutes) − 1`,
a 24/7 year of 365 days, so a fold that holds a 29 February has an exponent
slightly under one rather than being idealised away — its maximum drawdown, their
ratio as the Calmar ratio, its profit factor over the trades it took, and its
trade count. The three validation folds chain into `validation_path`, which
carries the same five for the path as a whole. The path's maximum drawdown is at
least the largest of the folds' own, because a drawdown may run across a fold
boundary; that is the point of chaining rather than averaging.

**Sharpe and drawdown come from one equity process sampled two ways.** The
backtest writes a continuous 1-minute equity path starting at `E₀ = 1`; the
Sharpe is annualised by `√(periods per year)`, `MINUTES_PER_YEAR` over the minutes
of one decision bar (`module_ml/strategy.py:211–215`), from that path sampled at
the **decision bars' closes**, starting from `E₀` itself so the first decision bar
of a fold is not silently dropped; the maximum drawdown is measured on the **1m**
path, also from `E₀` — a sampling at bar closes would report a
1.00 → 0.91 → 0.99 excursion as −1 % instead of −9 %. `exposure` is
`Σ(exit − entry) / fold length`. The reported result is
**execution-cost-adjusted PnL, excluding funding**.

**What the chosen threshold was chosen out of.** The selection is a maximum over
the threshold grid, and a maximum reported alone is a number with no spread beside
it: the same score means one thing as the only point that qualified and another as
the best of eleven. `cleared_point_count`, `median_cagr_over_cleared` and
`max_cagr_over_cleared` ride beside it in `<TICKER>_strategy_evaluation.json`, in
every trial row of the serpentine search and in `ml_status.json` — three plain
statistics of the grid, with **no correction applied and none implied**. This layer
does not deflate the score, and saying so is the point: the correction belongs to
whoever reads the number, and it cannot be made at all without the population it
was a maximum over. All three are `null` when nothing qualified and the threshold
fell back to the grid floor, which is itself the loudest thing the three can say.

## 10. Artifacts and modules

Per asset, each name registered in `module_skills/skill_glossary.md` § Artifacts, and
the research artifacts listed with their sizes in the Files table of
`<TICKER>_README.md`: in the artifacts store, the asset's partitions of `labels` and `oos_predictions` on the decision
timeframe — `store/assets_artifacts/<family>/ticker=<TICKER>/timeframe=<tf>/<family>.parquet`,
each family's `schema.json` at its root — and in the asset's folder
`store/assets_artifacts/ticker=<TICKER>/` the three result files
`<TICKER>_parameters.json`, `<TICKER>_model_evaluation.json` and
`<TICKER>_strategy_evaluation.json`, the README, and `<TICKER>_score_response.json`,
the answer to the search's question until the next turn spends it; in the trials
store, the asset's partitions of
`hpo_trials` and `score_trials`. Beside them the layer reads the feature layer's
contract `<TICKER>_catalogue.json` and the catalogue partitions it names, the
`bars` partitions, the asset's partition of `ohlcv_1m_canonical` — the market
object every stage reads — and, once a hand has promoted them,
`<TICKER>_feature_set.json` and `<TICKER>_barriers.json`. The data files are
regenerable; `<TICKER>_parameters.json` and `<TICKER>_README.md` are tracked,
beside the serpentine search's profile, state and ledger and the promoted state
that `module_features` writes, because they are what makes the rest readable —
and reproducible: the parameters are tuned for the state they were searched
under, so they travel together — and none carries a timestamp, so an unchanged
experiment reproduces them byte for byte. Every JSON is canonical (sorted keys,
numpy scalars converted) and carries **only what it computed** — no provenance
envelope, no hashes. The settings a run used are `module_ml/config.py` at the
commit that ran it — the commit is the record, `ml_status.json` publishes its
`CONFIGURABLES` records beside the assets, and the parameters file carries only
what the search chose. The experiment is identified once, globally, in
`store/status/ml_status.json`: research window and seed.
Library versions are pinned once, in `requirements.txt`. Runs are reproducible
by construction — fixed seed, `nthread = 1`, pinned versions — and that claim
is not backed by a hash gate, because a gate proves the metadata, not the
mathematics. No booster is persisted: nothing in this repo performs inference,
so the numbers are the product.

Module layout — four runtime modules, in the order the data moves, and
`module_skills`, the canon, whose one sub-module measures the tree and joins no
dataflow of the chain: `module_data` (sources → normalised raw 1m → the venue
families and the canonical family, one partition per asset) · `module_features`
(the bars of the register, the feature catalogue and the serpentine search —
`module_features/skills/`) · `module_ml` (this document) · `module_monitoring`
(presentation of what each module measured about itself and of the dates of the
crawler's reports, and the server). Inside `module_ml`: `module_ml/config.py`
(the frozen constants of the research layer and its `CONFIGURABLES` records — the
window and the folds its own, the register and the grid read per asset from the
feature layer's contract, `<TICKER>_catalogue.json`) · `module_ml/validation.py`,
`module_ml/model.py` (pure numpy / xgboost kernels) · `module_ml/dataset.py`
(artifact IO: X/Y loading, canonical JSON, its own parquet writer — twice by
extraction, identical in `module_features/dataset.py`) · `module_ml/labels.py`,
`module_ml/hpo.py`, `module_ml/train.py`, `module_ml/strategy.py`,
`module_ml/status.py` (the stages of the chain,
`python -m module_ml.<stage> --tickers <TICKERS>`) · `module_ml/score.py` (the
stage outside the chain that answers the serpentine search's requests,
`python -m module_ml.score --tickers <TICKERS>`).
Constant convention: **experiment-semantic constants live in
`module_features/config.py` and `module_ml/config.py` — what an operator may set
as a record of `CONFIGURABLES`, a constant of the method below the block;
implementation constants** (chunk sizes, the equity-curve stride — daily in the
artifact, weekly on the page: seven daily points) **may stay local to their
module**. The canonical series is gated where it is read:
`labels.load_research_1m` asserts the full 1m grid inside the research window,
per asset; `data-ingest` writes one asset's partitions at a time.

## 11. Running the layer: one asset per process

Every stage takes `--tickers`, so the chain parallelises the only way an
experiment with frozen thread caps may — **externally**, one asset per
process. The fan-out's width is `JOBS` in the root Makefile, how many assets one
stage runs at once, one one-off container each: 1 by default, set by hand on the
make line with `JOBS=n` — `make ml-hpo JOBS=2`. No width is measured and none is
written for a machine: the hand that widens a run answers for the memory of `JOBS`
containers side by side. `features-bars`, `features-catalogue`, `ml-labels`,
`ml-hpo`, `ml-train`, `ml-strategy`, `features-serpentine-turn`, `ml-score` and the
loop of `features-serpentine-search` fan out by it; `data-ingest` stays at one asset
at a time, and the three status stages run once over the basket.

Thread caps stay at one — `nthread = 1`, `OMP_NUM_THREADS = 1` — for the
reason `DETERMINISM-THREAD-CAPS-FROZEN-AT-ONE` (`module_skills/skill_determinism.md`) states. The hyper-parameter search is
CPU-bound and one asset's study is sequential by construction, so the wall-clock
floor of `ml-hpo` is the slowest single asset.

Rerun only what a change actually invalidates — the searches are the expensive
stages, and most edits do not touch them:

| what changed | what to rerun |
|---|---|
| the canonical series (`make data-ingest`) | everything, from `features-bars` |
| a record of `CONFIGURABLES` in `module_ml/config.py` | what the record's own `requires_rerun` names |
| a feature definition offered but not in the default set, within the catalogue's warm-up | `features-catalogue features-status ml-status` |
| a feature definition entering the default set | `features-catalogue features-status ml-hpo ml-train ml-strategy ml-status` |
| a feature definition that widens the catalogue's warm-up | everything from `features-catalogue`: the decision grid starts later, so `ml-labels` and every stage after it |
| the research window — `RESEARCH_START_UTC` and `RESEARCH_END_UTC` of `module_features/config.py` and the first and last of `FOLD_BOUNDS_UTC` here, which must agree | everything, from `features-bars` |
| the validation fold ids | `ml-hpo ml-train ml-strategy ml-status` |
| a strategy rule | `ml-hpo ml-train ml-strategy ml-status` — the study's objective is the strategy's path CAGR |
| a serpentine search (`make features-serpentine-search`) | `features-status` — its proposals reach the page |
| a promotion (`make features-serpentine-search-promote`) | `ml-all` for the asset — run by the promotion itself — then `features-status`, whose search block then reads the recorded search as no longer current |
| the monitoring payload | `ml-status` |

A recorded serpentine search compares its inputs — the window, the seed and the
warm-up, `best_params`, the catalogue's columns, the asset's own state, its
profile and the beam width — by equality at every turn, and starts over by itself
when one of them has moved. What it evaluates with besides — the folds, the
label's barrier scale, the study's counts and space, the cost, the threshold grid,
the trade floor, the strategy's rules — it does not compare:
after a change of one of them a hand removes the asset's search with
`make features-serpentine-search-reset ASSET=<TICKER>` and runs it again, so that
no trial of another experiment is read as a cache hit.

This table is the layer's rebuild condition, held in a document a reader applies
rather than in a stage: what decides that an asset's artifacts are stale stays
separate from the stages that rebuild them — the rebuild condition
`module_skills/skill_pre_aws_solution.md` keeps separable.

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
by it: `source_switch_count` and `rel_divergence` — its 99th percentile and its
maximum — are published per asset in `data_status.json` precisely so the effect is
visible and countable.

Known limitations: no regime-conditional gating, a per-asset feature set
chosen by the serpentine search (§ 4) rather than learnt, no CUSUM event sampling,
no meta-labelling, no fractional differentiation, fixed costs, unit position
sizing. The class distribution is dominated by `y = 0` — at the geometry of
`START_BY_COORDINATE_DEFAULT` most events reach the vertical barrier before either
horizontal one — reported per asset, not resampled.

**A move has to clear the noise of its own pass, on every fold at once, and in the
recorded BTC search none does.** Under the calibrated gate of § 4 — a profile that
carries σ — BTC's start state stands at fold Calmar ratios of **−0.67, −0.73 and
−0.11**, and the search accepted **no** move: 31 scored states in one round, its
one study offering no candidate, no child of the five families clearing the gate,
and so no proposal
(`store/assets_artifacts/ticker=BTC/BTC_serpentine_search.json` and its ledger).
That is a correct result of the calculator, not a failure of it. The σ BTC's
profile carries was measured off the ledgers of earlier calibration runs, which
this tree does not carry. A search that clears the margin can still
stop short: every move is one coordinate, so an improvement that needs several
coordinates changed at once is out of its reach. That is a property of this
geometry, written down and not solved here. Whether the answer is a different
fold measure, a tolerance, or a champion that is not the beam leader is a
question for the research phase — deciding it now would be choosing a selection
rule by the result it gives on one asset, which is the thing this layer exists to
avoid.

**The phase this layer is in.** What is being built here is the correctness of
the machine, not a result from it: every stage has to answer like a calculator —
the same input to the same bytes, no number arrived at by a path nobody can name,
no constant inherited from a library default. Numbers this layer produces now are
evidence that the machine is right, not findings about the market, and nothing in
them is to be read as one. The palette of features and the compute the search is
given are the next thing to grow, on a larger machine; the artifacts worth keeping
are made there, once the machine is right. That is why § 7's counts are
activation values and say so: they are large enough that the sampler models and
every gate is evaluated on every study — the method runs whole, which is what
this phase has to show — and they are not a choice of how much searching the
research needs. That choice is calibration, made on the larger machine as a new
experiment, where a run's length is not the constraint either.

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
| [12] | Lundberg, S. M., Erion, G., Chen, H., DeGrave, A., Prutkin, J. M., Nair, B., Katz, R., Himmelfarb, J., Bansal, N., Lee, S.-I. (2020). From local explanations to global understanding with explainable AI for trees. *Nature Machine Intelligence*, 2(1), 56–67. doi:10.1038/s42256-019-0138-9 — SHAP values of a tree ensemble |
