"""The feature layer's configuration — the timeframe register, the frozen research window, the indicator register and
the feature catalogue: the one definition every timeframe-shaped and feature-shaped thing derives from, and the
descriptors of the two families this module writes. What an operator may set is a record of CONFIGURABLES, fixed a priori; changing one
defines a different experiment or run, and the git commit is the record of which one ran."""

import argparse
import os
from datetime import UTC, datetime
from pathlib import Path

from .indicators import INDICATORS  # re-exported: the indicator register, one record per token beside its kernel

# ---- CONFIGURABLES: what an operator may set in this module, one record each, its value written nowhere else but in
# its registered copies — the constants below read it, the module's snapshot publishes the records and `make skills-configurables` renders every
# module's into one table. DEFAULT is a starting point of the experiment and WIRING a technical setting of a run; a
# value derived from them and a constant of the method stand below the block, and a register is no configurable
CONFIGURABLES = (
    # twice by extraction
    {"name": "RESEARCH_START_UTC", "value": "2021-01-01", "class": "DEFAULT", "unit": "UTC day, inclusive",
     "meaning": "the first day of the frozen research window", "tui": False, "experiment_identity": True,
     "requires_rerun": "features-all, ml-all", "risk": "another experiment: every artifact of the chain changes"},
    # twice by extraction
    {"name": "RESEARCH_END_UTC", "value": "2026-08-26", "class": "DEFAULT", "unit": "UTC day, exclusive",
     "meaning": "the day after the last of the frozen research window", "tui": False, "experiment_identity": True,
     "requires_rerun": "features-all, ml-all", "risk": "another experiment: every artifact of the chain changes"},
    {"name": "HIERARCHY_TIMEFRAMES", "value": ("1h", "8h", "1d"), "class": "DEFAULT",
     "unit": "timeframe tokens, finest first",
     "meaning": "the timeframes of the register: one partition of `bars` and one of `catalogue` each, the coarsest the trend "
                "gate's", "tui": False, "experiment_identity": True, "requires_rerun": "features-all, ml-all",
     "risk": "the contract changes shape, and every ML stage reads the new hierarchy"},
    {"name": "DECISION_TIMEFRAME", "value": "1h", "class": "DEFAULT", "unit": "timeframe token",
     "meaning": "the grid the decisions, the labels and the strategy stand on", "tui": False,
     "experiment_identity": True, "requires_rerun": "features-catalogue, ml-all",
     "risk": "another population of decisions: every label, fit and trade changes"},
    # twice by extraction
    {"name": "DUCKDB_MEMORY_LIMIT", "value": "4GB", "class": "WIRING", "unit": "DuckDB memory size",
     "meaning": "the ceiling of every DuckDB connection of the module, beside threads=1", "tui": False,
     "experiment_identity": False, "requires_rerun": "none",
     "risk": "a stage stops on memory where its container holds less"},
)
# every record's value by its name — what a constant below reads
VALUE_BY_CONFIGURABLE = {record["name"]: record["value"] for record in CONFIGURABLES}

# twice by extraction
MILLISECONDS_PER_SECOND = 1000
# twice by extraction
MILLISECONDS_PER_MINUTE = 60_000
# twice by extraction
MILLISECONDS_PER_DAY = 86_400_000
# twice by extraction
DUCKDB_MEMORY_LIMIT = VALUE_BY_CONFIGURABLE["DUCKDB_MEMORY_LIMIT"]
# twice by extraction
STORE_ASSETS_ARTIFACTS_DIR = Path(os.environ["STORE_ASSETS_ARTIFACTS_DIR"])
# twice by extraction
STORE_STATUS_DIR = Path(os.environ["STORE_STATUS_DIR"])


# twice by extraction
def to_utc_ms(day: str) -> int:
    """A UTC calendar day, `YYYY-MM-DD`, as the epoch milliseconds of its midnight."""
    return int(datetime.fromisoformat(day).replace(tzinfo=UTC).timestamp() * MILLISECONDS_PER_SECOND)


# twice by extraction
def artifact_dir(ticker: str) -> Path:
    """The asset's folder of non-tabular files — the segment `ticker=<TICKER>/` a partition carries, at the root of the
    store; inside it one file per artifact, named for it."""
    return STORE_ASSETS_ARTIFACTS_DIR / f"ticker={ticker}"


# twice by extraction
def partition_dir(family: str, ticker: str, timeframe: str | None = None, store: Path = STORE_ASSETS_ARTIFACTS_DIR) -> Path:
    """One partition of a table family: `<store>/<family>/ticker=<TICKER>/[timeframe=<timeframe>/]` — Hive's
    `key=value`, the value the ticker in capitals and the compact token; the store the artifacts store unless the
    family lives in another."""
    partition = store / family / f"ticker={ticker}"
    return partition if timeframe is None else partition / f"timeframe={timeframe}"


# twice by extraction
def ohlcv_1m_canonical_parquet(ticker: str) -> Path:
    """The canonical series of the asset — the family `ohlcv_1m_canonical`, one Parquet file per partition, written by ingest alone."""
    return partition_dir("ohlcv_1m_canonical", ticker) / "ohlcv_1m_canonical.parquet"


# twice by extraction
def bars_parquet(ticker: str, timeframe: str) -> Path:
    """One timeframe's bars of the asset — the family `bars`, partitioned by asset and timeframe, written by bars alone."""
    return partition_dir("bars", ticker, timeframe) / "bars.parquet"


def catalogue_parquet(ticker: str, timeframe: str) -> Path:
    """One timeframe's catalogue of the asset — the family `catalogue`, partitioned by asset and timeframe; the ML layer
    reaches a partition through the contract, never through this descriptor."""
    return partition_dir("catalogue", ticker, timeframe) / "catalogue.parquet"


# twice by extraction
def schema_json(family: str, store: Path = STORE_ASSETS_ARTIFACTS_DIR) -> Path:
    """A family's schema as data, beside its partitions: the columns of the union of the partitions, written by the family's
    one writer; the store the artifacts store unless the family lives in another."""
    return store / family / "schema.json"


# twice by extraction
def build_ticker_parser(description: str) -> argparse.ArgumentParser:
    """The one CLI every stage shares: --tickers, required — the launcher names the basket, a stage never does."""
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--tickers", required=True, help="comma-separated tickers, e.g. BTC or BTC,ETH")
    return ap


# twice by extraction
def parse_tickers(tickers_csv: str) -> list[str]:
    """The --tickers value as a basket: split on commas, trimmed, upper case, an empty item dropped."""
    return [ticker.strip().upper() for ticker in tickers_csv.split(",") if ticker.strip()]


# twice by extraction
def rounded(value, ndigits: int):
    """round() that tolerates None: the NULL a scan reports when no row qualifies, the None a fold without trades reports."""
    return None if value is None else round(float(value), ndigits)


# twice by extraction
MINUTES_PER_HOUR = 60
MILLISECONDS_PER_HOUR = MINUTES_PER_HOUR * MILLISECONDS_PER_MINUTE

# ---- frozen research window (later data top-ups do not change this experiment). The start repeats module_data's
# DATA_WINDOW_START_UTC on purpose rather than importing it: the download window may be widened without moving an
# experiment already run against it.
# twice by extraction
RESEARCH_START_UTC = VALUE_BY_CONFIGURABLE["RESEARCH_START_UTC"]   # inclusive
# twice by extraction
RESEARCH_END_UTC = VALUE_BY_CONFIGURABLE["RESEARCH_END_UTC"]       # exclusive
# twice by extraction
RESEARCH_START_MS = to_utc_ms(RESEARCH_START_UTC)
# twice by extraction
RESEARCH_END_MS = to_utc_ms(RESEARCH_END_UTC)

# ---- the timeframe hierarchy: the experiment's literal, finest first — the decision grid, the trend gate's timeframe
# and the count the strategy's agreement reads all follow from it, so a new token is one line here and a new
# experiment. Every entry is an exact aggregation of the canonical 1m series, written by bars.py; a token is
# <integer><unit>, and its duration and the slot the snapshot carries derive from the token (skills/skill_feature_taxonomy.md)
HIERARCHY_TIMEFRAMES = VALUE_BY_CONFIGURABLE["HIERARCHY_TIMEFRAMES"]
DECISION_TIMEFRAME = VALUE_BY_CONFIGURABLE["DECISION_TIMEFRAME"]
TIMEFRAME_UNIT_MS = {"m": MILLISECONDS_PER_MINUTE, "h": MILLISECONDS_PER_HOUR, "d": MILLISECONDS_PER_DAY}
# the five slots of module_skills/skill_sorting_files_naming_standard.md, finest first, and the field each unit fills
TIMEFRAME_SLOT_FIELDS = ("ss", "mm", "hh", "dd", "MM")
TIMEFRAME_UNIT_SLOT_FIELD = {"m": 1, "h": 2, "d": 3}


def timeframe_duration_ms(token: str) -> int:
    return int(token[:-1]) * TIMEFRAME_UNIT_MS[token[-1]]


def timeframe_slot(token: str) -> str:
    """The token in the five slots: its number, zero-padded, in its unit's field; the unit letters everywhere else."""
    fields = list(TIMEFRAME_SLOT_FIELDS)
    fields[TIMEFRAME_UNIT_SLOT_FIELD[token[-1]]] = f"{int(token[:-1]):02d}"
    return "-".join(fields)


TIMEFRAME_DURATION_MS = {timeframe: timeframe_duration_ms(timeframe) for timeframe in HIERARCHY_TIMEFRAMES}
TIMEFRAME_SLOT = {timeframe: timeframe_slot(timeframe) for timeframe in HIERARCHY_TIMEFRAMES}
# ---- the terms: a series of the bars, or an indicator of the register with its one integer parameter glued to the
# token in a name (exponential_smoothing20, recursive_mean_gain_share14); the series' and the indicators' invariants
# are their register records in indicators.py, and the operators and normalisers that compose them are the registers
# beside their kernels in catalogue.py

# ---- the feature catalogue: one record per feature definition, from which the name, the computation, the history
# and the required warm-up derive. A term is ("<indicator>", <parameter_bars>) on the default series close,
# ("<series>", "<indicator>", <parameter_bars>) on another series, or ("<series>",) — a bare series. The five
# definitions of the default set lead, in the order the frozen experiment stacks them: the column order is what
# the model samples by position. `tier` says how structurally flexible a definition is, and
# `historical_aliases` the popular names that denote the whole of it — provenance, never a key or a column.
FEATURE_CATALOGUE = (
    {"terms": (("exponential_smoothing", 20), ("exponential_smoothing", 50), ("true_range", "recursive_mean", 14)),
     "operators": ("minus", "over"),
     "range": "unbounded, dimensionless", "timeframes": HIERARCHY_TIMEFRAMES, "tier": "CORE",
     "historical_aliases": ("MACD line",),
     "definition_in_default_set": True},
    {"terms": (("recursive_mean_gain_share", 14),), "normaliser": "centered",
     "range": "[-1, 1]", "timeframes": HIERARCHY_TIMEFRAMES, "tier": "EXTENDED",
     "definition_in_default_set": True},
    {"terms": (("true_range", "recursive_mean", 14), ("close",)), "operators": ("over",),
     "range": "> 0, dimensionless", "timeframes": HIERARCHY_TIMEFRAMES, "tier": "CORE",
     "historical_aliases": ("ATR", "NATR"),
     "definition_in_default_set": True},
    {"terms": (("rolling_range_position", 20),),
     "range": "[0, 1]", "timeframes": HIERARCHY_TIMEFRAMES, "tier": "CORE",
     "definition_in_default_set": True},
    {"terms": (("logarithmic_volume", "rolling_standard_score", 50),),
     "range": "dimensionless", "timeframes": HIERARCHY_TIMEFRAMES, "tier": "CORE",
     "historical_aliases": ("Relative volume",),
     "definition_in_default_set": True},
    {"terms": (("rolling_standard_score", 20),),
     "range": "dimensionless", "timeframes": HIERARCHY_TIMEFRAMES, "tier": "CORE",
     "definition_in_default_set": False},
    {"terms": (("close",), ("rolling_mean", 50), ("true_range", "recursive_mean", 14)),
     "operators": ("minus", "over"),
     "range": "unbounded, dimensionless", "timeframes": HIERARCHY_TIMEFRAMES, "tier": "CORE",
     "definition_in_default_set": False},
    {"terms": (("close",), ("rolling_mean", 200), ("true_range", "recursive_mean", 14)),
     "operators": ("minus", "over"),
     "range": "unbounded, dimensionless", "timeframes": HIERARCHY_TIMEFRAMES[-1:], "tier": "CORE",
     "definition_in_default_set": False},
    # ---- the definitions the conversion of the recurring human and academic families brought in, appended so the
    # positions above do not move; none of them joins the default set, which stays the frozen experiment's five
    {"terms": (("close",), ("exponential_smoothing", 20), ("true_range", "recursive_mean", 14)),
     "operators": ("minus", "over"),
     "range": "unbounded, dimensionless", "timeframes": HIERARCHY_TIMEFRAMES, "tier": "CORE",
     "definition_in_default_set": False},
    {"terms": (("rolling_standard_deviation", 20), ("close",)), "operators": ("over",),
     "range": "> 0, dimensionless", "timeframes": HIERARCHY_TIMEFRAMES, "tier": "CORE",
     "definition_in_default_set": False},
    {"terms": (("relative_change", 10),),
     "range": "unbounded, dimensionless", "timeframes": HIERARCHY_TIMEFRAMES, "tier": "CORE",
     "definition_in_default_set": False},
    {"terms": (("close",), ("open",), ("true_range", "recursive_mean", 14)), "operators": ("minus", "over"),
     "range": "unbounded, dimensionless", "timeframes": HIERARCHY_TIMEFRAMES, "tier": "CORE",
     "definition_in_default_set": False},
    {"terms": (("high",), ("low",), ("true_range", "recursive_mean", 14)), "operators": ("minus", "over"),
     "range": ">= 0, dimensionless", "timeframes": HIERARCHY_TIMEFRAMES, "tier": "CORE",
     "definition_in_default_set": False},
    {"terms": (("recursive_mean_upward_movement_share", 14),), "normaliser": "centered",
     "range": "[-1, 1]", "timeframes": HIERARCHY_TIMEFRAMES, "tier": "EXTENDED",
     "definition_in_default_set": False},
    {"terms": (("recursive_mean_directional_movement_imbalance", 14),),
     "range": "[0, 100]", "timeframes": HIERARCHY_TIMEFRAMES, "tier": "EXTENDED",
     "definition_in_default_set": False},
    {"terms": (("close",), ("rolling_volume_weighted_mean", 20), ("true_range", "recursive_mean", 14)),
     "operators": ("minus", "over"),
     "range": "unbounded, dimensionless", "timeframes": HIERARCHY_TIMEFRAMES, "tier": "EXTENDED",
     "definition_in_default_set": False},
    {"terms": (("cumulative_signed_volume", "rolling_standard_score", 50),),
     "range": "dimensionless", "timeframes": HIERARCHY_TIMEFRAMES, "tier": "EXTENDED",
     "historical_aliases": ("OBV",),
     "definition_in_default_set": False},
    {"terms": (("rolling_volume_weighted_close_location", 20),),
     "range": "[-1, 1]", "timeframes": HIERARCHY_TIMEFRAMES, "tier": "EXTENDED",
     "definition_in_default_set": False},
    {"terms": (("rolling_money_flow_gain_share", 14),), "normaliser": "centered",
     "range": "[-1, 1]", "timeframes": HIERARCHY_TIMEFRAMES, "tier": "EXTENDED",
     "definition_in_default_set": False},
    {"terms": (("exponential_smoothing", 8), ("exponential_smoothing", 21), ("true_range", "recursive_mean", 14)),
     "operators": ("minus", "over"),
     "range": "unbounded, dimensionless", "timeframes": HIERARCHY_TIMEFRAMES, "tier": "COMPOSITE",
     "historical_aliases": ("Market Cipher ribbon",),
     "definition_in_default_set": False},
    {"terms": (("exponential_smoothing", 21), ("exponential_smoothing", 55), ("true_range", "recursive_mean", 14)),
     "operators": ("minus", "over"),
     "range": "unbounded, dimensionless", "timeframes": HIERARCHY_TIMEFRAMES, "tier": "COMPOSITE",
     "historical_aliases": ("Market Cipher ribbon",),
     "definition_in_default_set": False},
)


def term_name(term: tuple) -> str:
    """A term as its name is written: a bare series is its token; an indicator glues its parameter, prefixed by its
    series unless the series is close or the indicator's inputs are fixed."""
    if len(term) == 1:
        return term[0]
    series, indicator, parameter_bars = ("close",) + term if len(term) == 2 else term
    prefix = "" if series == "close" or "inputs" in INDICATORS[indicator] else f"{series}_"
    return f"{prefix}{indicator}{parameter_bars}"


def feature_definition_name(definition: dict) -> str:
    """[<normaliser>_]<term>{_<operator>_<term>} — read off the record, never written by hand."""
    name = term_name(definition["terms"][0])
    for operator, term in zip(definition.get("operators", ()), definition["terms"][1:]):
        name += f"_{operator}_{term_name(term)}"
    normaliser = definition.get("normaliser")
    return f"{normaliser}_{name}" if normaliser else name


# twice by extraction
def feature_id(definition_name: str, timeframe: str) -> str:
    """The column of X and the key of an importance: the definition aligned to the decision grid on one timeframe."""
    return f"{definition_name}_{timeframe}"


def term_indicator(term: tuple) -> str | None:
    """The indicator token of a term — a bare series has none."""
    return None if len(term) == 1 else term[-2]


def term_warmup_bars(term: tuple) -> int:
    """Bars of the term's timeframe before its value is settled; a bare series needs none. A window over changes
    needs the bar before it as well, its record's `warmup_offset_bars`: its first change is taken off that bar."""
    if len(term) == 1:
        return 0
    record = INDICATORS[term_indicator(term)]
    return record["warmup_multiple"] * term[-1] + record.get("warmup_offset_bars", 0)


def definition_warmup_bars(definition: dict) -> int:
    return max(term_warmup_bars(term) for term in definition["terms"])


# The experiment's warm-up, in bars of the top timeframe — read off the catalogue, not written beside it, so a
# definition with a longer memory raises it by itself and is never evaluated before its own value has settled.
WARMUP_TOP_TIMEFRAME_BARS = max(definition_warmup_bars(definition) for definition in FEATURE_CATALOGUE)
WARMUP_END_MS = RESEARCH_START_MS + WARMUP_TOP_TIMEFRAME_BARS * TIMEFRAME_DURATION_MS[HIERARCHY_TIMEFRAMES[-1]]


def definition_effective_history_hours(definition: dict, timeframe: str) -> float:
    """The longest parameter of the definition read on that timeframe: a window's history is the window, a
    recursion's the bars carrying most of its weight — the number the nesting of the timeframes compares."""
    longest_parameter_bars = max((term[-1] for term in definition["terms"] if len(term) > 1), default=0)
    return longest_parameter_bars * TIMEFRAME_DURATION_MS[timeframe] / MILLISECONDS_PER_HOUR


def catalogue_columns(timeframe: str) -> tuple[str, ...]:
    """The definitions offered on one timeframe, in catalogue order — the columns of that timeframe's parquet."""
    return tuple(feature_definition_name(definition) for definition in FEATURE_CATALOGUE
                 if timeframe in definition["timeframes"])


# every feature id the catalogue offers, timeframe-major and catalogue-order within
CATALOGUE_COLUMNS = tuple(feature_id(name, timeframe)
                          for timeframe in HIERARCHY_TIMEFRAMES for name in catalogue_columns(timeframe))
# the set an asset holds until a promotion: the default definitions on every timeframe they are offered on
DEFAULT_FEATURE_COLUMNS_BY_TIMEFRAME = {
    timeframe: tuple(feature_definition_name(definition) for definition in FEATURE_CATALOGUE
                     if definition["definition_in_default_set"] and timeframe in definition["timeframes"])
    for timeframe in HIERARCHY_TIMEFRAMES
}


def catalogue_schema() -> list[dict[str, str]]:
    """The schema of the `catalogue` family, from the register: the decision grid, then every definition offered on a
    timeframe of the hierarchy, in catalogue order — the union of the partitions' columns, a partition holding the
    definitions offered on its timeframe."""
    return [{"column": "decision_ts", "type": "BIGINT"},
            *({"column": feature_definition_name(definition), "type": "DOUBLE"} for definition in FEATURE_CATALOGUE
              if any(timeframe in definition["timeframes"] for timeframe in HIERARCHY_TIMEFRAMES))]


FEATURES_STATUS_JSON_PATH = STORE_STATUS_DIR / "features_status.json"   # the snapshot this module writes: the catalogue's facts, each asset's row counts and its serpentine search


# twice by extraction
def catalogue_json(ticker: str):
    """The asset's copy of the feature layer's contract — what the ML layer reads instead of the feature configuration."""
    return artifact_dir(ticker) / f"{ticker}_catalogue.json"


def catalogue_contract(ticker: str) -> dict:
    """The catalogue as the ML layer needs it, per asset: the decision grid, the hierarchy with each timeframe's
    duration, the warm-up, the columns offered per timeframe in catalogue order, the default set, and the partition of
    the catalogue family each timeframe's columns live in, as a path under the artifacts store — so ML parses no token,
    builds no path from this module's grammar and imports nothing."""
    return {
        "decision_timeframe": DECISION_TIMEFRAME,
        "timeframes": [{"timeframe": timeframe, "duration_ms": TIMEFRAME_DURATION_MS[timeframe]}
                       for timeframe in HIERARCHY_TIMEFRAMES],
        "warmup_top_timeframe_bars": WARMUP_TOP_TIMEFRAME_BARS,
        "warmup_end_ms": WARMUP_END_MS,
        "columns_by_timeframe": {timeframe: list(catalogue_columns(timeframe)) for timeframe in HIERARCHY_TIMEFRAMES},
        "default_columns_by_timeframe": {timeframe: list(DEFAULT_FEATURE_COLUMNS_BY_TIMEFRAME[timeframe])
                                         for timeframe in HIERARCHY_TIMEFRAMES},
        "parquet_by_timeframe": {timeframe: catalogue_parquet(ticker, timeframe).relative_to(STORE_ASSETS_ARTIFACTS_DIR).as_posix()
                                 for timeframe in HIERARCHY_TIMEFRAMES},
    }
