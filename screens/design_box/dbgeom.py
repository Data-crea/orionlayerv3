"""The Ship Designer's three pickers' native geometry — transcribed.

Every anchor is the original's own offset from the box's base
(`DESBOX::_replacement_box_base_x/_y`), and the base is READ OFF THE WIRE:
each picker adds a catch-all field whose origin is that base (desbox.cpp
`Add_Generic_Replacement_Fields_` :810-864, `Add_Replacement_Weapon_Fields_`
:284-540, `Add_Special_System_Fields_` :2662-2763), so the page is laid where the game laid it, not
where HD guesses. The weapon picker's table and lower box hang off its
first row field and its arc / rack box field, for the same reason: their
y depends on the height of DESIGN.LBX's box sprites, which is the
original's measurement and not ours to repeat (dev:CLAUDE.md: an asset is not
a measurement).
"""
GAME_SCREEN_ID = 55                      # the weapon picker, open fix 45
EXTRA_SCREEN_IDS = (54, 56)              # shield / computer, special

TYPE_BUTTON, TYPE_HIDDEN = 0, 7
ESC = 27
FULL_SCREEN = (0, 0, 0x27F, 0x1DF)

#: Shield / computer (`Print_Shield_Data_`, desbox.cpp:2333-2426, and
#: `Print_Computer_Data_`, :2428-2534): the text origin is base + 0x14,
#: the headers at base y + 0x37, the rows 0x12 below in steps of 14.
GENERIC_X, GENERIC_HEAD_Y, GENERIC_ROW_DY, GENERIC_STEP = 0x14, 0x37, 0x12, 14
#: Column offsets from the text origin: shields name, cost, space;
#: computers name, bonus, cost (the name printed 3 to the right).
SHIELD_COLS = ((0x33, 0), (0x34, 0xDC), (0x35, 0x15E))
COMPUTER_COLS = ((0x29, 3), (0x2A, 0xE1), (0x2B, 0x195))
NO_SHIELD, NO_COMPUTER = 0x36, 0x2D
#: `_design_screen_replacement_type` of a shield: TECH_APPLICATION_TYPE_
#: SHIELD (orion2_consts.h:633; the computer's is 8, :639, which the
#: recorded computer picker carries) — the test fix 45's writer makes.
REPLACEMENT_SHIELD = 2

#: The weapon table (`Print_Main_Weapon_Box_`, desbox.cpp:2184-2331),
#: from x = base + 0x16 and the table's top T = first row field's y - 0x13
#: (`Add_Replacement_Weapon_Fields_`: field_y = T + 0x13): headers at T + 3.
WEAPON_X, WEAPON_ROW_DY, WEAPON_HEAD_DY, WEAPON_STEP = 0x16, 0x13, 3, 14
#: (HESTR id, x offset, alignment) — "Dam" is printed right-aligned.
WEAPON_HEADS = ((0x2E, 0x1C, "left"), (0x2F, 0xC6, "right"),
                (0x2B, 0xD3, "left"), (0x30, 0xFD, "left"),
                (0x31, 0x183, "left"))
#: Row columns: name, damage (right), cost (right), space (right), note.
WEAPON_COLS = {"name": 0x0C, "damage": 0xC6, "cost": 0xE9, "space": 0x11F,
               "note": 0x131}
NO_WEAPON = 0x32
#: The lower box, from B = the arc / rack box field's y - 0x46
#: (`Add_Replacement_Weapon_Fields_`: rack_box_y = B + 0x46): the arc
#: picture at base + (33, B + 73), the arc words at (base + 119, B + 84)
#: in steps of 16, the rack words at (base + 127, B + 88) in steps of 15
#: (`Draw_Weapons_Arc_Box_` / `Draw_Weapons_Rack_Box_`).
ARC_BOX_DY = 0x46
ARC_PICT = (33, 73)
ARC_TEXT, ARC_STEP = (119, 84), 16
RACK_TEXT, RACK_STEP = (127, 88), 15
#: The modification box: where `Draw_Weapons_Mod_Box_` draws its blank
#: sprite (base + 0xE0, B + 0x46), 297 x 102 — the extent the original
#: paints there, which the HD panel takes (DEVIATION `hud_frameless`).
MOD_BOX = (0xE0, 0x46, 0xE0 + 297, 0x46 + 102)
#: The four filters at (base + x, B + 10), in the order of DSBX's filters.
FILTER_XS = (0x66, 0xCC, 0x146, 0x1AD)
#: `WEAPON_FIRING_ARC_*` (orion2_consts.h:1079-1085) in the order of the
#: arc words; `Draw_Weapons_Arc_Box_` lights the first bit found in this
#: order after Forward, and Forward when none is.
ARC_BITS = (0x01, 0x02, 0x04, 0x08, 0x10)

#: The special-system picker (`Print_Special_System_Data_`,
#: desbox.cpp:2765-2925): headers at base y + 0x46, rows from base y +
#: 0x59 in steps of 16 (the row fields', `+89+16i`).
SPECIAL_HEAD_DY, SPECIAL_ROW_DY, SPECIAL_STEP = 0x46, 0x59, 16
SPECIAL_HEADS = ((0x37, 0x44), (0x30, 0xBE), (0x2B, 0x106), (0x38, 0x156))
#: Row columns: name, space (right), cost (right), description.
SPECIAL_COLS = {"name": 0x20, "space": 0xE3, "cost": 0x124,
                "description": 0x13E}
NO_SPECIAL = 0x39

#: The title band HD puts at the box's top (HD EXTENSION `box_titles`):
#: the height of the band the original's box art paints its headline in.
TITLE_BAND_H = 0x20
