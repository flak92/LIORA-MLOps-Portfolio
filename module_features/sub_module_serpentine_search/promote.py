"""Promotion of the serpentine search's proposal into the asset's own state — a hand's choice, never a derivation:
the whole state the proposal holds is copied, its columns into <TICKER>_feature_set.json, its barrier geometry into
<TICKER>_barriers.json and its hyper-parameter point into <TICKER>_hyperparameter_point.json, and nothing else. A
search proposes one state at most, its champion, so there is no proposal to choose, and a search that proposes none
is refused in one line. The ML chain is rerun after it, and its study starts from the promoted point on the promoted
state's own X and Y, so the point it keeps is worth at least the proposal's path CAGR; the commit history is the
record of every promotion, and the same proposal again changes nothing."""

from __future__ import annotations

from .. import config as features_config
from .. import dataset
from . import config, coordinate_feature_set, serpentine_search


def main() -> int:
    args = features_config.build_ticker_parser(
        "copy the serpentine search's proposal into the asset's own state").parse_args()
    for ticker in features_config.parse_tickers(args.tickers):
        cat = dataset.load_json(features_config.catalogue_json(ticker))
        timeframes = config.timeframes(cat)
        # the one proposal of the search, or none — no search, or a search that ended without one; a proposal names
        # its trial, and the state it holds is that trial's line of the ledger
        search_path = config.serpentine_search_json(ticker)
        proposals = dataset.load_json(search_path)["proposals"] if search_path.exists() else []
        if not proposals:
            raise SystemExit(f"{ticker}: no proposal to promote — the serpentine search proposes none")
        trial_index = proposals[0]["trial_index"]
        state = serpentine_search.theta(
            dataset.load_jsonl(config.serpentine_search_trials_jsonl(ticker))[trial_index - 1])
        # the asset's own state as a search starts from it: the active columns, the active geometry and the point
        # its ML chain chose last
        active = {"columns_by_timeframe": {timeframe: list(columns) for timeframe, columns
                                           in serpentine_search.load_feature_columns(ticker, cat).items()},
                  "best_params": serpentine_search.load_best_params(ticker),
                  **serpentine_search.load_barrier_coordinates(ticker)}
        if state == active:
            print(f"{ticker} state unchanged — the proposal, trial {trial_index}, is the active state", flush=True)
            continue
        added = coordinate_feature_set.column_count(coordinate_feature_set.columns_added(
            state["columns_by_timeframe"], active["columns_by_timeframe"], timeframes), timeframes)
        removed = coordinate_feature_set.column_count(coordinate_feature_set.columns_removed(
            state["columns_by_timeframe"], active["columns_by_timeframe"], timeframes), timeframes)
        moved = [name for name in (*config.BARRIER_COORDINATE_NAMES, "best_params") if state[name] != active[name]]
        dataset.write_json(config.feature_set_json(ticker), {"columns_by_timeframe": state["columns_by_timeframe"]})
        dataset.write_json(config.barriers_json(ticker),
                           {name: state[name] for name in config.BARRIER_COORDINATE_NAMES})
        dataset.write_json(config.hyperparameter_point_json(ticker), {"best_params": state["best_params"]})
        print(f"{ticker} <- the proposal, trial {trial_index} (+{added} -{removed} columns"
              f"{', ' + ', '.join(moved) if moved else ''}); rerun the ML chain for this asset", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
