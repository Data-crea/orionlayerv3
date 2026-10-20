"""orion2re screen-ID name tables — the one place they live.

Display-only. Routing never uses this module: screens self-describe
via GAME_SCREEN_ID (see core/dispatcher.py), so nothing here can
break auto-switching if a name is wrong or missing.

Before this module existed, the same id -> name mapping was copied
independently into core/dispatcher.py (status bar), dev:tools/ext_diag.py
(SCREEN_NAMES) and dev:doc/v3_orion2re_index.md (Screen-Enum table) — and
they had already drifted: dispatcher.py was missing id 7 (EXIT),
dev:tools/ext_diag.py was missing id 50 (the synthetic custom_race screen from
the ext-API patch). This is exactly the failure mode described in
the 28 Aug project status entry ("A field dump is not documentation")
that mis-labelled Galaxy Map field 14 for two weeks — a label copied
into more than one place is a label that can go stale in some of
them. Zero project imports (no pygame), so tools/ext_diag*.py can
still import it without pulling in the rest of the package.

No project import needed elsewhere either — pure data.

ENGINE_NAMES: the orion2re SCREEN enum name (orion2_consts.h),
    UPPER_SNAKE, for wire-protocol / diagnostic output.
ORIONLAYER_NAMES: the OrionLayer screen/folder name shown on the
    status bar, or None where no HD screen exists yet (falls back
    to the original framebuffer).

Every label here is interpretation until checked against
orion2_consts.h — same caveat as any other field/screen label in
this project (see dev:doc/v3_orion2re_index.md, "Arbeitsweise").
"""

#: id -> (ENGINE_NAME, orionlayer_name_or_None)
SCREENS = {
    -1: ("UNKNOWN",         None),
     0: ("MAIN",            "galaxy_map"),       # SCREEN_MAIN
     1: ("COLONY",          "colony"),
     3: ("DESIGN",          "ship_design"),
     4: ("FLEET",           "fleets"),
     6: ("RACE",            "races"),   # work order 175 C
     7: ("EXIT",            None),
     8: ("GAME",            "game_menu"),  # the overlay, decision 59
     9: ("INFO",            "info"),
    10: ("MAIN_MENU",       "main_menu"),
    12: ("NEXT_TURN",       None),
    13: ("NEW_GAME",        "new_game"),
    14: ("HALL_OF_FAME",    "hall_of_fame"),   # work order 188 (open fix 50)
    #: 15-17, 21, 22, 37, 41: the multiplayer screens (orion2_consts.h:
    #: 475-495), one HD screen since work order 188 — the setup read off
    #: its own list, every other step only with open fix 51's MPLY.
    15: ("MULTI_PLAYER",    "multiplayer"),
    16: ("HOTSEAT",         "multiplayer"),
    17: ("HOTSEAT_SELECT_PLAYER", "multiplayer"),
    #: 18, 39, 40: no HD screen folder (work order 315 C2, audit S4).
    #: The status bar still reads "planet_data" / "reports" /
    #: "turn_summary", from the engine name. 39 is the report phase's id
    #: for one tick (`Reports_Screen_`, mainscr2.cpp:104); 40's Turn Summary is
    #: drawn by the App over the held frame (`core/turnpopup.py`), not by
    #: a screen.
    18: ("PLANET_DATA",     None),
    21: ("START_NET",       "multiplayer"),
    22: ("JOIN_NET",        "multiplayer"),
    37: ("NET_NEXT_TURN",   "multiplayer"),
    41: ("LOAD_NET",        "multiplayer"),
    20: ("COLONY_SUMMARY",  "colony_summary"),
    25: ("QUEUE_POPUP",     "build_queue"),   # work order 180 C
    #: 28: F9's distance between stars, a loop over the map
    #: (mainscr2.cpp:193-262) — the galaxy map in that mode since work
    #: order 231 D (`screens/galaxy_map/distance.py`).
    28: ("DISTANCE_BETWEEN_STARS", "galaxy_map"),
    29: ("OFFICERS",        "leaders"),
    30: ("COLONIZATION_IN_MAIN", None),
    32: ("PLANET_SUMMARY",  "planets"),
    #: 35 and 43, the galaxy map's Freighters and Command windows
    #: (mainscr_main.cpp:714-732, work order 310): no HD view, so the F12
    #: notice names them (decision 22); before 310 they had no entry and the
    #: notice said "#35" / "#43".
    35: ("SCRAP_FREIGHTERS", None),
    #: 36 is the engine's own SCREEN_TECH_CHANGE, and the slug named
    #: a folder that never existed: HD had select mode only, so
    #: "research" resolved to nothing and 36 fell through to the
    #: framebuffer. `screens/research_change/` is it, built by work
    #: order 165 part B.
    36: ("TECH_CHANGE",     "research_change"),
    39: ("REPORTS",         None),
    40: ("TURN_SUMMARY",    None),
    43: ("SHOW_COMMAND_POINTS", None),
    #: orion2re v2 added the credits (orion2_consts.h SCREEN_CREDITS);
    #: `screens/credits/` draws it since work order 316 E.
    44: ("CREDITS",         "credits"),
    #: 50 has no entry in the SCREEN enum — synthetic value used
    #: only by the ext-API patch in Racial_Option_Screen_ (racesel.cpp)
    #: while Custom Race's own input loop runs. See
    #: dev:doc/ext_api_dokumentation_v3.md, "racesel.cpp — 3 insertions".
    50: ("(synthetic)",     "custom_race"),
    #: 51, synthetic too: race SELECTION, reported by the same patch
    #: (`Race_Selection_Screen_`) since work order 128 / open fix 22.
    #: It borrowed SCREEN_RACE (6) until then, which is the Races screen
    #: the galaxy map's RACES button opens — so HD drew Select Race over
    #: diplomacy (seen live, 17 September 2026).
    51: ("(synthetic)",     "select_race"),
    #: 52 and 53, synthetic and ON THE WIRE ONLY (work order 129 B, open
    #: fix 24): the science room that presents a completed project and the
    #: SELECT NEW RESEARCH list that follows it, both of which run under
    #: SCREEN_MAIN and would otherwise be indistinguishable from the galaxy
    #: map.
    #: 52 has no HD screen and falls back to the original picture
    #: (decision 22) — which since work order 130 A is a picture that
    #: also forwards clicks, so the presentation dialog can be answered
    #: inside OrionLayer's window.
    #: 53 is `screens/research_select/` since work order 130 E, and it
    #: hands BACK to that same fallback whenever it cannot vouch for the
    #: list it would draw (`ScreenBase.wants_original`).
    52: ("(synthetic)",     None),
    53: ("(synthetic)",     "research_select"),
    #: 54, 55, 56, synthetic, ON THE WIRE ONLY WITH OPEN FIX 45 (work
    #: order 185, NOT APPLIED): the Ship Designer's shield / computer,
    #: weapon and special-system pickers, which run under SCREEN_DESIGN.
    #: One HD screen answers all three (`EXTRA_SCREEN_IDS`).
    54: ("(synthetic)",     "design_box"),
    55: ("(synthetic)",     "design_box"),
    56: ("(synthetic)",     "design_box"),
    #: 57 and 58, synthetic, ON THE WIRE ONLY WITH OPEN FIX 46 (work order
    #: 185, NOT APPLIED): the diplomacy audience the player opened (57) and
    #: the one an AI asked for (58), which run under their caller's id.
    57: ("(synthetic)",     "audience"),
    58: ("(synthetic)",     "audience"),
    #: 59-64, synthetic, ON THE WIRE ONLY WITH OPEN FIX 49 (work order 188):
    #: the report phase's popups, which run under SCREEN_MAIN (and the
    #: combat target choice under 12). No HD SCREEN claims them: the App
    #: draws them over the held frame (`core/turnpopup.py`, through
    #: `core.handover.overlay_for`), as it draws 40, 52 and 33's content.
    59: ("(synthetic)",     None),    # leader for hire
    60: ("(synthetic)",     None),    # colonisation planet choice
    61: ("(synthetic)",     None),    # new system explored
    62: ("(synthetic)",     None),    # a leader gains a level
    63: ("(synthetic)",     None),    # GNN
    64: ("(synthetic)",     None),    # combat target choice
    #: 65-67, synthetic, ON THE WIRE ONLY WITH OPEN FIX 52 (work order 194):
    #: a tactical battle (which reported 12 — 37 in a network game — for
    #: its whole length: nothing in the combat code writes _current_screen),
    #: its scan view and its board popup. The battle is HD's since work
    #: order 197 C, while CMBT is on the wire; the scan view and the board
    #: popup since work order 199 C1, while open fix 66's CPOP is on the
    #: wire as well (without it the F12 notice, as before).
    65: ("(synthetic)",     "combat"),  # a tactical battle (HD: work order 197 C)
    66: ("(synthetic)",     "combat"),  # the battle's scan view (HD: 199 C1)
    67: ("(synthetic)",     "combat"),  # the battle's board popup (HD: 199 C1)
    #: 68 and 69, synthetic, ON THE WIRE ONLY WITH OPEN FIX 91 (work order
    #: 232 C): the colony combat popup — the invasion choice and the
    #: bombing — which the App draws over the held map like 59-64
    #: (`screens/galaxy_map/invasionpopup.py`, through
    #: `core.handover.overlay_for`), and the ground combat, an HD screen.
    68: ("(synthetic)",     None),            # the colony combat popup
    69: ("(synthetic)",     "ground_combat"),  # the ground combat
    #: 70, synthetic, ON THE WIRE ONLY WITH OPEN FIX 96 (work order 270):
    #: the galactic council (`council::Main_Council_Screen`), an HD screen
    #: while TPOP kind 12 is on the wire; before it the council ran under
    #: the processing id 12 with the F12 notice.
    70: ("(synthetic)",     "council"),        # the galactic council
    #: 71, synthetic, ON THE WIRE ONLY WITH OPEN FIX 98 (work order 274):
    #: the colony screen's troop popup (`NEWPUP::Troop_Popup`), which the
    #: App draws over the held colony screen like 59-64.
    71: ("(synthetic)",     None),             # the troop popup
    #: 80 and 82, synthetic, ON THE WIRE ONLY WITH OPEN FIXES 104 AND 105
    #: (work order 316; numbers left free below them for other orders):
    #: the slider popup
    #: (`MAINPUPS::Slider_Popup_`) and the Antaran room
    #: (`ANTAROOM::Main_Antaran_Room_Screen_`), which the App draws over the
    #: held frame like 59-64.
    80: ("(synthetic)",     None),             # the slider popup
    82: ("(synthetic)",     None),             # the Antaran room
}

#: The last value of orion2re's own SCREEN enum:
#: SCREEN_CREDITS = 44 in orion2re v2 (43, SCREEN_SHOW_COMMAND_POINTS, in
#: 1.60, orion2_consts.h:496). A synthetic id
#: must lie above it, or it means a real screen too. Copied by hand, so
#: `tools/version_check.py` reads the enum and fails on a mismatch
#: (decision 36), and the smoke test holds every synthetic entry above it.
ENGINE_SCREEN_MAX = 44


def engine_name(screen_id):
    """orion2re SCREEN enum name, e.g. 'MAIN', 'RACE'."""
    entry = SCREENS.get(screen_id)
    return entry[0] if entry else f"#{screen_id}"


def orionlayer_name(screen_id):
    """OrionLayer screen/folder name, or None if not built in HD
    (falls back to the original framebuffer)."""
    entry = SCREENS.get(screen_id)
    return entry[1] if entry else None
