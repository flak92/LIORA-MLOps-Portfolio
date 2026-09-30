"""The barrier axis of the search: the geometry of an event, moved one grid point at a time.

Two search families, in the order a pass expands them. **trade** moves the trade's own exit — its take-profit and
its stop, which the label never sees. **label** moves the geometry Y itself is written with — the multiplier
the barriers stand at and the label horizon they stand for.

That ordering is the whole economy of the axis: the children of the trade family differ from each other only
in where a position leaves, and the evaluator reads that off the search states themselves and fits them once.
This axis says which search states there are, never what they cost."""

from . import config

# which coordinates each search family of `config.ROUND_SCHEDULE` moves
COORDINATES_BY_SEARCH_FAMILY = {"trade": config.TRADE_EXIT_COORDINATE_NAMES,
                                "label": ("label_barrier_true_range_multiplier", "label_horizon")}


def grid(profile: dict, name: str) -> list:
    """One coordinate's grid as the search state carries its values, in the order it is searched."""
    return [config.BARRIER_COORDINATE_CASTS[name](value) for value in profile["grid_by_coordinate"][name]]


def moves(search_state: dict, profile: dict, search_family: str) -> tuple:
    """Every legal move of one search family from one search state: one grid point down and one up, per coordinate
    the family moves, in the order the register names them.

    A barrier move only ever grows a search state, so it is compared forward — strictly better on every validation
    fold. A grid that does not hold the search state's own value fails on the lookup: a profile says where a search
    may go, and it has to say where it starts."""
    return tuple(
        (config.SERPENTINE_SEARCH_MOVE_FORWARD,
         f"{name} {search_state[name]} -> {points[neighbour]}",
         {**search_state, name: points[neighbour]})
        for name in COORDINATES_BY_SEARCH_FAMILY[search_family]
        for points in (grid(profile, name),)
        for neighbour in (points.index(search_state[name]) - 1, points.index(search_state[name]) + 1)
        if 0 <= neighbour < len(points))
