"""The single-colony screen's own 640x480 geometry — every rectangle, sourced.

**TRANSCRIBED, NOT DESIGNED** — the Leaders and Races rule
(`screens/leaders/ldrgeom.py`): each number is a literal of orion2re at
`orionlayer-local` 9ab84230 (the colony sources unchanged since
`b44cbf76`, work order 180 B1), read in `dev:doc/colony_screen_reading.md`
and re-read for this module. The HD screen draws each thing at the HD
image of its native rectangle (`core/researchnative`), so the drawing,
the hit test and a native screenshot speak one coordinate system.

The button rectangles come from the ART (`Add_Button_Field_` reads the
extent from the picture, fields.cpp:366-367) and are not in the source;
they are the live list's, recorded on 27 September 2026
(work order 180's evidence, `B_record`), and `colwire` finds every field in
the list it is sending into, so a different art size moves the button's
field, never HD's idea of it.
"""

NATIVE_W, NATIVE_H = 640, 480

#: `SCREEN_COLONY` (orion2_consts.h:463).
GAME_SCREEN_ID = 1

#: Field types as the wire reports them (fields.cpp:241-245, :634-639).
TYPE_BUTTON, TYPE_SCROLL, TYPE_HIDDEN, TYPE_MULTI_HOT = 0, 6, 7, 8
ESC = 0x1B

# ── The top band (colony.cpp:621-635; help table erichelp.cpp:90-108) ──

#: `Draw_Info_Name_And_Pop_` (colony_main.cpp:806-873).
TITLE_CENTRE = (320, 0)
STATUS_AT = (0, 0)                      # Blockaded / Plague / Pop Boom
POP_RIGHT = (638, 3)                    # `Print_Right_`, E 424

#: `COLSYSDI::Draw_Col_Sys_Disp_(7, 24)` (colony_main.cpp:129;
#: colsysdi.cpp:8-49): five orbit rows 24 px apart, the planet centred at
#: (x+15, y+24i+14), the summary paragraph at (x+28, y+7+24i), 89-x wide.
SYS_DISP = (7, 24, 115, 151)            # help 487
SYS_X, SYS_Y, SYS_ROW = 7, 24, 24
SYS_PLANET_DX, SYS_PLANET_DY = 15, 14
SYS_TEXT_DX, SYS_TEXT_DY = 28, 7
SYS_TEXT_W = 89 - 7

#: The four production rows, BC first: `Draw_Colony_Info_Production_For_`
#: and the fields `[13]`..`[16]` (colony.cpp:743-765; colony_main.cpp:
#: 1002-1005). ECON order in the engine: food 0, industry 1, research 2,
#: BC 3 — the rows are BC, food, industry, research top to bottom.
PROD_ROWS = {3: (128, 32, 301, 61), 0: (128, 62, 301, 91),
             1: (128, 92, 301, 121), 2: (128, 122, 301, 151)}
#: `[12]`: `COLDRAW::Draw_Info_Morale_(colony, 310, 33, 510)`.
MORALE = (310, 32, 510, 61)
#: The job rows, `_job_fields[0..2]` (coldraw.cpp:409): farmers, workers,
#: scientists at y 62 + 30i; icons from x 310 to 510.
JOB_ROWS = [(310, 62, 518, 92), (310, 92, 518, 122), (310, 122, 518, 152)]
JOB_ICON_X = (310, 510)

#: `Draw_Info_Build_` (colony_main.cpp:899-977): the window the picture
#: is clipped to (colony.cpp:779), the name paragraph (:959), the bar
#: (colony.cpp:977), the turn count (:994), the autobuild label (:969).
BUILD_WINDOW = (517, 17, 639, 158)
BUILD_NAME = (522, 38, 522 + 112, 38 + 141)
BUILD_BAR_AT = (606, 43)
#: The box the bar's art covers, measured off the native framebuffer
#: (g207_plague, colony 1, work order 208 B2): x 608..628, y 74..102 — clear
#: of the turns line, which `Print_Right_(624, 103)` puts under it.
BUILD_BAR_BOX = (608, 74, 628, 102)
BUILD_TURNS_RIGHT = (624, 103)
AUTOBUILD_CENTRE = (578, 28)

# ── The buttons, as the live list reports them ────────────────────────

#: (type, x, y) -> the field's identity; the rect is the list's.
CHANGE = (TYPE_BUTTON, 519, 123)        # [4], hotkey C shadowed by [5]
BUY = (None, 590, 123)                  # [3], type 0 buyable, 7 not
LEADERS = (TYPE_BUTTON, 556, 427)       # [17], hotkey L
RETURN = (TYPE_BUTTON, 556, 459)        # [1]

# ── The lower half ────────────────────────────────────────────────────

#: The officer: frame COLPUPS 0x16 at (544,351), portrait (550,357), the
#: name or `ETA:%d t` centred at (586,433) (colony.cpp:706-734).
OFFICER_FRAME = (544, 351, 628, 424)
OFFICER_NAME_CENTRE = (586, 433)
#: The unit strip: bottom-left, y 479 - h (colony_main.cpp:1193-1293).
UNITS = (1, 443, 176, 478)              # help 496
#: The hover strip, `Print_Scanned_String_` centred (319, 467).
HOVER_CENTRE = (319, 467)
#: The landscape: everything under the band.
SCENE = (0, 152, 639, 479)

# ── Right-click help, `_colony_screen_help_list` (erichelp.cpp:90-108) ──

#: (help id, (x1, y1, x2, y2)) in the table's order; the FIRST match
#: wins (fields.cpp:2916), and 483 "general" is last.
HELP = (
    (484, (1, 1, 120, 14)), (485, (122, 1, 506, 15)),
    (486, (508, 1, 638, 15)), (487, (7, 24, 115, 151)),
    (488, (526, 27, 632, 112)), (489, (124, 29, 304, 57)),
    (490, (307, 29, 512, 56)), (492, (125, 59, 305, 88)),
    (493, (125, 88, 305, 118)), (494, (125, 118, 305, 148)),
    (495, (307, 59, 512, 148)), (496, (1, 443, 176, 478)),
    (497, (520, 124, 578, 143)), (498, (591, 124, 625, 143)),
    (499, (552, 425, 638, 448)), (500, (551, 455, 638, 478)),
    (483, (0, 0, 639, 50)),
)


#: `COLONY::_building_cr[170]` (colony.cpp:4-20), copied by script from
#: the source and held to it by check 090p: the corners of the scene's
#: building cells, read by `Bldg_Coords_To_Centered_Screen_Coord_`
#: (colony.cpp:2273-2282) — used only with open fix 36's grid.
BUILDING_CR = (
    316, 492, 225, 461, 153, 428, 96, 401, 50, 379, 10, 361,
    -21, 348, 406, 461, 316, 430, 242, 404, 182, 381, 130, 363,
    88, 346, 53, 333, 480, 430, 391, 403, 317, 381, 255, 362,
    204, 348, 158, 334, 121, 322, 539, 403, 454, 382, 380, 363,
    319, 348, 264, 335, 219, 322, 180, 312, 587, 382, 505, 363,
    434, 348, 372, 334, 318, 323, 271, 312, 232, 303, 629, 364,
    549, 349, 479, 335, 419, 323, 367, 314, 318, 303, 277, 295,
    666, 351, 586, 336, 517, 324, 459, 313, 409, 304, 360, 295,
    320, 288, 316, 430, 242, 404, 182, 381, 130, 363, 88, 346,
    53, 333, 391, 403, 317, 381, 255, 362, 204, 348, 158, 334,
    121, 322, 454, 382, 380, 363, 319, 348, 264, 335, 219, 322,
    180, 312, 505, 363, 434, 348, 372, 334, 318, 323, 271, 312,
    232, 303, 549, 349, 479, 335, 419, 323, 367, 314, 318, 323,
    277, 295, 586, 336, 517, 324, 517, 313, 409, 304, 360, 295,
    320, 288,
)


def building_centre(grid_y, grid_x):
    """`Bldg_Coords_To_Centered_Screen_Coord_` for both axes: the middle of
    entries i and i+16, i = (grid_y * 7 + grid_x) * 2 + axis — C integer
    division, which truncates toward zero."""
    out = []
    for axis in (0, 1):
        i = axis + (grid_y * 7 + grid_x) * 2
        out.append(int((BUILDING_CR[i] + BUILDING_CR[i + 16]) / 2))
    return tuple(out)


def building_field(grid_y, grid_x):
    """The building's own field, `Add_Bldg_Fields_` (colony.cpp:1713-1722)."""
    cx, cy = building_centre(grid_y, grid_x)
    return (cx - 20, cy - 30, cx + 20, cy + 10)


def sys_row(i):
    """Orbit row i: (planet centre, text origin) in native pixels."""
    y = SYS_Y + i * SYS_ROW
    return ((SYS_X + SYS_PLANET_DX, y + SYS_PLANET_DY),
            (SYS_X + SYS_TEXT_DX, y + SYS_TEXT_DY))
