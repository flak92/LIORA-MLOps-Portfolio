"""The feature-set axis of the search: the algebra of a set of columns and the moves a pass expands
one by — a column of the catalogue in, a column of the set out. The two search families are expanded in that
order, the second seeded by what the first left, which is what makes a pass one pass and not two.

It scores nothing and runs nothing: a turn asks for a search state to be scored and decides which moves it keeps."""

from . import config
from .. import config as features_config


# the helpers take the hierarchy from the asset's contract, never from the feature layer's own register: a search
# state is read here off the one contract it is scored against
def columns_added(columns_by_timeframe: dict, active: dict, timeframes: tuple[str, ...]) -> dict:
    return {timeframe: [name for name in columns_by_timeframe[timeframe] if name not in active[timeframe]]
            for timeframe in timeframes}


def columns_removed(columns_by_timeframe: dict, active: dict, timeframes: tuple[str, ...]) -> dict:
    return columns_added(active, columns_by_timeframe, timeframes)


def column_count(columns_by_timeframe: dict, timeframes: tuple[str, ...]) -> int:
    return sum(len(columns_by_timeframe[timeframe]) for timeframe in timeframes)


def with_column(columns_by_timeframe: dict, timeframe: str, name: str, catalogue_columns: list[str]) -> dict:
    """The set with one definition added on one timeframe, kept in catalogue order — the order the contract lists."""
    kept = set(columns_by_timeframe[timeframe]) | {name}
    return {**columns_by_timeframe,
            timeframe: [column for column in catalogue_columns if column in kept]}


def without_column(columns_by_timeframe: dict, timeframe: str, name: str) -> dict:
    return {**columns_by_timeframe,
            timeframe: [column for column in columns_by_timeframe[timeframe] if column != name]}


def moves(search_state: dict, cat: dict, profile: dict, search_family: str) -> tuple:
    """Every legal move of one search family from one search state: the direction the gate compares in, the move's
    own name for the progress line, and the whole search state it leads to. The search families are the two
    `config.ROUND_SCHEDULE` names for this axis.

    The catalogue fixes the order — the profile says which columns are admitted, never in what order they
    are tried — and the last column of a set is never taken out, so a search state always has one."""
    timeframes, catalogue = config.timeframes(cat), cat["columns_by_timeframe"]
    admitted, active = profile["columns_admitted_by_timeframe"], search_state["columns_by_timeframe"]
    if search_family == config.SERPENTINE_SEARCH_MOVE_FORWARD:
        return tuple(
            (config.SERPENTINE_SEARCH_MOVE_FORWARD, f"+{features_config.feature_id(name, timeframe)}",
             {**search_state, "columns_by_timeframe": with_column(active, timeframe, name, catalogue[timeframe])})
            for timeframe in timeframes for name in catalogue[timeframe]
            if name in admitted[timeframe] and name not in active[timeframe])
    if column_count(active, timeframes) <= 1:
        return ()
    return tuple(
        (config.SERPENTINE_SEARCH_MOVE_BACKWARD, f"-{features_config.feature_id(name, timeframe)}",
         {**search_state, "columns_by_timeframe": without_column(active, timeframe, name)})
        for timeframe in timeframes for name in active[timeframe])
