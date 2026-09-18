#!/usr/bin/env python3
"""Check ORION2RE_VERSION against orion2re's own source.

The version shown on the main menu is maintained by hand, because
the Extension API does not report it: HELLO_REPLY carries only
PROTO_VERSION and the state snapshot has no version field. A number
copied out of somebody else's tree drifts silently, so this turns
"did Joes bump the version?" into a command instead of a memory task.

It reads the two places orion2re keeps it:

    src/version.h        ENGINE_VERSION[] = "<x.y.z>"
    src/game/consts.h    GAME_VERSION_LABEL[] = "Version <x.y.z>"

Those two are separate literals in orion2re, not one derived from
the other, so they can disagree with each other as well as with us.
All three are reported.

IT ALSO CHECKS THE LOCAL PATCHES, and `doc/ext_move_pop.patch` is
the one that matters: the pop-move command is a LOCAL divergence in
Joes' tree, and an engine without it accepts `MSG_SET_JOBS` by
throwing it away — `ProcessInput`'s switch has no case for an
unknown type and falls through to `default: break`. Nothing fails,
nothing moves, and the client waits for a snapshot that will never
differ. That is the silent failure decision 33 exists to refuse, so
an unpatched tree has to fail a CHECK instead. Detected by the
marker each patch leaves in the source, never by re-reading the
patch file: a `.patch` on disk says what was written down, not
what was built.

Usage (from the project root):
    python tools/version_check.py
    python tools/version_check.py ~/some/other/orion2re

Exit codes: 0 all three agree, 1 a mismatch, 2 the source tree was
not found (checked, not crashed — an unreachable tree is not the
same answer as a wrong version).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

from core.config import ORION2RE_VERSION  # noqa: E402

DEFAULT_TREES = ["~/orion2re", "~/src/orion2re", "/tmp/orion2re-main"]

RE_ENGINE = re.compile(
    r'ENGINE_VERSION\s*\[\s*\]\s*=\s*"([^"]+)"')
RE_LABEL = re.compile(
    r'GAME_VERSION_LABEL\s*\[\s*\]\s*=\s*"([^"]+)"')

#: Local patches that must be present in the tree, and the marker
#: that proves each one was applied — a symbol the patch introduces
#: and nothing else in orion2re defines. `file: (relative path,
#: marker, what breaks without it)`.
LOCAL_PATCHES = {
    # Applied 4 September 2026 (open fix 3, "INJECT_CLICK coordinates are
    # mapped as window coordinates"). Two halves; the marker is the
    # COORDINATE half, which lives wholly in src/ext and converts the
    # client's 640x480 point back to window space before the event is
    # pushed. Required here from work order 130 A on: the fallback view
    # now forwards a click for every screen no HD screen claims, and it
    # hands the game a game-space point. Without this half the engine
    # reads that point as a window coordinate, so on a 1920x1080 window
    # every forwarded click lands at roughly a third of its intended
    # distance from the top left — on the wrong field, silently.
    "doc/ext_inject_click.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "Game_Point_To_Window_Point_",
        "INJECT_CLICK and MSG_CANCEL_FIELD read their 640x480 point as a "
        "window coordinate, so every click the fallback view forwards "
        "lands somewhere else (open fix 3, the coordinate half)"),
    # Applied 17 September 2026 (work order 129 B, open fix 24): the two
    # turn-start research dialogs report synthetic ids 52 and 53 on the wire.
    # The marker is the guard in the science room, because the override
    # itself lives in src/ext and a tree carrying only that would report
    # nothing new.
    "doc/ext_research_screens.patch": (
        os.path.join("src", "game", "science.cpp"),
        "ext_screen_guard(52)",
        "the science room and SELECT NEW RESEARCH both report the galaxy "
        "map's screen 0, so HD keeps drawing the map over them and a click "
        "can reach the research list (open fix 23's crash)"),
    # Revised 17 September 2026 (work order 128 B, open fix 22): race
    # selection reports the synthetic 51, no longer SCREEN_RACE (6), which
    # is the Races screen. A tree with the old revision routes the galaxy
    # map's RACES button into HD Select Race — so the marker is the new
    # revision's own constant, not the patch's older lines.
    "doc/ext_screen_id.patch": (
        os.path.join("src", "game", "racesel.cpp"),
        "EXT_SCREEN_RACE_SELECTION = 51",
        "race selection reports 6, the Races screen's id, and HD draws "
        "Select Race over diplomacy (open fix 22)"),
    "doc/ext_move_pop.patch": (
        os.path.join("src", "game", "colmove.h"),
        "_ext_suppress_refusal_help",
        "MSG_SET_JOBS is dropped by ProcessInput's default case, so "
        "every pop move silently does nothing"),
    # Applied 16 September 2026 by Data, confirmed live the same evening:
    # the in-game Load dialog showed the engine's slot names (open fix 14).
    "doc/ext_save_slots.patch": (
        os.path.join("src", "ext", "ext_server.h"),
        "MSG_SAVE_SLOTS",
        "the GAME menu's Load and Save rows get no slot names, stardates or "
        "dates, and a name edit starts empty"),
    # Applied 15 September 2026 (briefs 118, 119), confirmed live on SAVE5.
    "doc/ext_fleet_selection.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        # Revision 2's own identifier: revision 1 also wrote "FSEL", and a
        # tree still carrying it must not read as the revision OrionLayer
        # parses (brief 119).
        "fsel_chain_len",
        "the snapshot carries no ship node table and no fleet box "
        "selection (open fix 20), so HD draws no fleet box and a fleet "
        "cannot be moved from the HD map"),
    "doc/ext_fleet_select_ship.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "Select_Ship_",
        "MSG_SELECT_SHIP falls into ProcessInput's default case, so a "
        "click on a ship cell silently selects nothing (open fix 21)"),
}

#: Patches that are REPORTED to Joes and not yet applied: listed with
#: their marker so a tree that has them says so, but a tree without them
#: is not a mismatch. The day one is applied it moves up into
#: LOCAL_PATCHES, and from then on its absence fails. Same
#: `file: (relative path, marker, what it enables)`. Empty since open
#: fixes 20 and 21 moved up (15 September 2026).
REPORTED_PATCHES = {}


def find_tree(argv):
    """First existing candidate tree, or None."""
    candidates = argv[1:] if len(argv) > 1 else DEFAULT_TREES
    for cand in candidates:
        path = os.path.expanduser(cand)
        if os.path.isfile(os.path.join(path, "src", "version.h")):
            return path
    return None


def has_marker(tree, rel, marker):
    """True when `marker` appears in `tree/rel`. None if unreadable."""
    path = os.path.join(tree, rel)
    if not os.path.isfile(path):
        return None
    with open(path, "r", errors="replace") as f:
        return marker in f.read()


def grep(path, pattern):
    """First capture group of pattern in path, or None."""
    if not os.path.isfile(path):
        return None
    with open(path, "r", errors="replace") as f:
        match = pattern.search(f.read())
    return match.group(1) if match else None


def main():
    tree = find_tree(sys.argv)
    print(f"OrionLayer  core/config.ORION2RE_VERSION : "
          f"{ORION2RE_VERSION}")

    if not tree:
        looked = sys.argv[1:] or DEFAULT_TREES
        print("\norion2re source not found — looked in: "
              + ", ".join(looked))
        print("Pass the path:  python tools/version_check.py "
              "~/path/to/orion2re")
        return 2

    print(f"orion2re    {tree}")
    engine = grep(os.path.join(tree, "src", "version.h"), RE_ENGINE)
    label = grep(os.path.join(tree, "src", "game", "consts.h"),
                 RE_LABEL)
    print(f"            src/version.h ENGINE_VERSION      : "
          f"{engine or '(not found)'}")
    print(f"            src/game/consts.h VERSION_LABEL   : "
          f"{label or '(not found)'}")

    problems = []
    if engine is None:
        problems.append("ENGINE_VERSION not found in src/version.h")
    elif engine != ORION2RE_VERSION:
        problems.append(
            f"engine is {engine}, OrionLayer says {ORION2RE_VERSION}"
            " — update core/config.ORION2RE_VERSION")
    if label is None:
        problems.append(
            "GAME_VERSION_LABEL not found in src/game/consts.h")
    elif engine and label != f"Version {engine}":
        # The two literals disagreeing is a bug in orion2re, not
        # here, but it decides which string the main menu shows.
        problems.append(
            f"orion2re disagrees with itself: label is {label!r}, "
            f"engine is {engine!r}")

    print()
    for patch, (rel, marker, breaks) in sorted(LOCAL_PATCHES.items()):
        found = has_marker(tree, rel, marker)
        state = ("APPLIED" if found else
                 "MISSING" if found is False else "NO SUCH FILE")
        print(f"            {patch:28} : {state}")
        if not found:
            problems.append(
                f"{patch} is not applied to {tree} (no {marker!r} in "
                f"{rel}) — without it {breaks}. Apply with: "
                f"cd {tree} && patch -p1 < {patch}")

    for patch, (rel, marker, enables) in sorted(REPORTED_PATCHES.items()):
        found = has_marker(tree, rel, marker)
        state = ("applied" if found else
                 "not applied (reported)" if found is False
                 else "no such file")
        print(f"            {patch:32} : {state} — {enables}")

    # core/screen_names.ENGINE_SCREEN_MAX is a hand copy of the enum's last
    # value, and synthetic screen ids are only safe above it (decision 36:
    # a copy gets a checker).
    from core.screen_names import ENGINE_SCREEN_MAX
    consts = os.path.join(tree, "src", "game", "orion2_consts.h")
    if os.path.exists(consts):
        values = [int(v) for v in re.findall(
            r"\bSCREEN_[A-Z0-9_]+\s*=\s*(\d+)", open(consts).read())]
        top = max(values) if values else None
        print(f"            SCREEN enum last value       : {top} "
              f"(OrionLayer ENGINE_SCREEN_MAX {ENGINE_SCREEN_MAX})")
        if top != ENGINE_SCREEN_MAX:
            problems.append(
                f"orion2_consts.h's SCREEN enum ends at {top}, "
                f"core/screen_names.ENGINE_SCREEN_MAX says "
                f"{ENGINE_SCREEN_MAX} — a synthetic screen id may now "
                f"collide with a real one")

    if problems:
        print("\nMISMATCH")
        for line in problems:
            print(f"  - {line}")
        return 1

    print("\nOK — all three agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
