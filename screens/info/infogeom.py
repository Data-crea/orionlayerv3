"""The Info screen's own 640x480 geometry — every rectangle, sourced.

The Leaders and Races rule: each number is a literal in
`src/game/info.cpp` (orion2re `orionlayer-local`, work order 175 D), and
HD draws each thing at the HD image of its native rectangle through
`core/researchnative`. Button sizes are INFO.LBX's own header sizes, the
number `Add_Button_Field_` reads (fields.cpp:405-406), measured on this
disk for work order 175.
"""

GAME_SCREEN_ID = 9                    # SCREEN_INFO, orion2_consts.h:469
TYPE_BUTTON, TYPE_MULTI, TYPE_HIDDEN = 0, 3, 7
ESC = 0x1B

#: EXIT: `Add_Button_Field_(0x217, 0x1B2, …, info_lbx[2], "\\x1B")`
#: (info.cpp:561), INFO.LBX 2 is 91 x 30.
EXIT = (535, 434, 535 + 91 - 1, 434 + 30 - 1)
#: The five tabs: `_sub_scr_field` (:174) with INFO.LBX 3-7 (164 wide,
#: 27/25/26/26/27 high), multi-buttons bound to `current_tab` (:563-574).
TAB_AT = ((21, 50), (21, 77), (21, 102), (21, 128), (21, 154))
TAB_SIZE = ((164, 27), (164, 25), (164, 26), (164, 26), (164, 27))
#: The page title, centred at (416, 31) (:1150 and each page's twin).
TITLE_AT = (416, 31)
TITLE_BOX = (212, 21, 620, 44)
#: The left panel: the stardate centred at (151, 27) (:578, :596).
STARDATE_AT = (151, 27)
LEFT_PANEL = (8, 8, 205, 471)
TAB_PANEL = (14, 44, 199, 188)
#: The chart (`Draw_Maint_Income_Chart_`, :732-776): the income bar at
#: (30, 212), the six maintenance bars right to left 18 apart, the net
#: income centred at (105, 196), the two headings at (42, 324) and
#: (120, 324), the seven labels from (25, 344) stepping 16, 160 x 20.
CHART_BOX = (14, 186, 199, 462)
NET_AT = (105, 196)
BAR_TOP, BAR_BOTTOM = 212, 316          # INFO.LBX 22 is the tall bar
INCOME_BAR_X = 30
BAR_W = 16
INCOME_HEAD_AT, MAINT_HEAD_AT = (42, 324), (120, 324)
LABEL_AT, LABEL_STEP, LABEL_SIZE = (25, 344), 16, (160, 20)
#: The content area (the interlaced fill, :596).
CONTENT = (212, 23, 620, 457)

# ── The pages' drop areas (info.cpp:118-322) ──────────────
HISTORY_LEGEND = (220, 60, 609, 122)
HISTORY_GRAPH = (220, 132, 609, 413)
HISTORY_BUTTON_X = (233, 323, 404, 457)      # `_graph_button_x`, y 427
HISTORY_BUTTON_Y, HISTORY_BUTTON_SIZE = 427, ((86, 19), (77, 19), (49, 19),
                                              (41, 19))
TECH_LIST = (218, 60, 425, 413)
TECH_NAME = (433, 60, 612, 104)
TECH_PICTURE = (433, 114, 612, 254)
TECH_BODY = (433, 264, 612, 413)
TECH_TAB_AT = ((216, 427), (318, 427), (373, 427), (438, 427))  # `_tech_rev_field`
TECH_TAB_SIZE = ((102, 18), (55, 18), (65, 18), (77, 18))       # INFO.LBX 16-19
RACE_PANELS = ((223, 60, 410, 230), (419, 60, 606, 230),
               (223, 243, 410, 413), (419, 243, 606, 413))
RACE_PAGE_BUTTON = (385, 427, 385 + 58 - 1, 427 + 21 - 1)       # INFO.LBX 20
TURNS_BOX = (218, 60, 612, 414)
REFERENCE_HEADS = ((218, 60, 414, 86), (418, 60, 613, 86))
REFERENCE_LISTS = ((218, 93, 414, 413), (418, 93, 613, 413))
#: Reference index rows: `(0xDD, y - 2, 0x19B, y + 18)` and `(0x1A5, …,
#: 0x263, …)` from y 100 stepping 20 (:1819, :1837).
INDEX_ROW_X = ((0xDD, 0x19B), (0x1A5, 0x263))
INDEX_ROW_Y0, INDEX_ROW_STEP = 100, 20
CATEGORY_HEAD = (218, 60, 613, 86)
CATEGORY_LIST = (218, 93, 414, 413)
CATEGORY_TEXT = (418, 93, 613, 413)
HOWTO_HEAD = (218, 60, 610, 86)
HOWTO_TEXT = (218, 93, 610, 416)
BACK_BUTTON = (386, 427, 386 + 55 - 1, 427 + 21 - 1)            # INFO.LBX 21


def tab_rect(k):
    (x, y), (w, h) = TAB_AT[k], TAB_SIZE[k]
    return (x, y, x + w - 1, y + h - 1)


def tech_tab_rect(k):
    (x, y), (w, h) = TECH_TAB_AT[k], TECH_TAB_SIZE[k]
    return (x, y, x + w - 1, y + h - 1)


def history_button_rect(k):
    x, (w, h) = HISTORY_BUTTON_X[k], HISTORY_BUTTON_SIZE[k]
    return (x, HISTORY_BUTTON_Y, x + w - 1, HISTORY_BUTTON_Y + h - 1)


def index_row(column, n):
    x1, x2 = INDEX_ROW_X[column]
    y = INDEX_ROW_Y0 + n * INDEX_ROW_STEP
    return (x1, y - 2, x2, y + 18)
