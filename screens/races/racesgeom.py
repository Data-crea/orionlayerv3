"""The Races screen's own 640x480 geometry — every rectangle, sourced.

**TRANSCRIBED, NOT DESIGNED** — the Leaders rule (`screens/leaders/
ldrgeom.py`): each number is a literal in `src/game/racescrn.cpp` at
orion2re's `orionlayer-local` (work order 175), and the HD screen draws
each thing at the HD image of its native rectangle through
`core/researchnative`, so the hit test and the drawing read one table
(decision 5).

The button sizes are the art's own header sizes (RACES.LBX 6-9, 60), the
number `Add_Button_Field_` / `Add_Radio_Button_Field_` itself reads for
the field's extent (fields.cpp:405-406: `x + Get_Width_ - 1`), measured
on this disk's RACES.LBX for work order 175 and held to the live list by
`raceswire`, which refuses a list that disagrees.
"""

NATIVE_W, NATIVE_H = 640, 480

#: `SCREEN_RACE` (orion2_consts.h:466).
GAME_SCREEN_ID = 6

#: The seven other races the screen has room for (`MAX_PLAYERS - 1`).
SLOTS = 7

#: Field types as the wire reports them (screens/fleets/fltwire.py).
TYPE_BUTTON, TYPE_RADIO, TYPE_MULTI, TYPE_HIDDEN = 0, 1, 3, 7
ESC = 0x1B

# ── Per race slot (racescrn.cpp:32-47) ────────────────────

PICTURE = [(21, 49), (21, 156), (21, 262), (21, 369),
           (544, 50), (544, 157), (544, 262)]
TEXT = [(125, 50), (125, 157), (125, 262), (125, 366),
        (333, 50), (333, 157), (333, 262)]
BAR = [(105, 49), (105, 155), (105, 262), (105, 370),
       (528, 49), (528, 156), (528, 261)]
SLIDER_X = [96, 96, 96, 96, 520, 520, 520]
SPIES = [(121, 98), (121, 205), (121, 311), (121, 417),
         (333, 98), (333, 206), (333, 311)]
SPY_BUTTONS = [(120, 126), (120, 233), (120, 338), (120, 445),
               (332, 126), (332, 233), (332, 338)]
#: `_spy_group_data`: (x1, y1, x2, y2) of each spy strip's icons.
SPY_GROUP = [(121, 98, 307, 122), (121, 205, 307, 229),
             (121, 311, 307, 335), (121, 417, 307, 441),
             (333, 98, 519, 122), (333, 206, 519, 230),
             (333, 311, 519, 335)]
AGENT_GROUP = (332, 392, 613, 415)

PORTRAIT = (76, 88)                 # RACES.LBX 32-44 (:328)
TEXT_BOX = (182, 43)                # `Squeeze_Paragraph_Centered_(…,0xB6,0x2B)`
NAME_DY, NAME_W = 76, 76            # (px, py + 0x4C), width 0x4C (:140-146)
NO_CONTACT_DX, NO_CONTACT_DY = 0x5B, 10   # (:121-125)
IGNORED_DX, IGNORED_DY = 37, 66     # (:569-572)
BAR_SIZE = (8, 88)                  # RACES.LBX 3
SLIDER_SIZE = (25, 13)              # RACES.LBX 2
#: The mission buttons' offsets and widths (RACES.LBX 10+i, 17+i, 24+i:
#: 75 x 13, 72 x 14, 40 x 13) — ESPIONAGE, SABOTAGE, HIDE. Multi-button
#: fields end at `x + Get_Width_ - 1` (fields.cpp:337-338), type 3.
MISSION_DX = (0, 76, 149)
MISSION_W = (75, 72, 40)
MISSION_H = (13, 14, 13)

#: `_slider_remap_list` and `_relation_name_table` (:30-31).
SLIDER_REMAP = (74, 72, 68, 66, 62, 60, 56, 54, 50, 48, 44, 42, 38, 36,
                32, 30, 26, 24, 20, 18, 14, 12, 8, 6, 2, 0)
RELATION_NAMES = (9, 21, 33, 45, 57, 69, 81, 93, 107, 119, 131, 143, 155,
                  167, 179, 191, 255)
#: An unused slot's slider stands at `bar_y + 0x4B` (:247-249).
SLIDER_PARKED = 0x4B

# ── The bottom right (racescrn.cpp:338-373, :222-229) ──────

#: name -> (origin, hotkey, field type, art size)
BUTTONS = {
    "exit":     ((535, 433), ESC, TYPE_BUTTON, (73, 18)),
    "ignore":   ((429, 444), ord("I"), TYPE_RADIO, (87, 17)),
    "report":   ((429, 423), ord("R"), TYPE_RADIO, (87, 17)),
    "audience": ((334, 423), ord("A"), TYPE_RADIO, (88, 17)),
    "war":      ((334, 444), ord("D"), TYPE_RADIO, (88, 17)),
}
ACTIONS = ("ignore", "report", "audience", "war")
#: `Squeeze_Centered_Print_(0x1A1, 0x174, …, 0x62)` and (0x207, …, 0x61).
SPY_BONUS_AT, SPY_BONUS_W = (0x1A1, 0x174), 0x62
AGENT_BONUS_AT, AGENT_BONUS_W = (0x207, 0x174), 0x61
#: The panels the background art paints (RACES.LBX 0, measured off the
#: extracted picture for work order 175 — drawing only, no field).
BONUS_BOX = (330, 365, 620, 416)
BUTTON_BOX = (330, 419, 620, 464)

AGENT_FIELD = (328, 386, 613, 415)  # (:433)
CATCHER = (0, 0, 639, 479)          # (:815)


def button_rect(name):
    """Inclusive, as `Add_Button_Field_` / `Add_Radio_Button_Field_` make it."""
    (x, y), _hk, _t, (w, h) = BUTTONS[name]
    return (x, y, x + w - 1, y + h - 1)


def slot_box(i):
    """The panel one race slot sits in (the background art's own box:
    left column x 16-312, right 328-624, from 4 px over the portrait)."""
    px, py = PICTURE[i]
    x0 = 16 if i < 4 else 328
    return (x0, py - 4, x0 + 296, py + 92)


def who_field(i):
    """`Setup_Race_Who_Fields_` (:459-488)."""
    x0 = 0 if i < 4 else 320
    y = PICTURE[i][1]
    return (x0, y, x0 + 319, y + 88)


def spy_field(i):
    x, y = SPIES[i]
    return (x, y - 6, x + 187, y + 25)


def bar_field(i):
    x, y = BAR[i]
    return (x - 6, y - 6, x + 8, y + 88)


def mission_rect(i, k):
    x, y = SPY_BUTTONS[i]
    return (x + MISSION_DX[k], y, x + MISSION_DX[k] + MISSION_W[k] - 1,
            y + MISSION_H[k] - 1)


def slider_y(i, relation):
    """`bar_y + _slider_remap_list[(rel + 100) / 8] - 6` (:304-312)."""
    idx = max(0, min(len(SLIDER_REMAP) - 1, (int(relation) + 100) // 8))
    return BAR[i][1] + SLIDER_REMAP[idx] - 6


def relation_word_id(relation):
    """BILLTEXT 0x21 + the first index whose table value reaches
    `rel + 100` (`Init_Race_Display_Data_`, :296-303)."""
    value = int(relation) + 100
    k = 0
    while k < len(RELATION_NAMES) - 1 and RELATION_NAMES[k] < value:
        k += 1
    return 0x21 + k


def icon_spacing(count, box, icon_w=28):
    """`Calculate_Icon_Group_Data_` (:57-86): the step between icons."""
    width = box[2] - box[0] + 1
    if count <= 1:
        return icon_w
    return max(0, min(icon_w, (width - icon_w) // (count - 1)))


def main_shape(n):
    """`(rect, type, hotkey)` of the main mode's fields after slot 0, in
    the order the source adds them (:338-373, :426-457, :815)."""
    out = [(button_rect("exit"), TYPE_BUTTON, ESC)]
    if n < 1:
        return out + [(CATCHER, TYPE_HIDDEN, 0)]
    for name in ACTIONS:
        out.append((button_rect(name), TYPE_RADIO, BUTTONS[name][1]))
    out.append((AGENT_FIELD, TYPE_HIDDEN, 0))
    for i in range(n):
        for k in range(3):
            out.append((mission_rect(i, k), TYPE_MULTI, 0))
        out.append((spy_field(i), TYPE_HIDDEN, 0))
        out.append((bar_field(i), TYPE_HIDDEN, 0))
    out.append((CATCHER, TYPE_HIDDEN, 0))
    return out


def who_shape(n):
    """The WHO mode's list: the five buttons, one field per race, the
    catcher (:459-488, :815)."""
    out = [(button_rect("exit"), TYPE_BUTTON, ESC)]
    for name in ACTIONS:
        out.append((button_rect(name), TYPE_RADIO, BUTTONS[name][1]))
    out += [(who_field(i), TYPE_HIDDEN, 0) for i in range(n)]
    return out + [(CATCHER, TYPE_HIDDEN, 0)]
