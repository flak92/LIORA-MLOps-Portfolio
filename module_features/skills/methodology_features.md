# Methodology — the feature catalogue on the canonical series

Per asset, independently, on the one market object the research layer studies: exact bars of the
canonical 1m series on every timeframe of the register, and the feature catalogue evaluated on each
of them, aligned to the decision grid. The names are `skill_feature_taxonomy.md`; the definitions
are here, equation by equation; the search that chooses a set from them is
`../../module_ml/skills/methodology_ml.md` § 4. *The repository shows the destination, not the
road*: the one guard is the finiteness assert of `catalogue.build_catalogue`.

## The register

The hierarchy is the experiment's literal, `HIERARCHY_TIMEFRAMES`; the duration and the slot of
each token are read off the token.

| timeframe | `timeframe_duration_ms` | bars per UTC day | ratio to the level below | `timeframe_slot` |
|---|---|---|---|---|
| `15m` | 900 000 | 96 | — (the decision timeframe) | `ss-15-hh-dd-MM` |
| `1h` | 3 600 000 | 24 | 4× | `ss-mm-01-dd-MM` |
| `4h` | 14 400 000 | 6 | 4× | `ss-mm-04-dd-MM` |

Bars are exact UTC-aligned aggregations of the canonical 1m series — O first, H max, L min, C last,
V sum; `arg_min` / `arg_max` by timestamp for determinism — written by `bars.py` into the asset's
own database, one table per entry of the hierarchy (`ohlcv_<timeframe>_canonical`).

## The kernels

Recursions run as explicit loops; rolling statistics use `sliding_window_view`; values inside a
window's lookback are NaN, and a recursion is finite from its first bar.

    ema_t   = ema_{t-1} + α (x_t − ema_{t-1}),  α = 2 / (n + 1),  ema_0 = x_0           SPAN n
    wilder  = w_{t-1} + (x_t − w_{t-1}) / n,  seeded with the mean of the first n         SMOOTHING_PERIOD n
    rsi     = 100 − 100 / (1 + wilder(gain) / wilder(loss)),  gain = max(Δclose, 0), loss = max(−Δclose, 0)
    atr     = wilder(true range),  true range = max(high − low, |high − prev close|, |low − prev close|)
    sma     = mean of the trailing n bars                                                   LOOKBACK n
    zscore  = (x − mean_n(x)) / sd_n(x),  sample sd; a zero sd gives 0                      LOOKBACK n
    range_position = (close − min_n(low)) / (max_n(high) − min_n(low));  a flat range gives 0.5   LOOKBACK n

`over` is a ratio that is 0 where the denominator is 0; `centered` maps a bounded oscillator to
[−1, 1] as (x − 50) / 50.

## The catalogue

The eight feature definitions as of this commit, on the timeframes they are offered on; the
effective history is the longest parameter read on that timeframe — a window's window, a
recursion's span or period — the warm-up what the definition's terms need in bars of their
timeframe.

| definition | on the timeframe's own bars | range | effective history 15m | effective history 1h | effective history 4h | offered on | warm-up (bars) | default set | ref. |
|---|---|---|---|---|---|---|---|---|---|
| `ema20_minus_ema50_over_atr14` | `(EMA20 − EMA50) / ATR14` | unbounded, dimensionless | 12.5 h | 50 h | 200 h | 15m, 1h, 4h | 200 | yes | [1][3] |
| `centered_rsi14` | `(RSI14 − 50) / 50` | [−1, 1] | 3.5 h | 14 h | 56 h | 15m, 1h, 4h | 56 | yes | [1][7] |
| `atr14_over_close` | `ATR14 / close` | > 0, dimensionless | 3.5 h | 14 h | 56 h | 15m, 1h, 4h | 56 | yes | [1][5] |
| `range_position20` | `(close − min(low, 20)) / (max(high, 20) − min(low, 20))` | [0, 1] | 5 h | 20 h | 80 h | 15m, 1h, 4h | 20 | yes | [2] |
| `log_volume_zscore50` | z-score of `log1p(volume)` over 50 bars | dimensionless | 12.5 h | 50 h | 200 h | 15m, 1h, 4h | 50 | yes | [1][6] |
| `zscore20` | z-score of `close` over 20 bars — the Bollinger reading: %b(20, 2σ) = zscore20 / 4 + 0.5, an affine map a tree model is invariant to, so no %b column exists | dimensionless | 5 h | 20 h | 80 h | 15m, 1h, 4h | 20 | no | [1] |
| `close_minus_sma50_over_atr14` | `(close − SMA50) / ATR14` | unbounded, dimensionless | 12.5 h | 50 h | 200 h | 15m, 1h, 4h | 56 | no | [1][3] |
| `close_minus_sma200_over_atr14` | `(close − SMA200) / ATR14` | unbounded, dimensionless | — | — | 800 h | 4h | 200 | no | [1][3] |

Nesting holds: 15m at most 12.5 h < 1h at least 14 h; 1h at most 50 h < 4h at least 56 h. The
longest warm-up on the top timeframe is 200 bars of 4h — the experiment's
`WARMUP_TOP_TIMEFRAME_BARS`; decision rows before `2021-02-03 08:00 UTC` are excluded everywhere.
The five definitions of the default set are the fifteen columns of the frozen experiment, in the
order it stacks them.

`log_volume_zscore50` measures the activity of the **canonical observation process**, not
venue-independent market activity: the sources differ in liquidity level, so a source switch may
induce a volume-level discontinuity. Normalising per source would push provider knowledge back
below the ingest boundary, so the limitation is stated rather than engineered away.
`rel_divergence` is a data-quality signal, never a feature [11]. Cross-timeframe trend agreement is
**not** a feature: the count of timeframes whose trend sign matches a given side is a deterministic
function of columns the model already has, so it can only add representation, never information;
the 2-of-3 agreement lives where it is used, in the strategy gate.

The keys in the last column are the reference list of
`../../module_ml/skills/methodology_ml.md` § 13 — one list for the research layer.
