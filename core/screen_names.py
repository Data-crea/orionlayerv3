"""orion2re screen-ID name tables — the one place they live.

Display-only. Routing never uses this module: screens self-describe
via GAME_SCREEN_ID (see core/dispatcher.py), so nothing here can
break auto-switching if a name is wrong or missing.

Before this module existed, the same id -> name mapping was copied
independently into core/dispatcher.py (status bar), tools/ext_diag.py
(SCREEN_NAMES) and doc/v3_orion2re_index.md (Screen-Enum table) — and
they had already drifted: dispatcher.py was missing id 7 (EXIT),
ext_diag.py was missing id 50 (the synthetic custom_race screen from
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
this project (see v3_orion2re_index.md, "Arbeitsweise").
"""

#: id -> (ENGINE_NAME, orionlayer_name_or_None)
SCREENS = {
    -1: ("UNKNOWN",         None),
     0: ("MAIN",            "galaxy_map"),       # SCREEN_MAIN
     1: ("COLONY",          "colony"),
     3: ("DESIGN",          "ship_design"),
     4: ("FLEET",           "fleet"),
     6: ("RACE",            "select_race"),
     7: ("EXIT",            None),
     8: ("GAME",            None),
     9: ("INFO",            "info"),
    10: ("MAIN_MENU",       "main_menu"),
    12: ("NEXT_TURN",       None),
    13: ("NEW_GAME",        "new_game"),
    14: ("HALL_OF_FAME",    None),
    18: ("PLANET_DATA",     "planet_data"),
    20: ("COLONY_SUMMARY",  "colony_summary"),
    25: ("QUEUE_POPUP",     None),
    29: ("OFFICERS",        "leaders"),
    30: ("COLONIZATION_IN_MAIN", None),
    32: ("PLANET_SUMMARY",  "planets"),
    36: ("TECH_CHANGE",     "research"),
    39: ("REPORTS",         "reports"),
    40: ("TURN_SUMMARY",    "turn_summary"),
    #: 50 has no entry in the SCREEN enum — synthetic value used
    #: only by the ext-API patch in Racial_Option_Screen_ (racesel.cpp)
    #: while Custom Race's own input loop runs. See
    #: ext_api_dokumentation_v3.md, "racesel.cpp — 3 insertions".
    50: ("(synthetic)",     "custom_race"),
}


def engine_name(screen_id):
    """orion2re SCREEN enum name, e.g. 'MAIN', 'RACE'."""
    entry = SCREENS.get(screen_id)
    return entry[0] if entry else f"#{screen_id}"


def orionlayer_name(screen_id):
    """OrionLayer screen/folder name, or None if not built in HD
    (falls back to the original framebuffer)."""
    entry = SCREENS.get(screen_id)
    return entry[1] if entry else None
