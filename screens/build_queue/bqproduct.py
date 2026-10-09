"""What the build popup shows for the selected product — work order 226 D.

Data's decision 3 of 9 October 2026: the picture box at the top left shows
the original's graphic for the selected project, the large box its
information. TRANSCRIBED from `COLBLDG::Draw_Current_Selection_`
(colbldg.cpp:822-986) and the functions it calls: which picture
(`screens/colony/colroom`) and which text each product has.

  a building      its picture, and the help record of its application
                  (`Draw_Building_Info_`, :1176-1201: `_buildings[id]
                  .tech_app`)
  Trade Goods,    MAINTEXT entries 12 and 13 (`Print_Setting_Description_`,
  Housing         :1044-1054)
  the people,     help records 6 farmer, 8 worker, 7 scientist, 166 spy;
  a spy           69 freighters, 41 colony ship, 109 outpost ship, 189
  the ships       transport (`Print_App_Description_`, :1056-1075)
  a design        the design's paragraph, the one Refit prints
                  (`Draw_Ship_Design_Info2_`, :1205-1215 ->
                  `Build_Ship_Design_Info_Formatted_Paragraph_`)
  a queued ship   its design's paragraph (`Draw_Ship_Info_`, :1880-1903)
  Repeat, Refit   no picture: a word centred in the box (:882-908)

The texts are the player's own (decision 38: `help_<lang>.json`,
`maintext_<lang>.json`); absent, the box says nothing invented.
"""
from core import prodname

#: `TECHDATA::_buildings[id]` (techdata.cpp:25-74): (tech_app, type). Type 7
#: is a satellite. A transcription with a checker: smoke check 090qd reads
#: techdata.cpp and holds this table to it.
BUILDINGS = {
    1: (5, 4), 2: (14, 0), 3: (15, 7), 4: (18, 1), 5: (19, 2), 6: (21, 1),
    7: (22, 3), 8: (27, 7), 9: (32, 1), 10: (39, 0), 11: (40, 0),
    12: (49, 0), 13: (50, 0), 14: (52, 7), 15: (61, 3), 16: (68, 1),
    17: (74, 1), 18: (75, 5), 19: (76, 5), 20: (86, 3), 21: (87, 0),
    22: (103, 0), 23: (129, 2), 24: (130, 1), 25: (131, 1), 26: (132, 2),
    27: (133, 2), 28: (134, 0), 29: (135, 1), 30: (136, 2), 31: (141, 0),
    32: (142, 0), 33: (152, 1), 34: (154, 1), 35: (155, 0), 36: (156, 3),
    37: (162, 0), 38: (163, 1), 39: (164, 0), 40: (168, 7), 41: (169, 7),
    42: (174, 0), 43: (178, 0), 44: (183, 0), 45: (197, 0), 46: (198, 0),
    47: (67, 0), 48: (16, 0),
}

TRADE_GOODS, HOUSING, FARMER, WORKER, SCIENTIST, SPY = -2, -3, -4, -5, -6, -7
REFIT, REPEAT, TRANSPORT, COLONY_SHIP = -8, -10, -11, -12
FREIGHTERS, OUTPOST_SHIP = -15, -17
#: colbldg.cpp's `Print_App_Description_` ids, per product.
APPS = {FARMER: 6, WORKER: 8, SCIENTIST: 7, SPY: 166, FREIGHTERS: 69,
        COLONY_SHIP: 41, OUTPOST_SHIP: 109, TRANSPORT: 189}
#: `Print_Setting_Description_` ids (MAINTEXT entries).
SETTINGS = {TRADE_GOODS: 12, HOUSING: 13}
#: `Remap_Draw_Ship_Seg_N_Centered_(244, 56, n)`: the special ships' pictures.
SHIP_PICTURES = {OUTPOST_SHIP: 46, FREIGHTERS: 48, COLONY_SHIP: 45,
                 TRANSPORT: 47}
#: The word Refit shows in the picture box, E_Strings 0x7D (:904); Repeat
#: shows its own name (:890).
WORD_IN_BOX = {REFIT: 0x7D}


def picture(product, race, design_picture=None, ship=None):
    """The `colroom.tile` spec for `product`, or None (no picture)."""
    if prodname.kind(product) == prodname.KIND_BUILDING:
        return ("building", int(product))
    if product == TRADE_GOODS:
        return ("trade_goods",)
    if product == HOUSING:
        # building 14's GROUND drawing, never its satellite: the case calls
        # `Draw_Building_Centered_In_Window_(14)` directly (colbldg.cpp:952)
        return ("ground", 14)
    if product in (FARMER, WORKER, SCIENTIST):
        return ("android",)
    if product == SPY:
        return ("spy", int(race))
    if product in SHIP_PICTURES:
        return ("ship", SHIP_PICTURES[product], 0)
    if prodname.kind(product) == prodname.KIND_SHIP_DESIGN and \
            design_picture is not None:
        return ("ship", int(design_picture), 0)
    if prodname.kind(product) == prodname.KIND_QUEUED_SHIP and ship is not None:
        return ("ship", int(ship.picture_num), int(ship.previous_owner))
    return None


def app_id(product):
    """The help record whose body the large box prints, or None."""
    if prodname.kind(product) == prodname.KIND_BUILDING:
        got = BUILDINGS.get(int(product))
        return got[0] if got else None
    return APPS.get(product)


def text(product, helptext, maintext):
    """The large box's text for `product` as (title, body), or None —
    the help record or the setting description, as the original prints
    it; designs and queued ships take the Refit paragraph (the caller)."""
    if product in SETTINGS:
        body = maintext.description(SETTINGS[product]) if maintext else None
        return (None, body) if body else None
    app = app_id(product)
    if app is None or helptext is None:
        return None
    return helptext.entry(app)
