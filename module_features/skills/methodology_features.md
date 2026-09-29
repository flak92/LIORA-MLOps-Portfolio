# Methodology — the feature catalogue on the canonical series

Per asset, independently, on the one market object the research layer studies: exact bars of the
canonical 1m series on every timeframe of the register, and the feature catalogue evaluated on each
of them, aligned to the decision grid — at each decision timestamp a feature is read from the last
bar of its timeframe that has closed, never from one still open. The rules — the tokens, the
registers, the names, the catalogue record, the warm-up, the two families and the contract — are
`skill_feature_taxonomy.md`, each cited here by its `rule_id`; the definitions are here, equation by
equation, with how a feature id is read off its computation and why the rules are what they are.
The serpentine search that chooses an asset's feature set and barrier geometry from them is this
module's own: its rules are `module_features/sub_module_serpentine_search/skill_serpentine_search.md`,
its mathematics § The serpentine search. This page is a reference for a human and holds no rule of
its own. *The repository shows the destination, not the road*: the two guards are the finiteness
assert of `catalogue.build_catalogue` and the causality assert of `indicators.asof_index`.

## The register

The hierarchy is the experiment's literal, `HIERARCHY_TIMEFRAMES`, a CONFIGURABLES record of
`config.py`, finest first: one partition of `bars` and one of `catalogue` per entry, the coarsest
entry the trend gate's. `DECISION_TIMEFRAME`, the record beside it, is the grid the decisions, the
labels and the strategy stand on. The duration and the slot of each token are read off the token
(`timeframe_duration_ms()`, `timeframe_slot()`). The values of both records stand in the records,
which `features_status.json` publishes (`configurables`), and it publishes, per timeframe, its
duration, its bars per UTC day, its ratio to the level below and its slot (`catalogue.timeframes`).
The slot travels in the contract and in no file name: a partition names its timeframe as
`timeframe=<tf>`.

A token enters the hierarchy on two conditions (`FEATURE-TAXONOMY-A-TIMEFRAME-TOKEN-DIVIDES-THE-DAY`).
Its duration is a whole multiple of the decision timeframe's and divides one UTC day: a bar opens on
a multiple of its duration from the epoch, so only such a token's bars close on UTC midnight and on
a decision — a week or a month would need an anchor the token does not carry. And adjacent entries
keep a ratio of at least three, because two levels closer than that sample the same price movement:
the triple-screen hierarchy (`module_ml/skills/methodology_ml.md` § 13 [10]). Everything that reads
the hierarchy is the experiment — the decisions stand on one of its entries, the trend gate reads
its coarsest and the strategy's agreement counts over all of them — so a new token is a new
experiment (`README_module_features.md` § Extending).

Bars are exact UTC-aligned aggregations of the canonical 1m series inside the frozen research
window, each bar opening on a multiple of its duration from the epoch — O first, H max, L min, C
last, V sum, plus `ffill_bars` and `zero_volume_bars`, the forward-filled and the valid no-trade
minutes inside each bar, carried up for a reader and read by no later stage; the first and the last
minute are chosen by timestamp (`arg_min` / `arg_max`), never by row order, so the aggregation is
deterministic — written by `bars.py` as the asset's partitions of the `bars` family,
`bars/ticker=<TICKER>/timeframe=<tf>/bars.parquet`, one per entry of the hierarchy, with the
family's `bars/schema.json` beside them (`FEATURE-TAXONOMY-TIMEFRAME-ARTIFACTS-FOLLOW-THE-REGISTER`).
An aggregate is a native bar of its token — the minutes a venue's own candle of that token spans,
combined the same way — and not a resample.

## The kernels

Recursions run as explicit loops; rolling statistics use `sliding_window_view`; values inside a
window's lookback are NaN, the exponential smoothing is finite from its first bar, and the recursive
mean from its n-th. Every token is the word of its operation: the popular name an operation answers
to is provenance and lives in the `historical_aliases` of its record in `indicators.py`, never in a
name.

    exponential_smoothing_t = e_{t−1} + α (x_t − e_{t−1}),  α = 2 / (n + 1),  e_0 = x_0          SPAN n
    recursive_mean_t        = w_{t−1} + (x_t − w_{t−1}) / n,  seeded with the mean of the first n  SMOOTHING_PERIOD n
    true_range              = max(high − low, |high − prev close|, |low − prev close|);
                              the first bar has no previous close, so it is its own
    rolling_mean            = mean of the trailing n bars                                        LOOKBACK n
    rolling_standard_deviation = sample standard deviation of the trailing n bars                LOOKBACK n
    rolling_standard_score  = (x − mean_n(x)) / sd_n(x),  sample sd                              LOOKBACK n
    rolling_range_position  = (close − min_n(low)) / (max_n(high) − min_n(low))                  LOOKBACK n
    relative_change         = close_t / close_{t−n} − 1                                          LOOKBACK n
    recursive_mean_gain_share = 100 − 100 / (1 + R(gain) / R(loss)),  R the recursive mean,
                              gain = max(Δclose, 0), loss = max(−Δclose, 0); the first bar is NaN —
                              the change grid realigned to the price grid                        SMOOTHING_PERIOD n
    recursive_mean_upward_movement_share = 100 · R(+DM) / (R(+DM) + R(−DM)),
                              +DM = Δhigh where Δhigh > −Δlow and Δhigh > 0, else 0;
                              −DM = −Δlow where −Δlow > Δhigh and −Δlow > 0, else 0              SMOOTHING_PERIOD n
    recursive_mean_directional_movement_imbalance = R( 100 · |R(+DM) − R(−DM)| / (R(+DM) + R(−DM)) ),
                              the outer recursion seeded at the first bar the inner one has a value,
                              because a mean seeded over a warm-up is NaN for good               SMOOTHING_PERIOD n
    rolling_volume_weighted_mean = Σ_n(close · volume) / Σ_n(volume)                             LOOKBACK n
    rolling_volume_weighted_close_location = Σ_n(location · volume) / Σ_n(volume),
                              location = ((close − low) − (high − close)) / (high − low)         LOOKBACK n
    rolling_money_flow_gain_share = 100 · Σ_n(rising flow) / Σ_n(rising flow + falling flow),
                              typical price = (high + low + close) / 3, flow = typical price × volume,
                              rising or falling with the typical price                           LOOKBACK n
    cumulative_signed_volume = Σ sign(Δclose) · volume,  0 at the first bar
    logarithmic_volume       = log1p(volume)

An operation that divides names the value it takes where its denominator is zero, and takes it after
the division rather than guarding before it, so a NaN that came from somewhere else is not quietly
turned into a number (`FEATURE-TAXONOMY-A-ZERO-DENOMINATOR-HAS-A-NAMED-NEUTRAL`). The value follows
the semantics of what the operation returns:

| operation | denominator that vanishes | the value it takes | why that value |
|---|---|---|---|
| `recursive_mean_gain_share` | no gain and no loss | 50 | a share with nothing on either side is the middle of its 0–100 range; a zero loss with a positive gain gives 100, the share's own ceiling |
| `recursive_mean_upward_movement_share` | no movement either way | 50 | the same share, the same middle |
| `rolling_money_flow_gain_share` | no flow either way | 50 | the same share, the same middle |
| `recursive_mean_directional_movement_imbalance` | no movement either way | 0 | the modulus of a centred magnitude: no imbalance is none |
| `rolling_volume_weighted_close_location` | a window of no volume, or a bar of no range | 0 | a signed location centred on the middle of its bar |
| `relative_change` | a zero starting price | 0 | a signed change against nothing is no change |
| `rolling_standard_score` | a zero standard deviation | 0 | a standardised value with no dispersion sits on its own mean |
| `rolling_range_position` | a flat range | 0.5 | a position inside a range that has collapsed is the middle of it |
| `rolling_volume_weighted_mean` | a window of no volume | the unweighted mean of the same window | equal weights say what volume no longer can — a fallback of the kernel, not of the definition that reads it |
| `over` | a zero denominator | 0 | the composition operator, stated here with the kernels it composes |

`over` is a ratio that is 0 where the denominator is 0; `centered` maps a bounded term to [−1, 1] as
(x − (low + high) / 2) / ((high − low) / 2), reading the `output_range` of the term's own indicator —
a 0-to-100 share gives (x − 50) / 50.

The record of each indicator in `INDICATORS` carries what its equation implies
(`FEATURE-TAXONOMY-A-REGISTER-IS-RECORDS-BESIDE-THEIR-KERNELS`): the bar columns it reads when its
inputs are fixed, whatever series its term names, and its range when that range is bounded — the
three shares and the directional imbalance 0 to 100, `rolling_range_position` 0 to 1,
`rolling_volume_weighted_close_location` −1 to 1. A bounded indicator is the one kind of term a
normaliser is written on (`FEATURE-TAXONOMY-A-NORMALISER-NEEDS-A-BOUNDED-TERM`).

## The catalogue

The twenty-one feature definitions as of this commit. A definition is one record of
`FEATURE_CATALOGUE` (`config.py`): its terms, the operators that compose them, an optional
normaliser, its range, the timeframes it is offered on, its tier, the popular names it answers to
(`historical_aliases`, provenance, never a key or a column), and whether it belongs to the default
set. Its name, its effective history and its warm-up are read off that record —
`feature_definition_name()`, `definition_effective_history_hours()`, `definition_warmup_bars()` —
and `features_status.json` publishes the whole register with the derived numbers beside each
definition, the effective history in hours on every timeframe it is offered on. The effective
history is the longest parameter the definition reads — a window's window, a recursion's span or
period, the bars carrying most of its weight: 1 − (1 − α)^n of it, about 86 % for an exponential
smoothing (α = 2 / (n + 1), tending to 1 − e^−2) and 63 % for a recursive mean (α = 1 / n, tending
to 1 − e^−1) — given here in bars of the timeframe it is evaluated on; the warm-up is what its terms
need, in the same bars.

| definition | on the timeframe's own bars | range | effective history (bars) | warm-up (bars) | offered on | tier | default set |
|---|---|---|---|---|---|---|---|
| `exponential_smoothing20_minus_exponential_smoothing50_over_true_range_recursive_mean14` | (exponential_smoothing(close, 20) − exponential_smoothing(close, 50)) / recursive_mean(true_range, 14) | unbounded, dimensionless | 50 | 200 | every level | CORE | yes |
| `centered_recursive_mean_gain_share14` | (recursive_mean_gain_share(close, 14) − 50) / 50 | [−1, 1] | 14 | 56 | every level | EXTENDED | yes |
| `true_range_recursive_mean14_over_close` | recursive_mean(true_range, 14) / close | > 0, dimensionless | 14 | 56 | every level | CORE | yes |
| `rolling_range_position20` | (close − min(low, 20)) / (max(high, 20) − min(low, 20)) | [0, 1] | 20 | 20 | every level | CORE | yes |
| `logarithmic_volume_rolling_standard_score50` | rolling_standard_score(log1p(volume), 50) | dimensionless | 50 | 50 | every level | CORE | yes |
| `rolling_standard_score20` | (close − rolling_mean(close, 20)) / rolling_standard_deviation(close, 20) — the Bollinger reading: %b(20, 2σ) taken with the same sample σ (`ddof=1`) is rolling_standard_score20 / 4 + 0.5, and with Bollinger's population σ the slope is √(20/19) / 4 — an affine map either way, which a tree model is invariant to, so no %b column exists | dimensionless | 20 | 20 | every level | CORE | no |
| `close_minus_rolling_mean50_over_true_range_recursive_mean14` | (close − rolling_mean(close, 50)) / recursive_mean(true_range, 14) | unbounded, dimensionless | 50 | 56 | every level | CORE | no |
| `close_minus_rolling_mean200_over_true_range_recursive_mean14` | (close − rolling_mean(close, 200)) / recursive_mean(true_range, 14) | unbounded, dimensionless | 200 | 200 | the top level alone | CORE | no |
| `close_minus_exponential_smoothing20_over_true_range_recursive_mean14` | (close − exponential_smoothing(close, 20)) / recursive_mean(true_range, 14) | unbounded, dimensionless | 20 | 80 | every level | CORE | no |
| `rolling_standard_deviation20_over_close` | rolling_standard_deviation(close, 20) / close | > 0, dimensionless | 20 | 20 | every level | CORE | no |
| `relative_change10` | close_t / close_{t−10} − 1 | unbounded, dimensionless | 10 | 11 | every level | CORE | no |
| `close_minus_open_over_true_range_recursive_mean14` | (close − open) / recursive_mean(true_range, 14) | unbounded, dimensionless | 14 | 56 | every level | CORE | no |
| `high_minus_low_over_true_range_recursive_mean14` | (high − low) / recursive_mean(true_range, 14) | ≥ 0, dimensionless | 14 | 56 | every level | CORE | no |
| `centered_recursive_mean_upward_movement_share14` | (recursive_mean_upward_movement_share(high, low, 14) − 50) / 50 | [−1, 1] | 14 | 56 | every level | EXTENDED | no |
| `recursive_mean_directional_movement_imbalance14` | recursive_mean_directional_movement_imbalance(high, low, 14) | [0, 100] | 14 | 112 | every level | EXTENDED | no |
| `close_minus_rolling_volume_weighted_mean20_over_true_range_recursive_mean14` | (close − Σ₂₀(close · volume) / Σ₂₀(volume)) / recursive_mean(true_range, 14) | unbounded, dimensionless | 20 | 56 | every level | EXTENDED | no |
| `cumulative_signed_volume_rolling_standard_score50` | rolling_standard_score(cumulative_signed_volume, 50) | dimensionless | 50 | 50 | every level | EXTENDED | no |
| `rolling_volume_weighted_close_location20` | Σ₂₀(location · volume) / Σ₂₀(volume) | [−1, 1] | 20 | 20 | every level | EXTENDED | no |
| `centered_rolling_money_flow_gain_share14` | (rolling_money_flow_gain_share(high, low, close, volume, 14) − 50) / 50 | [−1, 1] | 14 | 15 | every level | EXTENDED | no |
| `exponential_smoothing8_minus_exponential_smoothing21_over_true_range_recursive_mean14` | (exponential_smoothing(close, 8) − exponential_smoothing(close, 21)) / recursive_mean(true_range, 14) | unbounded, dimensionless | 21 | 84 | every level | COMPOSITE | no |
| `exponential_smoothing21_minus_exponential_smoothing55_over_true_range_recursive_mean14` | (exponential_smoothing(close, 21) − exponential_smoothing(close, 55)) / recursive_mean(true_range, 14) | unbounded, dimensionless | 55 | 220 | every level | COMPOSITE | no |

One record of `FEATURE_CATALOGUE`, field by field — what a record must carry is
`FEATURE-TAXONOMY-A-CATALOGUE-RECORD-CARRIES-EVERY-FIELD`; what a fault in a field breaks is this:

| field | what it holds | what a fault breaks |
|---|---|---|
| `terms` | the terms, each `("<indicator>", <parameter_bars>)` on `close`, `("<series>", "<indicator>", <parameter_bars>)` on another series or `("<series>",)` bare; the first names the definition and is the term a normaliser reads | an indicator outside `INDICATORS` fails the import of `config.py`, which reads every term's warm-up; a series outside `SERIES_KERNELS` and the bar columns fails in `catalogue.py` |
| `operators` | a key of `OPERATORS` between each pair of terms, one fewer than the terms | a key outside `OPERATORS` fails in `catalogue.py`; a missing operator drops the terms after it from the name and the column alike — `zip` folds both — while the snapshot's `terms`, the warm-up and the effective history still count them |
| `normaliser` | optional: a key of `NORMALISERS`, applied last | a key outside `NORMALISERS`, or a first term without an `output_range`, fails in `catalogue.py` |
| `range` | the words the snapshot publishes for the definition's range | `features-status` fails on a record without it |
| `timeframes` | `HIERARCHY_TIMEFRAMES` or a slice of it | without the key the import of `config.py` fails; a token outside the hierarchy has no bars, is evaluated nowhere and fails `features-status` on its duration |
| `tier` | `CORE`, `EXTENDED` or `COMPOSITE` — how structurally flexible the definition is | `features-status` fails on a record without it |
| `historical_aliases` | optional: the popular names that denote the whole definition — provenance, never a key or a column | — |
| `definition_in_default_set` | `True` puts the column into every asset's X until a promotion — a change of the frozen experiment; `False` offers it to the serpentine search alone | without the key the import of `config.py` fails |

The warm-up a term needs is a multiple of its parameter, the `warmup_multiple` of its record in
`INDICATORS`: a rolling window is counted settled after one window of bars, a recursion after four
times its parameter and a recursion of a recursion after eight; a window over changes adds the one bar
before it, its record's `warmup_offset_bars`. The multiples are a convention of
the register: the one guard, the finiteness assert, checks that a value exists, not how much weight
a recursion's seed still carries. The experiment's `WARMUP_TOP_TIMEFRAME_BARS` is the widest of
them all, read off the catalogue and counted in bars of the top timeframe — today the 220 bars of
`exponential_smoothing55`'s four spans — so a definition with a longer memory raises it by itself
and no second number is written to follow it. Decision rows before `WARMUP_END_MS`, the research
start plus that many bars of the top timeframe, are excluded everywhere
(`FEATURE-TAXONOMY-WARM-UP-ROWS-ARE-EXCLUDED`); `features_status.json` publishes the date
(`catalogue.warmup`). The boundary is inclusive: `asof_index` takes the last bar closed at or before
the decision, so the first decision reads the top timeframe's `WARMUP_TOP_TIMEFRAME_BARS`-th bar the
moment it closes. A window of n bars is finite from its n-th bar; a window over changes —
`relative_change`, `rolling_money_flow_gain_share` — only from its (n + 1)-th, since its first change
is taken off the bar before the window, which `warmup_offset_bars` counts.

The nesting criterion holds the longest effective history offered on a level below the shortest
offered on the level above: a long window on a fine level spans a coarser level's history in many
more bars, which is how a level smuggles in another level's regime — hence
`close_minus_rolling_mean200_over_true_range_recursive_mean14` is offered on the top level alone. It
is a criterion the catalogue's author reads, published and asserted by no stage
(`FEATURE-TAXONOMY-EFFECTIVE-HISTORIES-ARE-SHOWN-NOT-ASSERTED`): `features_status.json` publishes
both numbers for each adjacent pair (`catalogue.nesting`). This catalogue keeps it between the finest
level and the one above it and breaks it between that level and the top: the longest history
offered on the middle level,
`exponential_smoothing21_minus_exponential_smoothing55_over_true_range_recursive_mean14`, outlasts
the shortest on the top, `relative_change10`. The author decides what to offer; the importance
tables tell what it was worth.

The five definitions of the default set lead the catalogue: on every timeframe they are offered on
they are the columns of the frozen experiment, in the order it stacks them
(`DEFAULT_FEATURE_COLUMNS_BY_TIMEFRAME`), and an asset's model sees them until a promotion writes
`<TICKER>_feature_set.json` (`FEATURE-TAXONOMY-WITHOUT-A-PROMOTION-THE-DEFAULT-SET-HOLDS`). The
column order is what the model samples by position, so a definition is appended to the catalogue
and never inserted into it (`FEATURE-TAXONOMY-A-DEFINITION-IS-APPENDED`). The strategy reads one
definition by name on every timeframe, whatever the set holds — `TREND_GATE_FEATURE_DEFINITION` of
`module_ml/config.py`, the catalogue's first — because the hierarchy gate is a rule of the strategy,
not a feature the model chose; that definition is offered on every level.

`logarithmic_volume_rolling_standard_score50` measures the activity of the **canonical observation
process**, not venue-independent market activity: the sources differ in liquidity level, so a source
switch may induce a volume-level discontinuity. Normalising per source would push provider knowledge
back below the ingest boundary, so the limitation is stated rather than engineered away.
`rel_divergence` — the two venues' closes' divergence over their mid — measures the observation
process, not the asset: it says how far two recordings of one price disagree, which carries no
information about where the price goes, so it is a data-quality signal and never a feature [11].
Cross-timeframe trend agreement is **not** a feature: the count of timeframes whose trend sign
matches a given side is a deterministic function of columns the model already has, so it can only
add representation, never information; the agreement lives where it is used, in the strategy gate
(`MINIMUM_AGREEING_TREND_TIMEFRAMES`, `module_ml/config.py`). Both are
`FEATURE-TAXONOMY-A-QUALITY-SIGNAL-IS-NOT-A-FEATURE`.

The families the catalogue draws on, with the keys of the reference list of
`module_ml/skills/methodology_ml.md` § 13 — one list for the research layer: smoothed level and the
distance to it [1][3], the balance of smoothed gains and losses [1][7], the true-range scale [1][5],
rolling location inside a window [2], the activity anomaly [1][6], directional movement and its
imbalance, and price-conditioned volume flow.

## The feature id

The chain, smallest part first: a **term** — a series, or an indicator with its one parameter; the
terms of one timeframe composed into a **feature definition**; the definition bound to a timeframe
as a **feature**, whose id is the column of X and the key of an importance; the features an asset's
model sees as its **feature set**. The smallest part has one meaning and every larger structure is
composed deterministically from smaller ones, so any column can be taken apart and made to answer
what information, from which bars, over what history, with which parameters.

A feature id says what was computed: which series went in, which operations were applied to them,
with which parameters, normalised how, and on which timeframe. The same computation always carries
the same id, and one definition never carries two (`FEATURE-TAXONOMY-A-NAME-IS-DERIVED`); read with
this page, an id is enough to rebuild the computation without knowing the popular name of the
indicator it resembles.

    <feature id>  = [<normaliser>_]<term>{_<operator>_<term>}_<timeframe>
    <term>        = [<series>_]<indicator><parameter>  |  <series>

`feature_definition_name()` (`config.py`) reads a definition's name off its record, and
`feature_id()` appends the timeframe. A term's series is written only when it is neither `close` nor
fixed by the indicator itself: an indicator whose register record names its `inputs`
(`rolling_range_position` reads close, high and low) carries no prefix (`term_name()`,
`FEATURE-TAXONOMY-A-TERM-IS-ITS-TOKEN-AND-ONE-PARAMETER`). A bare series inside a definition —
`close` in `close_minus_rolling_mean50_over_true_range_recursive_mean14` — is written because it is
a term of the composition, not the input of an indicator. An id is derived in four steps: the
expression is written out; it is cut into terms at its composition operators; each term becomes its
series, its indicator token and its parameter; `feature_id()` joins them and appends the timeframe.

Every number in an id counts bars of the id's own timeframe: `rolling_range_position20_1d` spans
twenty daily bars, `rolling_range_position20_1h` twenty hourly ones. Nothing else is written into an
id — not the decision grid, not the label horizon, not the asset, not a category word, not a
wall-clock span (`FEATURE-TAXONOMY-AN-ID-NAMES-ITS-COMPUTATION-ALONE`). A partition's column is the
definition's name alone, because the partition's path holds the timeframe; the id with its suffix
is the column of X and the key of an importance. The one
copy downstream is `module_ml`'s registered, identical `feature_id(definition_name, timeframe)`,
which composes a name it received in `<TICKER>_catalogue.json` with its timeframe and translates
nothing.

- (exponential_smoothing(close, 20) − exponential_smoothing(close, 50)) / recursive_mean(true_range,
  14) on 8h bars — two terms on close joined by `minus`, over the true-range term — is
  `exponential_smoothing20_minus_exponential_smoothing50_over_true_range_recursive_mean14_8h`.
- (close − min(low, 20)) / (max(high, 20) − min(low, 20)) on daily bars is
  `rolling_range_position20_1d`: the inputs are fixed by the indicator, so no prefix is written.
- rolling_standard_score(log1p(volume), 50) on hourly bars is
  `logarithmic_volume_rolling_standard_score50_1h`: the series is neither close nor fixed by the
  indicator, so it prefixes the term.

A definition across timeframes is reserved and not written: it would carry a timeframe on every term
and no suffix, and be composed on the decision grid after each term is aligned. Until one exists, a
relation across timeframes stays a rule of the strategy (`module_ml/skills/methodology_ml.md` § 9;
`FEATURE-TAXONOMY-A-DEFINITION-STAYS-ON-ONE-TIMEFRAME`).

## The serpentine search

The serpentine search is a hand's research over one asset's state Θ, outside the chain
(`sub_module_serpentine_search/`; how it runs is `README_module_features.md` § Its sub-modules, its
rules `module_features/sub_module_serpentine_search/skill_serpentine_search.md`, each cited below by
its `rule_id`). A state is the columns of a feature set per timeframe, the four barrier coordinates —
the multiplier the label's barriers stand at, the horizon they stand for, the take-profit and the
stop a trade leaves at — and the hyper-parameter point `best_params` (`theta()`); its key is its own
canonical JSON text, so two states are equal exactly or not at all (`state_key()`,
`SERPENTINE-SEARCH-A-STATE-IS-KEYED-BY-ITS-CANONICAL-TEXT`). A trial is one scored
state: `ml-score` fits the three boosters before F2, F3 and F4 — a state of the same question that
differs only in the trade's exit shares those fits (`module_ml/score.py:57–77`) — predicts each fold
and runs the strategy's threshold selection on the predictions (`module_ml/score.py:145–191`), and
the answer comes back as `<TICKER>_score_response.json`. The turn computes no metric of a state: every number a
gate, a ranking or a proposal reads comes off an answer (`SERPENTINE-SEARCH-IT-COMPUTES-NO-METRIC`,
`SERPENTINE-SEARCH-THE-EVALUATOR-IS-A-FILE-AWAY`). File addresses below without a file name
are `sub_module_serpentine_search/serpentine_search.py`'s.

A round is `ROUND_SCHEDULE` (the sub-module's `config.py`) read in order: the barrier loop's `trade`
family, which moves the take-profit and the stop one grid point down or up; its `label` family, which
moves the label's multiplier and horizon; the feature-set loop's `forward` family, every state with
one more admitted column, in timeframe and catalogue order; its `backward` family, every state with
one column fewer, never the last; and the hpo loop's `study` family, one study per beam parent,
whose best admissible point that beats the parent comes back as its candidate
(`module_ml/hpo.py:205–220`) — last, so the turn that reads its answer ends the round
(`SERPENTINE-SEARCH-HPO-ENDS-THE-ROUND`). A profile searches the loops it names and the round skips
the rest.
Each family expands the beam once, seeded by the beam the family before it left, and a state already
in the ledger is looked up, never scored again.

### 1. The objective

A state's objective is the triple `state_objective` (:64–70), compared most significant first: the
CAGR of the chained validation path, then that path's Calmar ratio, then its profit factor, where a
path without a losing trade has no profit factor (`module_ml/validation.py:106–112`) and counts as
+∞. The path chains F2, F3 and F4 — each fold's 1m equity scaled by what the folds before it settled
at — and its CAGR is the product of the three folds' final equities annualised over their minutes
(`validation_path_cagr`, `module_ml/strategy.py:238–246`; `validation_path_block`, :257–279 there).
A trial stands at the entry edge threshold the one selection rule picks for it
(`module_ml/strategy.py:304–352`): the point of `ENTRY_EDGE_THRESHOLD_GRID` maximising that same
CAGR among the points that clear the trade floor on every validation fold, ties to the smaller
threshold. `ranking_key` (:164–168) orders trials by the objective, descending, then by the smaller
column count, then by the earlier trial.

### 2. The conditions every comparison shares

Two states are compared because both were scored under the same conditions. The same data: the
canonical 1m series inside the frozen research window, read only there
(`module_ml/labels.py:71–72`), a label kept only where its event's horizon ends inside it (:186
there). The same folds: WARMUP | TRAIN | PURGE | OOS | final holdout (`module_ml/config.py:211`,
`module_ml/validation.py`), each validation fold trained on the folds before it with its training
rows purged at the fold's start and scored on the rows whose horizon fits the block; F5 enters no
trial. The same cost, `EXECUTION_COST_RATE_PER_TRADE_SIDE`, on the entry and the exit of every trade
(`module_ml/strategy.py:166`), and the one seed of every fit and study, `SEED`. The same
annualisation: a CAGR over the path's own minutes in a 365-day year (`module_ml/validation.py:91–94`),
the Sharpe ratio reported beside it by the periods per year of the decision bar
(`module_ml/strategy.py:211–215`). The same causality: every feature value read from the last closed
bar of its timeframe (`indicators.asof_index`, `module_features/indicators.py:200`). A move of the
label's horizon changes the supervised population itself — a longer horizon drops more of each
fold's tail — so parent and child are scored on row sets that differ at the edges, on the same
calendar and the same capital: a property of the coordinate. These conditions hold inside one
experiment and nowhere else (§ One search, one experiment).

### 3. Progress and stopping

Each family leaves the beam `top_beam(children + beam)` (:498–499): the best
`SERPENTINE_SEARCH_BEAM_WIDTH` distinct states by the ranking key, among the children that cleared
the gate and the parents they came from. The parents stay in the race, so a family that finds
nothing better keeps what it had, and the leader of the beam — the champion, moved once at the end
of the round — never ranks worse than it did: the best ranked result never gets worse
(`SERPENTINE-SEARCH-THE-BEAM-KEEPS-ITS-PARENTS`).

`search_converged = not round_accepted` (:512): the search stops after a round in which no family of
the executed schedule changed the beam. From that beam another round would offer the same states
and, every fit and study being seeded, receive the same answers, so the search stands at a fixed
point of its own schedule and gate. That is not a global optimum, and not a local optimum of the
objective alone: a neighbour that raised the CAGR by less than the margin, or not on every fold, was
offered and refused, and a child that cleared the gate but ranked below a full beam was not kept
(`SERPENTINE-SEARCH-CONVERGED-MEANS-NO-FAMILY-MOVED-THE-BEAM`).

### 4. The thresholds

`is_gate_cleared` (:73–102) keeps a child only when three conditions hold against the parent it came
from (`SERPENTINE-SEARCH-A-MOVE-CLEARS-THE-NOISE-OF-ITS-PASS`):

- its threshold constraint is met — some threshold cleared `MINIMUM_TRADES_PER_VALIDATION_FOLD`
  trades on every validation fold (`module_ml/strategy.py:325–328`); a fallback row, scored at the
  grid floor nothing qualified for, is refused before it is compared;
- its Calmar ratio, `SELECTION_FOLD_MEASURE`, is strictly higher than its parent's on every
  validation fold F2–F4 — the fold is the unit of robustness;
- its CAGR beats its parent's by more than k(n)·σ, σ the asset's noise sigma drafted into the
  profile and n the candidates of its pass: every state the family offers from the beam, cache hits
  included (:465–467), or every point the pass's studies drew, pruned and completed alike
  (:439–442).

A calibration run — the profile's `path_cagr_noise_standard_deviation` null — passes no margin: a
child must be strictly better on the CAGR and on every fold, and a move that shrinks the state no
worse on either (:95–100). The barrier and hpo loops call every move `forward`. Inside a study,
`module_ml` already refuses a point that does not beat the parent on every fold at its own threshold
or on the path's CAGR; the turn's gate then adds the margin.

The fold condition compares ratios. Where a fold's CAGR is negative, its Calmar ratio — the CAGR over
the maximum drawdown (`module_ml/validation.py:97–103`) — rises toward zero as the drawdown deepens:
against a parent at −12% and a 24% drawdown (−0.5), a child at −12% and 48% (−0.25) clears the fold,
and a child at −8% and 12% (−0.67) does not. On a losing fold the condition reads the ratio, not a
smaller loss with a shallower drawdown.

The one proposal (`proposals_block`, :190–210) is the champion, as proposal 1, when its threshold
constraint is met, it is not the start state, no validation fold's Calmar ratio is below the start's,
and its CAGR beats the start's by more than k(N)·σ. N is the sum of `trial_count_by_loop`
(:222–224): the ledger's lines after the start in the loops that enumerate their moves, and every
point the studies drew — a study's candidate, itself a drawn point, counted once, as its line
(:457–459; `SERPENTINE-SEARCH-A-DRAWN-POINT-IS-COUNTED-ONCE`). A calibration run proposes nothing
(`SERPENTINE-SEARCH-ONLY-A-CHAMPION-ABOVE-THE-NOISE-IS-PROPOSED`).

These thresholds are this method's assumptions — the baseline it holds itself to — and not
conditions of correctness for every optimiser: another search could keep other moves and still be a
correct search.

### 5. The margin k(n)·σ is a heuristic

    rate(k, n) = P( max_i S_i − S_parent > k·σ ) = 1 − E_Z[ Φ(k + Z)^n ],   Z ~ N(0, 1)
    S = true value + σ·ε,  ε ~ N(0, 1) independent for the parent and each of the n candidates,
        every true value equal to the parent's

`false_exceedance_rate` (:112–116) is that chance: the best of n candidates beating a parent by k·σ
when none of them is truly better than it, the expectation a Gauss–Hermite quadrature on a fixed node
count. `gate_threshold_multiple` (:119–130) finds the k(n) at which the chance is 5%
(`GATE_THRESHOLD_FALSE_EXCEEDANCE_RATE`) by bisection on a fixed bracket in a fixed number of
halvings, so one n gives one k on every machine; k grows with n.

σ is `path_cagr_noise_standard_deviation` (:143–161), read off the ledgers of calibration runs —
the last turn of one prints the estimate of its own ledger (:521–524), and a hand drafts the number
into the profile (`SERPENTINE-SEARCH-THE-NOISE-SIGMA-IS-DRAFTED`). A child
and the parent its `parent_trial_index` names form one pair when both met the threshold constraint
and the child was fitted on its own — a move of the trade's exit alone shares its parent's fits and
is left out — each pair of states once; σ is the median absolute deviation of the pairs' path-CAGR
differences × 1.4826 / √2, the factor that makes a normal sample's median absolute deviation its
standard deviation, over the √2 of a difference of two scores. The pairs are pairs of different
states, so σ holds the effect of each change as well as the variability of an evaluation; a state
scored twice scores the same, every fit and study being seeded.

k(n)·σ is therefore a margin that grows with the size of a pass — a heuristic, not a test. Its model
assumes independent normal noise of one size; the candidates of a pass are correlated, sharing a
parent and differing by one move, the search is adaptive, every parent having been selected itself,
and a pass over several beam parents compares each child with its own parent, which the expression
does not model. It gives no 95% guarantee against a false acceptance under this search, and a
sentence that claims one is false.

### What success is

The search succeeds when it computes, compares and decides correctly: every state scored under the
conditions of § 2, every gate, ranking and proposal applied as written, and the state file and its
ledger recording what happened. A positive trading result is not a condition of success: a move from
a path CAGR of −12% to −8% improves the objective and is kept when it clears the gate, and a champion
that still loses money is a correct result of a correct search. A search that accepts no candidate —
its champion the start state, its proposals none — is a correct result too.

### One search, one experiment

The data inside the research window and the evaluation settings are constant for a whole
experiment, and a serpentine search is one experiment. What the search records in its `inputs`
(`build_search_inputs`, :228–246) — the research window with the seed and the warm-up, the asset's
`best_params`, the catalogue's columns, the asset's active columns and barriers, the profile and the
beam width — is compared by equality at every turn, and a difference starts a fresh state and a
fresh ledger by itself (:392–397; `SERPENTINE-SEARCH-INPUTS-DECIDE-RESUME`). What the scores depend
on beyond those fields is not recorded: the canonical data inside the window, the catalogue's
values, and the records of
`module_ml/config.py` — the execution cost, the threshold grid, the trade floor, the hyper-parameter
budget and space, the inner bounds of the folds, the barrier's true-range timeframe and period.
After any change of data or configuration outside `inputs` — a CONFIGURABLES record of `module_ml`
such as `EXECUTION_COST_RATE_PER_TRADE_SIDE` or `HYPERPARAMETER_SEARCH_TRIAL_COUNT`, or new data —
first `make all ASSET=<TICKER>` recomputes the dependent artifacts, then
`make features-serpentine-search-reset ASSET=<TICKER>` removes the recorded search, and then a new
search starts: a line scored before the change is not a state of the new experiment, and a resumed
search would read it as a cache hit (`SERPENTINE-SEARCH-A-CHANGE-OUTSIDE-THE-INPUTS-NEEDS-A-RESET`).
