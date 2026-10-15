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
from workdirs import BUNDLES  # noqa: E402,F401 (198: a tree is cloned from one)

#: README's "Getting started" clones the fork beside OrionLayer, so a
#: stranger's tree is `../orion2re`, first. Work order 244's way from zero
#: against GitHub: setup said "no orion2re found here" right after step 1
#: built it, and on this machine it measured `~/orion2re` instead.
README_TREE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "orion2re")
DEFAULT_TREES = [README_TREE, "~/orion2re", "~/src/orion2re",
                 "/tmp/orion2re-main"]
#: THE SOURCE OrionLayer's transcriptions cite (work order 243). Every
#: `file.cpp:line` in the tree, and every name a check holds a table to,
#: is orion2re 1.60's (`orionlayer-local`): the engine moved to v2.0.0,
#: which renamed almost every identifier and moved every line. That source
#: stays readable as a worktree of `orionlayer-local`; `~/orion2re` counts
#: while it is still 1.60.
SOURCE_160 = os.path.join(os.environ.get("ORIONLAYER_WORK",
                                         os.path.expanduser("~/claude")),
                          "engines", "orion2re_160_source")


def _same_version(label, engine):
    """`GAME_VERSION_LABEL` names `ENGINE_VERSION`: "Version 1.60.0" and
    "1.60.0" — or, as orion2re v2 writes them, "Version 2.00" and its
    three-part number (work order 243): the same numbers, zeros at the end
    aside."""
    def nums(text):
        parts = [int(n) for n in re.findall(r"\d+", text or "")]
        while parts and parts[-1] == 0:
            parts.pop()
        return parts
    return bool(label) and label.startswith("Version ") and \
        nums(label) == nums(engine)


def find_source_tree():
    """The orion2re 1.60 source the citations name, or None."""
    for cand in [SOURCE_160] + DEFAULT_TREES:
        path = os.path.expanduser(cand)
        version = os.path.join(path, "src", "version.h")
        if os.path.isfile(version) and '"1.60' in open(
                version, errors="replace").read():
            return path
    return None

RE_ENGINE = re.compile(
    r'ENGINE_VERSION\s*\[\s*\]\s*=\s*"([^"]+)"')
RE_LABEL = re.compile(
    r'GAME_VERSION_LABEL\s*\[\s*\]\s*=\s*"([^"]+)"')

#: The register of required and reported patches, each with its marker,
#: lives in `tools/patch_markers.py` (work order 246: the tables are data,
#: this file is the check); the names stay importable from here.
try:  # run as a script (tools/ on the path) or imported as tools.version_check
    from patch_markers import LOCAL_PATCHES, REPORTED_PATCHES  # noqa: E402
except ImportError:
    from tools.patch_markers import (  # noqa: E402
        LOCAL_PATCHES, REPORTED_PATCHES)


#: The open-fix number(s) each patch carries, for a reader who has to be
#: told WHICH fixes an engine needs rather than which files — `tools/
#: setup.py` prints them so a fresh clone on another machine learns it
#: (work order 181). Keyed exactly like LOCAL_PATCHES plus
#: REPORTED_PATCHES, and a smoke check holds the keys to both and each
#: number to the patch table's row that names the patch
#: (dev:doc/engine_patches.md, out of README since work order 249); the
#: numbers are the table's, never parsed out of the prose above.
FIX_NUMBERS = {
    "doc/ext_inject_click.patch": (3,),
    "doc/ext_select_race_old_race.patch": (5,),
    "doc/ext_move_pop.patch": (12,),
    "doc/ext_save_slots.patch": (14,),
    "doc/ext_fleet_selection.patch": (20,),
    "doc/ext_fleet_select_ship.patch": (21,),
    "doc/ext_screen_id.patch": (22,),
    "doc/ext_research_screens.patch": (24,),
    "doc/ext_tech_activate.patch": (25,),
    "doc/ext_fleet_screen_state.patch": (27,),
    "doc/ext_fleet_screen_select.patch": (28,),
    "doc/ext_officer_screen_state.patch": (30,),
    "doc/ext_present_no_vsync.patch": (31,),
    "doc/ext_info_screen_state.patch": (32,),
    "doc/ext_main_menu_save_slots.patch": (34,),
    "doc/ext_colony_screen_colony.patch": (35,),
    "doc/ext_colony_building_placement.patch": (36,),
    "doc/ext_colony_status_word.patch": (37,),
    "doc/ext_colony_product_cost.patch": (38,),
    "doc/ext_build_popup_queue.patch": (39,),
    "doc/ext_build_popup_lists.patch": (40,),
    "doc/ext_engine_window_hidden.patch": (41,),
    "doc/ext_input_delay_tick.patch": (42,),
    "doc/ext_engine_window_on_request.patch": (43,),
    "doc/ext_ship_designer_state.patch": (44,),
    "doc/ext_ship_designer_boxes.patch": (45,),
    "doc/ext_audience_screen.patch": (46,),
    "doc/ext_audience_state.patch": (47,),
    "doc/ext_fleet_move_verdict.patch": (48,),
    "doc/ext_message_box_text.patch": (29,),
    "doc/ext_turn_popups.patch": (49,),
    "doc/ext_hall_of_fame.patch": (50,),
    "doc/ext_multiplayer_state.patch": (51,),
    "doc/ext_inject_right_click.patch": (61,),
    "doc/ext_combat_screen_id.patch": (52,),
    "doc/ext_combat_state.patch": (53,),
    "doc/ext_combat_ordnance.patch": (55,),
    "doc/ext_combat_result.patch": (57,),
    "doc/ext_combat_targets.patch": (54,),
    "doc/ext_fleet_box_scroll.patch": (59,),
    "doc/ext_combat_events.patch": (56,),
    "doc/ext_combat_commands.patch": (58,),
    "doc/ext_activate_checked.patch": (62,),
    "doc/ext_combat_events_merge.patch": (63,),
    "doc/ext_combat_command_view.patch": (65,),
    "doc/ext_set_spies.patch": (64,),
    "doc/ext_combat_popup.patch": (66,),
    "doc/ext_msgbox_items.patch": (67,),
    "doc/ext_combat_options.patch": (68,),
    "doc/ext_help_list.patch": (69,),
    "doc/ext_language.patch": (70,),
    "doc/ext_combat_absorber.patch": (74,),
    "doc/ext_combat_sound.patch": (79,),
    "doc/ext_combat_waits.patch": (71,),
    "doc/ext_combat_fighter_beam.patch": (77,),
    "doc/ext_combat_waits_command.patch": (71,),
    "doc/ext_combat_beam_aim.patch": (82,),
    "doc/ext_combat_gyro_spin.patch": (83,),
    "doc/ext_field_list_content.patch": (84,),
    "doc/ext_refit_first_ship.patch": (85,),
    "doc/ext_fleet_box_buttons.patch": (86,),
    "doc/ext_name_box.patch": (87,),
    "doc/ext_text_fields.patch": (88,),
    "doc/ext_raw_key.patch": (89,),
    "doc/ext_system_window.patch": (90,),
    "doc/ext_invasion.patch": (91,),
    "doc/ext_settle_pops.patch": (92,),
    "doc/ext_layout_table.patch": (93,),
    "doc/ext_combat_absorber_charge.patch": (94,),
    "doc/ext_combat_converter_totals.patch": (95,),
    "doc/ext_council.patch": (96,),
    "doc/ext_planets_send.patch": (97,),
    "doc/ext_troop_popup.patch": (98,),
}


def required_fixes():
    """The open-fix numbers every LOCAL patch carries, sorted."""
    return sorted({n for patch in LOCAL_PATCHES for n in FIX_NUMBERS[patch]})


def tree_report(tree=None):
    """(tree, missing patches) for the first tree found, or (None, None)."""
    tree = tree or find_tree([None])
    if tree is None:
        return None, None
    return tree, [p for p, (rel, marker, _b) in sorted(LOCAL_PATCHES.items())
                  if not has_marker(tree, rel, marker)]

#: The stacked patches on `ext_api.cpp` and how a check takes them off a
#: copy live in `tools/patch_stack.py` (work order 186); the names stay
#: importable from here, where the checks have always found them.
try:  # run as a script (tools/ on the path) or imported as tools.version_check
    from patch_stack import (  # noqa: E402,F401
        COLONY_SERIES, STACKED_AFTER_COLONY, take_off_colony_series)
except ImportError:
    from tools.patch_stack import (  # noqa: E402,F401
        COLONY_SERIES, STACKED_AFTER_COLONY, take_off_colony_series)

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
    elif engine and not _same_version(label, engine):
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
