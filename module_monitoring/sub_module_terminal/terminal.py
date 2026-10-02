"""The monitoring terminal — the monitoring module's text-based user interface (TUI): the four snapshots the page reads,
then one action a hand chooses in the menu — `on` or `off`, every target of the Makefile carrying a `##` that
`MENU_TARGET_PATTERN` gives this module — started through `make`, its lines on this screen as they come; then it
closes. Drawn by tui.py to module_skills/skill_tui_designer.md.

Outside an action it creates no domain state and writes nothing: the snapshots it reads through its own `config.py`,
and each action is one of those targets, through `make` — the Makefile is where the presentation switch is named.

keys:
  Enter takes the option under the cursor; Esc cancels and writes nothing (exit 0); Ctrl-C ends the TUI (exit 130),
  and what make already started runs on.

output is plain — state words in brackets, no colour, no symbol, no border — when NO_COLOR is set and not empty, TERM
is dumb or standard output is not a terminal; the words, the order and the counts are the same in both.

exit codes:
  0 the action done, or cancelled with nothing written; 1 a failure, named last on stderr; 2 an unknown argument;
  130 Ctrl-C

examples:
  make monitoring-terminal             the TUI over the status store the Makefile exports
  NO_COLOR=1 make monitoring-terminal  the TUI in plain output
"""

import argparse
import re
import shlex
import shutil
import subprocess
import sys

from . import config, tui

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


def _snapshot_rows() -> list[dict]:
    """One row per snapshot the page reads: its `generated_at_utc` as the file carries it, `—` where the file carries no
    such key (skills_status.json), `absent` where the file is not there."""
    rows = []
    for name in config.SNAPSHOT_FILE_NAMES:
        path = config.STORE_STATUS_DIR / name
        rows.append({"snapshot": name, "generated_at_utc": (config.load_json(path).get("generated_at_utc", "—")
                                                            if path.is_file() else "absent")})
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


def main() -> int:
    argparse.ArgumentParser(prog="python3 -B -m module_monitoring.sub_module_terminal.terminal", description=__doc__,
                            formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False).parse_args()
    if not sys.stdin.isatty():
        return _failure_exit_code("the TUI needs a terminal", "standard input", "it is not a terminal, so no choice "
                                  "can be asked", "run make monitoring-terminal in a terminal")
    if not shutil.which("gum"):
        return _failure_exit_code("gum is not on PATH", "PATH", None,
                                  "install gum 2: https://github.com/charmbracelet/gum#installation")
    try:
        snapshots = _snapshot_rows()
        present_snapshot_count = sum(row["generated_at_utc"] != "absent" for row in snapshots)
        tui.gum_style(["Monitoring terminal", f"{present_snapshot_count} of {len(snapshots)} snapshots"], "CURRENT")
        print()
        tui.gum_table(("snapshot", "generated_at_utc"), snapshots)
        print()
        targets = _target_rows()
        action = tui.gum_choose("action", _option_rows(*(row["target"] for row in targets), "quit"), "option")
        if action in (None, "", "quit"):
            return _cancelled_exit_code()
        return _write_target(action, next(row["purpose"] for row in targets if row["target"] == action))
    except KeyboardInterrupt:
        print()
        print(f"{tui.state_label('CANCELLED')}  ended; what make already started runs on", file=sys.stderr)
        return tui.INTERRUPTED_EXIT_CODE


if __name__ == "__main__":
    raise SystemExit(main())
