"""The engine fixes OrionLayer requires, and the marker that proves each
one is built — the register `tools/version_check.py` checks a tree against.

Moved out of `version_check.py` by work order 246, byte for byte: the two
tables are data, the check is logic, and together they had reached the
40 KB limit (decision 6). Every name stays importable from
`version_check` (`version_check.LOCAL_PATCHES`, `.REPORTED_PATCHES`),
where callers and checks have always found it. A fix's open-fix number is
`version_check.FIX_NUMBERS`, beside the code that prints it.
"""
import os

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
    # patch file — until then the patch table named it and this list could
    # not. The one line carries no comment, so the line is the marker:
    # nothing else in orion2re writes `_old_race` from the loop index.
    "doc/ext_select_race_old_race.patch": (
        os.path.join("src", "game", "racesel.cpp"),
        "old_race = static_cast<int16_t>(i);",
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
        "fltscrn_stack_owner",
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
        "ORION2RE_NO_VSYNC",
        "ORION2RE_NO_VSYNC=1 is ignored, so a session-launched engine "
        "hangs in its first logo frames whenever its window is not drawn "
        "(open fix 31) and runs at a frame a second behind a full-screen "
        "window"),
    "doc/ext_officer_screen_state.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        # The block's own marker: "OFFS" is pushed a character at a time.
        "officer_star_displayed",
        "the snapshot carries none of the Leaders screen's view state "
        "(open fix 30), so POOL, DISMISS, assigning, PREV/NEXT, the star "
        "display and the ship grid stay the HD STATE placeholder"),
    "doc/ext_info_screen_state.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        # The block's own marker: "INFS" is pushed a character at a time.
        "bill_savegame[i]",
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
    # Applied 1 October 2026 by work order 199: 121950ed, on 9e19c9f3.
    "doc/ext_combat_popup.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 66.",
        "the engine does not send CPOP (open fix 66): the battle's scan view "
        "and board popup stay the F12 notice"),
    # Applied 1 October 2026 by work order 199: a8381e60, on 121950ed.
    "doc/ext_msgbox_items.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 67.",
        "the engine sends message boxes without their item values (open fix "
        "67): the boarding result's numbers are not printed"),
    # Applied 2 October 2026 by work order 200: 095ebac4, on a8381e60.
    "doc/ext_combat_options.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 68.",
        "the engine does not send COPT (open fix 68): the battle's OPTIONS "
        "panel is not offered and its options are read from the settings"),
    # Applied 2 October 2026 by work order 200: f031cbad, on 095ebac4.
    "doc/ext_help_list.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 69.",
        "the engine does not send HLPL (open fix 69): the audience's right-"
        "click help is not offered, and a forwarded right click cannot see "
        "the help that covers its field"),
    # Applied 2 October 2026 by work order 200: a8b5640b, on f031cbad.
    "doc/ext_language.patch": (
        os.path.join("src", "game", "mox2.cpp"),
        "OrionLayer, open fix 70.",
        "the engine ignores the player's language (open fix 70): its own "
        "texts stay English whatever Game Settings says"),
    # Applied 3 October 2026 by work order 210: e75477c5, on a8b5640b.
    "doc/ext_combat_absorber.patch": (
        os.path.join("src", "game", "cmbtfire.cpp"),
        "OrionLayer, open fix 74.",
        "the engine does not report the Energy Absorber's discharge (open fix "
        "74): its damage arrives with no shot to show"),
    # Applied 4 October 2026 by work order 212: 2b773c31, on e75477c5.
    "doc/ext_combat_sound.patch": (
        os.path.join("src", "game", "ericnet.cpp"),
        "OrionLayer, open fix 79.",
        "the engine plays the battle's sounds itself (open fix 79): they come "
        "before HD's picture, and HD has none to play"),
    # Applied 4 October 2026 by work order 212: 89494e72, on 2b773c31.
    "doc/ext_combat_waits.patch": (
        os.path.join("src", "game", "timer.cpp"),
        "OrionLayer, open fix 71.",
        "the hidden engine waits out every battle animation (open fix 71): "
        "each animated action reaches HD seconds late"),
    # Applied 4 October 2026 by work order 212: 3a076921, on 003af991 —
    # fix 71 amended: a taken battle command's first wait is skipped too.
    "doc/ext_combat_waits_command.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 71, amended.",
        "the hidden engine keeps the first wait of a commanded action (open "
        "fix 71, amended): 110 ms before a special weapon's picture"),
    # Applied 4 October 2026 by work order 212: 003af991, on 89494e72.
    "doc/ext_combat_fighter_beam.patch": (
        os.path.join("src", "game", "cmbtmis.cpp"),
        "OrionLayer, open fix 77.",
        "the engine does not report a fighter pass's beams (open fix 77): "
        "HD shows the pass's number only"),    "doc/ext_combat_beam_aim.patch": (
        os.path.join("src", "game", "beams.cpp"),
        "OrionLayer, open fix 82.",
        "the engine does not report where a beam is drawn (open fix 82): HD "
        "draws it between the units' centres and a miss's beat can differ"),
    "doc/ext_combat_gyro_spin.patch": (
        os.path.join("src", "game", "cmbtspec.cpp"),
        "OrionLayer, open fix 83.",
        "the engine does not report the gyro's spin (open fix 83): HD turns "
        "the target twice round"),
    # Applied 8 October 2026 by work order 223 (Data's decision): 8b1501f5,
    # on 910e1401.
    "doc/ext_field_list_content.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 84.",
        "the engine sends a field list only when its count changes (open fix "
        "84): a race report's RETURN to Races with the same count leaves HD "
        "on the report's list"),
    # Applied 9 October 2026 by work order 226 (Data's decision 1 of 9
    # October): bdc3009b, on 8b1501f5.
    "doc/ext_refit_first_ship.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 85.",
        "the engine does not report the refit ship list's first row (open "
        "fix 85): HD counts the pages it sent, and a slider moved in the "
        "game's window would put its cells on other ships"),
    # Applied 10 October 2026 by work order 229 (the standing decision of 4
    # October): 4642eb1e, on bdc3009b.
    "doc/ext_fleet_box_buttons.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 86.",
        "the engine does not say which field is which of the fleet box's "
        "order buttons (open fix 86): HD's fleet box offers no orders"),
    # Applied 10 October 2026 by work order 230 (decision 85): 34a1d873, on
    # 4642eb1e.
    "doc/ext_name_box.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 87.",
        "the engine does not send the name box (open fix 87): \"Enter Star "
        "Name\" after a star's first colony shows the F12 notice"),
    # Applied 10 October 2026 by work order 230 (decision 85): 6c431570.
    "doc/ext_text_fields.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 88.",
        "the engine does not send the text fields (open fix 88): Custom "
        "Race's name field shows nothing and reads nothing back"),
    # Applied 10 October 2026 by work order 230 (decision 85): 0ff8f875.
    "doc/ext_raw_key.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 89.",
        "the engine takes no raw key code (open fix 89): no F key, Alt+F "
        "key or Alt+letter reaches the game"),
    # Applied 10 October 2026 by work order 231 (decision 85): 48718673, on
    # 0ff8f875.
    "doc/ext_system_window.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 90.",
        "the engine does not send the star system window (open fix 90): the "
        "map's window has no fleet bar, and a window F5 / F6 opens is not "
        "drawn"),
    # Applied 11 October 2026 by work order 232 (decision 85): bbbc546c, on
    # 48718673.
    "doc/ext_invasion.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 91.",
        "the engine does not send the invasion (open fix 91): the invasion "
        "choice, the bombing and the ground combat show only the F12 "
        "notice"),
    # Applied 11 October 2026 by work order 233 (decision 85): 90a930f9, on
    # bbbc546c.
    "doc/ext_settle_pops.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 92.",
        "the engine takes no colonists to another colony (open fix 92): "
        "colonists carried on the colony screen cannot be dropped on "
        "another colony of the system display"),
    # Work order 243: the v2 branch's own fix (decision 97), on the fork's
    # branch `orionlayer` only.
    "doc/ext_layout_table.patch": (
        os.path.join("src", "ext", "ext_server.cpp"),
        "OrionLayer, open fix 93.",
        "the engine sends no LAYOUT (open fix 93): OrionLayer reads the "
        "records at the offsets of orion2re 1.60, and on v2 every value from "
        "s_player's total_pop on is read from the wrong bytes (no stars on "
        "the map, wrong sidebar)"),
    # Work order 259: on the fork's branch `orionlayer` only, 42f32654.
    "doc/ext_combat_absorber_charge.patch": (
        os.path.join("src", "game", "cmbtfire.cpp"),
        "OrionLayer, open fix 94.",
        "the engine does not send the Energy Absorber's charge (open fix "
        "94): HD draws the glow only once the state after a FIRE arrives, "
        "after the shot the original already shows it under"),
    # Work order 266: on the fork's branch `orionlayer` only, cb2bf131.
    "doc/ext_combat_converter_totals.patch": (
        os.path.join("src", "game", "cmbtspec.cpp"),
        "OrionLayer, open fix 95.",
        "the engine does not send the Stellar Converter's two totals (open "
        "fix 95): HD shows no damage numbers after the converter, where the "
        "original shows two over its target"),
    # Work order 270: on the fork's branch `orionlayer` only, be79dadf.
    "doc/ext_council.patch": (
        os.path.join("src", "game", "council.cpp"),
        "OrionLayer, open fix 96.",
        "the engine does not send the galactic council (open fix 96): it "
        "runs under id 12 and HD shows only the F12 notice"),
    # Work order 271: on the fork's branch `orionlayer` only, 360b8d0c.
    "doc/ext_planets_send.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "open fix 97.",
        "the engine does not send the Planets screen's state (open fix "
        "97): HD cannot send colony or outpost ships, show an order or "
        "undo it"),
    # Work order 274: on the fork's branch `orionlayer` only, 2a09cb76.
    "doc/ext_troop_popup.patch": (
        os.path.join("src", "game", "newpup.cpp"),
        "OrionLayer, open fix 98.",
        "the engine does not send the colony screen's troop popup (open "
        "fix 98): a click on the marines or armour shows only the F12 "
        "notice"),
    # Work order 295: on the fork's branch `orionlayer` only, 29047f2d.
    "doc/ext_bitmap_line_short.patch": (
        os.path.join("src", "game", "bitmap.cpp"),
        "OrionLayer, open fix 99.",
        "a tractor beam clipped to one pixel at the screen's edge stops the "
        "engine with SIGFPE (open fix 99): the battle ends without a "
        "message"),
    # Work order 306: on the fork's branch `orionlayer` only, 35486477.
    "doc/ext_combat_refusal_boxes.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 101.",
        "BOARD at an own ship and FIRE at a phased enemy are refused "
        "silently (open fix 101): the original's boxes (KENTEXT 0x40, 80) "
        "never show"),
    # Work order 310: on the fork's branch `orionlayer` only, f93344f6.
    "doc/ext_merge_relocation_mode.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 102.",
        "the engine does not send the galaxy map's merge-relocation mode "
        "(open fix 102): after F4 HD shows no sign that the next star click "
        "re-routes every relocation"),
    # Work order 316: on the fork's branch `orionlayer` only, 96c39753.
    "doc/ext_settle_anywhere.patch": (
        os.path.join("src", "ext", "ext_api.cpp"),
        "OrionLayer, open fix 103.",
        "the engine takes colonists only to a colony at the same star (open "
        "fix 103): no TRANSPORT button, no move from the Colonies list, and "
        "the original's questions answered NO"),
    # Work order 316: on the fork's branch `orionlayer` only, 4b77ed0b.
    "doc/ext_slider_popup.patch": (
        os.path.join("src", "game", "mainpups.cpp"),
        "OrionLayer, open fix 104.",
        "the engine does not send the slider popup (open fix 104): the "
        "galaxy map's freighter scrap and the leader cheat show only the "
        "F12 notice"),
    # Work order 316: on the fork's branch `orionlayer` only, 29c61acd.
    "doc/ext_antaran_room.patch": (
        os.path.join("src", "game", "antaroom.cpp"),
        "OrionLayer, open fix 105.",
        "the engine does not send the Antaran room (open fix 105): an "
        "Antaran attack's message shows only the F12 notice"),
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
