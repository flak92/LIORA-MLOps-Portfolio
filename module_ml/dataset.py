"""Shared IO for the ML layer: load_catalogue — the one read of the feature layer's contract, once per stage — load_xy
and build_xy with the asset's feature set, load_barriers, load_feature_columns, build_x, write_json and load_json, and the
parquet writer and the schema read off a written partition the label and prediction writers use — twice by extraction,
identical in module_features/dataset.py."""

import csv
import json
import tempfile
from pathlib import Path

import duckdb
import numpy as np

from . import config


# twice by extraction
def load_partition_schema(con: duckdb.DuckDBPyConnection, path: Path) -> list[dict[str, str]]:
    """The columns of a written partition, as data: `column` and DuckDB's `type` in the file's order — the schema of a
    homogeneous family, whose every partition carries the same; the partition keys stay out because the file is read
    as a file, not as a Hive tree."""
    return [{"column": name, "type": kind}
            for name, kind, *_ in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{path}', hive_partitioning=false)").fetchall()]


# twice by extraction
def write_parquet(path: Path, columns: dict[str, str], rows, order_by: str, family: str | None = None) -> Path:
    """zstd parquet from an iterable of rows via a CSV spool: numpy -> repr(float) -> read_csv round-trips float64 exactly.
    Named a homogeneous family's partition, it writes the family's `schema.json` beside the partitions too."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="") as f:
        csv.writer(f).writerows(rows)
        spool = Path(f.name)
    try:
        spec = ", ".join(f"'{name}': '{sqltype}'" for name, sqltype in columns.items())
        con = duckdb.connect()
        con.execute(f"SET memory_limit='{config.DUCKDB_MEMORY_LIMIT}'")
        con.execute("SET threads=1")   # float summation must not be reordered
        con.execute(
            f"""COPY (SELECT * FROM read_csv('{spool}', header=false, columns={{{spec}}})
                      ORDER BY {order_by})
                TO '{path}' (FORMAT PARQUET, COMPRESSION zstd)"""
        )
        if family is not None:
            write_json(config.schema_json(family), load_partition_schema(con, path))
        con.close()
    finally:
        spool.unlink(missing_ok=True)
    return path


# twice by extraction
def to_json_safe(obj):
    """numpy containers and scalars to canonical Python; a non-finite float becomes null."""
    if isinstance(obj, dict):
        return {str(k): to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_json_safe(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return [to_json_safe(v) for v in obj.tolist()]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.floating):
        obj = float(obj)
    if isinstance(obj, float) and not np.isfinite(obj):
        return None
    return obj


# twice by extraction
def write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_json_safe(payload), sort_keys=True, indent=1) + "\n", encoding="utf-8")


# twice by extraction
def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def append_jsonl(path: Path, payload: dict) -> None:
    """One object a line, appended: a ledger grows by what it gains and is never rewritten, so writing a
    trial costs the trial and not the trials before it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as ledger:
        ledger.write(json.dumps(to_json_safe(payload), sort_keys=True) + "\n")


# twice by extraction
def load_jsonl(path: Path) -> list[dict]:
    """A ledger as it was written: one object a line, in the order they were appended."""
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def load_catalogue(ticker: str) -> dict:
    """The feature layer's contract for the asset, as features-catalogue wrote it — read once per stage and carried as
    `cat`; the one I/O the contract ever costs."""
    return load_json(config.catalogue_json(ticker))


# twice by extraction
def load_feature_columns(ticker: str, cat: dict) -> dict[str, tuple[str, ...]]:
    """The asset's feature set by timeframe: the promoted file's columns, in catalogue order, else the default set."""
    path = config.feature_set_json(ticker)
    if not path.exists():
        return {timeframe: tuple(cat["default_columns_by_timeframe"][timeframe]) for timeframe in config.timeframes(cat)}
    promoted = load_json(path)["columns_by_timeframe"]
    return {timeframe: tuple(sorted(promoted[timeframe], key=cat["columns_by_timeframe"][timeframe].index))
            for timeframe in config.timeframes(cat)}


def barriers_from(coordinates: dict) -> dict:
    """The barrier geometry a search state carries, with its label horizon token turned into minutes — the one place a
    token becomes a number, whether it came from the promoted file or from a search state.

    Every coordinate is cast here too, by the register's own casts: a promoted file is JSON a hand may edit,
    and `2` is an int where `2.0` is a float, which a search state key compares as a different search state."""
    return {**coordinates,
            **{name: config.BARRIER_COORDINATE_CASTS[name](coordinates[name])
               for name in config.BARRIER_COORDINATE_NAMES},
            "label_horizon_minutes": config.HORIZON_TOKEN_MINUTES[coordinates["label_horizon"]]}


def load_barriers(ticker: str) -> dict:
    """The asset's barrier geometry: the promoted file's when it exists, else the frozen constants of
    the experiment. The label horizon travels as a duration token and is turned into minutes here and
    nowhere else, so the grid, the purge, the scored population and the trade's eligibility read one
    number."""
    path = config.barriers_json(ticker)
    promoted = load_json(path) if path.exists() else {}
    return barriers_from({
        name: promoted.get(name, start) for name, start in config.START_BY_COORDINATE_DEFAULT.items()
    })


def load_maximum_label_horizon_minutes(ticker: str, barriers: dict) -> int:
    """The maximum label horizon of the asset's experiment, in minutes — the longest of the label horizons it admits:
    every token of the label_horizon grid its serpentine search profile froze, and the asset's own, which a searchable
    grid holds anyway and which is the whole grid of an asset with no profile. Every search state of the experiment and
    the chain are scored on the decisions it leaves room for, so a promoted search state scores in the chain what it
    scored in the search (`RESEARCH-SEMANTICS-COMPARABLE-STATES-SHARE-ONE-EVALUATION-POPULATION`). Each token becomes
    minutes through `barriers_from()`, the one place a token becomes a number."""
    path = config.serpentine_search_profile_json(ticker)
    grid = load_json(path)["grid_by_coordinate"]["label_horizon"] if path.exists() else []
    return max(barriers_from({**barriers, "label_horizon": token})["label_horizon_minutes"]
               for token in [barriers["label_horizon"], *grid])


def build_x(catalogue_values: dict[str, np.ndarray], columns_by_timeframe: dict[str, tuple[str, ...]],
            timeframes: tuple[str, ...]) -> tuple[np.ndarray, tuple[str, ...]]:
    """The model's matrix from the catalogue's values: the set's features, timeframe-major and catalogue-order
    within — the order is what the model samples by position. Returns (x, its feature ids)."""
    feature_columns = tuple(config.feature_id(name, timeframe)
                            for timeframe in timeframes for name in columns_by_timeframe[timeframe])
    return np.column_stack([catalogue_values[c] for c in feature_columns]), feature_columns


def load_feature_material(ticker: str, cat: dict, timeframes: tuple[str, ...]) -> tuple[dict, list]:
    """The catalogue's partitions as build_xy takes them: every catalogue column's values, keyed by feature id,
    and the decision grid each timeframe was read on. `score.py`, which relabels an asset for a search state, reads
    these once and joins them to each new Y."""
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{config.DUCKDB_MEMORY_LIMIT}'")
    con.execute("SET threads=1")   # float summation must not be reordered
    catalogue_values, decision_grids = {}, []
    for timeframe in timeframes:
        per_timeframe = con.execute(
            f"SELECT * FROM read_parquet('{config.catalogue_parquet(cat, timeframe)}', hive_partitioning=false) ORDER BY decision_ts"
        ).fetchnumpy()
        for name in cat["columns_by_timeframe"][timeframe]:
            catalogue_values[config.feature_id(name, timeframe)] = per_timeframe[name]
        decision_grids.append(per_timeframe["decision_ts"].astype(np.int64))
    con.close()
    return catalogue_values, decision_grids


def load_label_events(ticker: str, cat: dict) -> dict[str, np.ndarray]:
    """Y as labels.py wrote it, by decision."""
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{config.DUCKDB_MEMORY_LIMIT}'")
    con.execute("SET threads=1")   # float summation must not be reordered
    label_events = con.execute(
        f"""SELECT * FROM read_parquet('{config.labels_parquet(ticker, cat["decision_timeframe"])}', hive_partitioning=false)
            ORDER BY decision_ts"""
    ).fetchnumpy()
    con.close()
    return label_events


def load_xy(ticker: str) -> dict:
    """The asset's catalogue and labels partitions read once and handed to build_xy: X and Y on Y's decision
    grid, with the values of every catalogue column beside X and the contract that named them; X may
    carry tail rows Y had to drop."""
    cat = load_catalogue(ticker)
    timeframes = config.timeframes(cat)
    catalogue_values, decision_grids = load_feature_material(ticker, cat, timeframes)
    barriers = load_barriers(ticker)
    return build_xy(cat, timeframes, catalogue_values, decision_grids, load_label_events(ticker, cat),
                    load_feature_columns(ticker, cat), barriers, load_maximum_label_horizon_minutes(ticker, barriers))


def build_xy(cat: dict, timeframes: tuple[str, ...], catalogue_values: dict[str, np.ndarray],
             decision_grids: list[np.ndarray], label_events: dict[str, np.ndarray],
             columns_by_timeframe: dict[str, tuple[str, ...]], barriers: dict,
             maximum_label_horizon_minutes: int) -> dict:
    """X and Y on Y's decision grid from arrays already in memory — the feature grids joined to Y by
    position, every catalogue column narrowed to Y's rows and the set's columns stacked. It reads no
    file, so `score.py`, relabelling an asset in process, builds X and Y the way the stage does."""
    # the files are joined by position, so they must share one decision grid
    x_decision_ts = decision_grids[0]
    assert all(np.array_equal(x_decision_ts, grid) for grid in decision_grids[1:]), \
        "the catalogue's partitions disagree on the decision grid"
    y_decision_ts = label_events["decision_ts"].astype(np.int64)
    pos = np.searchsorted(x_decision_ts, y_decision_ts)
    assert np.array_equal(x_decision_ts[pos], y_decision_ts), "X/Y decision grids do not align"
    catalogue_values = {c: catalogue_values[c][pos] for c in config.catalogue_feature_ids(cat)}
    x, feature_columns = build_x(catalogue_values, columns_by_timeframe, timeframes)
    return {
        "catalogue": cat,
        # the geometry that produced Y, carried beside it: the label horizon its labels and a trade's exit walk, and
        # the multipliers the trade's own exit is scaled by
        "barriers": barriers,
        # the experiment's, not the search state's: the one evaluation population every fold admits and scores
        "maximum_label_horizon_minutes": maximum_label_horizon_minutes,
        "timeframes": timeframes,
        "decision_ts": y_decision_ts,
        "entry_ts": label_events["entry_ts"].astype(np.int64),
        "x": x,
        "feature_columns": feature_columns,
        "catalogue_values": catalogue_values,
        "y": label_events["y"].astype(np.int8),
        "event_end_ts": label_events["event_end_ts"].astype(np.int64),
        "entry_minute_traded": label_events["entry_minute_traded"].astype(bool),
        "label_valid": label_events["label_valid"].astype(bool),
        # the supervised population: a traded entry minute and an unambiguous event
        "sample_valid": label_events["entry_minute_traded"].astype(bool) & label_events["label_valid"].astype(bool),
        "entry_price": label_events["entry_price"].astype(np.float64),
        "upper_barrier": label_events["upper_barrier"].astype(np.float64),
        "lower_barrier": label_events["lower_barrier"].astype(np.float64),
    }
