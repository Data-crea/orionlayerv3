"""Refit's native geometry — colrefit.cpp (work order 223).

Two popups under the build popup's id 25: the ship list
(`Colony_Refit_Popup_`) and the design list (`Colony_Refit2_Popup_`).
Every rectangle is the original's 640 x 480 one.
"""
SHARED_SCREEN_ID = 25
TYPE_BUTTON, TYPE_SCROLL, TYPE_HIDDEN = 0, 6, 7

#: REFITPUP.LBX 0 / 4, 348 x 470, drawn at (0x93, 6) (:279, :306).
POPUP = (0x93, 6, 0x93 + 348 - 1, 6 + 470 - 1)
#: The parts of the ship list, `_refit_ship_popup_help_list`
#: (erichelp.cpp:118-126): the grid, the info box, up, the track, down,
#: Cancel — the same rectangles the fields and the art carry.
GRID = (159, 47, 460, 230)
INFO_BOX = (159, 239, 459, 424)
UP = (468, 46, 478, 65)                   # `_fields[2]` (0x1D4, 0x2E), '-'
TRACK = (468, 69, 479, 405)               # `_fields[4]`, the scroll field
DOWN = (469, 407, 477, 425)               # `_fields[1]` (0x1D5, 0x197), '+'
CANCEL = (274, 440, 361, 460)             # `_fields[3]` (0x112, 0x1B8)
#: The title band the art carries its headline in (measured, the native
#: picture of a live list).
TITLE = (162, 19, 456, 31)
#: A ship's cell: 15, five by three, 55 x 56 (:393-411).
CELLS, COLUMNS = 15, 5


def cell(i):
    x, y = 161 + 60 * (i % COLUMNS), 49 + 61 * (i // COLUMNS)
    return (x, y, x + 55, y + 56)


#: The paragraphs' boxes (`Squeeze_Print_Formatted_Paragraph_`): a ship's
#: (168, 248, 283, 169) (:471), a design's (168, 248, 305, 169) (:345).
SHIP_TEXT = (168, 248, 283, 169)
DESIGN_TEXT = (168, 248, 305, 169)


def design_row(k):
    """Design row k (0-4) and k = 6 the last row: `179 (k + 1) / 8 + 49`
    to `179 (k + 2) / 8 + 48` (:612-628)."""
    return (0xA1, 179 * (k + 1) // 8 + 49, 0x1DE, 179 * (k + 2) // 8 + 48)


DESIGN_NAME_X, DESIGN_COLON_X, DESIGN_HULL_RIGHT = 183, 320, 457
DESIGN_TITLE_Y = 20
GOTO_ROW = 6
#: The design list's own box, the art's (REFITPUP.LBX 4): rows and the
#: paragraph; measured on the native picture of a live list.
DESIGN_BOX = (161, 49, 478, 229)

#: E_Strings (estrings): the cells' refusal words (:440-462), the design
#: list's last row and title (:524-532), the paragraph's lines
#: (colbldg.cpp:1217-1336).
E_NO_BASE, E_CAPTURED, E_LOKNAR = 0x18B, 0xD8, 0x16A
E_GOTO_DESIGN, E_PICK_DESIGN = 800, 801
E_NAME, E_NAME_OFFICER = 79, 78
E_COST, E_SHIELD, E_COMPUTER, E_ARMOR, E_FTL = 99, 119, 98, 91, 104
E_WEAPONS, E_SPECIALS = 130, 129
E_GOTO_TEXT = 0x322
LOKNAR_PICTURE = 44
#: H_Message: the crew's words by `crew_quality` (flt2.cpp:749-772).
H_CREW = 0x8A
#: A design or ship size from which a star base is needed
#: (`SHIP_SIZE_LARGE`, the build popup's rule, `bqdraw.design_needs_base`).
SHIP_SIZE_LARGE = 2


def kind(fields):
    """"ships", "designs" or None: which of the two lists is live. The
    ship list has its arrows; the design list its rows from x 161 to
    0x1DE and no arrows. Both have Cancel."""
    live = [f for f in fields or () if f.index != 0]

    def has(rect, ftype):
        return any((f.x, f.y, f.x_end, f.y_end) == rect and
                   f.field_type == ftype for f in live)
    if not has(CANCEL, TYPE_BUTTON):
        return None
    if has(UP, TYPE_BUTTON) and has(DOWN, TYPE_BUTTON):
        return "ships"
    rows = [f for f in live if f.field_type == TYPE_HIDDEN and
            (f.x, f.x_end) == (161, 478)]
    return "designs" if rows else None
