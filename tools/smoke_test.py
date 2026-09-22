#!/usr/bin/env python3
"""OrionLayer smoke test — verify the project after any change.

Runs headless (no window, no orion2re needed) and exercises:
  - resource resolution + mod override (example_mod)
  - skin palette loading
  - screen auto-discovery + dispatcher game-ID map
  - full lifecycle of every screen (enter/update/render/click/
    resize/exit)
  - sub-screen lock behavior
  - editor toggle, selection, overlay rendering
  - App boot in standalone mode

Usage (from the project root):
    python tools/smoke_test.py            # every check's sentence
    python tools/smoke_test.py --quiet    # failures and the summary only

--quiet sends everything the run prints — the check sentences, the
reports, the log lines, anything SDL writes — to a temporary file and
shows only the summary; on a failure it shows the last 60 lines of that
file before the traceback. The reason is context, not time (work order
126, part C): a green run's 300 lines land in a session's context on
every commit. The last line of either mode is the process's peak
resident memory, and a crash prints Python's stack through faulthandler
to the real stderr, since a segfault never reaches any other print.

Exit code 0 = all good. Run this before shipping a ZIP or a
mod, and after touching anything in core/.
"""
import faulthandler

# AT THE TOP, BEFORE ANY OTHER IMPORT (work order 128 F). A segfault — the
# exit 139 of 16 September — kills the process before any print or
# traceback, so without this its output simply vanishes. Enabled here it
# writes the Python stack of every thread to stderr for a crash anywhere,
# imports included, which makes every ordinary run a probe. `_run` re-points
# it at a duplicate of the real stderr before --quiet redirects descriptor 2.
faulthandler.enable()

import ast
import collections
import glob
import hashlib
import io
import logging
import math
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
if "--quiet" in sys.argv[1:]:
    # pygame greets on import, before the run can redirect anything.
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame  # noqa: E402

#: THE ENGINE ALWAYS SENDS A FIELD 0, AND IT IS NOT A FIELD.
#: `fields::Clear_Fields_` sets `_fields_count = 1`, not 0
#: (fields.cpp:207), so slot 0 is never cleared and no `Add_*_Field_`
#: ever writes it — and `SerializeFields` sends every field from
#: `i = 0` (ext_api.cpp:326). So every list on the wire opens with
#: whatever that slot happens to hold, and decision 59 says exactly
#: that: "never field 0, which after a message box carries whatever
#: geometry the list held before".
#:
#: A FIXTURE WITHOUT IT IS A LIST THE ENGINE CANNOT PRODUCE, and that
#: is where work order 137 A's fault hid: the RECORDED fixtures
#: (`tools/galaxy_box_fields.json`, `tools/game_menu_fields.json`)
#: carry it because they were captured live, the HAND-BUILT ones did
#: not, and the rule that choked on it passed every check for two days.
#: Live on 19 September 2026 it was the ONE stranger in a list of 92
#: and the whole reason the Fleets screen was never seen (140).
#:
#: The geometry here is JUNK ON PURPOSE and not zeros. The live one
#: read `(0, 0, 0, 0)`, but zeros are falsy and a rule that happens to
#: survive them is not a rule that survives the slot; the recorded
#: fixtures already cover the all-zero shape.
#: `(index, x, y, x_end, y_end, field_type, hotkey)`.
FIELD_ZERO_ROW = (0, 7, 9, 11, 13, 0, 0)

PASS = 0

#: THE PUSH-ONLY TIER — work order 158, implementing 157's Option A.
#:
#: `name -> (checks it produces, what makes it expensive)`. **This dict
#: is the only place the slow list lives**, and a check below holds the
#: tree to it in both directions: every `slow("x")` call site in this
#: file must be declared here, and every name declared here must have a
#: call site. That is the marker inventory's shape, and it is here for
#: the marker inventory's reason — a list kept by hand is legitimate
#: only with a checker.
#:
#: **Nothing here is skipped in the default run.** `python
#: tools/smoke_test.py` runs everything, exactly as before; only an
#: explicit `--fast` selects the reduced tier, and only the pre-commit
#: hook passes it. The tiers change WHEN a check runs, never what it
#: asserts — every one of these still runs, unchanged, before a push.
#:
#: The cost of that, accepted by Data with work order 158: a fault only
#: these checks can see lands at push time instead of commit time. The
#: drop-marker hit area and the colony list's plating were both found
#: by checks on this list.
SLOW_TIER = {
    "figure_pick": (1,
        "renders the colony summary and reads the drawn pixels back for "
        "1..20 figures in every job column at three resolutions, then "
        "again over the player's OWN extracted figures — 28.2 s, 36 % of "
        "the suite, and the second pass is most of the 15 s by which "
        "this machine's run is slower than a clone's (157 sections 2, 4)"),
    "return_cutout": (1,
        "lays the colony summary out at twelve resolutions to measure "
        "RETURN's label clearance — the twelve sizes are the point, and "
        "they are 13.7 s of the suite (157 section 2)"),
    "game_menu_frame_opening": (1,
        "loads the GAME menu frame through the resource roots and "
        "measures its one hole against the artwork — 3.0 s"),
    "game_menu_frame_drawn": (1,
        "draws the GAME menu frame on a first opening and samples the "
        "metal's opaque pixels off the result — 1.2 s"),
    "fallback_verdict_log": (1,
        "stands the app up repeatedly to watch main._verdict change its "
        "decision and its reason — 2.3 s"),
    "sidebar_research": (1,
        "renders the galaxy map sidebar's research readout through "
        "core/research for the original's four cases — 2.3 s"),
    "tools_import": (1,
        "starts 49 fresh Python processes, one per runnable tool — the "
        "only expensive check in the suite that renders nothing, 2.0 s"),
}

#: The tier this run is in. Set from argv in `_run`; "full" unless
#: `--fast` is given, so every path that does not ask for the fast tier
#: gets the whole suite.
TIER = "full"

#: `name -> checks not run`, filled by `slow()` in the fast tier.
SKIPPED = {}

#: Every `slow()` name this run consulted — the runtime half of the
#: inventory check. Both tiers consult all of them, because the guard
#: is evaluated either way.
SLOW_SEEN = set()


def slow(name):
    """True if the push-only block `name` runs in this tier.

    A `slow(...)` guard wraps a whole check — its measurement AND its
    `ok()` — and never a part of one. Each block was chosen by asking
    what a later check would miss if it did not run: the blocks behind
    these guards bind no name a later statement reads before rebinding
    it, and mutate nothing defined outside them. Shared setup in front
    of a slow check stays OUTSIDE the guard and keeps running in both
    tiers, which is why some expensive segments in 157's table are not
    on this list at all — their cost is setup other checks need.
    """
    assert name in SLOW_TIER, (
        f"slow({name!r}) is not declared in SLOW_TIER. The list lives "
        f"in exactly one place and a check holds the tree to it")
    SLOW_SEEN.add(name)
    if TIER == "fast":
        SKIPPED[name] = SLOW_TIER[name][0]
        return False
    return True


#: The screen a `--screen` run is showing, and the group of the module
#: running right now. **They gate the PRINTING and nothing else.**
#:
#: Work order 162 part 4 measured the alternative before choosing this
#: one: a selector that actually SKIPS the other screens' checks needs
#: a dependency closure, and this suite's checks share their fixtures
#: through objects — `d.active`, `app`, a laid-out screen — that are
#: filled by method calls no name analysis can see. Under a rule that
#: counts every method call as a change, one screen's closure is 96 %
#: of the suite; under a practical net it is 87 % and a narrowed run
#: still died on the galaxy map's own screen object. 157 had already
#: refused this shape once, for the caching idea, in one sentence: "a
#: check that inherits another check's app is a new class of fault
#: this project has not had yet."
#:
#: So nothing is skipped and nothing can pass on state the run never
#: built. What a `--screen` run saves is the OUTPUT — which is what
#: lands in a session's context, and the order's own measure.
SCREEN = None
AREA = None

#: How many sentences a `--screen` run actually printed, so its last
#: line can say what it showed as well as what it ran.
SHOWN = 0


def ok(msg):
    global PASS, SHOWN
    PASS += 1
    if SCREEN is None or AREA in ("core", SCREEN):
        SHOWN += 1
        print(f"  ok  {msg}")


#: WHERE THE STAND-INS LIVE, and the one way a check gets a derived
#: catalogue. See `tools/make_derived_fixtures.py` and the fundament
#: under Diagnosis: a check that reads the player's own extracted
#: files passes on the machine that wrote them, and it has done so
#: four times. `derived` hands the loader a committed tree instead,
#: through the loader's OWN code path — the `root=` every one of them
#: already takes — so a clone measures exactly what this machine
#: measures and there is no absence to branch on.
#:
#: A check that is ABOUT a loader still reads the real thing, and
#: says so in `_REAL_DERIVED_OK` below.
DERIVED_ROOT = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tools", "fixtures", "derived")


def derived(loader, language="en"):
    """A derived-data loader bound to the committed stand-ins."""
    got = loader(language, root=DERIVED_ROOT)
    state = getattr(got, "state", None)
    if state is None:                      # ArcWords reports differently
        assert not getattr(got, "absent", ""), (
            f"{loader.__name__} could not read its stand-in: "
            f"{got.absent} — run `python tools/make_derived_fixtures.py`")
    else:
        assert state == "ok", (
            f"{loader.__name__} reports {state!r} for its stand-in — "
            f"run `python tools/make_derived_fixtures.py`")
    return got


def colony_rects():
    """{box name: reference rect} for colony_summary, DERIVED.

    `boxes.json` carries no rectangle for that screen since
    12 September 2026 — the fourteen cutouts come from
    `layout_reference.json` and the six columns from `list_columns`,
    both seated at load by `colonyplates.reseat`. Every check that
    used to read a rect out of the file asks here instead, through the
    same pure function the screen itself goes through.
    """
    from core.config import SCREENS_DIR as _sd
    from screens.colony_summary import colonyplates as _c
    data, _w = _c.load_reference(_c.reference_path(os.path.dirname(_sd)))
    return _c.all_rects(data)


def _seated(path, win_w, win_h):
    """colony_summary's boxes, loaded AND given their rectangles.

    `load_boxes` returns them with none: the geometry is
    `layout_reference.json`'s and `colonyplates.seat` is what puts it
    on a box. Every check that used to load and lay out by hand goes
    through the screen's own seating, so a check cannot measure a
    geometry the screen would not use.
    """
    from core.box import load_boxes as _lb
    from core.layout import Layout as _L
    from screens.colony_summary import colonyplates as _c
    boxes = _lb(path, win_w, win_h)
    _c.seat(boxes, colony_rects(), _L(win_w, win_h))
    return boxes


def report(msg):
    """A measured value with no pass/fail, and NOT a check.

    Added 11 September 2026 with the "chosen rules become Data's
    choices" entry in the fundament. A layout rule that was CHOSEN by
    us — the lower band flush with the list, the panel gaps equal, a
    gap equal to its role's strut, the ring pinned to the main-screen
    master — stops being enforced when Data draws her own frame, and
    every one of them lands here instead. The value is still measured
    on every run, so a change is visible in the output; it simply does
    not decide whether the suite passes.

    **It deliberately does not touch PASS.** A report is not a check
    and must not inflate the count the two documents are held to. The
    enforcements that became reports on 11 September were re-homed in
    `tools/colony_frame_check.py`, a read-only validator that met
    Data's artwork where it actually was; that tool is deleted with
    the rest of the plate machinery (Phase B, decision 55) and the
    artwork it would have checked is in the tree now, so the suite
    measures it directly.
    """
    if SCREEN is None or AREA in ("core", SCREEN):
        print(f"  --  {msg}")


#: THE SUITE IS A DIRECTORY NOW — work order 162.
#:
#: `main()` was 21 883 lines and 1.15 MB, and every new screen's checks
#: made the next one more expensive: a check had to be placed inside a
#: file nobody can see whole, beside fixtures that had to be found by
#: grep, and a development run executed every check in the tree. The
#: checks live in `tools/smoke_suite/` now, one group of modules per
#: screen plus a shared core, and THIS file runs them.
#:
#: **They are executed, not imported, and into ONE namespace.** That is
#: not a shortcut: the checks bind names that later checks read — an
#: app, a laid-out screen, a parsed snapshot — which is exactly what
#: `main()` did with its locals. Importing each module would give every
#: one its own namespace and turn a move into a rewrite. So the whole
#: suite still runs in the order it always ran, in one scope, and the
#: only thing that changed is which file a check is written in.
SUITE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "smoke_suite")


def suite_modules():
    """Every check module, in the order the suite runs them.

    File-name order, and the leading number is what makes it an order.
    A module holds a contiguous run of the original `main()`, so
    running them in name order runs the suite in its original order —
    which is a constraint, not a convention: a check that depends on
    state an earlier one set up still has to see it.
    """
    return [os.path.join(SUITE_DIR, n) for n in sorted(os.listdir(SUITE_DIR))
            if n.endswith(".py")]


#: THE SUITE'S OWN SOURCE, AS A SET OF PATHS. Four checks grep the
#: whole tree for a second home of something and have to exclude the
#: file that names it in an assertion; while the suite was one file
#: that exclusion was one path. Both spellings are in, because the
#: callers compare against `os.path.relpath` results.
SUITE_FILES = frozenset(
    [os.path.join("tools", "smoke_test.py"), "tools/smoke_test.py"]
    + [os.path.join("tools", "smoke_suite", os.path.basename(p))
       for p in suite_modules()]
    + ["tools/smoke_suite/" + os.path.basename(p) for p in suite_modules()])


def suite_source():
    """Every line of the suite, as one text.

    Two checks read the suite's own source — one parses it to find any
    construction of a derived loader that bypasses the stand-ins, one
    greps it for the `slow(...)` guards and holds them against
    `SLOW_TIER`. Both used `__file__` and both would now see a
    ninetieth of the suite and pass on nothing. The concatenation
    parses as one module, and the line numbers it reports are the
    concatenation's, which only ever reach an assertion message.
    """
    out = [io.open(os.path.abspath(__file__), encoding="utf-8").read()]
    out += [io.open(path, encoding="utf-8").read() for path in suite_modules()]
    return "\n".join(out)


#: HALF THE READING BUDGET, PER CHECK MODULE — work order 162 part 5.
#: Work order 127 set 80 KB as what a session may read of one thing;
#: a check module gets half of it, so a screen's checks and the core
#: they lean on both fit. **This is a SETTING, not a measurement**,
#: and Data may change it — the number decides how often a screen's
#: group gains another module, and nothing else.
#:
#: The check that holds the suite to it is in `tools/smoke_suite/`,
#: in the core, with its exceptions listed in `v3_projektstatus.md`
#: the way decision 6 lists a file over 300 code lines. An exception
#: here is always the same thing: ONE section that is bigger than the
#: limit on its own, and a section is one check's block.
CHECK_MODULE_LIMIT = 40 * 1024

#: The first line of every check module declares the group it belongs
#: to. `tools/smoke_inventory.py` writes and reads the same marker —
#: one home, so a module renamed by hand still says what it is.
AREA_MARK = "# smoke-suite area:"


def module_area(path):
    """The group a check module belongs to, off its own first line."""
    with io.open(path, encoding="utf-8") as fh:
        first = fh.readline().strip()
    assert first.startswith(AREA_MARK), (
        f"{os.path.basename(path)} does not declare its group. Every "
        f"check module opens with `{AREA_MARK} <screen or core>`")
    return first[len(AREA_MARK):].strip()


def territory(screen):
    """The paths a `--screen` run is allowed to find changed.

    **One place, and it is computed.** A screen owns its own folder and
    its own check modules and nothing else; a new screen needs no edit
    here. Everything outside — `core/`, `assets/shared/`, `main.py`,
    `tools/`, another screen, the suite's core — widens the run,
    because a change there can break a check whose sentence this run
    would not have shown.
    """
    mine = [f"screens/{screen}/"]
    for path in suite_modules():
        if module_area(path) == screen:
            mine.append("tools/smoke_suite/" + os.path.basename(path))
    return mine


def _changed_outside(screen):
    """Files changed against HEAD that are not this screen's own.

    Index and working tree both, and untracked files too: a new file
    outside the screen is exactly the case 157 section 5(a) is about.
    A tree git cannot read at all widens, and says so — a tool that
    cannot measure something must not report the thing as absent.
    """
    import subprocess
    try:
        done = subprocess.run(["git", "status", "--porcelain"],
                              cwd=os.path.dirname(SUITE_DIR), text=True,
                              capture_output=True, timeout=60)
    except OSError as exc:
        return [f"(git could not be run: {exc})"]
    if done.returncode != 0:
        return [f"(git status failed: {done.stderr.strip()[:80]})"]
    mine = tuple(territory(screen))
    out = []
    for line in done.stdout.splitlines():
        path = line[3:].split(" -> ")[-1].strip().strip('"')
        if path and not path.startswith(mine):
            out.append(path)
    return sorted(out)


def main(screen=None):
    """Run the suite: every check module, in order, in one namespace.

    `screen` narrows what is PRINTED, never what runs — see `SCREEN`
    above for the measurement that decided that, and decision 31 in
    the fundament for the gates, which work order 162 did not touch.
    """
    global SCREEN, AREA
    SCREEN = screen
    for path in suite_modules():
        AREA = module_area(path)
        exec(compile(io.open(path, encoding="utf-8").read(), path, "exec"),
             globals())
    AREA = "core"

    # THE TIER IS IN THE LINE, so a fast pass can never be read as a
    # full one in a log, a hook's output or a report (work order 158).
    # And the SCREEN is in it too (work order 162), on the last line as
    # well as the first: a narrowed run is not a gate run, and a line
    # only at the top is a line a scrolled log does not carry.
    _sk = sum(SKIPPED.values())
    _tier = (f", {_sk} push-only checks NOT run of {PASS + _sk} total"
             if TIER == "fast" else "")
    if screen is not None:
        print(f"\nSMOKE TEST PASSED (SCREEN {screen} ONLY — NOT A GATE) "
              f"— {PASS} checks green{_tier}, {SHOWN} of them shown: "
              f"{screen}'s own and the core's. Nothing was skipped for "
              f"the screen; the rest simply did not print. Run "
              f"`python tools/smoke_test.py` before any handoff.")
    elif TIER == "fast":
        print(f"\nSMOKE TEST PASSED (FAST TIER) — {PASS} checks green"
              f"{_tier}. The full suite runs before every push.")
    else:
        print(f"\nSMOKE TEST PASSED — {PASS} checks green")
    return 0


QUIET_TAIL = 60


def _peak_rss_line():
    """The peak resident set of this process, read once at exit.

    `ru_maxrss` is kilobytes on Linux. It is the high-water mark over the
    whole run, which is the figure the thirty-run table needs: whether a
    run that grows is the run that crashes.
    """
    import resource
    kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return f"peak resident memory: {kb / 1024:.0f} MB"


def _run(quiet, screen=None):
    import faulthandler
    import tempfile
    # A duplicate of the REAL stderr, taken before any redirection, so a
    # segfault's stack reaches the terminal in quiet mode too. Kept
    # referenced for the life of the process: faulthandler writes to the
    # descriptor, and a collected file object would close it.
    global _FAULT_FILE
    _FAULT_FILE = os.fdopen(os.dup(2), "w")
    faulthandler.enable(file=_FAULT_FILE)
    if not quiet:
        rc = main(screen)
        print(_peak_rss_line())
        return rc
    sys.stdout.flush()
    sys.stderr.flush()
    log = tempfile.TemporaryFile()
    saved = os.dup(1), os.dup(2)
    os.dup2(log.fileno(), 1)
    os.dup2(log.fileno(), 2)

    def restore():
        sys.stdout.flush()
        sys.stderr.flush()
        os.dup2(saved[0], 1)
        os.dup2(saved[1], 2)
        log.seek(0)
        return log.read().decode("utf-8", "replace").splitlines()

    try:
        rc = main(screen)
    except BaseException:
        lines = restore()
        print("\n".join(lines[-QUIET_TAIL:]))
        print(_peak_rss_line())
        sys.stdout.flush()
        raise
    lines = restore()
    if rc:
        print("\n".join(lines[-QUIET_TAIL:]))
    else:
        print(next((l for l in reversed(lines)
                    if l.startswith("SMOKE TEST PASSED")), ""))
    print(_peak_rss_line())
    return rc


if __name__ == "__main__":
    # FULL IS THE DEFAULT, and that is the point of the flag being
    # opt-in (work order 158). A bare `python tools/smoke_test.py`
    # runs everything, exactly as it did before the tiers existed, so
    # Data, a forker, or a session that has never read work order 158
    # gets the whole suite by doing the obvious thing. Only the
    # pre-commit hook passes --fast; the pre-push hook does not.
    if "--fast" in sys.argv[1:]:
        TIER = "fast"
    # THE NAMES HERE CARRY A PREFIX, and that is not style. The check
    # modules are executed into THIS namespace, so a bare `_why` at
    # module level is a name eighty-odd check modules can rebind — and
    # one of them does. It cost the widening line its second printing
    # before the check in `tools/smoke_suite` that now refuses the
    # collision was written.
    _cli_screen = (sys.argv[sys.argv.index("--screen") + 1]
                   if "--screen" in sys.argv[1:] else None)
    _cli_why = None
    if _cli_screen is not None:
        _cli_known = {module_area(p) for p in suite_modules()}
        assert _cli_screen in _cli_known, (
            f"no check module belongs to {_cli_screen!r}. The groups "
            f"are {sorted(_cli_known)}")
        # THE SELECTOR WIDENS ITSELF; IT NEVER TRUSTS THE SESSION TO
        # REMEMBER (work order 162, part 4). Before it narrows anything
        # it asks git what has changed against HEAD — index, working
        # tree and untracked alike. A change outside this screen's own
        # territory can break a check whose sentence a narrowed run
        # would not have shown, so the run becomes the fast tier with
        # its full output and says which file did it: on the FIRST
        # line, before the checks, and again on the last, because a
        # line only at the end is a line a scrolled-away log does not
        # carry.
        _cli_outside = _changed_outside(_cli_screen)
        if _cli_outside:
            _cli_why = (
                f"WIDENED TO FAST TIER: {', '.join(_cli_outside[:4])}"
                + (f" and {len(_cli_outside) - 4} more"
                   if len(_cli_outside) > 4 else "")
                + f" changed outside screens/{_cli_screen}/")
            print(_cli_why, flush=True)
            TIER, _cli_screen = "fast", None
        else:
            print(f"SMOKE TEST (SCREEN {_cli_screen} ONLY — NOT A GATE): "
                  f"every check still runs; only {_cli_screen}'s own "
                  f"sentences and the core's are printed. Run the full "
                  f"suite before any handoff.", flush=True)
    _cli_rc = _run("--quiet" in sys.argv[1:], _cli_screen)
    if _cli_why:
        print(_cli_why)
    sys.exit(_cli_rc)
