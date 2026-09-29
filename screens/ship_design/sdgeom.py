"""The Ship Designer's native geometry — transcribed, 640x480.

Every rectangle and anchor the page draws or clicks, from the original's
own calls (`DESIGN::Print_Current_Design_`, `Add_Design_Buttons_`,
design_main.cpp) and checked against the field list recorded live on a
scratch engine (work order 185, `dev:doc/ship_designer_reading.md` section
10). The drawing, the hit test and a native screenshot therefore speak the
same coordinates (decision 5), mapped to the window by `ldrdraw` as the
colony and Leaders screens map theirs.
"""
GAME_SCREEN_ID = 3                       # SCREEN_DESIGN (orion2_consts.h)
#: The pickers' synthetic ids — open fix 45 (ext_api.h).
PICKER_IDS = {54: "generic", 55: "weapon", 56: "special"}

TYPE_BUTTON, TYPE_MULTI, TYPE_HIDDEN, TYPE_STRING = 0, 3, 7, 11

#: The three bottom buttons (design_main.cpp `Add_Design_Buttons_`): the
#: origin is the source's, the size the art's — found in the live list by
#: type and origin, never by index (decision 20).
CANCEL = (TYPE_BUTTON, 0x1CD, 0x1BB)     # hotkey ESC
CLEAR = (TYPE_BUTTON, 0x176, 0x1BB)      # hotkey L
BUILD = (TYPE_BUTTON, 0x223, 0x1BB)      # hotkey B; absent when over space
#: The icon arrows beside the ship picture.
PICTURE_LEFT = (TYPE_BUTTON, 0x11, 0x52)
PICTURE_RIGHT = (TYPE_BUTTON, 0x5E, 0x52)
#: The name field (a continuous string input, 15 characters).
NAME = (TYPE_STRING, 0x12, 0x17)
#: Its rectangle, as the list gives it (x_end 0x98 = 0x12 + 0x86 width,
#: y_end 0x28 = y + the font height + 2, design_main.cpp:686-690; the
#: recorded list agrees: (18, 23)-(152, 40)). HD's text field covers it.
NAME_RECT = (0x12, 0x17, 0x98, 0x28)
#: The shield and computer panels (hidden fields, `Add_Design_Buttons_`).
SHIELD = (TYPE_HIDDEN, 0x1B5, 0x38)
COMPUTER = (TYPE_HIDDEN, 0x1B5, 0x61)
#: The six hull buttons, Frigate .. Doom Star: x 118..227 and the rows
#: design.cpp's `Add_Size_Button_` gives (the recorded list agrees).
HULL_ROWS = ((54, 69), (70, 84), (85, 102), (103, 117), (118, 132),
             (133, 149))
HULL_X = (118, 227)

#: The weapon table: eight rows from y 0xA9 in steps of 13 (the fields) and
#: printed from y 0xAA; the window it is clipped to.
WEAPON_ROW_Y0, ROW_STEP = 0xA9, 13
WEAPON_HEAD_Y = 0x9C
WEAPON_TEXT_Y0 = 0xAA
#: x of each column: count (right), name, damage (centre), arc (centre),
#: cost (centre), space (centre), modifications (centre); the headers'.
WEAPON_COLS = {"count": 0x31, "name": 0x55, "damage": 0x10B, "arc": 0x149,
               "cost": 0x179, "space": 0x1B4, "mods": 0x211}
WEAPON_HEADS = ((0x5E, 0x53), (0x5F, 0xF9), (0x60, 0x13C), (0x185, 0x167),
                (0x30, 0x19E), (0x61, 0x1DF))
#: minus / plus per row: origins 0x37 and 0x13.
MINUS_X, PLUS_X = 0x37, 0x13
#: The specials table.
SPECIAL_HEAD_Y = 0x132
SPECIAL_HEADS = ((0x62, 0x1E), (0x38, 0x118))
SPECIAL_ROW_Y0 = 0x13F
SPECIAL_TEXT_Y0 = 0x140
SPECIAL_COLS = {"name": 0x23, "description": 0x10E}

#: The drive / armour and shield / computer blocks' anchors.
DRIVE_NAME = (0xEC, 0x38)
DRIVE_LINES = ((0xFB, 0x47), (0xFB, 0x56))
ARMOR_NAME = (0xEC, 0x6B)
ARMOR_LINES = ((0xFB, 0x7A), (0xFB, 0x89))
SHIELD_NAME = (0x1B5, 0x38)
SHIELD_LINES = ((0x1C5, 0x47), (0x1C5, 0x55))
COMPUTER_NAME = (0x1B5, 0x61)
COMPUTER_LINE = (0x1C5, 0x70)
BEAM_DEFENSE = (0x1B5, 0x7D)
MISSILE_EVASION = (0x1B5, 0x89)
VALUE_RIGHT = 0x26A
#: The ship picture's box (centred in it) and the hull space line.
PICTURE_BOX = (0x27, 0x3A, 0x27 + 0x36, 0x3A + 0x3A)
SPACE_LABEL = (0x19, 0x81)
SPACE_RIGHT = 0x6A
#: The bottom line: Cost and Space Available, style 4 (the y is
#: `(0x18 - font height) / 2 + 0x1BC`; HD centres on that band).
BOTTOM_BAND = (0x1BC, 0x1BC + 0x18)
COST_LABEL_X, COST_RIGHT = 0x18, 0x87
AVAIL_LABEL_X, AVAIL_RIGHT = 0xA3, 0x160

#: Panels HD draws behind the page's groups (the original's background art
#: frames these areas; DEVIATION `hud_frameless`): the name + picture box,
#: the hull column, drive / armour, shield / computer, the two tables, the
#: bottom line.
PANELS = ((0x0E, 0x14, 0x9A, 0x2A), (0x0E, 0x2E, 0x72, 0x96),
          (0x74, 0x2E, 0xE6, 0x96), (0xE8, 0x2E, 0x1B0, 0x96),
          (0x1B2, 0x2E, 0x274, 0x96), (0x0E, 0x99, 0x274, 0x11E),
          (0x0E, 0x12F, 0x274, 0x1B2), (0x0E, 0x1B8, 0x164, 0x1D8))
