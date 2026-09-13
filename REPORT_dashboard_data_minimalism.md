# Report: the data views reviewed for excess

## In short

The data layer publishes forty-six fields and reads six full passes of each
asset's database to fill them. Against its own rule — *if its purpose cannot be
named, it goes* — nineteen of the forty-six cannot name a purpose: seven in the
envelope, the whole `symbols` table, a count of an intermediate file, a geometry
count a stronger one subsumes, two venue-named shares, one share and one mean.
Six fields the reader actually needs are absent, and every one of them rides a
pass that already runs. One published number is wrong in the direction that
matters: `longest_flat_run_minutes` counts forward-filled minutes as a quiet
market, so the day a provider is replaced a run of fabricated bars is reported
as calm. And two of the six passes are the same query written twice.

What the views must hold is § The minimum each view holds; the argument field by
field is § Field by field: what could be less, and whether it is; what the two
tabs still cannot see is § What the tabs do not catch. The count is
forty-six fields to thirty-three — nineteen removed, six added, one corrected —
and six passes to five.

This report was written as a specification and is kept at the state in which it
was executed: every number below is the number the tree now produces.

## The measure, and where it comes from

The rule is `AGENTS.md` § Values, *Minimalism*: **every line, file, module and
dependency has a concrete purpose; if its purpose cannot be named, it goes.**
`REPORT_pre_aws_minimalism.md` applied it to infrastructure — *the seat of each
thing is the cheapest that keeps its boundary*. This report applies it to the
fields of a view:

> A field is kept only if removing it would lose a question the view exists to
> answer; a field is excess if it says nothing another field already on the page
> could not.

Four questions cut a field, in order, each taken from the tree rather than
invented here:

1. **Does anything read it?** `module_monitoring/skills/skill_dashboard_conventions.md`
   — *the payload carries only fields the page reads*.
2. **Can the page rebuild it from fields of the same row?** The same skill — the
   page does presentation arithmetic over already measured values, and moving
   that arithmetic into the payload *would grow it without adding a fact*. The
   line is precise: a share is the page's arithmetic when **both** its operands
   are published keys in the same row, and it stays in the payload when an
   operand is a measurement the payload does not publish. `ffill_pct` is the
   first; `coverage_pct`, whose `distinct` and `expected` are published nowhere,
   is the second.
3. **Does it say the same thing as a field already kept?**
4. **Is it a fact about the data at all?** This one is **last**, not first — a
   naive reading of it would also cut `download_cadence_minutes` and
   `window_start_utc`, which are compile-time constants and stay.

One question keeps a field, and it is the owner's:

> **Can it reveal a shortcoming in the data that would survive a change of
> provider?**

That question is not new either. `module_data/skills/skill_candle_canonicalisation.md`
§ 16 already splits these numbers in two: `duplicate_count` and
`ohlc_violation_count` are **invariants** — a non-zero value is a defect — and
every other number is an **observation**, of which *no value is by itself a
failure*. The split is the reading rule the tabs have never stated, and § The
minimum each view holds states it.

Because the invariants are the only numbers with a known correct value, the test
that an observation has "no nameable threshold" cuts nothing: by § 16 no
observation has one. Where this report cuts an observation it cuts it for
duplication, never for the absence of a threshold.

## The count

| container | today | after | what moved |
|---|---|---|---|
| the envelope | 10 | 4 | five `flow` keys, `window_end_utc`, `duckdb_version` out; `source_venues` in |
| `symbols` | 6 | 0 | the table is deleted whole; nothing is relocated out of it |
| `venues.<venue>` | 13 | 13 | `zip_count` and `ohlc_violation_count` out; `invalid_row_count` and `last_close` in |
| `canonical_source` | 17 | 16 | `binance_pct`, `bybit_pct`, `ffill_pct`, `relative_divergence_mean` out; `source_share_pct_by_venue`, `longest_ffill_run_minutes`, `repeated_candle_count` in |
| **fields** | **46** | **33** | 19 removed, 6 added, 1 corrected |
| **passes per asset** | **6** | **5** | the max-return scan is folded into the source-switch scan |

The passes were `module_data/status.py`'s five SQL constants: the venue scan run
once per venue, the canonical scan, the max-return scan, the source-switch scan
and the longest-flat-run scan, beside a directory listing of the day ZIPs per
venue. They are now four constants and five passes, the listing gone. Measured on one asset of 2 985 120 canonical minutes, `data-status`
took 3.57 s before and takes 3.75 s after, of a chain that takes 837.6 s.
**This report promises no faster chain and did not deliver one.** One pass is
gone, and the six detectors added spend slightly more than it saved; the data
layer is four tenths of one percent of the chain either way. What the count buys
is a payload, a file and a set of documents a reader can hold in mind at once —
and one wrong number made right.

## The minimum each view holds

The navigation does not move: five tabs, the DevOps jump, the names as
`module_skills/glossary.md` § Container status endpoint enumerates them. What
changes is that **the invariants are marked**: the cells of a column whose only
correct value is zero carry the class `invariant`, so colour marks the category
the way the house rule allows, and a broken invariant still reads as a warning.
The columns are named by their header in the render function, never counted by
position, so an invariant is added by naming it.

The invariants are the three of § 16 and no more. `gap_count` and `ffill_bars`
are **not** among them — the skill is explicit that no observation's value is by
itself a failure, and an earlier draft of this report was wrong to put them under
a must-be-zero heading.

**The reading rule, which the page states in its footnote:** after a change of
provider the columns that must be 0 must **still** be 0; the observations beside
them are **expected** to move, and are read by comparing them with the previous
provider's. A reader who does not know which of the two he is looking at cannot
be alarmed by the right number.

### Pipeline — *is there a dataset, and how much of it is real?*

One row per asset, from `canonical_source`.

| invariants | observations |
|---|---|
| *(none — the Pipeline tab is the inventory, not the verdict)* | `row_count` · first and last observation · real-data share *(the page's arithmetic)* · `ffill_bars` · `longest_ffill_run_minutes` · `longest_flat_run_minutes` |

The envelope above it holds four fields and nothing else: `generated_at_utc`,
`window_start_utc`, `download_cadence_minutes`, and `source_venues` — the
provider set in tier order, the one definition every per-provider section,
column and share cell of the page is built from.

### Data Quality — *which provider delivered what, do they agree, and did stitching them hurt?*

One row per asset per venue, then one row per asset for the canonical series.

| invariants | observations |
|---|---|
| per venue: `duplicate_count` · `invalid_row_count` — on the canonical series: `ohlc_violation_count` | per venue: `row_count` · `coverage_pct` · `gap_count` · `gap_count_after_first_observation` · `zero_volume_bars` · `flat_bars` · `last_close` · first and last observation — then the canonical construction: `source_share_pct_by_venue` · `source_switch_count` · `max_abs_return_at_switch` · `max_abs_return_1m` · `relative_divergence_p99` · `relative_divergence_max` · `repeated_candle_count` |

**No column appears on both tabs.** `canonical_source` is read by both, and
disjointly: Pipeline takes the completeness of the grid, Data Quality takes the
join that built it.

## Field by field: what could be less, and whether it is

| field | could it go | does it, and why | where the tree says so |
|---|---|---|---|
| `generated_at_utc` | nothing — a measurement without its moment is not one | no: every number below it is a claim about a time, and this is the time | `glossary.md` § Payload structure, *the one timestamp of a payload* |
| `window_start_utc` | it is a config constant, not a fact about the data — question 4 would cut it | no, and this is where question 4 shows it must come last: it is the one fixed reference against which a venue's `first_observation_utc` reads as a provider's missing history, and `module_monitoring/serve.py` computes `research_window_covered` from it | `status.py`, `DATA_WINDOW_START_UTC`; `module_monitoring/serve.py`, the data block |
| `download_cadence_minutes` | it is `MINUTES_PER_DAY`, a constant, and `data.js` never reads it | no: the DevOps panel reads it, and its skill forbids a cadence to be a literal in a page — the seat of the constant is the payload precisely so the page has none | `module_monitoring/skills/skill_devops_panel.md`, the polling and warning paragraphs |
| `window_end_utc` | the page could take the newest `last_observation_utc` and add one grid step | **yes, it goes** — and it should have gone before it was ever read: it is that maximum over the whole basket, while `venue_block` judges *every asset against its own canonical end*, so with two assets it names a window that all but the newest do not have. Its one reader is the envelope line; `serve.py` already declines it in favour of `window_start_utc` and the asset's own `last_observation_utc` | `status.py`, the window comment above `venue_block`, and the report's own window comment in `main` |
| `flow.binance_row_count`, `flow.bybit_row_count`, `flow.canonical_row_count` | the page can sum the rows it is already showing | **yes, they go** — question 2, exactly: three sums over `venues[].row_count` and `canonical_source[].row_count`, both kept | `skill_dashboard_conventions.md`, presentation arithmetic |
| `flow.binance_zip_count`, `flow.bybit_zip_count` | the page cannot rebuild these — they come from a directory listing, not from the payload | **yes, they go, but not for that reason** — question 4: a ZIP is an intermediate file, not data, and a ZIP that landed empty or short appears as a deficit in `row_count`, `coverage_pct` and `gap_count`. The page's flow line loses its first term and reads *rows → canonical rows* | `README_module_data.md` § What the status stage measures |
| `duckdb_version` | nothing reads it once the envelope line is rewritten | **yes, it goes** — question 1. What is lost should be said rather than waved away: the register calls it the engine that wrote every asset's database, and § Parity rests on that engine's pinned orders for byte equality. It is the only in-payload record that explains a parity difference, and that explanation moves to the image pins and the DevOps view | `glossary.md` § Payload structure; `README.md` § Parity |
| `symbols[].row_count`, `symbols[].ffill_bars` | they are the same alias of the same scan as the canonical row's | **yes, they go** — question 3, byte for byte, not by coincidence: one `CANONICAL_SCAN`, two blocks reading the same returned row | `status.py`, `symbol_block` and `canonical_source_block` over one `canonical_rows[ticker]` |
| `symbols[].real_data_pct` | `100 − ffill_pct` | **yes, it goes** — question 2, both operands in the row. The page keeps the number and does the subtraction | `skill_dashboard_conventions.md`, presentation arithmetic |
| `symbols[].ticker`, `symbols[].symbol` | already in the canonical row | **yes, they go** — question 3 | `glossary.md` § Payload structure, *lists whose rows carry `ticker`* |
| `symbols[].db_bytes` | it looks like the table's one survivor, and an earlier draft of this report relocated it | **yes, it goes too, and the table is deleted whole** — three ways. It is `stat().st_size` of the entire `<TICKER>_research_ohlcv.duckdb`, which also holds the three `ohlcv_<tf>_canonical` tables the feature module writes, so a `features-bars` run moves it with no change to any candle — seated in `canonical_source` it would be the one field in that row a *downstream* stage can change. The panel that wants a file size computes its own from disk and never reads this one. Its single reader is the envelope line being dismantled with `duckdb_version`. A change of provider changes candles, never gigabytes | `status.py`, the `stat` in `main`; `skill_candle_canonicalisation.md` § 13, the tables of the file; `module_monitoring/serve.py`, the footprint and data blocks |
| `venues[].zip_count` | the row count already proves the data landed | **yes, it goes** — question 4, with `flow`'s two zip counts, and the directory listing of ~2 073 names per venue per asset goes with it | as above |
| `venues[].row_count` | nothing | no: how much raw material the provider delivered, before anything chose between providers | `glossary.md` § Data quality, *rows* |
| `venues[].coverage_pct` | it is `distinct / expected`, so it looks like arithmetic | no: neither operand is published, so question 2 does not reach it. It is *the* number that puts two providers side by side | `status.py`, `share_pct(distinct, expected)` |
| `venues[].gap_count` | it is the same fact as `coverage_pct` | no: a share lies about scale. A thousandth of one percent of three million minutes is half an hour of missing market, and the count is the only form in which a reader sees that | `glossary.md` § Data quality, *gaps* |
| `venues[].gap_count_after_first_observation` | it equals `gap_count` for any asset listed at the window start | no, and this is the field a careless cut would take first: it is what separates a **young asset** from a **dead feed**. Without it a late-listed symbol is charged with history it never had, and a provider that stopped printing looks like one that started late | `status.py`, the comment above it; `skill_candle_canonicalisation.md` § 16 |
| `venues[].duplicate_count` | nothing | no: an **invariant**. A provider sending a minute twice is a defect, not a market | `skill_candle_canonicalisation.md` § 16 |
| `venues[].ohlc_violation_count` | the stronger predicate below subsumes it — a broken ordering is one of the ways `OHLC_INTACT_PREDICATE` fails | **yes, it goes, and `invalid_row_count` takes its place**. Two overlapping counters on one row, read by subtracting one from the other, is the complication this review was asked not to add: one column, catching strictly more, is the simpler and the safer answer. The geometry invariant stays where the object is different — on the canonical series | § 4, the validity table; § 16 |
| `venues[].zero_volume_bars`, `venues[].flat_bars` | `flat_bars` is a subset of `zero_volume_bars`, so one of the two is redundant | no, both stay, because the fact worth reading is their **difference**: a minute with no volume that is not flat is a price that moved with nobody trading. Neither column shows that alone, and the register already names both. Their levels are also a provider's own liquidity signature — 181 against 92 across two venues *is* the comparison | § 16, *a subset of `zero_volume_bars`*; `glossary.md` § Data quality |
| `venues[].first_observation_utc` | nothing | no: the date this provider's history begins, read against `window_start_utc` | `glossary.md` § Data quality, *first / last* |
| `venues[].last_observation_utc` | the canonical row already carries one | no: that one is the canonical series'. This one is **per provider**, and a provider that stopped is visible only here | as above |
| `venues[].ticker`, `venues[].symbol` | `symbol` is `ticker + QUOTE_ASSET`, so the page could build it | no — but not for the reason an earlier draft gave. `config.symbol()` takes no venue, so both venues carry the same string; it is **not** the provider's own name for the asset today. It stays because the module names the asset it measured and no reader derives it. Should a provider ever need its own name, that is a change to `config.symbol()`'s signature, not a claim one can make about this payload | `glossary.md` § Payload structure, *a reader never derives it from `symbol`*; `status.py`, `symbol_block`'s own docstring |
| `canonical_source[].row_count`, `.last_observation_utc` | nothing | no: the size and the end of the series research actually consumes; `serve.py` reads the second | `module_monitoring/serve.py`, the data block |
| `canonical_source[].binance_pct`, `.bybit_pct` | the shares themselves cannot go — they are the proof the tier order held, and the plainest statement of what "combining providers" produced — but the venue in the **key** can | **the shares stay, the two keys go**: one `source_share_pct_by_venue`, keyed by venue, replaces them. This mints no convention — the payload's `venues` object is already keyed by venue, and `<what>_by_<dimension>` is the grammar of `row_count_by_timeframe` and `columns_by_timeframe` — it applies one that was already binding to the last place breaking it. With `source_venues` beside it, a third provider now adds no key at all | `AGENTS.md` § Canonical vocabulary, *rule-derived structure*, which names **venues** as one of the families; `glossary.md` § Payload structure |
| `canonical_source[].ffill_bars` | nothing | no: the count of minutes nobody observed and the pipeline invented. It is the purest *shit-in* counter in the file | § 10; § 16 |
| `canonical_source[].ffill_pct` | `ffill_bars / row_count` | **yes, it goes** — question 2, both operands in the row | `skill_dashboard_conventions.md` |
| `canonical_source[].zero_volume_bars` | the venue rows already carry one each | no: a different object. Those measure what a provider printed; this measures what the canonical series became after the choice between them | § 6 |
| `canonical_source[].source_switch_count` | nothing | no: how often the series changed hands. It is the count that gives the next field a denominator, and the only measure of how much stitching the basket is doing | § 16 |
| `canonical_source[].max_abs_return_at_switch` | it cannot separate an artefact from a coincidence — a switch landing on a genuine large move inflates it | no, and the limit is stated rather than hidden: read **against** `max_abs_return_1m`, it answers one question honestly — *is the worst move at a handover larger than the worst move anywhere?* If it is not, stitching invented nothing. If it is, a hand looks | § 16; § 12 |
| `canonical_source[].max_abs_return_1m` | nothing | no: the print that will dominate every triple-barrier label, and the reference the field above is read against | § 16 |
| `canonical_source[].relative_divergence_p99` | one of the three divergence fields could carry the distribution | no: this is the one that carries it. Two providers agreeing to a basis point for ninety-nine minutes in a hundred is a structural fact about the pair, and a timestamp convention shifted on **one** venue explodes exactly this number — the strongest reason to keep it | § 12, *the distribution is exposed as mean / p99 / max* |
| `canonical_source[].relative_divergence_max` | p99 already says the providers agree | no: the single worst disagreement is precisely the shortcoming the owner's question asks for, and a p99 cannot show one minute | § 12 |
| `canonical_source[].relative_divergence_mean` | p99 and max carry the distribution | **yes, it goes** — question 3, and only that. Averaged over three million minutes it is dominated by the bulk and sits at two ten-thousandths of a percent whatever happens; a systematic provider offset moves p99 with it, so p99 already carries the reading the mean was kept for. `status.py`'s own printed table has never included it | § 12 |
| `canonical_source[].ohlc_violation_count` | the venue rows carry it | no: an **invariant**, and on a different object — the series after the join, which is what everything downstream reads | § 16 |
| `canonical_source[].longest_flat_run_minutes` | nothing — but it is **wrong** | no, it stays, **corrected**. Its scan calls a minute flat when `volume = 0` and open, high, low and close are equal. A forward-filled row is, by contract, the previous close repeated with zero volume — it satisfies that predicate on every row, while the stored `zero_volume` flag beside it is **false** on the same row. The block therefore carries two incompatible definitions of a minute without trades. With `ffill_bars` at zero the fault is invisible; the day a provider is replaced it becomes the headline number and reports a run of fabricated bars as a quiet market. The register already glosses it correctly — *the longest unbroken run of such minutes*, where such means valid canonical minutes — so only the predicate is wrong, and it takes `AND source <> 'ffill'` | `status.py`, the flat-run scan, against § 16's gloss; § 6, *`zero_volume` … is therefore false on every `ffill` row*; § 10, the forward-filled row; `module_data/ingest.py`, `CANONICAL_INSERT` |

## What is added, and why a report on excess adds anything

Six fields are absent that the owner's own question demands, and adding them is
the same rule as cutting: a purpose that can be named, and a seat that is the
cheapest keeping it. **Every one rides a pass that already runs.** Two of the six
— `source_venues` and `source_share_pct_by_venue` — are the generalisation
argued in the table above; the four below are detectors.

| field | the shortcoming nothing today catches | its seat |
|---|---|---|
| `venues[].invalid_row_count` | `ingest.py` rejects a venue row on a predicate far stronger than the status scan's: finite on all five fields, prices above zero, volume not negative. The status scan tested **geometry alone**. A provider shipping five percent of its rows with a zero price, a NaN or a sign-flipped volume showed coverage of 100.000 %, no gaps and no violations — the rejection was counted **nowhere**, and its only trace was one venue's share sagging in a table further down. Verified on a copy of the database: one row with `volume = -1` moves this counter from 0 to 1 and moves neither `coverage_pct` nor `gap_count` | a `FILTER` term in the venue scan, on the predicate **imported** from `ingest.py` — § 4 forbids a second copy of the validity rule. It replaces the geometry counter it subsumes |
| `canonical_source[].longest_ffill_run_minutes` | a provider dark for three days and a provider dropping 4 320 scattered minutes over four years publish an **identical** `ffill_bars`. The first is a fabricated regime a model will learn; the second is noise | a second run-group on `source = 'ffill'` in the flat-run scan, which already groups runs over the same ordering |
| `canonical_source[].repeated_candle_count` | the commonest dead-feed signature is the previous candle replayed **with its volume**. Timestamps differ, so there are no duplicates; geometry is intact, so there are no violations; volume is non-zero, so neither flatness column sees it; and `max_abs_return_1m` is a maximum and cannot see a long run of zeros | a lag over the five fields in the source-switch scan's existing window |
| `venues[].last_close` | every other content field is dimensionless — shares, ratios, counts. Nothing in the payload knows what a price *is*, so a delivery under the wrong symbol passes untouched | `arg_max(close, timestamp_ms)`, a streaming aggregate in the venue scan |

And one pass leaves. The max-return scan and the source-switch scan are the same
query: the switch scan's subquery already computes the lagged close and already
evaluates the absolute one-minute return. Added as a third select item to the
source-switch scan, `max_abs_return_1m` costs nothing and deletes a full window
pass over every canonical minute — measured at 0.22 s, and the value it returns
is identical to the one the deleted pass returned. `main` already merges scans by
alias, and the file's own rule — *every alias a scan publishes is the key it
becomes* — is untouched.

The run scan was rewritten rather than doubled. Asking it for two runs by adding
a second grouping cost 0.52 s; asking it instead for **the one state each minute
is in** — forward-filled, flat, or traded, decided in that order — answers both
in one grouping, at 0.60 s against the 0.62 s the single run cost before. The
second detector is free, and the state ladder is also what makes the correction
below unambiguous rather than a special case.

**First light.** On the current basket the new detectors report `invalid_row_count`
0 on both venues, and `repeated_candle_count` **1**: on 2025-06-29 Binance printed
a candle identical to the previous minute down to its volume of 2.723. One minute
in three million is not an alarm; that no existing field could see it is the point.

## What the tabs do not catch

Stated, not mitigated. Two shortcomings survive all thirty-three fields, and the
views must not be read as if they did not.

- **A timestamp convention shifted on both providers at once.** Bar-close
  against bar-open is a clean sixty-second offset. On **one** venue it explodes
  `relative_divergence_p99`. On **both** — which is exactly what replacing a
  provider does — the grid still joins, coverage is 100 %, there are no gaps, no
  duplicates and no forward fill, and one bar of look-ahead enters everything
  downstream. No field of a dimensionless payload can see it. `last_close` is
  half an anchor; the other half is a comparison against a source outside this
  pipeline, and that remains a hand's work.
- **Volume level, though volume chooses the venue.** § 7 makes volume
  load-bearing: the failover fires when the primary printed no trade and the
  secondary did. The payload observes volume only through the predicate
  `volume = 0`. A provider switching from base volume to quote turnover, or
  shipping a contract multiplier that is not one, changes every canonical volume
  by orders of magnitude with every field of this report unmoved — and volume
  flows straight into the feature layer. Measuring it is a decision this report
  does not take: a level is not a defect, and no threshold for one exists.

## What a stranger would still ask, and the answer

- **"You are writing a report on excess and it adds fields."** It adds
  six and removes nineteen, and the rule is the same in both directions: a field
  stays, goes or arrives on whether its purpose can be named. Three of the four
  answer the one question the owner asked and no existing field answers; the
  fourth is the first reader of two columns the tree has been writing and
  ignoring since the canonical table was created.
- **"You promised no faster chain, then deleted a pass."** One pass of six, by
  noticing two constants were one query — worth about a second on this basket,
  against a chain of fourteen minutes. It is a tidiness, not a speed-up, and
  the four tenths of one percent stands. The computation that is genuinely
  excessive is in the ML layer, not here: the per-fold SHAP attribution, the six
  strategy fields computed at all sixty-one threshold points and discarded at
  sixty of them, and the strategy half of every feature-set-search trial — each
  declared *never selected on* by the methodology that produces it. That is the
  next report, not this one.
- **"`glossary.md` calls `duplicate_count` minutes printed more than once."**
  It does, and `status.py` computes surplus **rows**. The two agree only at
  zero, which is where the field must be, so nothing has ever been wrong on the
  page. It is a wording defect that predates this review and is logged here
  rather than corrected in passing.

## What moves with it

`README_module_data.md` requires that the documents naming a fact move in the
same commit as the fact. For this change that is:
`module_skills/glossary.md` § Data quality and § Payload structure, in the canon
and in the four module copies the distribution stamps;
`module_data/skills/skill_candle_canonicalisation.md` § 16, whose rows gain the
four new observations and whose gloss of flatness is corrected against forward
fill; `README_module_data.md` § What the status stage measures; `README.md` § Dashboard and § Parity — the latter losing its `symbols[].db_bytes`
exclusion outright rather than repointing it; and
`README_module_monitoring.md` § Design rationale, the section-scripts row.
In code: `module_data/status.py`, `module_monitoring/data.js` and `index.html`,
and `module_monitoring/serve.py`, whose data block now reads one table where it
read two.

## Verdict

The data layer is not minimal against its own rule. Nineteen of forty-six fields
name no purpose the tree cannot already name elsewhere — an envelope carrying a
derived window and an engine version, a whole table that is another table read
twice, a count of ZIP files, a share and a mean. Cutting them costs nothing and
returns a payload of thirty-three fields, one table fewer and a set of documents
that says each thing once.

It was also not sufficient against the question its owner asks of it. A provider
shipping impossible rows, a provider going dark for days, and a provider frozen
on one candle all passed the forty-six fields without moving one of them; four
detectors close the first three, and the fourth — a timestamp convention shifted
on both providers at once — is named here as what it is, unmeasurable from inside
this pipeline. And one number, `longest_flat_run_minutes`, was wrong and silent
about it only because forward fill happened to be zero: on a copy of the database
with thirty forward-filled minutes inserted, the old scan reported a flat run of
thirty — fabrication as a quiet market — and the new one reports a flat run of
zero beside a forward-fill run of thirty.

Three invariants and thirty observations, in two tables, the invariants marked
and a rule for reading them: after a change of provider the invariants must still
be zero, and the observations are meant to move. No key names a provider any
more, so the next one is a line in `SOURCE_VENUES` and nothing else. That is the
cheapest shape that keeps the boundary this layer exists to hold — that what
enters the research is measured, and what was invented says so.
