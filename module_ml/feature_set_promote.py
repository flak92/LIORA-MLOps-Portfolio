"""Promotion of one proposal of the feature-set search into the asset's feature set — a hand's choice, never a
derivation: the proposal's columns are copied into <TICKER>_feature_set.json and nothing else; the Makefile reruns
the ML chain after it, and the commit history is the record of every promotion. The same columns again change
nothing."""

from __future__ import annotations

from . import config, dataset, feature_set_search


def main() -> int:
    parser = config.build_ticker_parser("copy one proposal of the feature-set search into the asset's feature set")
    parser.add_argument("--proposal", type=int, default=1, help="the proposal's rank in the feature-set search result")
    args = parser.parse_args()
    for ticker in config.parse_tickers(args.tickers):
        # the proposals by their rank, so a rank the search result does not hold fails on the lookup itself
        proposals = {row["proposal"]: row for row in dataset.load_json(config.feature_set_search_json(ticker))["proposals"]}
        columns_by_timeframe = feature_set_search.to_tuples(proposals[args.proposal]["columns_by_timeframe"])
        active = dataset.load_feature_columns(ticker)
        if columns_by_timeframe == active:
            print(f"{ticker} feature set unchanged — proposal {args.proposal} is the active set", flush=True)
            continue
        path = config.feature_set_json(ticker)
        added = feature_set_search.column_count(feature_set_search.columns_added(columns_by_timeframe, active))
        removed = feature_set_search.column_count(feature_set_search.columns_removed(columns_by_timeframe, active))
        dataset.write_json(path, {"columns_by_timeframe": columns_by_timeframe})
        print(f"{ticker} {path.name} <- proposal {args.proposal} (+{added} -{removed} columns); ml-all follows", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
