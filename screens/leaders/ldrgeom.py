"""The Leaders screen's own 640x480 geometry — every rectangle, sourced.

**TRANSCRIBED, NOT DESIGNED.** Every number below is a literal in
`src/game/officer.cpp` (or the file named beside it) at orion2re
`e6199966`. The HD screen draws each thing at the HD image of its
native rectangle through `core/researchnative.to_hd` — the one
conversion that also places the fallback view's picture — so an HD
screenshot lines up with a native one of the same save pixel for pixel
at the proportion, and nothing here is measured off an asset.

**THE ONE PLACE A SIZE COMES FROM THE ART, AND WHY THAT IS THE SOURCE.**
The buttons are `Add_Button_Field_` / `Add_Hidden_Field_(x, y,
x + Get_Width_(art), y + Get_Height_(art), …)` (officer.cpp:2831-2908):
the ORIGINAL takes the field's size from the art (fields.cpp:366-367).
So `BUTTON_SIZE` is the art's header size — the number the original
itself reads — and not a measurement of an HD picture. The live field
list carries the same rectangles on every snapshot; `ldrwire` compares
the two and refuses a list that disagrees.

`from core import researchnative` is where the conversion lives; this
module keeps the NUMBERS only, so the drawing and the hit test read one
table (decision 5).
"""

NATIVE_W, NATIVE_H = 640, 480

#: `SCREEN_OFFICERS` (orion2_consts.h:484).
GAME_SCREEN_ID = 29

#: The two views, `_officer_scrn_type` (`LEADER_TYPE_*`).
VIEW_SHIP, VIEW_COLONY = 0, 1

# ── The four leader rows ─────────────────────────────────

#: Rows step 0x6D (officer.cpp:1923, :1977, :2935) from y 0x22 (:2912).
ROWS = 4
ROW_PITCH = 0x6D                  # 109
ROW_TOP = 0x22                    # 34

#: `help_field_1`: the text block (officer.cpp:2915-2922), and
#: `help_field_2`: the portrait (:2923-2930). Inclusive rects.
TEXT_FIELD = (0x5C, 0, 0x128, 0x6C)       # (92, y, 296, y + 108)
PORTRAIT_FIELD = (0x08, 0, 0x5B, 0x60)    # (8, y, 91, y + 96)

#: `Print_Officer_Data_`'s arguments from `Wrapper_For_Offscrn_Data_`
#: (officer.cpp:1975-1991), per row `i`: text at (0x5C, 0x26 + 109 i),
#: the portrait box at (8, 0x22 + 109 i), 0x53 wide, its status line
#: 0x60 below, and the right column 0xCC right of the text.
TEXT_X = 0x5C                      # 92
TEXT_DY = 0x26 - ROW_TOP           # 4: text_y = row top + 4
PORTRAIT_X = 0x08
PORTRAIT_W = 0x53                  # 83
STATUS_DY = 0x60                   # 96
RIGHT_COLUMN = 0xCC                # 204

#: The name is centred in 0xA0 px starting 0x16 right of text_x
#: (officer.cpp:3630-3631).
NAME_DX, NAME_W = 0x16, 0xA0
#: The two cost lines end 2 px left of the right column
#: (officer.cpp:3647-3671), the skill values 3 px (:3794).
COST_RIGHT_INSET = 2
VALUE_RIGHT_INSET = 3
#: The skill lines start 0x10 below the name (:3751) and step 0x11
#: (:3799); the icon sits 2 px right of text_x and 4 px up (:3758,
#: :3575), the name 0x16 right of the icon's x (:3778).
SKILL_DY, SKILL_STEP = 0x10, 0x11
SKILL_ICON_DX, SKILL_ICON_DY = 2, -4
SKILL_NAME_DX = 2 + 0x16
#: `Set_Fitted_Font_Style_(status, …, 4, 0x4A, 1)` (:3719-3726): the
#: status line is fitted to 74 px.
STATUS_FIT_W = 0x4A
#: The portrait is centred in a 75 x 90 cell at (12, 37 + 109 i)
#: (`Draw_Officer_Screen_To_Back_`, officer.cpp:640-641).
PORTRAIT_CELL = (12, 37, 75, 90)
#: The skill help fields: `Add_Skill_Description_Help_Fields_(0x5E,
#: 0x32 + 109 i, …)` (:1903-1924), stepping 0x11. **The two loops do not
#: make the same rectangle**: a SPECIAL skill's field is `(x, y - 1,
#: x + 0xBE, y + 0xF)` (:3928-3935) and a GENERAL skill's `(x, y, x +
#: 0xBE, y + 0xF)` (:3956-3963) — one pixel lower at the top. Five slots
#: are kept (:3970-3974) and no leader shows more: the maximum over
#: HERODATA.LBX and every save on this disk is five (work order 167).
SKILL_HELP_X, SKILL_HELP_TOP, SKILL_HELP_W = 0x5E, 0x32, 0xBE
SKILL_HELP_MAX = 5


def row_top(i):
    return ROW_TOP + i * ROW_PITCH


def text_field(i):
    x1, _y1, x2, dy2 = TEXT_FIELD
    y = row_top(i)
    return (x1, y, x2, y + dy2)


def portrait_field(i):
    x1, _y1, x2, dy2 = PORTRAIT_FIELD
    y = row_top(i)
    return (x1, y, x2, y + dy2)


def portrait_cell(i):
    x, y, w, h = PORTRAIT_CELL
    y += i * ROW_PITCH
    return (x, y, x + w - 1, y + h - 1)


def portrait_origin(i, width, height):
    """Where a portrait of this size is drawn (officer.cpp:640-641):
    `(75 - w) / 2 + 12`, `37 + 109 i + (90 - h) / 2`. C division of a
    non-negative difference, so floor — a portrait wider than the cell
    does not exist in OFFICER.LBX (all 67 are 73 x 88)."""
    cx, cy, cw, ch = PORTRAIT_CELL
    return ((cw - width) // 2 + cx, i * ROW_PITCH + cy + (ch - height) // 2)


def text_y(i):
    return row_top(i) + TEXT_DY


def status_y(i):
    return row_top(i) + STATUS_DY + 1


def skill_rows(i, count):
    """The native y of each of `count` skill lines of row `i`."""
    y0 = text_y(i) + SKILL_DY
    return [y0 + k * SKILL_STEP for k in range(count)]


def skill_help_rects(left, top, n_special, n_general):
    """The help fields `Add_Skill_Description_Help_Fields_` adds for a
    leader with these displayed skills, top down (officer.cpp:3893-3975):
    the special ones from `top` with their top edge one pixel up, then
    the general ones from `top + n_special * 0x11`."""
    out = []
    for k in range(n_special):
        y = top + k * SKILL_STEP
        out.append((left, y - 1, left + SKILL_HELP_W, y + 0xF))
    for k in range(n_general):
        y = top + (n_special + k) * SKILL_STEP
        out.append((left, y, left + SKILL_HELP_W, y + 0xF))
    return out


def row_skill_help_rects(i, n_special, n_general):
    """Row `i`'s skill help fields on the screen (officer.cpp:1903-1924)."""
    return skill_help_rects(SKILL_HELP_X, SKILL_HELP_TOP + i * ROW_PITCH,
                            n_special, n_general)


# ── Buttons ──────────────────────────────────────────────

#: `name -> (field origin, hotkey, field type, art)`; `art` is the
#: OFFICER.LBX entry whose size the original gives the field
#: (officer.cpp:2831-2908). Type 0 is `Add_Button_Field_`, 7 is
#: `Add_Hidden_Field_` (the types the wire reports; screens/fleets/
#: fltwire.py measured both).
TYPE_BUTTON, TYPE_HIDDEN = 0, 7
ESC = 0x1B
BUTTONS = {
    "tab_colony": ((0x09, 0x0B), ord("C"), TYPE_HIDDEN, "tab_colony"),
    "tab_ship":   ((0x9C, 0x0B), ord("S"), TYPE_HIDDEN, "tab_ship"),
    "hire":       ((0x139, 0x1B9), ord("H"), TYPE_BUTTON, "hire"),
    "pool":       ((0x184, 0x1B9), ord("P"), TYPE_HIDDEN, "pool"),
    "dismiss":    ((0x1CF, 0x1B9), ord("D"), TYPE_HIDDEN, "dismiss"),
    "cancel":     ((0x1CC, 0x1B7), ord("X"), TYPE_BUTTON, "cancel"),
    "return":     ((0x21A, 0x1B9), ESC, TYPE_BUTTON, "return"),
    "prev":       ((0x147, 0xCD), ord(","), TYPE_BUTTON, "prev"),
    "next":       ((0x238, 0xCD), ord("."), TYPE_BUTTON, "next"),
    "scroll_up":  ((0x265, 0x16), ord("-"), TYPE_BUTTON, "scroll_up"),
    "scroll_down": ((0x265, 0xAA), ord("+"), TYPE_BUTTON, "scroll_down"),
}

#: The art's own size, which IS the field's size in the original (see
#: the module docstring). From OFFICER.LBX's entry headers — the value
#: `animate::Get_Width_` / `Get_Height_` return — and checked against
#: the extracted headers by the smoke test whenever the art is there.
BUTTON_SIZE = {
    "tab_colony": (150, 23), "tab_ship": (140, 23),
    "hire": (74, 27), "pool": (74, 27), "dismiss": (74, 27),
    "cancel": (77, 29), "return": (80, 27),
    "prev": (35, 21), "next": (35, 21),
    "scroll_up": (10, 19), "scroll_down": (11, 21),
}

#: Where the TABS are DRAWN, which is not where their fields are
#: (officer.cpp:836, :839 against :2883-2899): the art is placed a few
#: pixels off its own hit area.
TAB_DRAW = {"tab_colony": (7, 10), "tab_ship": (160, 10)}

#: The dull buttons stand where the live ones would (officer.cpp:781-794).
DULL = {"hire": "hire_dull", "pool": "pool_dull", "dismiss": "dismiss_dull"}

#: Hire mode's panel under the buttons and the cost line in it
#: (officer.cpp:797-807): OFFICER.LBX 17 at (300, 441), text at
#: (315, 450) fitted to 132 px.
HIRE_PANEL_AT = (300, 441)
HIRE_PANEL_SIZE = (237, 30)
HIRE_COST_AT, HIRE_COST_FIT_W = (315, 450), 132


def button_rect(name):
    """The button's field rectangle, inclusive, AS THE WIRE REPORTS IT.

    The two field kinds end differently, and that is the source's and
    not a rounding of ours: `Add_Button_Field_` sets `x_end = x +
    Get_Width_(pic) - 1` (fields.cpp:370-371), while the hidden fields
    here are handed `x + Get_Width_(art)` by officer.cpp itself
    (:2832-2836, :2883-2899) and `Add_Hidden_Field_` stores it as given
    (fields.cpp:310-313). So a hidden button is one pixel wider and
    taller than the same art as a real one.
    """
    (x, y), _hk, ftype, _art = BUTTONS[name]
    w, h = BUTTON_SIZE[name]
    if ftype == TYPE_BUTTON:
        return (x, y, x + w - 1, y + h - 1)
    return (x, y, x + w, y + h)


# ── The right half ───────────────────────────────────────

#: The view's box art, OFFICER.LBX 1 (ship) / 2 (colony) at (300, 12)
#: (officer.cpp:1197-1203); 330 / 329 x 189.
VIEW_BOX = (300, 12, 629, 200)
#: The system display's origin in the colony view (officer.cpp:1935-1945).
SYSTEM_AT = (0x132, 0x11)
#: The big-icon grid in the ship view: 5 x 3 from (0x12E, 0x13),
#: stepping 62 and 60 (officer.cpp:929-933; `Get_Fltscrn_Big_Icon_XY_`,
#: flt2.cpp:116-128); each icon's field is 0x39 square on this screen
#: (flt2.cpp:288-293).
GRID_COLUMNS, GRID_ROWS = 5, 3
GRID_ORIGIN = (0x12E, 0x13)
GRID_STEP = (62, 60)
GRID_CELL = 0x39


def grid_cell(slot):
    """Big icon `slot`'s field rectangle, inclusive."""
    ox, oy = GRID_ORIGIN
    x = ox + (slot % GRID_COLUMNS) * GRID_STEP[0]
    y = oy + (slot // GRID_COLUMNS) * GRID_STEP[1]
    return (x, y, x + GRID_CELL, y + GRID_CELL)


#: The scroll bar's track, `FLT2::Fleet_Screen_Big_Icon_Fields_(…,
#: 0x264, 0x2D, 0xA, 0x79)` (officer.cpp:2959) — x, y, width, length.
SCROLL_TRACK = (0x264, 0x2D, 0x264 + 0xA, 0x2D + 0x79)

#: The strip under the view box: the star (colony view, officer.cpp:
#: 824-825, centred on 466 at y 210, fitted to 203) or the scanned ship
#: (ship view, :725-726, y 211, fitted to 204). Its rectangle is help
#: 318's (evanhelp.cpp:178).
VIEW_STRIP = (364, 203, 566, 226)
VIEW_STRIP_CENTRE_X = 466

#: The galaxy map box: `Draw_Galaxy_Map_Box_(…, 306, 235, 318, 169, …)`
#: (officer.cpp:756) and its fields (:2998-3011).
GALAXY_BOX = (306, 235, 306 + 318 - 1, 235 + 169 - 1)
GALAXY_BOX_XYWH = (306, 235, 318, 169)
#: The strip under the map, `Print_Galmap_Scanned_Ship_` on this screen
#: (officer.cpp:2102-2105): (0x16C, 0x19C), 0xCB wide, two lines.
MAP_STRIP = (0x16C, 0x19C, 0x16C + 0xCB, 0x19C + 22)

#: The catch-all field the screen adds last (officer.cpp:3013-3020).
CATCHER = (0, 0, 0x27F, 0x1DF)
#: `MAINSCR::_debug_field` (officer.cpp:2986-2993).
DEBUG_FIELD = (0, 0x1D6, 0x0A, 0x1DF)

# ── Right-click help (evanhelp.cpp:170-212) ───────────────
#
# The two tables live in `help.json` — ONE home, with each entry's
# native rectangle — and this module only knows the RULE the original
# applies to them on every redraw.

#: Ship view: with no big icon shown one help 333 over the whole grid,
#: else one per EMPTY cell from the first unused one (evanhelp.cpp:499-507).
HELP_EMPTY_GRID = 333
HELP_EMPTY_GRID_ALL = (301, 16, 610, 198)


def help_empty_cells(icons_added):
    """The appended help-333 rectangles (evanhelp.cpp:499-507)."""
    if icons_added == 0:
        return [HELP_EMPTY_GRID_ALL]
    out = []
    for i in range(icons_added, GRID_COLUMNS * GRID_ROWS):
        x1 = (i % 5) * 63 + 301
        y1 = (i // 5) * 62 + 16
        out.append((x1, y1, x1 + 63, y1 + 62))
    return out


def help_list(regions, view, skill_counts):
    """`[(help id, native rect)]` for `view`, in the original's order.

    `regions` is `help.json`'s list; `skill_counts` the number of skill
    lines each of the four rows shows (0 for an empty row) —
    `Get_N_Skills_Per_Officer_Displayed_`. A row's own entry loses
    `n * 17 + 16` from its top (evanhelp.cpp:479-483, :493-497).
    """
    want = "colony" if view == VIEW_COLONY else "ship"
    out = []
    for spec in regions:
        if spec.get("view") != want:
            continue
        x1, y1, x2, y2 = spec["native"]
        row = spec.get("row")
        if row is not None and 0 <= row < ROWS and skill_counts[row] > 0:
            y1 += skill_counts[row] * SKILL_STEP + SKILL_DY
        out.append((int(spec["help_id"]), (x1, y1, x2, y2)))
    return out
