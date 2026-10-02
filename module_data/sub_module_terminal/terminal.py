"""The data terminal — the data module's text-based user interface (TUI): each asset's raw days and its canonical series,
then one action a hand chooses in the menu — every target of the Makefile carrying a `##` that
`MENU_TARGET_PATTERN` gives this module — started through `make`, its
lines on this screen as they come; then it closes. Drawn by tui.py to module_skills/skill_tui_designer.md.

It creates no domain state — what it counts, it counts to display: it counts the Lean day ZIPs each venue's leaf holds and reads whether the asset's canonical series
stands, through this module's own `config.py` and `lean.py`, and starts every stage through `make` — the Makefile is
where the module's stages are named. Every action is started as `make <target> ASSET=<TICKER>` for the asset chosen
on its screen, which narrows a per-asset stage and leaves a basket-wide one — the download, the status — whole.

keys:
  Enter takes the option under the cursor; Esc cancels and writes nothing (exit 0); Ctrl-C ends the TUI (exit 130),
  and a stage already started stays.

output is plain — state words in brackets, no colour, no symbol, no border — when NO_COLOR is set and not empty,
TERM is dumb or standard output is not a terminal; the words, the order and the counts are the same in both.

exit codes:
  0 the action done, or cancelled with nothing written; 1 a failure, named last on stderr; 2 an unknown
  argument; 130 Ctrl-C

examples:
  make data-terminal             the TUI over the basket the Makefile names
  make data-terminal ASSET=BTC   the TUI over one asset
  NO_COLOR=1 make data-terminal  the TUI in plain output
"""

import argparse
import re
import shlex
import shutil
import subprocess
import sys

from . import config, tui
from .. import config as data_config
from .. import lean

# the state table: the asset, its canonical dataset, one column of day counts per venue of the one definition, the last day
STATE_COLUMNS = ("asset", "canonical dataset", *(f"{venue} days" for venue in data_config.SOURCE_VENUES), "last day")
STATE_COLUMNS_DROP_ORDER = ("last day", *(f"{venue} days" for venue in data_config.SOURCE_VENUES))
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


def _raw_days(ticker: str, venue: str) -> list[str]:
    """The UTC days one venue's leaf holds for the asset, `YYYYMMDD` each in day order — read off the day ZIPs
    `lean.py` enumerates, the one grammar of the raw tree."""
    return [lean.LEAN_DAY_ZIP_NAME_PATTERN.match(path.name).group(1)
            for path in lean.load_lean_day_zip_paths(data_config.raw_symbol_dir(ticker, venue))]


def _asset_rows(tickers: list[str]) -> list[dict]:
    """One row per asset — whether its canonical series stands, how many day ZIPs each venue's leaf holds and the last day
    either holds; every cell a value as it stands, `—` where no day is there."""
    rows = []
    for ticker in tickers:
        days_by_venue = {venue: _raw_days(ticker, venue) for venue in data_config.SOURCE_VENUES}
        rows.append({"asset": ticker,
                     "canonical dataset": _present(data_config.ohlcv_1m_canonical_parquet(ticker)),
                     **{f"{venue} days": len(days) for venue, days in days_by_venue.items()},
                     "last day": max((days[-1] for days in days_by_venue.values() if days), default="—")})
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
        prog="python3 -B -m module_data.sub_module_terminal.terminal",
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    parser.add_argument("--tickers", help="the assets this invocation is about, comma-separated, e.g. BTC")
    args = parser.parse_args()

    if not sys.stdin.isatty():
        return _failure_exit_code("the TUI needs a terminal", "standard input", "it is not a terminal, so no "
                                  "choice can be asked", "run make data-terminal in a terminal")
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
        canonical_dataset_count = sum(1 for row in rows if row["canonical dataset"] == "yes")
        tui.gum_style(["Data terminal", f"{' '.join(tickers)} · {len(tickers)} assets · {canonical_dataset_count} canonical datasets"],
                      "CURRENT")
        print()
        tui.gum_table(STATE_COLUMNS, rows, STATE_COLUMNS_DROP_ORDER)
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
