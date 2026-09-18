"""The select panel's own 640x480 rectangles, and what they scale to.

**THE GEOMETRY IS TRANSCRIBED, NOT DESIGNED** (work order 130 E:
"Layout transcribed from the original's own rectangles ... each box
carrying its 640x480 source as provenance"). Every rectangle below
carries the tech.cpp line it comes from.

**AND THE PROVENANCE IS NOT ON THE BOX.** `Box.to_dict` serializes a
fixed key set, so a `native` key on a box would be dropped silently the
first time the F5 editor saved this screen — the trap decision 38 names
for `help_id`, and the reason `screens/colony_summary/boxes.json`
carries no rectangle either. So `boxes.json` here names the boxes and
`seat()` gives them their rectangles from this module, which means an
HD box CANNOT drift from the native rect it stands for: there is only
one number and it is here.

Frame and artwork come later (Data, 17 September: "Rahmen und Visuelles
kommen später darüber"), so this is structure only.

THE PANEL, in select mode (`_Tech_Select_(0)`, tech.cpp:216-231):

    _g_scrn_x = 161, _g_scrn_y = 0                     (tech.cpp:170)
    the art at (161, 0), the black fill it draws over
        (s+4, 4) .. (s+0x1D7, 0x1D8) = (165, 4)-(632, 472) (:281)
    the eight entries at `_tech_select_pos`                 (:20-23)
    each entry's block field (x-2, y+18, x+215, y+99)      (:225-231)

x 0..160 is the SCIENCE ROOM animation (`SR_R%x_SC.LBX`, :245-273) and
is NOT drawn by this build — an OMISSION, marked in screen.py and in a
check. The help list covers it as part of help id 254.
"""
from core.researchlist import (
    BLOCK_DX1, BLOCK_DY1, BLOCK_DX2, BLOCK_DY2, ENTRY_POS_SELECT,
    PANEL_ORIGIN_SELECT)

NATIVE_W, NATIVE_H = 640, 480

#: The black fill `_Tech_Select_` draws under the art (tech.cpp:281):
#: `(s+4, 4)` to `(s+0x1D7, 0x1D8)`. The source gives no size for the
#: TECHSEL art itself (doc/tech_change_reading.md §7: NOT SETTLED), so
#: the fill is the best source-side bound for what the panel covers,
#: and it is the one this screen uses.
PANEL_RECT = (PANEL_ORIGIN_SELECT + 4, 4,
              PANEL_ORIGIN_SELECT + 0x1D7, 0x1D8)

#: THE FILL IS NOT THE PANEL'S VISIBLE EDGE, and the difference matters
#: for the help bands. `doc/tech_change_reading.md` §7 derives the
#: panel's edge from the help rectangles instead — y 26..448 here —
#: because those are what the original treats as "not the panel". The
#: fill is larger and reaches under the top and bottom bands. Both are
#: source facts; this module draws the fill and lets the bands sit over
#: its edges, exactly as the original does.

#: The science room's strip, x 0..160 — everything left of the panel.
#: Its right edge is the panel origin, not help 254's 163: the help
#: rectangle is a hit area and the animation is what is drawn.
SCIENCE_ROOM_RECT = (0, 0, PANEL_ORIGIN_SELECT - 1, NATIVE_H - 1)

#: The two bands above and below the panel. These are HIT AREAS and
#: nothing else — they exist so help id 254's second and third
#: rectangles have a box to resolve against (decision 38: a region's
#: rectangle is the union of the boxes it names, so it follows an F5
#: nudge instead of drifting from it). They are the help rectangles
#: themselves, from billhelp.cpp:44-45, because here the box IS the hit
#: area and there is nothing drawn for it to be sized to. `boxes.json`
#: marks both hidden.
TOP_BAND_RECT = (163, 0, NATIVE_W - 1, 25)

#: The HD title's strip.
#: HD EXTENSION: the original's headline is part of the TECHSEL art and
#: is not a string tech.cpp prints, so there is no native rectangle to
#: transcribe — this one is chosen. It is chosen inside the TOP BAND,
#: which is where the original's art carries that headline and where a
#: right click opens help 254, "Select New Research". The band is the
#: only strip of the panel with nothing in it: below it the radio
#: buttons already start at y 30 and the entry blocks at y 48.
TITLE_RECT = (PANEL_ORIGIN_SELECT + 8, 3, NATIVE_W - 9, 23)
BOTTOM_BAND_RECT = (163, 449, NATIVE_W - 1, NATIVE_H - 1)


def entry_block_rect(index):
    """Entry `index`'s block rectangle (tech.cpp:225-231).

    The eight exist whether or not the category offers anything, which
    is what `core.researchlist.expected_fields` validates against.
    """
    x, y = ENTRY_POS_SELECT[index]
    return (x + BLOCK_DX1, y + BLOCK_DY1, x + BLOCK_DX2, y + BLOCK_DY2)


#: The boxes `boxes.json` names, and the native rectangle each stands
#: for. A box named here and not there (or the other way round) is a
#: mismatch the screen refuses to seat, because a box with no rectangle
#: draws at (0, 0) and looks like a layout bug rather than a missing
#: entry.
BOX_NATIVE = dict(
    {"panel": PANEL_RECT, "science_room": SCIENCE_ROOM_RECT,
     "title": TITLE_RECT,
     "top_band": TOP_BAND_RECT, "bottom_band": BOTTOM_BAND_RECT},
    **{f"entry_{i}": entry_block_rect(i) for i in range(8)})


def to_hd(native_rect, layout):
    """A 640x480 rect as an HD `(x, y, w, h)` in reference space.

    ONE conversion for the whole screen, so the panel, an entry and a
    row cannot land on three different scales. The picture is the
    largest 4:3 area that fits and is centred, exactly as the fallback
    view places the game's own framebuffer (`OriginalView.placement`) —
    which is what makes an HD screenshot line up with the native one
    beside it.

    Inclusive native rectangles in, half-open HD rect out: the native
    `(x1, y1, x2, y2)` covers x2 and y2, so the width is x2 - x1 + 1.
    """
    ref_w, ref_h = layout.ref_w, layout.ref_h
    scale = min(ref_w / NATIVE_W, ref_h / NATIVE_H)
    off_x = (ref_w - NATIVE_W * scale) / 2.0
    off_y = (ref_h - NATIVE_H * scale) / 2.0
    x1, y1, x2, y2 = native_rect
    return (int(round(off_x + x1 * scale)),
            int(round(off_y + y1 * scale)),
            int(round((x2 - x1 + 1) * scale)),
            int(round((y2 - y1 + 1) * scale)))


def to_hd_point(native_point, layout):
    """A 640x480 point as an HD reference-space point."""
    x, y = native_point
    return to_hd((x, y, x, y), layout)[:2]


def from_hd_point(hd_point, layout):
    """An HD reference-space point back to 640x480, or None outside.

    The inverse of `to_hd_point`, and the one the hit test goes
    through: a click resolves to a native pixel first and is compared
    against native rectangles, so the hover, the drawing and the hit
    test all speak the original's coordinates (decision 5). None
    outside the picture — there is no native pixel there.
    """
    ref_w, ref_h = layout.ref_w, layout.ref_h
    scale = min(ref_w / NATIVE_W, ref_h / NATIVE_H)
    off_x = (ref_w - NATIVE_W * scale) / 2.0
    off_y = (ref_h - NATIVE_H * scale) / 2.0
    nx = int((hd_point[0] - off_x) / scale)
    ny = int((hd_point[1] - off_y) / scale)
    if not (0 <= nx < NATIVE_W and 0 <= ny < NATIVE_H):
        return None
    return (nx, ny)


def window_rect(native_rect, layout):
    """A 640x480 rect straight to WINDOW pixels.

    `to_hd` gives reference space (1920x1080) because that is where
    boxes and every other stored geometry live (decision 1); this is
    the one step further, for anything that blits. Both go through the
    same conversion, so nothing can land on two different scales.
    """
    return layout.rect(to_hd(native_rect, layout))


def window_point(native_point, layout):
    """A 640x480 point straight to WINDOW pixels."""
    return layout.pos(*to_hd_point(native_point, layout))


def window_width(native_x, native_y, native_w, layout):
    """A 640x480 width in WINDOW pixels, at that native position.

    Takes the position too, because the rounding is not the same
    everywhere: `to_hd` rounds each edge, so a width measured at one x
    is not the width at another, and a text that fits the measured
    width but not the drawn one is clipped by a pixel.
    """
    return window_rect((native_x, native_y,
                        native_x + native_w - 1, native_y), layout)[2]


def seat(boxes, layout):
    """Give every box its rectangle from `BOX_NATIVE`, and lay it out.

    `derived` is set for the same reason `colonyplates.seat` sets it:
    `Box.to_dict` omits the rect of a derived box, so the F5 editor
    cannot write a copy of a number that lives here — and the copy it
    would write is the one that goes stale.

    Returns the names it could not seat, so the caller can refuse
    rather than draw a screen with boxes at the origin.
    """
    unseated = []
    for box in boxes:
        native = BOX_NATIVE.get(box.name)
        if native is None:
            unseated.append(box.name)
            continue
        box.ref_rect = to_hd(native, layout)
        box.derived = True
        box.update_layout(layout)
    return unseated
