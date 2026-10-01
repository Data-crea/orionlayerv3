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
    # Applied 17 September 2026 as found (work order 126 A, open fix 5,
    # orion2re 6598052c); required from work order 192, which gave it its
    # patch file — until then README's table named it and this list could
    # not. The one line carries no comment, so the line is the marker:
    # nothing else in orion2re writes `_old_race` from the loop index.
    "doc/ext_select_race_old_race.patch": (
        os.path.join("src", "game", "racesel.cpp"),
        "_old_race = static_cast<int16_t>(i);",
        "accepting a Custom Race can crash the Flag Screen on "
        "racesel.lbx [entry 138] (open fix 5)"),
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
    # Applied 27 September 2026 by work order 181 (Data's approval of the
    # series in brief 180; orion2re c5d4dacd … 2097b0c6 on
    # orionlayer-local, in this order). Every marker is the block's own
    # "OrionLayer, open fix N." comment, one line each since 181 re-wrapped
    # fix 39's.
    "doc/ext_colony_screen_colony.patch": (
        os.path.join("src", "ext", "ext_api.cpp"), "OrionLayer, open fix 35.",
        "the snapshot does not say which colony screen 1 and the build popup "
        "(25) show (open fix 35), so both stay the game's own picture"),
    "doc/ext_colony_building_placement.patch": (
        os.path.join("src", "ext", "ext_api.cpp"), "OrionLayer, open fix 36.",
        "the colony screen's building grid is not on the wire (open fix 36) "
        "and the colony screen stays the game's own picture"),
    "doc/ext_colony_status_word.patch": (
        os.path.join("src", "ext", "ext_api.cpp"), "OrionLayer, open fix 37.",
        "Plague and Pop Boom are not on the wire (open fix 37) and the "
        "colony screen stays the game's own picture"),
    "doc/ext_colony_product_cost.patch": (
        os.path.join("src", "ext", "ext_api.cpp"), "OrionLayer, open fix 38.",
        "the product's cost and turns are not on the wire (open fix 38) and "
        "the colony screen and the build popup stay the game's own picture"),
    "doc/ext_build_popup_queue.patch": (
        os.path.join("src", "ext", "ext_api.cpp"), "OrionLayer, open fix 39.",
        "the build popup's queue under edit is not on the wire (open fix "
        "39) and the popup stays the game's own picture"),
    "doc/ext_build_popup_lists.patch": (
        os.path.join("src", "ext", "ext_api.cpp"), "OrionLayer, open fix 40.",
        "the build popup's two lists and their numbers are not on the wire "
        "(open fix 40) and the popup stays the game's own picture"),
    # Applied 27 September 2026 by work order 183 (Data's approval; written,
    # proved and parked by 182; orion2re 4bf152e4 on orionlayer-local). The
    # marker is on one line at both changed places. Read in platform.cpp
    # since work order 186: open fix 43 replaced 41's line in ext_api.cpp
    # (the flag now starts from ORION2RE_HIDE_WINDOW) and kept 41's other
    # half, a hidden window presenting without VSync, with its marker.
    "doc/ext_engine_window_hidden.patch": (
        os.path.join("src", "game", "platform.cpp"), "OrionLayer, open fix 41.",
        "the engine's own window is shown on the player's desktop at every "
        "start (open fix 41), beside OrionLayer's, and the original follows "
        "the real pointer over it"),
    # Applied 28 September 2026 by work order 186 (Data's approval; written,
    # proved and parked by 185). One commit per fix on orionlayer-local, in
    # the order 44, 45, 46, 47, 43: 70d31b10, 4af9fefa, 8aea1a25, ba9b6bc6,
    # 230a0638. 45 sits on 44 and 47 on 46; 43 amends 41 (the window hidden
    # only when the starter asks, shown again on request). 43, 46 and 47 were
    # re-cut on the tip they were applied to (positions only).
    "doc/ext_engine_window_on_request.patch": (
        os.path.join("src", "ext", "ext_api.cpp"), "OrionLayer, open fix 43.",
        "an engine started without OrionLayer is invisible for good and F12 "
        "cannot show the engine's own window (open fix 43)"),
    "doc/ext_ship_designer_state.patch": (
        os.path.join("src", "ext", "ext_api.cpp"), "OrionLayer, open fix 44.",
        "the Ship Designer's design is not on the wire (open fix 44) and the "
        "designer stays the game's own picture"),
    "doc/ext_ship_designer_boxes.patch": (
        os.path.join("src", "game", "desbox.cpp"), "OrionLayer, open fix 45.",
        "the Ship Designer's three pickers report 3 and their lists are not "
        "on the wire (open fix 45): they stay the game's own picture"),
    "doc/ext_audience_screen.patch": (
        os.path.join("src", "game", "dip_scrn_main.cpp"),
        "OrionLayer, open fix 46.",
        "the diplomacy audience has no id of its own (open fix 46) and stays "
        "the game's own picture"),
    "doc/ext_audience_state.patch": (
        os.path.join("src", "ext", "ext_api.cpp"), "OrionLayer, open fix 47.",
        "the diplomacy audience's statement, reply and menu are not on the "
        "wire (open fix 47) and the audience stays the game's own picture"),
    # Applied 28 September 2026 by work order 188 (the order's advance
    # approval of the engine fixes a part needs): 010870bc, on 230a0638.
    "doc/ext_fleet_move_verdict.patch": (
        os.path.join("src", "ext", "ext_api.cpp"), "OrionLayer, open fix 48.",
        "the move verdict for the fleet box's selection is not on the wire "
        "(open fix 48) and the galaxy map draws no travel line on hover"),
    # Applied 28 September 2026 by work order 188: 76f8c438, on 010870bc.
    "doc/ext_message_box_text.patch": (
        os.path.join("src", "game", "gendraw.cpp"), "OrionLayer, open fix 29.",
        "the generic message box's text is not on the wire (open fix 29): "
        "HD shows the F12 notice in every box's place"),
    # Applied 29 September 2026 by work order 188: 6859e163, on 76f8c438.
    "doc/ext_turn_popups.patch": (
        os.path.join("src", "game", "turnsum.cpp"), "OrionLayer, open fix 49.",
        "the turn-time popups have no id of their own and their content is "
        "not on the wire (open fix 49): they stay behind the F12 notice"),
    # Applied 29 September 2026 by work order 188: 65b41b66, on 6859e163.
    "doc/ext_hall_of_fame.patch": (
        os.path.join("src", "game", "score.cpp"), "OrionLayer, open fix 50.",
        "the Hall of Fame's entries are not on the wire (open fix 50): it "
        "stays behind the F12 notice"),
    # Applied 29 September 2026 by work order 188: 8f7bd9e3, on 65b41b66.
    "doc/ext_multiplayer_state.patch": (
        os.path.join("src", "game", "multplay.cpp"), "OrionLayer, open fix 51.",
        "the multiplayer steps are not on the wire (open fix 51): all but "
        "the setup stay behind the F12 notice"),
    # Applied 29 September 2026 by work order 191: 96da4c4d, on 8f7bd9e3.
    "doc/ext_input_delay_tick.patch": (
        os.path.join("src", "game", "fields.cpp"), "OrionLayer, open fix 42.",
        "a screen is silent on the wire during its input delay (open fix "
        "42): the research panel's list arrives ~550 ms late on every entry"),
    # Applied 30 September 2026 by work order 194: ab3f6892, on 96da4c4d.
    "doc/ext_inject_right_click.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 61.",
        "the wire has no right click at a point (open fix 61): the F12 view "
        "cannot turn a ship on the battle map"),
    # Applied 30 September 2026 by work order 194: 2495e1cf, on ab3f6892.
    "doc/ext_combat_screen_id.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 52.",
        "a tactical battle has no screen id (open fix 52): it reports 12 "
        "and no combat block is written"),
    # Applied 30 September 2026 by work order 194: 9b7dcba0, on 2495e1cf.
    "doc/ext_combat_state.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 53.",
        "the tactical battle's state is not on the wire (open fix 53): no "
        "unit, turn, view origin or legal move reaches HD"),
    # Applied 30 September 2026 by work order 194: f506bc6c, on 9b7dcba0.
    "doc/ext_combat_ordnance.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 55.",
        "the ordnance in flight is not on the wire (open fix 55): no "
        "missile, torpedo or fighter reaches HD"),
    # Applied 30 September 2026 by work order 194: f1e6c581, on f506bc6c.
    "doc/ext_combat_result.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 57.",
        "how a battle ended is not on the wire (open fix 57): HD sees the "
        "result only as a changed ship list"),
    # Applied 30 September 2026 by work order 194: 750434ef, on f1e6c581.
    "doc/ext_combat_targets.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 54.",
        "what the acting unit's weapons can hit is not on the wire (open "
        "fix 54): HD would have to recompute arcs, range and legality"),
    # Applied 30 September 2026 by work order 194: 6f87c151, on 750434ef.
    "doc/ext_fleet_box_scroll.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 59.",
        "the fleet box's scroll row is not on the wire (open fix 59): HD "
        "shows a stack past nine ships from its first nine"),
    # Applied 30 September 2026 by work order 194: 5bd4c404, on 6f87c151.
    "doc/ext_combat_events.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 56.",
        "the battle's events are not on the wire (open fix 56): HD cannot "
        "animate a battle or hold a result until its animation"),
    # Applied 30 September 2026 by work order 194: e4b2256a, on 5bd4c404.
    "doc/ext_combat_commands.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 58.",
        "a battle cannot be played without clicks on the original's view "
        "(open fix 58): no move, fire or turn command"),
    # Applied 30 September 2026 by work order 197: 6f69de27, on e4b2256a.
    "doc/ext_activate_checked.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 62.",
        "an activation is taken by whatever list comes next (open fix 62): "
        "SELECT NEW RESEARCH can commit a row nobody chose (open fix 26)"),
    # Applied 1 October 2026 by work order 197: ee844b0b, on 6f69de27.
    "doc/ext_combat_events_merge.patch": (
        os.path.join("src", "game", "cmbtmis.cpp"),
        "OrionLayer, open fix 63.",
        "CMEV reports hundreds of missile merges of empty slots (open fix "
        "63): the battle's event stream does not fit its state"),
    # Applied 1 October 2026 by work order 197: 76c7b880, on ee844b0b.
    "doc/ext_combat_command_view.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 65.",
        "a battle command can name a cell outside the original's view (open "
        "fix 65): a tractoring ship moved there crashes the engine"),
    # Applied 1 October 2026 by work order 197: 9e19c9f3, on 76c7b880.
    "doc/ext_set_spies.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 64.",
        "the engine does not take MSG_SET_SPIES (open fix 64): the HD Races "
        "screen cannot move spies or set a mission"),
}

#: Patches that are REPORTED to Joes and not yet applied: listed with
#: their marker so a tree that has them says so, but a tree without them
#: is not a mismatch. The day one is applied it moves up into
#: LOCAL_PATCHES, and from then on its absence fails. Same
#: `file: (relative path, marker, what it enables)`. Empty from open
#: fixes 20 and 21 moving up (15 September 2026) until open fix 34
#: (work order 177), again since 34 moved up (work order 179), and again
#: since work order 181 moved up open fixes 35-40, which work order 180
#: had parked here — until 182 parked open fix 41 here, and again since
#: work order 183 moved 41 up — until work order 184 parked open fix 42,
#: and work order 185 open fixes 43-47, which work order 186 moved up;
#: 42 stayed (Data: not approved) until work order 191 moved it up
#: (Data: "Open Fix 42" in its bug list).
REPORTED_PATCHES = {
}


#: The open-fix number(s) each patch carries, for a reader who has to be
#: told WHICH fixes an engine needs rather than which files — `tools/
#: setup.py` prints them so a fresh clone on another machine learns it
#: (work order 181). Keyed exactly like LOCAL_PATCHES plus
#: REPORTED_PATCHES, and a smoke check holds the keys to both and each
#: number to the README row that names the patch; the numbers are the
#: README table's, never parsed out of the prose above.
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
