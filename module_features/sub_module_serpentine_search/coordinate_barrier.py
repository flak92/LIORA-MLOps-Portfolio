"""The barrier coordinate of the search: the geometry of an event, moved one grid point at a time.

Two families, in the order a pass expands them. **trade** moves the trade's own exit — its take-profit and
its stop, which the label never sees. **label** moves the geometry Y itself is written with — the multiplier
the barriers stand at and the horizon they stand for.

That ordering is the whole economy of the loop: the children of the trade family differ from each other only
in where a position leaves, and the evaluator reads that off the states themselves and fits them once. This
coordinate says which states there are, never what they cost."""

from __future__ import annotations

from . import config

# which coordinates each family of `config.ROUND_SCHEDULE` moves
FAMILY_COORDINATES = {"trade": config.TRADE_EXIT_COORDINATE_NAMES,
                      "label": ("label_barrier_true_range_multiplier", "label_horizon")}


def grid(profile: dict, name: str) -> list:
    """One coordinate's grid as the state carries its values, in the order it is searched."""
    return [config.BARRIER_COORDINATE_CASTS[name](value) for value in profile["grid_by_coordinate"][name]]


def moves(state: dict, profile: dict, family: str) -> tuple:
    """Every legal move of one family from one state: one grid point down and one up, per coordinate the
    family moves, in the order the register names them.

    A barrier move only ever grows a state, so it is compared forward — strictly better on every validation
    fold. A grid that does not hold the state's own value fails on the lookup: a profile says where a search
    may go, and it has to say where it starts."""
    return tuple(
        (config.SERPENTINE_SEARCH_MOVE_FORWARD,
         f"{name} {state[name]} -> {points[neighbour]}",
         {**state, name: points[neighbour]})
        for name in FAMILY_COORDINATES[family]
        for points in (grid(profile, name),)
        for neighbour in (points.index(state[name]) - 1, points.index(state[name]) + 1)
        if 0 <= neighbour < len(points))
