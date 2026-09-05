# Glossary — one concept, one name

*The repository shows the destination, not the road*: the register confirms; no check reads it.
Every concept below has exactly one name in the code, one key in the artifacts
and one label in the interface. Names that are standard
in the field (`fold`, `purge`, `embargo`, out-of-sample, Sharpe) appear as
confirmation; the rest of the concept column states what the name means.

## Validation and folds

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| one chronological segment of the research window — `F1`, the first, is trained on and never evaluated (`../module_ml/skills/methodology_ml.md` § 6) | `fold`, `fold_id` | `fold_2` … `fold_5` | `F2` … `F5` | split, period, chunk |
| the segment boundaries | `fold_bounds()`, `FOLD_BOUNDS_MS` | — | — | split_bounds |
| the folds used for the data-driven selection of model hyper-parameters, the entry edge threshold and, once a set is promoted, the feature set | `VALIDATION_FOLD_IDS` = (2, 3, 4) | `validation` | `F2`–`F4` | test folds, CV folds, "the folds that choose every parameter" |
| the fold that is only ever evaluated | `FINAL_HOLDOUT_FOLD_ID` = 5 | `final_holdout`, `final_holdout_fold_id` | `F5 — final holdout (out-of-sample)` | test, test set, locked test, final OOS |
| the evaluated block of a fold, and which one a prediction belongs to | `oos`, `oos_fold_id` | `oos_fold_id` (parquet column) | out-of-sample | test block, test period |
| dropping training events that overlap the evaluated block | `purge` — `event_end_ts <= oos_start` | — | purged | gap, buffer |
| a forced wait after the evaluated block — **width zero here**, forward chaining needs none | — (the field's term, carried by no identifier, because there is nothing to implement) | — | — | cooldown, post-test embargo |
| bars consumed before the first decision is allowed — the experiment's literal, in bars of the top timeframe of the register; what each term of the catalogue needs is shown beside it, never derived into the window | `WARMUP_TOP_TIMEFRAME_BARS` = 200, `WARMUP_END_MS`; `term_warmup_bars()`, `definition_warmup_bars()` | `warmup_excluded_decision_count`; `warmup.top_timeframe_bars`, `warmup_bars` of a catalogue definition | warm-up excluded; warm-up (bars) | burn-in; `WARMUP_4H_BARS` (a timeframe token in the name lies once the register grows) |

## Market object

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| the external minute-bar format the raw store is byte-compatible with | Lean — `module_data/lean.py` | — (the raw tree only) | — | QC, quantconnect-format, `lean` lower-case mid-sentence; a project-cased spelling of its tree |
| the studied series, and the only series below the ingest boundary | `ohlcv_1m_canonical` and its aggregates | — (tables of the asset's own DuckDB; no copy of the series is published) | canonical dataset | fused series, index, blended price |
| which asset a database holds | the file name, `<TICKER>_research_ohlcv.duckdb`, and nothing inside it | `symbol` — a key of data_status.json only | — | a `symbol` column in any table, a `WHERE symbol = …` predicate, a `GROUP BY symbol` |
| the timeframe hierarchy — the experiment's literal, finest first: every timeframe the repository builds from the canonical 1m series, the one definition the bars, the parquets, the catalogue's offered timeframes, the decision grid and the trend gate derive from (`../module_features/skills/skill_feature_taxonomy.md` § The timeframe register) | `HIERARCHY_TIMEFRAMES` = ("15m", "1h", "4h"), `module_features/config.py` | `catalogue.timeframes` — `timeframe`, `duration_ms`, `bars_per_day`, `ratio_to_lower`, `slot` | 15m / 1h / 4h | levels, LEVELS, a hierarchy derived from a dict, a second list of timeframes anywhere |
| the timeframe a decision is taken on — the experiment's literal beside the hierarchy | `DECISION_TIMEFRAME` = "15m" | `catalogue.decision_timeframe` | the decision timeframe (the register box) | DECISION_TF, `HIERARCHY_TIMEFRAMES[0]` written where the literal should be |
| how long one bar of a token lasts, and the token's file-name slot — both read off the token: the number and the unit | `timeframe_duration_ms()`, `timeframe_slot()`, `TIMEFRAME_UNIT_MS`, `TIMEFRAME_SLOT_FIELDS`, `TIMEFRAME_UNIT_SLOT_FIELD` — the unit's duration, the five slots of the sorting standard and the field a unit fills; `TIMEFRAME_DURATION_MS` and `TIMEFRAME_SLOT`, the two read off the hierarchy | `duration_ms`, `slot` | — | TF_MS, a duration or a slot written by hand per token |
| the timeframe whose last closed bar sets the barrier width of a label — an entry of the hierarchy, the label's own literal | `LABEL_BARRIER_ATR_TIMEFRAME` = "1h", `module_ml/config.py` | — | — | `"1h"` in a query or an assert |
| a data provider, above the ingest boundary only | `binance` / `bybit`, in `module_data` | `venues.*`, `binance_pct` / `bybit_pct` | Raw source | venue or exchange used below ingest |
| which provider a canonical minute came from | `source`, `source_switch_count` | `source_switch_count`; `source` is a database column, published only as the shares `binance_pct` / `bybit_pct` / `ffill_pct` | primary / secondary / ffill | — |
| a minute with no observed trade | `volume = 0`, `zero_volume` | `zero_volume_bars`; `zero_volume` is a database column | zero-vol | carried-forward price (true only of forward-filled minutes) |
| a synthesised continuity minute | `source = 'ffill'` | `ffill_bars` | ffill | gap, missing bar |
| quality columns that are never features | `binance_valid`, `bybit_valid`, `rel_divergence` | — (database columns; `rel_divergence` is published only as `relative_divergence_mean` / `relative_divergence_p99` / `relative_divergence_max`) | — | signal, feature |

## Event and sample

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| the moment a decision may be taken — close of the 15m bar | `decision_ts` | `decision_ts` | — | signal time |
| the candidate entry minute after the decision — an entry is permitted here, not guaranteed | `entry_ts` | `entry_ts` | — | fill time, first tradable minute |
| the canonical open of that minute | `entry_price` | `entry_price` | — | `p0` as an identifier (`P₀` stays in the equations) |
| the take-profit price of a long, the stop of a short | `upper_barrier` | `upper_barrier` | upper_barrier | `upper`, ceiling, band |
| the stop of a long, the take-profit of a short | `lower_barrier` | `lower_barrier` | lower_barrier | `lower`, floor, band |
| the vertical barrier, in minutes (240 = 16 × 15m bars) | `LABEL_HORIZON_MINUTES`, `LABEL_HORIZON_MS` | — | 240-minute horizon | HORIZON_BARS, W, H |
| the exclusive end of the event | `event_end_ts` | `event_end_ts` | — | exit time |
| the price that closes the event | `exit_reference_price` | `exit_reference_price` | — | exit_ref |
| how the event ended | `event_resolution` | `event_resolution`, `exit_counts.*` | upper_barrier / lower_barrier / vertical / ambiguous | reason, exit_reason |
| the four resolutions | `EVENT_RESOLUTION_{UPPER_BARRIER, LOWER_BARRIER, VERTICAL, AMBIGUOUS}` | `event_resolution` | — | bare 1 / −1 / 0 / 9 |
| the entry minute traded at all — knowable at `entry_ts`, may gate an entry | `entry_observable` | `entry_observable`; its complement is counted as `unobservable_entry_count` | unobservable entry | tradable, valid entry |
| the event can be classified — knowable only afterwards, never gates an entry | `label_valid` | `label_valid`; its complement is counted as `ambiguous_event_count` | ambiguous | masked |
| the supervised population: both of the above | `sample_valid` | `trainable_row_count`, `trainable_row_pct` | trainable rows | valid rows |
| how little an event overlaps its neighbours **within one population** — measured after the purge, never stored in Y | `average_uniqueness_weight()`, `train_weight` / `scoring_weight` | — | — | `weight` as a Y column, class weight |

`decision_ts`, `entry_ts` and `event_end_ts` are the three epoch-millisecond
columns spelled `_ts`, a contract with the parquets on disk; every new
epoch-millisecond key is `_ms`.

## Signal and strategy

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| the model's directional lean, `p_long − p_short` | `directional_probability_edge` | — | edge | `edge` as a code name |
| how much of that lean a signal must carry to be traded | `entry_edge_threshold` (τ) | `entry_edge_threshold` | τ (entry edge threshold) | `tau` as an identifier |
| the grid searched for it | `ENTRY_EDGE_THRESHOLD_GRID` | — | — | TAU_GRID |
| whether any threshold on the grid cleared the trade floor | `entry_edge_threshold_constraint_met` | same | `constraint met` (yes / fallback); `!` beside a fallback threshold | `tau_ok`, a name that says a constraint without saying which |
| the trade floor — a selection guardrail, not an acceptance gate | `MINIMUM_TRADES_PER_VALIDATION_FOLD` = 30 | — | — | MIN_TRADES, acceptance gate |
| how many timeframes must agree with the side | `MINIMUM_AGREEING_TREND_TIMEFRAMES`, `agreeing_trend_timeframe_count` | `minimum_agreeing_trend_timeframes` | at least `n` of `m` timeframes agree — both counts from the payload, the hierarchy's length among them | AGREE_MIN, n_agree, level |
| replaying the strategy over the canonical price path | `backtest()` | `<TICKER>_strategy_evaluation.json` | STRATEGY | live execution, exchange execution |
| the execution cost charged on entry and on exit | `EXECUTION_COST_RATE_PER_TRADE_SIDE` = 0.0006 | `execution_cost_rate_per_trade_side` | cost per side | costs_per_side, cost_per_side, fees |

The symbol τ may stay in equations and in table headers; its first use in any
document or on any page spells out `entry edge threshold`.

## Counts

Every count is `<what>_count`; a bare `n`, a bare plural (`gaps`) or an
adjective (`ambiguous`) names no number.

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| decisions on the 15m grid after the warm-up whose horizon still fits the research window — the labelled population, so it is short of the feature grid by the dropped tail | `decision_count` | `decision_count` | decisions | rows, `n` |
| rows a fold's metrics are computed on | `scored_row_count` | `scored_row_count` | scored | `n` |
| rows the model is fitted on, and the events purged before them | `training_row_count`, `purged_event_count` | same | trained on / purged | n_train, n_purged |
| rows in a prediction window | `window_row_count` | `window_row_count` | window | n_window |
| trades a fold produced | `trade_count` | `trade_count` | trades | n_trades |
| trials a search ran — the hyper-parameter search's, or the scored sets of the feature-set search | `trial_count` | `trial_count` | trials | n_trials |
| passes of the feature-set search — one forward move and one backward move over the champion | `pass_count` | `pass_count` | passes | rounds (the boosting rounds' word), iterations (the Map's word) |

## Data quality (data_status.json)

Written by `module_data/status.py`; every alias a scan publishes is the key it becomes.

| concept | artifact key | UI label | never |
|---|---|---|---|
| minutes a venue printed / the canonical grid holds | `row_count` | rows (`canonical rows` on the Pipeline tab) | rows, n |
| grid minutes a venue did not print (whole window / since its first observation) | `gap_count`, `gap_count_after_first_observation` | gaps | gaps |
| minutes printed more than once | `duplicate_count` | dups | duplicates |
| candles whose OHLC ordering is broken | `ohlc_violation_count` | ohlc bad | ohlc_violations |
| minutes whose source differs from the previous minute | `source_switch_count` | switches | source_switches |
| the largest 1m move at a switch / anywhere on the canonical series | `max_abs_return_at_switch`, `max_abs_return_1m` | max \|ret\| | `*_ret_*` |
| a venue's first and last printed minute | `first_observation_utc`, `last_observation_utc` | first / last | `first_ts` (a `_ts` is epoch ms) |
| the data window | `window_start_utc`, `window_end_utc` | window | `window_start` |
| totals across the flow | `binance_zip_count`, `bybit_zip_count`, `binance_row_count`, `bybit_row_count`, `canonical_row_count` | flow | `zips_binance`, `rows_canonical`; the drawing's `flow` is an edge between primitives (§ Developer experience) |
| bars of a kind inside a bar or a series (a unit, not a bare count) | `ffill_bars`, `zero_volume_bars`, `flat_bars` | ffill (`ffill bars` on the Pipeline tab) / zero-vol / flat | `n_ffill` |
| shares | `coverage_pct`, `binance_pct`, `bybit_pct`, `ffill_pct`, `real_data_pct` | coverage / primary / secondary / ffill / real-data share | ratio without `_pct` |
| cross-venue close divergence over the canonical series | `relative_divergence_mean`, `relative_divergence_p99`, `relative_divergence_max` | rel. divergence mean / p99 / max | `rdiv` |

## Metrics

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| log-loss of the weighted training class prior | `prior_logloss` | `prior_logloss` | prior log-loss (`prior LL` in a cross-section header) | baseline |
| log-loss of the model on the evaluated block | `model_logloss` | `model_logloss` | model log-loss (`model LL` in a cross-section header) | loss |
| information beyond the prior, `1 − model / prior` — the model's objective, and the one the feature-set search selects on | `relative_logloss_skill` | `relative_logloss_skill` | skill (`rel. skill`, `val skill F<n>`, `mean val skill`, `holdout skill`, `skill F<n>` in the tables) | accuracy, edge |
| the search for model hyper-parameters, and the stage that runs it | HPO — `module_ml/hpo.py`, `make ml-hpo` | `hyperparameter_search_result` | search | tuning, optimisation, autoML; `HPO` spelled out mid-document after its first use; `search` alone for the feature-set search |
| the feature-set search — the stepwise choice of an asset's columns on the validation folds under the frozen hyper-parameters, selected on the model's validation skill fold by fold, and the stage that runs it (`../module_ml/skills/methodology_ml.md` § 4); its selection overfitting is bounded and exposed, never absent — a move is accepted only by every fold, the catalogue is small, and the trial count stands on the page beside every proposal | `module_ml/feature_set_search.py`, `make ml-feature-set-search`, its docker twin and its detached twin `tmux-ml-feature-set-search` in the tmux session `feature-set-<ticker>` (`FEATURE_SET_SEARCH_SESSION`), one asset per session, gone with the search | `feature_set_search` (a block of ml_status.json), `<TICKER>_feature_set_search.json` | feature-set search | feature selection (as a name), optimisation, the search (HPO's word); a search selected on a strategy number; "no overfitting" |
| one scored set of the feature-set search — its columns, its skill per fold and their mean, what the strategy would do with it, the pass and the move that scored it | a row of `trials` | `trials`, each `columns_by_timeframe`, `validation` (per fold `relative_logloss_skill`, `sharpe`, `trade_count`), `mean_relative_logloss_skill`, `entry_edge_threshold`, `entry_edge_threshold_constraint_met`, `selection_score_mean_sharpe`, `pass`, `move` | trial | candidate (as a key), step |
| the mean over the validation folds of a trial's relative log-loss skill — the search's objective | `mean_relative_logloss_skill` | `mean_relative_logloss_skill` | mean skill; `Δ vs active` for a proposal's mean skill minus the active set's (`best proposal Δ skill` in the cross-section header, the first proposal's), page arithmetic printed in percentage points (`pp`) | score (the strategy's word for its own selection) |
| the set the search stands on — the best accepted so far, the one the next pass starts from | `champion_trial` | `champion_trial` | — | incumbent, current best |
| the two moves of a pass — one column in when every fold's skill rises, one column out at no worse skill on every fold | `FEATURE_SET_SEARCH_MOVE_FORWARD`, `FEATURE_SET_SEARCH_MOVE_BACKWARD` | `move` = `forward` / `backward` | — (the stage's progress line prints them; no page shows a move) | add / drop, greedy, step; a margin, a ceiling or a floor on the count of columns |
| whether a pass accepted nothing — the search is over | `search_converged` | `search_converged` | converged | done, finished, stopped |
| the promotion — a hand copying one proposal's columns into the asset's feature set and rerunning its ML chain, one asset at a time, never fanned out; the promoted set is re-tuned, so its realised result differs from the search's and the next search starts again; the same proposal twice changes nothing, and the commit history is the record of every promotion | `module_ml/feature_set_promote.py`, `make ml-feature-set-promote ASSET=<TICKER> PROPOSAL=<n>` | `<TICKER>_feature_set.json` with `columns_by_timeframe` and nothing else | — (the page shows a promotion only as the set's `source`) | the promotion threshold of `skill_pre_aws_solution.md` § The databases (a database's word); apply, activate, deploy; a promotion of the whole basket; a counter or a rank in the file — git holds the history |
| where an asset's feature set came from — the promoted file when it exists, else the default set of the catalogue | `feature_set_block()` | `feature_set` with `source` = `default` / `promoted`, `columns_by_timeframe` | source; `columns <timeframe>` in the cross-section | origin, provenance, `final_holdout_evaluation_count` (a counter git already records) |
| the sets a hand may promote — every trial no validation fold scores below the active set, by mean skill, ties to the smaller set, and the champion first when a pass accepted one; at most `FEATURE_SET_PROPOSAL_COUNT` | `proposals` | `proposals`, each `proposal`, `trial`, `columns_by_timeframe`, `added_columns_by_timeframe`, `removed_columns_by_timeframe`, `mean_relative_logloss_skill`, `validation`, `entry_edge_threshold`, `entry_edge_threshold_constraint_met`, `selection_score_mean_sharpe` | PROPOSALS — `#` for the rank, `columns added / removed` for the two differences | recommendations, top sets, best features; a set worse on any validation fold; the highest mean without the fold test |
| the inputs a search recorded, compared by equality when it is rerun — equal, it resumes; different, it starts again — the one copy of another file's content an artifact carries, admitted as the key of that comparison | `build_search_inputs()`, `inputs` | `inputs` with `research_window` (`start_utc`, `end_utc`, `seed`, `warmup_top_timeframe_bars`), `best_params`, `catalogue_columns_by_timeframe`, `active_columns_by_timeframe` | — | fingerprint, hash, checksum |
| whether a recorded search's inputs are still the asset's — false after a promotion, a retuning or a catalogue change, and the page then compares nothing | `feature_set_search_block()` | `inputs_current` | the note *the search predates the active set or its parameters*, in place of PROPOSALS and in the cross-section cell | stale, dirty, outdated; a guard that refuses the promotion |
| the HPO objective value at the chosen point | `best_logloss` | `best_logloss` | best mean F2–F4 log-loss (`best LL` in the search table) | best_value, score |
| what the search chose: the point, its objective value and the trial count | `hyperparameter_search_result` | `hyperparameter_search_result` (a section of the parameters file, a block of ml_status.json) | search | a second name for the same block |
| the chosen point itself — the closed set of eight, in xgboost's own spelling because `module_ml/hpo.py` is a named boundary | the keys of `HYPERPARAMETER_SEARCH_SPACE`, `module_ml/config.py` — the one definition the search, the file and the table all derive from | `best_params`: `alpha`, `colsample_bytree`, `eta`, `lambda`, `max_depth`, `min_child_weight`, `num_boost_round`, `subsample` | depth, eta, min child, subsample, colsample, lambda, alpha, rounds — the search table's columns | a project synonym for an xgboost parameter; a second name for any of the eight; registering them one by one |
| what the search never touches — the constants the experiment freezes before it starts | `module_features/config.py`: the research window, `WARMUP_TOP_TIMEFRAME_BARS`, the hierarchy and the catalogue with every parameter in its terms; `module_ml/config.py`: `ATR_BARRIER_MULTIPLIER`, `LABEL_BARRIER_ATR_TIMEFRAME` and `ATR_WILDER_SMOOTHING_PERIOD_BARS` (the barrier's width), `LABEL_HORIZON_MINUTES`, `XGBOOST_FIXED_PARAMETERS`, `ANNUALISATION_PERIOD_15M_BARS`, `EXECUTION_COST_RATE_PER_TRADE_SIDE` | — (they define the experiment, so the git commit publishes them, not a payload) | the values quoted in methodology_ml.md and methodology_features.md | a searched parameter among them; a value changed without a commit that says so; a feature parameter copied out of the catalogue into a named constant |
| annualised Sharpe of the 15m equity path | `sharpe` | `sharpe`, `selection_score_mean_sharpe` | Sharpe; `selection score` for the validation mean, and `degradation` for holdout Sharpe minus the selection score — presentation arithmetic; in a proposal, what the strategy would do — reported, never selected on | return/risk; a deflated Sharpe ratio of nested trials |
| maximum drawdown of the 1m equity path | `max_drawdown` | `max_drawdown` | maxDD | DD |
| share of the fold spent in a position | `exposure` | `exposure` | exposure | utilisation |
| share of a fold's trades that ended positive | `hit_rate` | `hit_rate` | hit | win rate |
| mean cost-adjusted return of a trade | `average_trade_return` | `average_trade_return` | avg trade | expectancy, `avg_trade_ret` |
| equity at the end of the fold, starting from 1.0 | `final_equity` | `final_equity` | final equity | PnL |
| total gain per feature column of a validation fold's booster, zero for a column its trees never split on | `gain_importance()` | `gain_importance` under `validation_importance.fold_<n>` | gain | importance (bare), weight, the final-holdout booster's gain |
| mean absolute SHAP value (SHapley Additive exPlanations, `methodology_ml.md` § 13 [12]) per feature column of a validation fold's booster, over the fold's scoring rows and the three classes, in margin space, unweighted | `mean_abs_shap_importance()` | `mean_abs_shap_importance` | mean \|SHAP\| | `shap` as a key; SHAP importance (a method, not a quantity) |
| the two importances of every validation booster, the block the page takes its cross-fold means from | `validation_importance_block()`; `fold_importance_block()` of `train.py` measures one fold's two | `validation_importance` with `fold_2` … `fold_4`, each holding the two keys above | FEATURE SET — the two importance columns of its tables | an importance of the final-holdout booster; a mean over folds in the payload; a permutation importance (MDA) — a third importance selected on |
| the columns the model saw — the asset's feature set as feature ids, timeframe-major; beside them every catalogue column's values on the decision grid, keyed by feature id | `feature_columns` and `catalogue_values` of `load_xy()` | `feature_columns` | in set ✓ | a column literal in the page; `catalogue_columns` for the values |

## Payload structure

The container and envelope keys of the two snapshots, so that every published
key is in this register.

| concept | artifact key | holds |
|---|---|---|
| when the snapshot is written | `generated_at_utc` | the one timestamp of a payload |
| the frozen experiment, once, globally | `research_window` with `start_utc`, `end_utc`, `seed` | the window and the seed, published once — no per-asset copy |
| the per-asset reports of ml_status.json | `assets` (a list) with `ticker`, `sample`, `hyperparameter_search_result` (`best_params`, `best_logloss`, `trial_count`), `validation`, `final_holdout`, `feature_columns`, `feature_set` (`source`, `columns_by_timeframe`), `validation_importance`, `feature_set_search` (`null` while no search has run; else `trial_count`, `pass_count`, `search_converged`, `inputs_current`, `proposals`), `strategy`, `artifacts` | the experiment flow, sample → search → validation → holdout → attribution → the feature-set search → strategy, then the folder |
| the classes of the supervised population | `class_counts` with `short`, `neutral`, `long` | counts, named by class |
| the structural facts the page needs beside the assets | `final_holdout_fold_id`, `minimum_agreeing_trend_timeframes`, `trend_gate_feature`, `catalogue` | which fold is the final holdout; how many timeframes the gate needs; the feature id the gate reads; the register, the warm-up, every catalogued definition with its terms, histories and warm-up, and the nesting of the levels — the facts of `module_features/config.py`, published here because that module measures no run state |
| the catalogue block | `catalogue` with `decision_timeframe`, `timeframes`, `warmup` (`top_timeframe_bars`, `end_utc`), `definitions` (per definition: `feature_definition`, `terms` — `inputs`, `indicator`, `parameter_word`, `parameter_bars`, `output_range` —, `operators`, `normaliser`, `range`, `timeframes`, `effective_history_hours_by_timeframe`, `warmup_bars`, `definition_in_default_set`), `nesting` (per adjacent pair: `lower`, `upper`, `lower_longest_effective_history_hours`, `upper_shortest_effective_history_hours`) | the catalogue as the register presents it — the catalogue frame of the ML Research tab reads nothing else |
| how the trades of a fold ended | `exit_counts` with `upper_barrier`, `lower_barrier`, `vertical`, `ambiguous` | counts, named by `event_resolution` |
| the final-holdout equity path | `equity_curve` with `equity` | weekly-sampled values only; the last value is `final_equity` |
| the three tables of data_status.json | `symbols`, `venues` (one list per venue), `canonical_source` — lists whose rows are keyed by `symbol`, derived at the report boundary from `config.symbol(ticker)`; no database column carries it | the pipeline, raw-source and canonical-construction tables |
| the flow totals | `flow` | one `<venue>_zip_count` and `<venue>_row_count` per venue, plus `canonical_row_count`; not the drawing's `flow`, an edge (§ Developer experience) |
| the engine of the databases | `duckdb_version` | the engine that wrote every asset's database |
| an asset's database on disk | `db_bytes` (a `symbols` row) | the size of `<TICKER>_research_ohlcv.duckdb` |
| the last canonical minute of an asset | `last_observation_utc` (a `canonical_source` row) | the asset's grid end; in a venue row the same key names that venue's last printed minute |
| the unit of download work, and the cadence a measurement's age is judged against | `download_cadence_minutes` | one UTC day; the DevOps panel warns above it |
| when the model evaluation was last written | `artifacts` with `model_evaluation_modified_utc` | a fact of the folder, published in ml_status.json only, never in the timestamp-free README |
| day files a venue's tree holds | `zip_count` | one per UTC calendar day — `zips` on the page |
| the longest run of flat no-trade minutes | `longest_flat_run_minutes` | a duration, in minutes — `flat run (min)` on the page |

## Stores

**The store is the boundary between compute and state.** Every stage reads and
writes only the four stores, and learns where they are from the environment:
one variable per store, set by the launcher (the Makefile on the host, the
compose file inside a container) and read by each `config.py` as
`Path(os.environ[...])` — a missing variable is the interpreter's own
`KeyError`, not a guard. A module reads only the stores it touches, and no
module writes into another module's source tree. Until the mount is narrowed,
`.:/app` also exposes each store at `/app/store_<content>`: the store contract is
the env-named path, and the second path is a local accident, not an address.

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| the store contract: one environment variable per store, naming the directory that store is | `STORE_RAW_1M_DIR`, `STORE_ASSETS_ARTIFACTS_DIR`, `STORE_RUN_RECORDS_DIR`, `STORE_STATUS_DIR`; on the host `$(CURDIR)/store_<content>`, in a container `/store/<content>` | — | — | a path derived from `__file__` two levels up (`REPO_ROOT`), a store named by a literal at the point of use, a second name for the same directory |
| the status store: where every module's snapshot lands, tracked so a fresh clone opens on real numbers | `store_status/`, `STORE_STATUS_DIR`; `DATA_STATUS_JSON_PATH`, `ML_STATUS_JSON_PATH` in the configs of the modules that write and read them | `data_status.json`, `ml_status.json` | the page's footer names both files | a snapshot written into `module_monitoring/` or any other module's directory |
| the snapshot route: the dashboard serving a status object by its file name | `STORE_STATUS_ROUTE_SEGMENT`, `GET /store_status/<name>` in `serve.py`, mapped onto `store_status_file(name)` under `STORE_STATUS_DIR` | — | — | a snapshot fetched from the page's own directory, a route per snapshot |

## Artifacts

**One file per distinct artifact responsibility; no duplicate representations
of the same result.** One directory per ticker under `store_assets_artifacts/`;
every file carries the `<TICKER>_` prefix, a time series carries its grid in
timeframe slots, and paths are built only by the descriptors of
`module_features/config.py` (the feature parquets) and `module_ml/config.py`
(the rest); whether an asset holds its three result files is asked
once, by `is_artifact_set_complete()` beside them.

The eleven manifest files in `LC_COLLATE=C` listing order — the order
`FILE_MANIFEST` in `module_ml/status.py` and the generated README share; the
two a hand's stages write are listed with no size until they exist:

| file | written by | holds |
|---|---|---|
| `<TICKER>_README.md` | `module_ml/status.py` | what the folder holds and what came out of it; no timestamp |
| `<TICKER>_feature_set.json` | `module_ml/feature_set_promote.py` | `columns_by_timeframe` — the promoted feature set, a hand's choice, and nothing else; absent, the default set is the asset's; tracked, like the parameters it conditions |
| `<TICKER>_feature_set_search.json` | `module_ml/feature_set_search.py` | `inputs`, `trials`, `champion_trial`, `pass_count`, `search_converged`, `proposals` — the ledger of every scored trial, the search's own state, rewritten after every scored trial; present once a search has run |
| `<TICKER>_features_ss-15-hh-dd-MM.parquet` | `module_features/catalogue.py` | the catalogue on 15m — `decision_ts` and every definition offered on 15m, on the decision grid |
| `<TICKER>_features_ss-mm-01-dd-MM.parquet` | `module_features/catalogue.py` | the catalogue on 1h — `decision_ts` and every definition offered on 1h |
| `<TICKER>_features_ss-mm-04-dd-MM.parquet` | `module_features/catalogue.py` | the catalogue on 4h — `decision_ts` and every definition offered on 4h |
| `<TICKER>_label_events_ss-15-hh-dd-MM.parquet` | `module_ml/labels.py` | Y — `decision_ts`, `entry_ts`, `y`, `event_end_ts`, `entry_observable`, `label_valid`, `event_resolution`, `entry_price`, `upper_barrier`, `lower_barrier`, `exit_reference_price` |
| `<TICKER>_model_evaluation.json` | `module_ml/train.py` | `validation.fold_2..4` and `final_holdout`, each `prior_logloss`, `model_logloss`, `relative_logloss_skill`, `scored_row_count`; `validation_importance.fold_2..4`, each `gain_importance` and `mean_abs_shap_importance` per column; `feature_columns`; `class_counts`, `labels`, `segments` |
| `<TICKER>_oos_predictions_ss-15-hh-dd-MM.parquet` | `module_ml/train.py` | `decision_ts`, `oos_fold_id`, `p_short`, `p_neutral`, `p_long` — the full windows of F2–F5; metrics score only the supervised subset |
| `<TICKER>_parameters.json` | `module_ml/hpo.py` | `hyperparameter_search_result` (`best_params`, `best_logloss`, `trial_count`) |
| `<TICKER>_strategy_evaluation.json` | `module_ml/strategy.py` | `entry_edge_threshold`, `entry_edge_threshold_constraint_met`, `selection_score_mean_sharpe`, `execution_cost_rate_per_trade_side`; per fold `sharpe`, `max_drawdown`, `trade_count`, `hit_rate`, `average_trade_return`, `exposure`, `exit_counts`, `final_equity`; the final holdout's `equity_curve` |

Three files are tracked — `<TICKER>_README.md`, `<TICKER>_parameters.json` and,
once a hand has promoted one, `<TICKER>_feature_set.json`: together they make a
folder readable, and reproducible, without a run, because the parameters are
tuned for the set they were searched under. The eight others are regenerable —
the seven the chain rebuilds from the database, and the search result a hand
reruns. Beside the manifest, outside it, `<TICKER>_research_ohlcv.duckdb`
holds the canonical series and its aggregations: its size moves with every
top-up, and the README is byte-reproducible for an unchanged experiment.

## Features

The grammar is `../module_features/skills/skill_feature_taxonomy.md`, the definitions
`../module_features/skills/methodology_features.md`; this register confirms the words.

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| a series of one timeframe's bars, with no parameter | `open`, `high`, `low`, `close`, `volume` — a bar column — and `log_volume`, the one series with a kernel: `SERIES_KERNELS`, `module_features/catalogue.py` | `inputs` of a term | the series token | a series with a parameter |
| an indicator — one computation with exactly one integer parameter, glued to its token; its kernel carries the token's name in `module_features/indicators.py`, `zscore` alone reading `rolling_zscore` for the family it belongs to, and its invariants — the kernel, the parameter word, the warm-up multiple, the fixed inputs, the output range when it is bounded — are one record of the register beside it | `ema<n>`, `sma<n>`, `rsi<n>`, `atr<n>`, `zscore<n>`, `range_position<n>`; `INDICATORS` — `kernel`, `parameter_word`, `warmup_multiple`, `inputs`, `output_range` of a record, `module_features/indicators.py` | `indicator`, `parameter_word`, `parameter_bars`, `output_range` of a term | the token, and `output 0–100` beside it when the indicator is bounded | `rsi_14`, `sma_200`, `bb20`; a table of indicator facts in `config.py` beside the register; `kernel` for the operating system's accounting — that is the Lifecycle tab's word |
| a term — a series or an indicator inside a feature definition | `("ema", 20)`, `("log_volume", "zscore", 50)`, `("close",)`; `term_name()` | `terms` | terms | atom (the prose word of the skill, never an identifier) |
| a feature definition — terms of one timeframe composed by the operators, with an optional normaliser; the timeframe-less half of a feature | one record of `FEATURE_CATALOGUE`; `feature_definition_name()`; `OPERATORS` = {`minus`, `over`} and `NORMALISERS` = {`centered`}, one record per token beside its kernel in `module_features/catalogue.py` | `feature_definition` | definition | molecule, family, feature family, indicator (for a composite); `trend`, `momentum`, `volatility`, `structure`, `activity` — a category, not a computation |
| a feature — a definition aligned to the decision grid on one timeframe; the column of X and the key of an importance | `feature_id()` = `<definition>_<timeframe>` | `feature_columns`, the keys of an importance | the feature id | a column literal in a page script; a parquet column with a timeframe (the file name carries it) |
| the feature catalogue — every definition the repository can compute, with the timeframes it is offered on; drafted, like the rest of `config.py` | `FEATURE_CATALOGUE`, `catalogue_columns()`, `CATALOGUE_COLUMNS`; the stage `features-catalogue`, `module_features/catalogue.py` | `catalogue` | CATALOGUE | palette (the drawing's word for a colour set — `paletteOf` of the template), feature list, feature store |
| the effective history a parameter covers on a timeframe, `bars × timeframe` — a window's window, a recursion's span or period, the bars carrying most of its weight — the number the nesting rule compares | `definition_effective_history_hours()` | `effective_history_hours_by_timeframe`; `lower_longest_effective_history_hours`, `upper_shortest_effective_history_hours` of `nesting` | effective history | history (bare — a recursion has no window), span (the EMA parameter word), lookback hours |
| the trade's Bollinger reading of `zscore20` — %b(20, 2σ) = zscore20 / 4 + 0.5, an affine map a tree model is invariant to; no %b column exists | — | — | Bollinger %b, in the definitions table | `bb20`, `%b` as a column, `z / 2 + 0.5` |
| the definitions an asset's model sees until a promotion — the frozen experiment's fifteen columns, in the order it stacks them | `DEFAULT_FEATURE_COLUMNS_BY_TIMEFRAME`; `definition_in_default_set` of a record | `definition_in_default_set` | default set | the frozen fifteen (as a name) |
| the definition the strategy hierarchy reads on every timeframe, set or no set | `TREND_GATE_FEATURE_DEFINITION` = the first of the catalogue, `TREND_GATE_TIMEFRAME` | `trend_gate_feature` | the gate | `TREND_FAMILY`; a column literal in `asset.js` |

The strategy hierarchy reads the trend definition through `TREND_GATE_FEATURE_DEFINITION`, so
the name appears once in the code rather than in three string literals; `centered_rsi14` keeps
its American spelling (`skill_pre_aws_solution.md` § What stays as it is, and why).

## Asset containers

The concepts of `docker-compose.yml` and of `serve.py`'s asset role. They name
how a stage is run, never what it computes.

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| the one asset a container is | `ASSET` (environment) = `ticker` (code, key, folder); read by the fan-out's command line, `--tickers $ASSET`, by `serve.py` choosing its role, and by `record.py` for the service a stage ran in and, failing a `--tickers`, the assets it covered — never by a stage module, never the default of `build_ticker_parser` | `ticker` (the endpoint envelope) | — | `TICKER`, `SYMBOL`, `ASSET_TICKER`, a per-asset `.env` |
| a compose service that is one asset's container: resident, answering `/status`, and locally the place every fanned-out per-asset stage runs | `asset-<ticker lowercase>` — one service per ticker under the file's `x-server` anchor | — | — | `asset-BTC`, `container-btc`, a one-off `run --rm` container beside a resident, a `restart:` policy, a published port |
| the one service that holds the docker socket, and the only one | `devops` — the `x-service` anchor plus its own command, `group_add` and the two mounts | `compose_project`, `own_project` | DevOps | the socket in the dashboard or an asset; a third-party socket proxy; a TCP daemon endpoint; a published port |
| the command the servers run — the server, its role by `ASSET`, on the internal port | the `x-server` anchor's `command:`; `CONTAINER_PORT` = 8900 and `BIND_ADDRESS` = `0.0.0.0` in `module_monitoring/config.py` | — | — | a per-service command, a port or a bind address read from the environment or the command line, `PORT` inside a container |
| where the dashboard's proxy reads one asset's endpoint | `http://asset-<ticker>:8900/status`, built by `asset_status_url()` in `module_monitoring/config.py` | — | — | an IP, a published port |
| the host port: the host side of the dashboard's mapping, measured at invocation, never hardcoded | `PORT` of the Makefile — the port the dashboard already publishes, else the first free port from 8900 upward; `PORT=n` overrides (`skill_asset_containers.md` § The topology); `${PORT:-8900}` in `docker-compose.yml`; the `PORT` environment `record.py` reads on the host | — | — | `8900` as the page's address in a document, a command or a comment; a second variable for it; `PORT` inside a container (the row of the command the servers run); a measurement outside the Makefile |
| the one image every service runs | `image: mlops-portfolio-1m-pipeline` | — | — | compose's `<project>-<service>` default, one image per service |
| the memory ceiling every service runs under | the `x-service` anchor's `deploy.resources.limits.memory` | — | — | `mem_limit` beside it, a CPU quota, a reservation, a service written outside the anchor and so without a ceiling |
| how long a container lives: one-off — a `run --rm` process that exits with its stage — or resident — a server that stays up | the `lifetime` column of `skill_asset_containers.md` § The topology | — | — | one-shot, ephemeral, daemon, long-running; `task` or `job` for the one-off |
| the presentation switch: the whole stack up with the page open, or everything down, in one word | `make on` = `docker-up`, `make off` = `docker-down` — the one alias pair the Makefile grammar admits | — | — | `start` / `stop` (the panel's verbs for one container), bare `up` / `down` (compose's), `run`, a third alias |

## Container status endpoint

The keys `module_monitoring/serve.py` answers with — `GET /containers` on the
dashboard, `GET /status` on an asset container.

| concept | artifact key | holds |
|---|---|---|
| the basket, as the dashboard serves it | `tickers` | `module_data.config.TICKERS`, in order |
| how often the page asks | `poll_interval_seconds` | published by the server, never a literal in the page |
| when the server of an asset container started — how long it has been up, for the tab | `started_at_utc` | one UTC string, beside the envelope's `generated_at_utc` |
| the asset's data, as last measured | `data` with the snapshot's `generated_at_utc`, `row_count`, `last_observation_utc`, `db_bytes`, and `observation_lag_minutes`, `measurement_age_minutes`, `research_window_covered` | `null` when the snapshot has no row for the asset or the database it describes is gone, so `db_bytes` is a size and never `null`; is the market data behind, is anyone still measuring, does the grid cover the frozen window |
| the asset's folder, as last measured | `artifacts` with `model_evaluation_modified_utc`, `entry_edge_threshold_constraint_met` | `null` when the ML snapshot has no block for the asset, or the folder no longer holds the artifact set that block describes |
| what only the container can see about itself | `footprint` with `memory_bytes`, `memory_peak_bytes`, `memory_limit_bytes`, `cpu_usage_seconds`, `cpu_count` | the cgroup's accounting: `memory_bytes` is what the kernel charges, page cache included; the limit is the cgroup ceiling or `MemTotal` when it sets none; the CPU count is the host's, the basket sets no quota. A CPU rate is the page's arithmetic over two polls, never a key |

The asset-container columns and labels are the table of
`../module_monitoring/skills/skill_devops_panel.md`. The page's navigation: the
tabs *Pipeline*, *Data Quality*, *ML Research*, *ML Assets*, *Lifecycle*, the two
jumps *DX* and *DevOps*, and the ML Assets views *Labels & data*,
*Classification*, *Strategy*, *Search*, *Feature set*.

## Run record

What one recorded run of the chain leaves in `store_run_records/<run_id>/` — one
record for the whole basket and never one per asset, because a run of the chain
is one event and every asset's stages belong to it — written by
`module_monitoring/record.py` wrapping each stage command in the container that
stage already runs in. Its paths come from the descriptors of
`module_monitoring/config.py` and from nowhere else. `run_id` is `<YYYYMMDDTHHMMSS>Z_<git short commit>`: not a
content hash, but git's own identity, the record `module_ml/config.py` already
names — so it sorts chronologically and points at the code that ran.

**In `events.jsonl` and `resources.jsonl` a `process_` key is the stage and a `container_` key
is not.** `summary.json` needs no prefix on the stage's own numbers, because every unprefixed
number in a stage row is already the stage's; only the container ones are marked there. The stage's cost
comes from `wait4` rusage of the process the recorder spawned and reaped — exact,
never sampled. The cgroup counters carry the whole container over the same
window: the resident server, the recorder and the stage together.

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| one recorded execution of the chain — the execution name, read forward | `run_id` | `run_id` | run | build, job, a content hash |
| one command of a run, named in the Makefile's target grammar — one seam, `data-download`, runs two stages (`skill_pre_aws_solution.md` § The Makefile is the developer interface) | `stage_of()` | `stage` | stage | step, task |
| the compose service the stage ran in | `docker_service()` | `docker_service` | container | host; a bare `container`, which the DevOps panel already uses for up/down |
| CPU the stage process and its reaped descendants used | `rusage.ru_utime + ru_stime` | `process_cpu_seconds` | CPU | cpu, cpu_pct, cpu_time |
| peak resident set of the stage process | `rusage.ru_maxrss` | `process_memory_peak_bytes` | peak resident set | RSS, RAM, mem, max_rss |
| bytes the stage moved through `read()` / `write()`, independent of the page cache | `/proc/<pid>/io` | `process_read_chars`, `process_write_chars` | read / write | io, bytes_in |
| physical blocks the stage caused, cache-dependent and writeback-delayed | `rusage.ru_inblock`, `ru_oublock` | `process_disk_read_bytes`, `process_disk_write_bytes` | — | a headline I/O number |
| the whole container over the stage's window | the cgroup | `container_cpu_seconds_delta`, `container_memory_charged_peak_bytes`, `container_disk_*_bytes_delta`, `container_network_*_bytes_delta` | container | any of these as a stage cost |
| how many 1 s samples the stage window held | `sample_count` | `sample_count` | samples | n_samples |
| wall time between stages: docker exec setup and teardown | — | `orchestration_seconds` | orchestration | overhead, a hidden remainder |
| the stage that took the longest | — | `bottleneck_stage` | bottleneck | slowest, hotspot |
| the readiness check that closes a run | `fetch_dashboard_ready()` | `dashboard_ready` — the registry at the top level, one answer per ticker in `assets` | dashboard | healthcheck, ping; one asset's answer standing for the basket |
| the basket one run covered | `TICKERS` | `tickers` | — | `ticker`, the first of the basket standing for it |
| the assets one stage covered — its command's `--tickers`, else its container's `ASSET`, else the basket | `recorded_tickers()` | `tickers` — a key of `events.jsonl` | — | `ticker`; the container standing for the command's scope |
| the asset containers of a run, one row per ticker | `container_identity()` | `asset_containers` | — | `asset_container`, one container standing for the basket |
| where a run's record lives | `STORE_RUN_RECORDS_DIR`, `run_dir()` | — | — | a `runtime/` folder under an asset, one run record per asset |

The four files of a run: `manifest.json` (what ran, where, on what host, and how
it ended), `events.jsonl` (one line per stage, appended by the stage itself from
whichever container ran it), `resources.jsonl` (the 1 s container-wide samples,
likewise from every container of the run), `summary.json` (the stage table and
the run totals, plus `measurement_notes`, which states in the payload what each
number is and is not). One appended line is one `write()` to a file opened
`O_APPEND`, so two containers never interleave a record; the readers put the
lines back in order by their own timestamps, because the file holds arrival
order. `logs/<stage>_<docker_service>.log` holds that stage's output verbatim,
one file per container that ran it, because one stage name runs once per asset
and two containers must never open one log. None of it is committed;
`.gitignore` covers `store_run_records/`.

The routes: `GET /runs` lists the run ids newest first, `GET /runs/<run_id>`
answers one run's manifest, summary and samples, the samples strided to
`RUN_SAMPLE_POINT_LIMIT` so a long run is thinned and never truncated.

## Developer experience

**Developer experience (DX)** is the repository read as something a person works in rather than as
something that runs: how quickly its shape can be seen, and how little has to be held in the head to
change it. `DX` is used as an abbreviation only after that first spelling, and only for the
sub-module and the control that opens its page.

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| the tracked tree drawn as one self-contained page | `module_monitoring/sub_module_dx/visualise.py` | `module_monitoring/sub_module_dx/files_and_folders_visualisation.html` | Files and Folders | diagram, chart, map |
| one group of paths the configuration declares, and the id a digit key answers to | story | `stories`, `story_map`, `story_order`, `default_story` | the story ids of the active view — `S1` … `S6` as tracked, `S1` … `S9` on the primitives | group, cluster, section |
| the arc of the root's ring a story occupies — its roots at the island radius, their fans beyond | `island`, `ISLANDS`, `ISLAND_ORDER`, `ISLAND_RADIUS`, `ISLAND_GAP` | `island` (the per-node map of a view) | — | a second word for the story in the configuration; band, cluster, section |
| the key that isolates one island | the digit of the story id, and the digit the island's name begins with — the page reads `S` plus the digit, and offers only the digits the active view's stories answer to; a legend row does the same by click | — | `1` … `6`, `1` … `9` in the deployment view | a story id that is not `S` plus a digit; a key offered for an island that does not exist |
| the node at the centre of an island, per view | `hub` | `hub` | — | anchor, root of the island |
| a folder collapsed to a single node | `aggregate` | `aggregate` | the folder's own name | rollup, summary node |
| the disc a node and everything beneath it occupy, and the fan, ring and island spacing derived from it | `extentOf`, `ringRadiusOf`, `fanAround` | — | — | padding, margin, bounding box |
| a node's shade: the island colour turned per nesting level below the hub | `shadeStr`, `paletteOf` | — | — | tint (the white mix inside one shade), a second colour per story |
| the commit the tree was read from, and its date | `load_provenance_stamp()` | the tail of `subtitle` | `tree as of <hash> · <date>` | generated at, build date |
| the control that opens the drawing from the status page | — | — | DX | help, docs, about |
| the two views of one tree — the development view, the tree as tracked, its islands the stories; the deployment view, the same tree seated beside the primitives the mapping table's rows become (the 4+1 model's two names; a view, not a deployment — nothing is built) | `VIEWS`, `VIEW_ORDER`, `activeView`, `setView`; `build_view` | the top level of `visualisation_config.json`, and its `deployment` block | *development view* / *deployment view* — the legend heading | production view, cloud view, AWS view, simulation, target, mode, layer, physical view; "reset view" for the camera — that control is Reset camera |
| the control that flips the page to the other view, and back | `btnView` | — | ☁ / ⌂, "Deployment view / development view (v)", the key `v`, `v deployment` / `v development` in the hint | switch (the presentation switch), toggle, a tab, a second page |
| the legend: the active view by name, and its islands in layout order | `renderLegend`, `legend` | — | the island names | key (the edge key is `.edgekey`), map |
| a primitive: a node a view declares for a row of the mapping table no tracked path is — an island root drawn as its icon, the hub when the story names it | `type: 'primitive'`, `drawPrimitiveIcon`, `PRIMITIVE_KEYS`, `PRIMITIVE_ROLES` | `primitives` — id → `role`, `name`, `absent` | its name; the head before the dash or the parenthesis on the canvas | construct (the infrastructure-as-code word), service box, resource, component; icon or node as the noun for it |
| a primitive's role: which icon it is drawn as and the word the panel shows — the same `role` every node has, from one closed set | `role`; `PRIMITIVE_ROLES` = `registry`, `instance`, `container`, `store`, `database`, `state_machine`, `event_rule`, `log_streams`, `front`, `secret` | `role` | the word after the island name | kind, symbol, logo, shape, type (a node's type is core / folder / file / primitive); `bucket` for a store, `task` for a container, `logs` for the streams; `volume` as a role — a durable disk is drawn as a store |
| an absent object — a primitive, an orchestration state, a skill — nothing local answers to and a document describes: a dashed outline and a paler glyph on the drawing, and a sentence ending, or a verdict reading, *absent here — described* | `absent` | `"absent": true` | the sentence | planned, TODO, future, ghost, placeholder, missing; a solid icon for it |
| a flow: an edge between two primitives of one view — dashed, arrowed at its target, coloured by the island it leaves, rising with its length | `type: 'flow'`, `FLOW_LIFT_PER_LENGTH`, `FLOW_TIP_GAP` | `flows` — `{from, to}` over primitive ids | the third row of the edge key | arrow, pipeline, dataflow, dependency, link, chord; a flow to a path; the `flow` block of `data_status.json`, a count table |
| an instance: one virtual machine of the deployment view — the host containers run on: the task host, its durable volume drawn beside it as a store, and the strategy host | role `instance`; "host" in a primitive's name | — | Task host / Strategy host | `instance` or `host` for a container — a container is a *machine* in the DevOps panel; a host per asset; node |
| a role a view gives a path for itself — the aggregate folder a `database` on the primitives, an `artifact` as tracked | `roles` in the `deployment` block | `deployment.roles` | the word the panel shows in that view | a second `aggregate`; a role that changes the tree |
| the notice: the words a view shows in the top right, in red capitals — what the picture is, in the presenter's words | `notice` | `notice` (per view) | *Mapping functionalities into AWS-env architecture in progress — the files and folders of this repository are shaped for the move* on the deployment view | banner, watermark, disclaimer, badge; a notice on a view that has nothing to say |

The drawing is redrawn by hand with `make monitoring-dx-update` and by nothing else. It is a derived
artifact under *Derived, never drafted*: a hand edit to it is a violation, and the provenance stamp
is what says how old it is — a committer date, written in UTC like every other time this repository
prints. `../module_monitoring/skills/skill_developer_experience_drawing.md` holds the configuration surface key by key.

## Documentation ownership

Where a rule is written is itself a named decision. `AGENTS.md` § The default
choice holds the rule; these are the names it uses.

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| a normative document describing one module's own responsibility | `module_<name>/skills/<document>.md` | — | — | module-specific rules kept in `module_skills/`; a per-module `docs/` or `doc/` folder |
| a normative document that crosses modules or governs the repository | `module_skills/<document>.md` | — | — | a cross-cutting rule filed under one module |
| the directory holding one module's own skills | `module_<name>/skills/` | — | — | `module_<name>/skill/`, `module_<name>/documentation/` |
| the link surface that finds every skill without holding one | `module_skills/README.md` | — | — | a collection of copies; an index that restates a rule it links to |
| one module's reader-facing front door | `module_<name>/README_module_<name>.md` | — | — | `module_<name>/README.md`; a front door that restates a skill or a decision table |
| a review report: the tree reviewed against one question, kept at the root beside the contract and the overview — `REPORT_pre_aws_minimalism.md` asks whether each seat of the mapping is the cheapest that keeps its boundary | `REPORT_<subject>.md` | — | — | a report inside a module; a report that restates a rule instead of citing it; a work order or a plan kept in the tree |
| the design rationale: the section of a module's orientation that says, per object or analogous pair or the module's documents, why here, why beside these, why this boundary and which mapping row it answers to — the fourth the test of the first three | `## Design rationale` of each `README_module_<name>.md` | — | — | a decision table; a rule restated; an object with no row or two; ADR, decision record, decision log, `docs/` |

## Pre-AWS direction

The names `AGENTS.md` § Pre-AWS architectural direction and
`skill_pre_aws_solution.md` use — how the repository is drawn, not what it
computes; the rules are there, not here. The mapping table is
`skill_pre_aws_solution.md` § The mapping table, and *the elsewhere column*
its column *the same responsibility elsewhere*. Cloud proper nouns are
external vocabulary; the closed list of where one may be spoken is
`AGENTS.md` § Pre-AWS architectural direction, and no identifier, key or path
carries one.

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| the stance: a local academic architecture whose boundaries would survive a move onto standard cloud primitives, with no cloud used and none planned | Pre-AWS — a word of the documents; `pre_aws` in two file stems, the skill's and the report's, no identifier carries it | — | — | cloud-ready, AWS-ready, cloud-native, a migration plan, a deployment guide; `pre-aws` or `PreAWS` in prose |
| compute: a process that reads a store, writes a store and exits, owning no asset state between invocations | every stage's `main()`, `python -m <module>.<stage> --tickers <TICKER>`; the container that runs it; elsewhere a task on the one host every asset's runs share, `task` being the elsewhere column's word | — | — | a container as the home of an asset's state; a resident as a requirement of a stage; an in-process cache between stages; `worker`, `processor` |
| the rebuild condition: whether an asset's artifacts must be rebuilt from its canonical series, answered without launching anything | `is_artifact_set_complete()` is its completeness half; freshness has no predicate yet — its names when written: `has_new_market_data()`, `requires_canonical_rebuild()`, `requires_feature_rebuild()`, `requires_model_rebuild()`; until then the rerun table of `../module_ml/skills/methodology_ml.md` § 11 is read by a human | — | — | a scheduler, a watcher, an event bus, a function that both detects new data and trains; `should_run()`, `check_update()`, `trigger()` |
| the mapping table: where cloud proper nouns are spoken — what this repository has, beside the shape the same responsibility takes elsewhere — and what the drawing's deployment view draws, primitive by primitive, a row whose primitive has no local counterpart drawn absent | `skill_pre_aws_solution.md` § The mapping table | — | — | an adapter, a cloud config file, a proper noun outside the places `AGENTS.md` § Pre-AWS architectural direction lists; a path of the elsewhere column read as a proposal for a local directory |
| the seat: the one paragraph of a local skill, or one bullet where the skill has no headings, that names the primitive its object answers to, in the mapping table's words with the proper noun in parentheses as the table spells it, and cites the skill for the rest | — (a word of four documents: `skill_asset_containers.md`, `skill_determinism.md`, `../module_data/skills/skill_candle_canonicalisation.md` § 15, `../module_monitoring/skills/skill_devops_panel.md`) | — | — | a second seat in one skill; a seat that restates a row or a ladder; a seat in a `README_module_<name>.md`, whose form is the design rationale; `target`, `cloud note`, `mapping section` |
| the resource role: the name a cloud resource would carry — `<project>-<environment>-<resource-role>`, the role the primitive id of the deployment view with `_` read as `-`, the project the head the image name already carries | — (no identifier; `mlops-portfolio-1m-pipeline` is the one name of that shape the tree holds, with no environment token) | — | — | a second list of roles; a role that is not a primitive id; `dev` or `prod` in a tracked name; a ticker in a resource name; an environment token on the image tag |
| a state name: the state a stage would be — one per row of `skill_pre_aws_solution.md` § The Makefile is the developer interface, and PublishStores, the copy state no stage answers to; *Publish* in a state name means: write the object where its readers read it | — (a word of the elsewhere column; no identifier) | — | — | registering them one by one; a state name with "and" in it; *publish* as *make public* |
| the store volume: the task host's durable disk mounted at `/app` — every asset's folder and the other `store_*` roots at today's paths | `.:/app` in `docker-compose.yml`, read forward as `<volume>:/app`; `store_volume`, a primitive id of the deployment view — no identifier carries it | — | — | asset volume; a volume per asset; a shared network filesystem; the volume as the copy; `data_volume` |
| the ladder: the three phases in which the runtime elsewhere becomes true, each named for what it changes — *the lift*, *the idiom*, *the image carries the code* | — (a word of `skill_pre_aws_solution.md` § The retrain runtime is a ladder; no identifier) | — | — | a letter or a number for a phase; a phase as a branch or an environment; `dev` / `prod`; a phase built here; rung |
| the promotion threshold: a second concurrent writer or a cross-asset query — the one condition under which a managed database replaces an asset's embedded file | — (a word of `skill_pre_aws_solution.md` § The databases; no identifier) | — | — | a database process for one writer; a threshold in rows or bytes |
| the active version: the one `<version>` of an asset's artifacts a reader reads, chosen where the reader is | — (`<version>` is the execution name, `run_id`; no identifier) | — | — | latest, current, prod; a mark inside a file |
| the tunnel: how a reader reaches the page on a host that is not theirs — `ssh -L 8900:127.0.0.1:<port> <host>` of `../README.md` § Quickstart; elsewhere a port-forward, the elsewhere column's word | — (a command of the README; no identifier) | — | — | a public port; a load balancer |
| read forward: a local object read as the same responsibility elsewhere — the mapping table's column — with nothing moved | — (a phrase of the documents; no identifier) | — | — | migrated, ported, deployed, in production |
| the move: what a local thing's seat elsewhere costs it — a rename, one edit, or absent here — described; the fourth column of the mapping table | — (a word of `skill_pre_aws_solution.md` § The mapping table; no identifier) | — | the notice's *shaped for the move* | migration, deployment, a plan, a roadmap |

## DevOps panel

The names of `module_monitoring/sub_module_devops` — the machines the
project runs on, and the three verbs offered for them. The contract is
`../module_monitoring/skills/skill_devops_panel.md`.

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| the panel and its sub-module — named, like `sub_module_dx`, for the persona whose page it is | `sub_module_devops`; the compose service `devops` | — | DevOps | `portraefik` (the retired coinage), `sub_module_docker`, Portainer, Traefik, a tool's brand as a name, any routing the old name suggested |
| one container the daemon reports, whether or not this project owns it | `machine` — `machines` in the payload, `machine_row()` | `machines` | container | `node`, `host`, `instance` (an instance is the deployment view's host, § Developer experience); a foreign container hidden rather than listed |
| whether a container belongs to the project the panel itself runs in | `own_project`, compared on `com.docker.compose.project` read from the panel's own labels | `own_project`, `compose_project` | `own` | a match on service name or image; the project written as a literal |
| the whole set of state changes the panel offers | `CONTAINER_ACTIONS` = `("start", "stop", "restart")` | `actions` | start / stop / restart | `rm`, `exec`, `prune`, compose up/down from the browser, an action outside the tuple |
| the refusal of an action on another project's container | HTTP 403 with `refused` and `reason` | `refused`, `reason` | the reason, shown | a silent no-op, a disabled button as the only guard, a 404 that hides the reason |
| the panel's own API, proxied by the dashboard and reached by literal name from the page | `DEVOPS_ROUTE_PREFIX` = `/devops`, `devops_api_url()` | `GET /devops/api/{machines,networks,volumes,image,events}`, `POST /devops/api/machines/<id>/<action>` | — | a route on the dashboard that opens the socket; a second prefix for the same panel |
| what one machine row publishes about a container | `machine_row()` | `container_id`, `name`, `compose_project`, `compose_service`, `own_project`, `state`, `image`, `started_at_utc`, `restart_count`, `ports`, `memory_bytes`, `memory_limit_bytes`, `cpu_usage_seconds`, `cpu_count` | the container table's columns | a key the page does not read; `mem`, `cpu_pct`, a bare duration for uptime |
| what the three engine inventories publish beside the machines | `networks_payload()`, `volumes_payload()`, `image_payload()` | `networks` with `name`, `driver`, `scope`, `attached`; `volumes` with `name`, `driver`, `size_bytes`, `reference_count`; `bind_mounts` with `source`, `destination`, `writable`, `containers`; the image as `image`, `image_id`, `size_bytes`, `created_utc`, `repo_tags` | the networks, volumes, bind-mount and image tables | a hash as an image identity; a volume size the daemon did not report |
| one daemon event of this project, over a doubly bounded window | `events_payload()` | `events` with `time_utc`, `type`, `action`, `name`, `compose_service` | the events table | an unbounded `/events`; a host's other stacks in this project's tail |
| an action the container's state already satisfies | HTTP 304 from the engine, forwarded with no body | — (the status is the answer) | `changed nothing … already in that state` | `refused` for a 304; an error style for a success |
| a control that leaves a page for another persona's page | `.jump` | — | DX / DevOps / Status | `dx-link` as the class of a second control, a tab for a machine view |
| the toolkit every page loads before its own sections | `page.js` | — | — | `utils.js`, `common.js`, `shared.js`, `lib.js`; a page-specific element written from it |
