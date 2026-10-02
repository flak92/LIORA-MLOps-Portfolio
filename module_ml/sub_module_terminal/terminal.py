"""The ML terminal — the ML module's text-based user interface (TUI): each asset's artifacts, then one action a hand
chooses in the menu — a stage of the chain started through `make` (labels, hpo, train, strategy, status, all)
or the scoring of a request (score) — its lines on this screen as they come; then it closes. Drawn by tui.py to
module_skills/skill_tui_designer.md.

It creates no domain state and writes nothing of its own: it reads the feature layer's contract as JSON and looks
whether this module's own artifacts stand, and starts every stage through `make` — the Makefile is where the module's
stages are named.

keys:
  Enter takes the option under the cursor; Esc cancels and writes nothing (exit 0); Ctrl-C ends the TUI (exit 130),
  and a stage already started stays.

output is plain — state words in brackets, no colour, no symbol, no border — when NO_COLOR is set and not empty,
TERM is dumb or standard output is not a terminal; the words, the order and the counts are the same in both.

exit codes:
  0 the action done, or cancelled with nothing written; 1 a failure, named last on stderr; 2 an unknown
  argument; 130 Ctrl-C

examples:
  make ml-terminal             the TUI over the basket the Makefile names
  make ml-terminal ASSET=BTC   the TUI over one asset
  NO_COLOR=1 make ml-terminal  the TUI in plain output
"""

import argparse
import re
import shlex
import shutil
import subprocess
import sys

from . import config, tui
from .. import config as ml_config

STATE_COLUMNS = ("asset", "catalogue", "labels", "parameters", "model", "strategy")
STATE_COLUMNS_DROP_ORDER = ("strategy", "model", "parameters", "labels")
# a line of `make help`, which the shared recipe prints as `<target> — <purpose>`; the first ` — ` ends the name, a
# purpose holding more of them, and the lower case refuses a variable that carries a `##` by accident
# twice by extraction
HELP_LINE_PATTERN = re.compile(r"^([a-z][a-z0-9-]*) — (.+)$")


# ---- the screens' own rows ------------------------------------------------------------------------------

# twice by extraction
def _option_rows(*options: str) -> list[dict]:
    return [{"option": option} for option in options]


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


# twice by extraction
def _present(path) -> str:
    return "yes" if path.exists() else "no"


def _asset_rows(tickers: list[str]) -> list[dict]:
    """One row per asset — which of its files stand; every cell a value as it stands, `—` where the contract that
    would name a file is not there."""
    rows = []
    for ticker in tickers:
        catalogue_path = ml_config.catalogue_json(ticker)
        catalogue = config.load_json(catalogue_path) if catalogue_path.exists() else None
        rows.append({"asset": ticker,
                     "catalogue": "yes" if catalogue else "no",
                     "labels": _present(ml_config.labels_parquet(ticker, catalogue["decision_timeframe"])) if catalogue else "—",
                     "parameters": _present(ml_config.parameters_json(ticker)),
                     "model": _present(ml_config.model_evaluation_json(ticker)),
                     "strategy": _present(ml_config.strategy_evaluation_json(ticker))})
    return rows


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


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -B -m module_ml.sub_module_terminal.terminal",
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    parser.add_argument("--tickers", help="the assets this invocation is about, comma-separated, e.g. BTC")
    args = parser.parse_args()

    if not sys.stdin.isatty():
        return _failure_exit_code("the TUI needs a terminal", "standard input", "it is not a terminal, so no "
                                  "choice can be asked", "run make ml-terminal in a terminal")
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
        complete_artifact_set_count = sum(1 for ticker in tickers if ml_config.is_artifact_set_complete(ticker))
        tui.gum_style(["ML terminal", f"{' '.join(tickers)} · {len(tickers)} assets · "
                                      f"{complete_artifact_set_count} artifact sets complete"], "CURRENT")
        print()
        tui.gum_table(STATE_COLUMNS, _asset_rows(tickers), STATE_COLUMNS_DROP_ORDER)
        print()
        targets = _target_rows()
        action = tui.gum_choose("action", _option_rows(*(row["target"] for row in targets), "quit"), "option")
        if action in (None, "", "quit"):
            return _cancelled_exit_code()
        ticker = tui.gum_choose("asset", [{"asset": ticker} for ticker in tickers], "asset")
        if ticker in (None, ""):
            return _cancelled_exit_code()
        return _write_target(action, next(row["purpose"] for row in targets if row["target"] == action),
                             f"ASSET={ticker}")
    except KeyboardInterrupt:
        print()
        print(f"{tui.state_label('CANCELLED')}  ended; a stage already started stays", file=sys.stderr)
        return tui.INTERRUPTED_EXIT_CODE


if __name__ == "__main__":
    raise SystemExit(main())
