"""The race report's native geometry — racerprt.cpp:9-155 (work order 223).

Every rectangle is the original's 640 x 480 one; the drawing maps it
through `core/researchnative` as the Races and Info screens do.
"""
#: The report has no id of its own: the game shows it under Races' 6
#: (racescrn.cpp, `Race_Report_Screen_` is called from the Races loop).
SHARED_SCREEN_ID = 6
TYPE_BUTTON, TYPE_MULTI = 0, 3
ESC = 0x1B

#: RETURN: `Add_Button_Field_(0x216, 0x1B1, …, RACERPRT.LBX 1, "\x1B")`
#: (:86) — the field the live list carries (work order 223, g207_base).
EXIT = (534, 433, 639, 479)
#: The Tech Review subscreen's four tabs, Info's own (`_tech_rev_field`,
#: `infogeom.TECH_TAB_AT`): the report's list carries them at y 427.
TAB_Y = 427

#: The left column (racerprt.cpp:104-133).
PORTRAIT = (0x46, 0x1C)                    # RACES.LBX 0x20 + race, 76 x 88
PORTRAIT_SIZE = (76, 88)
NAME = (0x2A, 0x87, 0x80, 0x1A)            # Squeeze_Paragraph_Centered_
TEXT = (0x18, 0xA7, 0xA4, 0x2A)            # personality \r objective
SPY_GROUP = (24, 216, 187, 239)            # `_spy_group_data`
SPY_LINE = (0x18, 0xDE, 0xA4)              # Squeeze_Centered_Print_
TREATIES = (0x18, 0x123, 0xA4, 0xAA)       # Squeeze_Formatted_Paragraph_Centered_
#: The boxes RACERPRT.LBX 0 paints under them, measured on the native
#: picture of a live report (between the bright rims; work order 223):
#: name, personality, spies, an empty one, treaties.
FIELDS = ((19, 133, 192, 161), (19, 166, 192, 209), (19, 214, 192, 241),
          (19, 245, 192, 285), (19, 289, 192, 462))
#: The panel the left column stands in — Info's, the same art's place.
LEFT_PANEL = (8, 8, 205, 471)
CONTENT = (212, 23, 620, 457)

#: BILLTEXT lines (racerprt.cpp:68-80, :115-128) and the label tables
#: (ESTRINGS 0x268-0x26E, 0x26F-0x274; estrings.cpp:76-89).
B_NO_SPIES, B_NO_ALLIES, B_NO_WARS, B_ALLIES, B_WARS = 0x1C, 0x1D, 0x1E, 0x1F, 0x20
B_SPIES, B_ONE_SPY = 0x4A, 0x4B
E_PERSONALITY, E_OBJECTIVE = 0x268, 0x26F
OBJECTIVE_HUMAN = 100                      # PLAYER_OBJECTIVE_HUMAN
TREATY_ALLIANCE, TREATY_WAR = 2, 4
#: The report's help: one entry over the whole screen (billhelp.cpp:85-87).
HELP_ID = 263


def is_report(fields):
    """True when the live list is the report's: its RETURN and the Tech
    Review's four tabs. Neither Races shape has either."""
    live = [f for f in fields or () if f.index != 0]
    exit_ok = any((f.x, f.y, f.x_end, f.y_end) == EXIT and
                  f.field_type == TYPE_BUTTON and f.hotkey == ESC
                  for f in live)
    tabs = [f for f in live if f.field_type == TYPE_MULTI and f.y == TAB_Y]
    return exit_ok and len(tabs) == 4
