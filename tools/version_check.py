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
    # Applied 18 September 2026 (work order 130 B, open fix 25): an
    # ACTIVATE_FIELD into the research selection chooses the row it names.
    # The marker is the flag itself, in src/ext, because the tech.cpp
    # insertion reads it and a tree carrying only one of the two would
    # not compile — so either half proves the other.
    "doc/ext_tech_activate.patch": (
        os.path.join("src", "ext", "ext_api.h"),
        "g_activated_input",
        "the research selection commits the entry under the game's own "
        "pointer instead of the activated row, or dereferences null and "
        "kills the engine (open fixes 25 and 23) — so the HD research "
        "screen cannot choose a research at all"),
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
    # Applied 19 September 2026 (work order 134 C, open fixes 27 and 28).
    # NOT confirmed live — 134's live part is parked. Two entries because
    # they are two patches and either can be taken back alone; the read
    # half is useless without the screen and the write half is useless
    # without the read half, but a tree can carry either.
    "doc/ext_fleet_screen_state.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        # The block's own marker. "FLTS" would not do: it is four
        # characters pushed one at a time, so the literal is not in the
        # source as a word.
        "_fltscrn_stack_owner",
        "the snapshot carries none of the fleet screen's view state "
        "(open fix 27), so the HD screen cannot know which stack is "
        "shown, which ships are in the grid or which of them are "
        "selected, and hands over to the original picture"),
    "doc/ext_fleet_screen_select.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "Select_Fltscrn_Ship_",
        "MSG_SELECT_SHIP on screen 4 goes to open fix 21's handler, "
        "which refuses without the fleet box and writes an array this "
        "screen does not read (open fix 28) — so a single ship cannot "
        "be selected and only ALL changes the selection"),
    # Applied 26 September 2026 by work order 175 on Data's authorisation
    # (orion2re orionlayer-local f98b8547 and cc542e02).
    "doc/ext_present_no_vsync.patch": (
        os.path.join("src", "game", "platform.cpp"),
        "Present_VSync_Interval_",
        "ORION2RE_NO_VSYNC=1 is ignored, so a session-launched engine "
        "hangs in its first logo frames whenever its window is not drawn "
        "(open fix 31) and runs at a frame a second behind a full-screen "
        "window"),
    "doc/ext_officer_screen_state.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        # The block's own marker: "OFFS" is pushed a character at a time.
        "_officer_star_displayed",
        "the snapshot carries none of the Leaders screen's view state "
        "(open fix 30), so POOL, DISMISS, assigning, PREV/NEXT, the star "
        "display and the ship grid stay the HD STATE placeholder"),
    "doc/ext_info_screen_state.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        # The block's own marker: "INFS" is pushed a character at a time.
        "MOX::_bill_savegame[i]",
        "the snapshot carries neither the history divisors nor the turn "
        "messages (open fix 32), so the Info screen's History Graph draws "
        "no curves and its Turn Summary lists nothing"),
    # Applied 26 September 2026 (work order 179, Data's approval; orion2re
    # 9ab84230 on orionlayer-local). The marker is the new condition's name.
    "doc/ext_main_menu_save_slots.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "main_menu_load",
        "the main menu's Load dialog sends no save slots (open fix 34), so "
        "HD cannot draw it and shows the game's own picture through the "
        "safety net"),
}

#: Patches that are REPORTED to Joes and not yet applied: listed with
#: their marker so a tree that has them says so, but a tree without them
#: is not a mismatch. The day one is applied it moves up into
#: LOCAL_PATCHES, and from then on its absence fails. Same
#: `file: (relative path, marker, what it enables)`. Empty from open
#: fixes 20 and 21 moving up (15 September 2026) until open fix 34
#: (work order 177), and again since 34 moved up (work order 179). Work
#: order 180 B/C parked open fixes 35-40 here; without them the colony
#: screen and the build popup stay the game's own picture.
REPORTED_PATCHES = {
    "doc/ext_colony_screen_colony.patch": (
        "src/ext/ext_api.cpp", "OrionLayer, open fix 35.",
        "the colony screen and the build popup in HD (which colony)"),
    "doc/ext_colony_building_placement.patch": (
        "src/ext/ext_api.cpp", "OrionLayer, open fix 36.",
        "the colony screen's building grid"),
    "doc/ext_colony_status_word.patch": (
        "src/ext/ext_api.cpp", "OrionLayer, open fix 37.",
        "Plague and Pop Boom on the colony screen"),
    "doc/ext_colony_product_cost.patch": (
        "src/ext/ext_api.cpp", "OrionLayer, open fix 38.",
        "the production bar and the turn count"),
    "doc/ext_build_popup_queue.patch": (
        "src/ext/ext_api.cpp", "OrionLayer, open fix 39.",
        "the build popup's queue under edit"),
    "doc/ext_build_popup_lists.patch": (
        "src/ext/ext_api.cpp", "OrionLayer, open fix 40.",
        "the build popup's two lists and their numbers"),
}


#: Open fixes 35-40 in the order they are stacked on `ext_api.cpp` (work
#: order 181). Each appends its block after the one before, so they sit
#: on the trailing context of every earlier block in `SerializeState` —
#: a check that proves an earlier patch comes back off (`patch -R`) has to
#: take these off a copy first, last one first, as the stack was applied.
COLONY_SERIES = (
    "doc/ext_colony_screen_colony.patch",
    "doc/ext_colony_building_placement.patch",
    "doc/ext_colony_status_word.patch",
    "doc/ext_colony_product_cost.patch",
    "doc/ext_build_popup_queue.patch",
    "doc/ext_build_popup_lists.patch",
)


def take_off_colony_series(workdir, root):
    """Reverse every applied fix of COLONY_SERIES in `workdir` (a copy
    holding `src/ext/ext_api.cpp`), last first. Returns the list of
    (patch, returncode, output); a patch whose marker the copy does not
    carry is skipped, so a tree without the series passes through."""
    import subprocess
    api = os.path.join(workdir, "src", "ext", "ext_api.cpp")
    done = []
    for patch in reversed(COLONY_SERIES):
        table = LOCAL_PATCHES if patch in LOCAL_PATCHES else REPORTED_PATCHES
        marker = table[patch][1]
        with open(api, "r", errors="replace") as f:
            if marker not in f.read():
                continue
        run = subprocess.run(
            ["patch", "-R", "-p1", "-i", os.path.join(root, patch)],
            cwd=workdir, capture_output=True, text=True)
        done.append((patch, run.returncode, run.stdout + run.stderr))
        if run.returncode != 0:
            break
    return done

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
