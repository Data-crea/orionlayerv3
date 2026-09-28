"""The audience's native geometry — transcribed, 640x480.

From the reading (`doc/audience_reading.md` §1.2-1.3): the statement is
printed at x 80, 470 wide, centred on y 440 (`Print_Formatted_Paragraph_
(0x50, 0x1B8 - height/2, 0x1D6, …)`, dip_scrn_main.cpp:1583-1586); every
menu is `Get_List_Field_` at (10, 118), 245 wide — its fields give each
row (fields.cpp:769-822). Both pictures are drawn at (0, 0), the room
640x480, the ambassador 480x480 (file_ani.cpp's `Draw_(0, 0, …)`).
"""
#: The synthetic ids open fix 46 reports: the player's, the AI's.
GAME_SCREEN_ID = 57
EXTRA_SCREEN_IDS = (58,)

TYPE_LIST = 10
FULL_SCREEN = (0, 0, 0x27F, 0x1DF)

STAGE = (0, 0, 639, 479)
STATEMENT_X, STATEMENT_W, STATEMENT_CY = 0x50, 0x1D6, 0x1B8
#: The panel HD puts behind the statement (DEVIATION `hud_frameless`): the
#: paragraph's column, 8 px of margin, from y 400 to the screen's foot.
STATEMENT_PANEL = (0x50 - 8, 400, 0x50 + 0x1D6 + 8, 476)
#: The menu's column (x 10..255) and margin.
MENU_X1, MENU_X2, MENU_MARGIN = 10, 255, 6
#: The text's native height: the menu's rows are 21 px apart (the list's
#: own pitch, font height plus spacing, fields.cpp:1591 — measured on the
#: recorded fields, part 11), the statement in the same style 4; HD draws
#: both at 16 native px, the height that pitch leaves room for.
TEXT_PX = 16
#: The original's menu colours, measured on its own frames (work order 187
#: part 4; the same values on 185's `P11` and 186's `P3` menu frames, two
#: runs): an item and the title (44, 164, 28), a DISABLED item (0, 92, 0),
#: the hovered item (92, 208, 44). HD keeps its HUD palette and transcribes
#: the RELATION (the fundament: a proportion is the transcription): a
#: disabled item at the original's brightness ratio of disabled to normal.
ORIGINAL_ITEM, ORIGINAL_DISABLED = (44, 164, 28), (0, 92, 0)


def luminance(rgb):
    r, g, b = rgb
    return 0.299 * r + 0.587 * g + 0.114 * b


#: 0.48 — a disabled item is about half as bright as an enabled one.
DISABLED_DIM = luminance(ORIGINAL_DISABLED) / luminance(ORIGINAL_ITEM)
