"""The features terminal — the feature module's text-based user interface (TUI): each asset's bars, its catalogue
and its contract, then one action a hand chooses in the menu — one of the module's stages started through
`make`, its lines on this screen as they come, or one of the serpentine search's own: draft the profile, read the
recorded search or promote the proposal — its forms and its result drawn by tui.py to module_skills/skill_tui_designer.md; then it closes.

Outside an action it creates no domain state: how many timeframes an asset's bars and its catalogue hold a partition
for and whether its contract stands it reads off the artifacts store by the descriptors config.py carries, it reads the serpentine search's files as JSON and
writes the one file `<TICKER>_serpentine_search_profile.json`, and every stage is `make features-<stage>
ASSET=<TICKER>`, the promotion among them — the Makefile is where the module's stages are named.

keys:
  Enter takes the option under the cursor; x toggles a column, a coordinate or a search axis; Esc cancels and writes
  nothing (exit 0); Ctrl-C ends the TUI (exit 130), and a stage already started stays.

output is plain — state words in brackets, no colour, no symbol, no border — when NO_COLOR is set and not empty,
TERM is dumb or standard output is not a terminal; the words, the order and the counts are the same in both.

exit codes:
  0 the action done, or cancelled with nothing written; 1 a failure, named last on stderr; 2 an unknown argument;
  130 Ctrl-C

examples:
  make features-terminal             the TUI over the basket the Makefile names
  make features-terminal ASSET=BTC   the TUI over one asset
  NO_COLOR=1 make features-terminal  the TUI in plain output
"""

import argparse
import re
import shlex
import shutil
import subprocess
import sys

from . import config, tui

DRAFT_STEPS = ["action", "columns to admit", "start search state", "coordinates to search", "search axes", "plan"]
STATE_COLUMNS = ("asset", "bars", "catalogue", "contract", "profile", "state evaluations")
STATE_COLUMNS_DROP_ORDER = ("state evaluations", "profile", "catalogue", "contract")
PROPOSAL_COLUMNS = ("#", "state evaluation", "changes", "path CAGR", "path Calmar", "path maxDD", "trades")
PROPOSAL_COLUMNS_DROP_ORDER = ("path maxDD", "trades", "path Calmar", "changes")
PATH_COLUMNS = ("#", "round", "search axis", "search family", "state evaluation", "path CAGR", "path Calmar",
                "path maxDD", "trades")
PATH_COLUMNS_DROP_ORDER = ("trades", "path maxDD", "path Calmar", "search family")
# a line of `make help`, which the shared recipe prints as `<target> — <purpose>`; the first ` — ` ends the name, a
# purpose holding more of them, and the lower case refuses a variable that carries a `##` by accident
# twice by extraction
HELP_LINE_PATTERN = re.compile(r"^([a-z][a-z0-9-]*) — (.+)$")


# ---- the screens' own rows ------------------------------------------------------------------------------

# twice by extraction
def _option_rows(*options: str) -> list[dict]:
    return [{"option": option} for option in options]


def _step_rows(steps: list[str], chosen: dict[str, str]) -> list[dict]:
    """The action's steps in order: each answered DONE with its choice, the first unanswered CURRENT, the rest PENDING."""
    current = next(step for step in steps if step not in chosen)
    return [{"step": step, "state": tui.state_label("DONE" if step in chosen else "CURRENT" if step == current
                                                    else "PENDING"),
             "choice": chosen[step] if step in chosen else "select now" if step == current else "—"} for step in steps]


def _step_answer(steps: list[str], chosen: dict[str, str], rows: list[dict], value_column: str,
                 drop_order: tuple[str, ...] = (), selected: list[str] | None = None) -> str | None:
    """The answer to the action's current step under the steps table; a step of one option draws nothing, gum
    answering it, and the next steps table shows it DONE."""
    step = next(step for step in steps if step not in chosen)
    if len(rows) > 1:
        tui.gum_table(("step", "state", "choice"), _step_rows(steps, chosen))
        print()
    return tui.gum_choose(step, rows, value_column, drop_order, selected)


# twice by extraction
def _cancelled_exit_code() -> int:
    """Esc, cancel or quit: one line, nothing written, exit 0."""
    print(f"{tui.state_label('CANCELLED')}  nothing written")
    return 0


# twice by extraction
def _failure_exit_code(what: str, where: str, why: str | None, next_action: str) -> int:
    """A failure as the invocation's last block, on stderr: exit 1."""
    tui.gum_style(tui.error_lines(what, where, why, next_action), "ERROR", sys.stderr)
    return 1


# twice by extraction
def _make(*arguments: str) -> int:
    """The one call of make: its lines reach this terminal as they come, and its exit code is the answer. The
    Makefile is where every action is named (AGENTS.md § Canonical vocabulary)."""
    command = ("make", *arguments)
    print(f"{tui.state_label('CURRENT')}  {shlex.join(command)}", flush=True)
    return subprocess.run(command).returncode


# twice by extraction
def _target_rows() -> list[dict]:
    """Every target `make help` lists whose name this terminal's `MENU_TARGET_PATTERN` matches, in the Makefile's
    order — the target and the purpose its `##` carries.

    The Makefile is the register: a target of this terminal's module carrying a `##` is an option of this menu and
    one without it is not, and this program keeps no second list of them (`AGENTS.md` § Canonical vocabulary, the
    terminal-menu row).
    """
    listing = subprocess.run(("make", "help"), capture_output=True, text=True, check=True).stdout
    return [{"target": found.group(1), "purpose": found.group(2)}
            for line in listing.splitlines()
            if (found := HELP_LINE_PATTERN.match(line)) and config.MENU_TARGET_PATTERN.match(found.group(1))]


def _profile_state(profile: dict | None, search: dict | None) -> str:
    """Where the asset's profile stands against the serpentine search recorded under it — the one comparison this
    terminal makes, on parsed objects and not on bytes: the search records the profile it was run with, verbatim."""
    if profile is None:
        return "not drafted"
    if search is None:
        return "no search"
    return "matches the search" if search["inputs"]["profile"] == profile else "differs from the search"


def _load_asset_json(ticker: str) -> tuple[dict | None, dict | None, dict | None]:
    """The three files of one asset the serpentine search's actions read as objects — the contract, the profile and
    the search's progress — each None where the file is not there."""
    catalogue_path = config.catalogue_json(ticker)
    profile_path, search_path = config.serpentine_search_profile_json(ticker), config.serpentine_search_json(ticker)
    return (config.load_json(catalogue_path) if catalogue_path.exists() else None,
            config.load_json(profile_path) if profile_path.exists() else None,
            config.load_json(search_path) if search_path.exists() else None)


def _state_evaluation_rows(ticker: str) -> list[dict]:
    """The serpentine search's ledger, line by line — the state evaluations, where the search's progress holds where
    it stands."""
    ledger = config.serpentine_search_state_evaluations_jsonl(ticker)
    return config.load_jsonl(ledger) if ledger.exists() else []


def _asset_rows(tickers: list[str]) -> list[dict]:
    """One row per asset — how many timeframes its bars and its catalogue hold a partition for, whether its contract
    stands, where its serpentine search profile stands and how many state evaluations its ledger holds; every cell a
    value as it stands, the count 0 where a family holds no partition of the asset and `—` where no ledger holds a
    state evaluation."""
    rows = []
    for ticker in tickers:
        catalogue, profile, search = _load_asset_json(ticker)
        state_evaluations = _state_evaluation_rows(ticker)
        rows.append({"asset": ticker,
                     "bars": len(list(config.partition_dir("bars", ticker).glob("timeframe=*/bars.parquet"))),
                     "catalogue": len(list(config.partition_dir("catalogue", ticker).glob("timeframe=*/catalogue.parquet"))),
                     "contract": "no" if catalogue is None else "yes",
                     "profile": _profile_state(profile, search),
                     "state evaluations": len(state_evaluations) if state_evaluations else "—"})
    return rows


def _recorded_search_rows(ticker: str, profile: dict | None, search: dict,
                state_evaluations: list[dict]) -> list[dict]:
    """What the asset holds, one fact a row — every cell the file's own value, never an age or a share."""
    rows = [{"parameter": "asset", "value": ticker},
            {"parameter": "profile", "value": _profile_state(profile, search)}]
    if profile is not None:
        rows.append({"parameter": "coordinates searched",
                     "value": f"{sum(len(grid) > 1 for grid in profile['grid_by_coordinate'].values())} of {len(config.GRID_BY_COORDINATE_DEFAULT)}"})
        rows.append({"parameter": "search axes", "value": " ".join(profile["search_axes"]) or "—"})
    # the serpentine search counted these at a round boundary; the terminal shows them and adds nothing to them
    by_search_axis = search["selection_hypothesis_count_by_search_axis"]
    rows += [{"parameter": "serpentine search",
              "value": f"{len(state_evaluations)} state evaluations in {search['round_count']} rounds"},
             {"parameter": "selection hypotheses", "value": search["selection_hypothesis_count"]},
             {"parameter": "selection hypotheses by search axis",
              "value": " ".join(f"{search_axis} {count}"
                                for search_axis, count in sorted(by_search_axis.items())) or "—"},
             {"parameter": "outcome", "value": (search["search_outcome"] or "in progress").replace("_", " ")},
             {"parameter": "beam changed in the last round",
              "value": {None: "—", True: "yes", False: "no"}[search["beam_changed"]]},
             {"parameter": "champion", "value": search["champion_state_evaluation_index"] or "—"},
             {"parameter": "proposals", "value": len(search["proposals"])}]
    return rows


def _number(value, digits: int = 4) -> str:
    return "—" if value is None else f"{value:+.{digits}f}"


def _path_block_cells(block: dict) -> dict:
    return {"path CAGR": _number(block["cagr"]), "path Calmar": _number(block["calmar"], 2),
            "path maxDD": _number(block["max_drawdown"], 4), "trades": block["trade_count"]}


def _proposal_rows(search: dict, state_evaluations: list[dict]) -> list[dict]:
    """The proposals, each read off the ledger line its state evaluation index names — the search's progress holds
    the rank and the index, and no number of the state evaluation."""
    return [{"#": proposal["proposal"], "state evaluation": proposal["state_evaluation_index"],
             "changes": _moved(state_evaluations[proposal["state_evaluation_index"] - 1], search),
             **_path_block_cells(state_evaluations[proposal["state_evaluation_index"] - 1]["validation_path"])}
            for proposal in search["proposals"]]


def _path_rows(search: dict, state_evaluations: list[dict]) -> list[dict]:
    return [{"#": number, "round": entry["round"], "search axis": entry["search_axis"],
             "search family": entry["search_family"], "state evaluation": entry["state_evaluation_index"],
             **_path_block_cells(state_evaluations[entry["state_evaluation_index"] - 1]["validation_path"])}
            for number, entry in enumerate(search["path"], start=1)]


def _moved(state_evaluation: dict, search: dict) -> str:
    """What one state evaluation changes against the asset's own search state the serpentine search was run on, as
    its inputs record it — the columns it holds that the search state does not and the ones it drops, each barrier
    coordinate whose value is not the search state's, and the hyper-parameter point when it is not. Membership and
    equality on the two files' own values: no number is computed."""
    active_columns, active_barriers = (search["inputs"]["active_columns_by_timeframe"],
                                       search["inputs"]["active_barriers"])
    columns = [f"+{name}_{timeframe}"
               for timeframe, names in sorted(state_evaluation["columns_by_timeframe"].items())
               for name in names if name not in active_columns[timeframe]]
    columns += [f"-{name}_{timeframe}" for timeframe, names in sorted(active_columns.items())
                for name in names if name not in state_evaluation["columns_by_timeframe"][timeframe]]
    barriers = [f"{name} {state_evaluation[name]}" for name in sorted(config.GRID_BY_COORDINATE_DEFAULT)
                if state_evaluation[name] != active_barriers[name]]
    point = ["best_params"] if state_evaluation["best_params"] != search["inputs"]["best_params"] else []
    return " ".join(columns + barriers + point) or "—"


# ---- the actions ----------------------------------------------------------------------------------------

# twice by extraction
def _write_target(target: str, purpose: str, *variables: str) -> int:
    """One target of the Makefile, started through make after the plan and its gate.

    A target that opens a program of its own is no exception: it is an ordinary action that hands the screen over and
    comes back.
    """
    tui.gum_table(("parameter", "value"),
                  [{"parameter": "target", "value": target}, {"parameter": "purpose", "value": purpose},
                   *({"parameter": name, "value": value}
                     for name, value in (variable.split("=", 1) for variable in variables))])
    print(f"command         {shlex.join(('make', target, *variables))}")
    print()
    decision = tui.gum_choose(f"{target}?", _option_rows(target, "cancel"), "option")
    if decision != target:
        return _cancelled_exit_code()
    print()
    code = _make(target, *variables)
    print()
    if code:
        return _failure_exit_code(f"{target} ended with exit {code}", shlex.join(("make", target, *variables)),
                                  f"make exited with {code}", "read make's lines above")
    tui.gum_style([f"{tui.state_label('DONE')}  {target} done"], "DONE")
    return 0


# twice by extraction
def _tickers(given: str | None) -> list[str] | None:
    """The assets this invocation is about: the ones `--tickers` named, or the ones a hand types when it named none.

    The Makefile's recipe passes the basket, or `ASSET` on the make line, as `--tickers`, so the answer is asked here
    only when an invocation names none. This module defines no basket of its own and reads none from a store: the
    launcher names the assets (`module_skills/skill_glossary.md` § Asset containers). None for Esc.
    """
    answer = given if given is not None else tui.gum_input("asset",
                                                           "the assets this invocation is about — BTC, or BTC,ETH")
    if answer is None:
        return None
    return [ticker.strip().upper() for ticker in answer.split(",") if ticker.strip()]


def _active_barrier(ticker: str, name: str):
    """Where an unsearched coordinate is pinned: where the asset stands — its promoted geometry, else the experiment's
    frozen one — the value a search starts from, so the one-point grid holds the start. The value takes the type of its
    frozen default, as the search's own casts give it."""
    path = config.barriers_json(ticker)
    promoted = config.load_json(path) if path.exists() else {}
    start = config.START_BY_COORDINATE_DEFAULT[name]
    return type(start)(promoted.get(name, start))


def _write_search_profile(ticker: str, catalogue: dict | None, profile: dict | None, search: dict | None) -> int:
    """Draft the asset's serpentine search profile: which columns it may admit, which search state it starts from,
    which coordinates it moves and which search axes a round runs. The grids are the one preset — another grid is a
    hand's edit of the file, which is what a drafted artifact permits, and so is the asset's noise sigma."""
    if catalogue is None:
        return _failure_exit_code(f"{ticker} has no feature contract", config.catalogue_json(ticker).name, None,
                                  f"make features-catalogue ASSET={ticker} first")
    while True:
        chosen = {"action": "draft"}
        timeframes = [entry["timeframe"] for entry in catalogue["timeframes"]]
        column_rows = [{"column": f"{name}_{timeframe}", "timeframe": timeframe, "definition": name}
                       for timeframe in timeframes for name in catalogue["columns_by_timeframe"][timeframe]]
        admitted = ([f"{name}_{timeframe}" for timeframe, names in profile["columns_admitted_by_timeframe"].items()
                     for name in names] if profile else [row["column"] for row in column_rows])
        answer = _step_answer(DRAFT_STEPS, chosen, column_rows, "column", ("definition", "timeframe"),
                              selected=admitted)
        if answer in (None, ""):
            return _cancelled_exit_code()
        admitted = answer.splitlines()
        chosen["columns to admit"] = f"{len(admitted)} of {len(column_rows)}"

        start_rows = [{"start search state": "the asset's own", "value": "null"}]
        if search is not None and search["champion_state_evaluation_index"]:
            start_rows.append({"start search state": "the recorded search's champion", "value": "champion"})
        answer = _step_answer(DRAFT_STEPS, chosen, start_rows, "value")
        if answer in (None, ""):
            return _cancelled_exit_code()
        start_columns = (None if answer == "null" else
                         _state_evaluation_rows(ticker)[search["champion_state_evaluation_index"] - 1]
                         ["columns_by_timeframe"])
        chosen["start search state"] = next(row["start search state"] for row in start_rows
                                            if row["value"] == answer)

        coordinate_rows = [{"coordinate": name, "grid": ", ".join(str(point) for point in grid),
                            "points": len(grid)}
                           for name, grid in sorted(config.GRID_BY_COORDINATE_DEFAULT.items())]
        searched = (sorted(name for name, grid in profile["grid_by_coordinate"].items() if len(grid) > 1)
                    if profile else sorted(config.GRID_BY_COORDINATE_DEFAULT))
        answer = _step_answer(DRAFT_STEPS, chosen, coordinate_rows, "coordinate", ("points", "grid"),
                              selected=searched)
        if answer is None:
            return _cancelled_exit_code()
        searched = answer.splitlines() if answer else []
        chosen["coordinates to search"] = f"{len(searched)} of {len(coordinate_rows)}"

        search_axis_rows = [{"search axis": search_axis} for search_axis in config.SERPENTINE_SEARCH_AXES]
        search_axes = profile["search_axes"] if profile else list(config.SERPENTINE_SEARCH_AXES)
        answer = _step_answer(DRAFT_STEPS, chosen, search_axis_rows, "search axis", selected=search_axes)
        if answer is None:
            return _cancelled_exit_code()
        search_axes = [search_axis for search_axis in config.SERPENTINE_SEARCH_AXES
                       if search_axis in answer.splitlines()]
        chosen["search axes"] = " ".join(search_axes) or "—"

        drafted = {
            "columns_admitted_by_timeframe": {
                timeframe: [name for name in catalogue["columns_by_timeframe"][timeframe]
                            if f"{name}_{timeframe}" in admitted]
                for timeframe in timeframes},
            # every coordinate, always: a profile that omits one leaves the serpentine search reading a key that is
            # not there, and a coordinate a hand did not tick is not a coordinate that stopped existing — it is
            # one pinned to where it stands. Its grid is that single point, which the kernel already handles,
            # because a one-point grid has no neighbour and a family with no neighbour makes no move
            "grid_by_coordinate": {name: (list(grid) if name in searched else [_active_barrier(ticker, name)])
                                   for name, grid in sorted(config.GRID_BY_COORDINATE_DEFAULT.items())},
            "search_axes": search_axes,
            # the asset's noise sigma is a decision recorded elsewhere and a hand's edit of the file, never a step of
            # this form: a draft carries the profile's own over unchanged, and a first profile has none — its search
            # is the calibration search that measures it
            "path_cagr_noise_standard_deviation": profile["path_cagr_noise_standard_deviation"] if profile else None,
            "start_columns_by_timeframe": start_columns,
        }
        path = config.serpentine_search_profile_json(ticker)
        changes = [{"parameter": key, "now": _to_line(profile.get(key) if profile else None), "after": _to_line(value)}
                   for key, value in sorted(drafted.items())
                   if not profile or profile.get(key) != value]
        tui.gum_table(("step", "state", "choice"), _step_rows(DRAFT_STEPS, chosen))
        print()
        if changes:
            tui.gum_table(("parameter", "now", "after"), changes)
        else:
            print("no profile changes")
        print()
        if search is not None and drafted != search["inputs"]["profile"]:
            print(f"{tui.state_label('WARN')}  the recorded search was run under another profile — the next turn "
                  f"starts a new search and overwrites {config.serpentine_search_json(ticker).name}")
            print()
        answer = tui.gum_choose(f"draft {path.name}?",
                                _option_rows(*(("draft",) if changes else ()), "back", "cancel"), "option")
        if answer == "back":
            continue
        if answer != "draft":
            return _cancelled_exit_code()
        config.write_json(path, drafted)
        print()
        tui.gum_style([f"{tui.state_label('DONE')}  drafted {path.name} · {len(admitted)} columns admitted · "
                       f"{len(searched)} coordinates · {' '.join(search_axes) or 'no'} search axes"], "DONE")
        return 0


def _recorded_search_tables(ticker: str, profile: dict | None, search: dict | None) -> int:
    """Read the recorded serpentine search: where it stands, the path it took and the search state it proposes. Writes
    nothing.

    Two files: the search's progress says where the search stands and names the state evaluations it took and
    proposes, the ledger holds those state evaluations and every number the tables show."""
    if search is None:
        return _failure_exit_code(f"{ticker} has no serpentine search",
                                  config.serpentine_search_json(ticker).name,
                                  "no turn has run for this asset", "draft a profile, then run "
                                  "make features-serpentine-search")
    state_evaluations = _state_evaluation_rows(ticker)
    tui.gum_table(("parameter", "value"), _recorded_search_rows(ticker, profile, search, state_evaluations))
    print()
    if search["path"]:
        tui.gum_table(PATH_COLUMNS, _path_rows(search, state_evaluations), PATH_COLUMNS_DROP_ORDER)
    else:
        print("no accepted move")
    print()
    if search["proposals"]:
        tui.gum_table(PROPOSAL_COLUMNS, _proposal_rows(search, state_evaluations), PROPOSAL_COLUMNS_DROP_ORDER)
    else:
        print("no proposal")
    return 0


def _write_promoted_proposal(ticker: str, search: dict | None) -> int:
    """Promote the proposal into the asset's own search state, through the Makefile — the target copies the proposal
    and then reruns the asset's ML chain. A search proposes one search state at most, so the plan shows it and the
    gate asks whether, with nothing to choose before it."""
    if search is None or not search["proposals"]:
        return _failure_exit_code(f"{ticker} has no proposal to promote",
                                  config.serpentine_search_json(ticker).name,
                                  "no turn has run for this asset" if search is None else "the search proposes none",
                                  "run make features-serpentine-search, then read its tables")
    state_evaluation_index = search["proposals"][0]["state_evaluation_index"]
    state_evaluations = _state_evaluation_rows(ticker)
    command = ("make", config.PROMOTE_TARGET, f"ASSET={ticker}")
    tui.gum_table(("parameter", "value"),
                  [{"parameter": "asset", "value": ticker},
                   {"parameter": "state evaluation", "value": state_evaluation_index},
                   {"parameter": "changes",
                    "value": _moved(state_evaluations[state_evaluation_index - 1], search)},
                   {"parameter": "writes",
                    "value": f"{config.feature_set_json(ticker).name}, {config.barriers_json(ticker).name}, "
                             f"{config.hyperparameter_point_json(ticker).name}"}])
    print(f"command         {shlex.join(command)}")
    print()
    decision = tui.gum_choose(f"promote the proposal of {ticker}?", _option_rows("promote", "cancel"), "option")
    if decision != "promote":
        return _cancelled_exit_code()
    print()
    code = _make(*command[1:])
    print()
    if code:
        return _failure_exit_code(f"the promotion of {ticker} did not finish", shlex.join(command),
                                  f"make exited with {code}", "read make's lines above")
    tui.gum_style([f"{tui.state_label('DONE')}  promoted the proposal of {ticker}; make's lines above are the "
                   f"chain's where the Makefile reruns it"], "DONE")
    return 0


def _to_line(value) -> str:
    """One profile value on one line: a list by its length, a mapping by its own, everything else as it stands."""
    if value is None:
        return "—"
    if isinstance(value, dict):
        return " ".join(f"{key} {len(value[key]) if isinstance(value[key], list) else value[key]}"
                        for key in sorted(value))
    if isinstance(value, list):
        return " ".join(str(item) for item in value) or "—"
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -B -m module_features.sub_module_terminal.terminal",
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    parser.add_argument("--tickers", help="the assets this invocation is about, comma-separated, e.g. BTC")
    args = parser.parse_args()

    if not sys.stdin.isatty():
        return _failure_exit_code("the TUI needs a terminal", "standard input", "it is not a terminal, so no "
                                  "choice can be asked", "run make features-terminal in a terminal")
    if not shutil.which("gum"):
        return _failure_exit_code("gum is not on PATH", "PATH", None,
                                  "install gum 2: https://github.com/charmbracelet/gum#installation")
    try:
        tickers = _tickers(args.tickers)
        if tickers is None:
            return _cancelled_exit_code()
        if not tickers:
            return _failure_exit_code("the TUI needs an asset", "the asset asked for", "no asset was named",
                                      "type at least one ticker, e.g. BTC")
        rows = _asset_rows(tickers)
        contract_count = sum(1 for row in rows if row["contract"] == "yes")
        tui.gum_style(["Features terminal", f"{' '.join(tickers)} · {len(tickers)} assets · {contract_count} contracts"],
                      "CURRENT")
        print()
        tui.gum_table(STATE_COLUMNS, rows, STATE_COLUMNS_DROP_ORDER)
        print()
        targets = _target_rows()
        action = tui.gum_choose("action", _option_rows(*(row["target"] for row in targets),
                                                       "draft", "recorded search", "quit"), "option")
        if action in (None, "", "quit"):
            return _cancelled_exit_code()
        ticker = tui.gum_choose("asset", [{"asset": ticker} for ticker in tickers], "asset")
        if ticker in (None, ""):
            return _cancelled_exit_code()
        catalogue, profile, search = _load_asset_json(ticker)
        # the target whose plan shows the search state it promotes keeps its own screen; everything else is the
        # Makefile's own target, run through the one plan and gate
        if action == config.PROMOTE_TARGET:
            return _write_promoted_proposal(ticker, search)
        if action == "draft":
            return _write_search_profile(ticker, catalogue, profile, search)
        if action == "recorded search":
            return _recorded_search_tables(ticker, profile, search)
        return _write_target(action, next(row["purpose"] for row in targets if row["target"] == action),
                             f"ASSET={ticker}")
    except KeyboardInterrupt:
        print()
        print(f"{tui.state_label('CANCELLED')}  ended; a stage already started stays", file=sys.stderr)
        return tui.INTERRUPTED_EXIT_CODE


if __name__ == "__main__":
    raise SystemExit(main())
