"""Promotion of the serpentine search's proposal into the asset's own search state — a hand's choice, never a
derivation: the whole search state the proposal holds is copied, its columns into <TICKER>_feature_set.json, its
barrier geometry into <TICKER>_barriers.json and its hyper-parameter point into <TICKER>_hyperparameter_point.json,
and nothing else. A search proposes one search state at most, its champion, so there is no proposal to choose, and a
search that proposes none is refused in one line. The ML chain is rerun after it, and its study starts from the
promoted point on the promoted search state's own X and Y, so the point it keeps is worth at least the proposal's
path CAGR; the commit history is the record of every promotion, and the same proposal again changes nothing."""

from .. import config as features_config
from .. import dataset
from . import axis_feature_set, config, serpentine_search


def main() -> int:
    args = features_config.build_ticker_parser(
        "copy the serpentine search's proposal into the asset's own search state").parse_args()
    for ticker in features_config.parse_tickers(args.tickers):
        cat = dataset.load_json(features_config.catalogue_json(ticker))
        timeframes = config.timeframes(cat)
        # the one proposal of the search, or none — no search, or a search that ended without one; a proposal names
        # its state evaluation, and the search state it holds is that state evaluation's line of the ledger
        search_path = config.serpentine_search_json(ticker)
        proposals = dataset.load_json(search_path)["proposals"] if search_path.exists() else []
        if not proposals:
            raise SystemExit(f"{ticker}: no proposal to promote — the serpentine search proposes none")
        state_evaluation_index = proposals[0]["state_evaluation_index"]
        search_state = serpentine_search.theta(
            dataset.load_jsonl(config.serpentine_search_state_evaluations_jsonl(ticker))[state_evaluation_index - 1])
        # the asset's own search state as a search starts from it: the active columns, the active geometry and the point
        # its ML chain chose last
        active = {"columns_by_timeframe": {timeframe: list(columns) for timeframe, columns
                                           in serpentine_search.load_feature_columns(ticker, cat).items()},
                  "best_params": serpentine_search.load_best_params(ticker),
                  **serpentine_search.load_barrier_coordinates(ticker)}
        if search_state == active:
            print(f"{ticker} search state unchanged — the proposal, state evaluation {state_evaluation_index}, is the "
                  f"active search state", flush=True)
            continue
        added_column_count = axis_feature_set.column_count(axis_feature_set.columns_added(
            search_state["columns_by_timeframe"], active["columns_by_timeframe"], timeframes), timeframes)
        removed_column_count = axis_feature_set.column_count(axis_feature_set.columns_removed(
            search_state["columns_by_timeframe"], active["columns_by_timeframe"], timeframes), timeframes)
        moved_coordinate_names = [name for name in (*config.BARRIER_COORDINATE_NAMES, "best_params")
                 if search_state[name] != active[name]]
        dataset.write_json(config.feature_set_json(ticker),
                           {"columns_by_timeframe": search_state["columns_by_timeframe"]})
        dataset.write_json(config.barriers_json(ticker),
                           {name: search_state[name] for name in config.BARRIER_COORDINATE_NAMES})
        dataset.write_json(config.hyperparameter_point_json(ticker), {"best_params": search_state["best_params"]})
        print(f"{ticker} <- the proposal, state evaluation {state_evaluation_index} "
              f"(+{added_column_count} -{removed_column_count} columns"
              f"{', ' + ', '.join(moved_coordinate_names) if moved_coordinate_names else ''}); "
              f"rerun the ML chain for this asset", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
