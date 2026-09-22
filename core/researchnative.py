"""The research panel's own 640x480 rectangles, per mode, and the scale.

**THE GEOMETRY IS TRANSCRIBED, NOT DESIGNED** (work order 130 E), and
it is the same geometry twice: `TECH::_Tech_Select_(changing_tech)`
draws ONE panel and every position in it is `_g_scrn_x + constant`
(tech.cpp:146-147, :170-171). Select mode's origin is 161, change
mode's is 80, and the 81 px between them is the whole difference in
layout. So this module carries one `Geometry` and two instances of it,
which is work order 165's "one implementation and two configurations,
not two copies".

**AND THE PROVENANCE IS NOT ON THE BOX.** `Box.to_dict` serializes a
fixed key set, so a `native` key on a box would be dropped silently the
first time the F5 editor saved a research screen — the trap decision 38
names for `help_id`. So each screen's `boxes.json` names its boxes and
`seat()` gives them their rectangles from here: an HD box CANNOT drift
from the native rect it stands for, because there is only one number
and it is in this file.

Frame and artwork come later (Data, 17 September: "Rahmen und Visuelles
kommen später darüber"), so this is structure only.

WHAT DIFFERS BETWEEN THE MODES, and every line of it is source:

    origin `_g_scrn_x`         161 select, 80 change   tech.cpp:146, :170
    entry origins              `_tech_select_pos` / `_tech_change_pos`
                                                        tech.cpp:20-28
    the strip left of the panel  select: the science room animation
                               (`SR_R%x_SC.LBX`, :245-273), x 0..160.
                               change: nothing — the galaxy map is
                               behind it, and the panel is drawn over
                               a map the game still owns
    the exit button            change only, `Add_Button_Field_(s+189,
                               452, …)` :198-200, hotkey ESC. Select
                               mode has none and no ESC field at all
                               (:207), which is why its only way out is
                               a commit
    help id and its rects      254 / three rects billhelp.cpp:42-46
                               255 / three rects billhelp.cpp:48-52

**THE EXIT BUTTON'S SIZE IS NOT IN THE SOURCE** and is not invented
here. `Add_Button_Field_` takes the rect from the ART
(fields.cpp:366-367), which is why `doc/tech_change_reading.md` §2 had
the end as NOT SETTLED. So this module gives its ORIGIN only and the
screen looks the field up in the live list by shape, the way every
other send on these screens does — the rect comes off the wire or the
button is not there to click.

**It was measured on 22 September 2026** (work order 165 part D, change
mode open on a live game): `(269, 452)-(360, 470)`, 91 x 18 px. That
number is NOT typed in here, and the reason is the rule it would break.
The wire carries it on every snapshot; a copy in this file would be the
second copy that goes stale the day the art changes, and the lookup
that already works would then have a constant to disagree with.
"""

NATIVE_W, NATIVE_H = 640, 480

#: `_g_scrn_x` per mode (tech.cpp:146-147, :170-171). `_g_scrn_y` is 0
#: in both, which is why no y is shifted anywhere below.
ORIGIN = {"select": 161, "change": 80}

#: The black fill `_Tech_Select_` draws under the art (tech.cpp:281,
#: :290): `(s+4, 4)` to `(s+0x1D7, 0x1D8)`. The source gives no size
#: for the TECHSEL art itself (doc/tech_change_reading.md §7: NOT
#: SETTLED), so the fill is the best source-side bound for what the
#: panel covers, and it is the one both modes use.
FILL_DX1, FILL_DY1, FILL_DX2, FILL_DY2 = 4, 4, 0x1D7, 0x1D8

#: `Add_Button_Field_(s + 189, 452, …)` — change mode's exit
#: (tech.cpp:198-200). Origin only; see the module docstring.
EXIT_BUTTON_DX, EXIT_BUTTON_Y = 189, 452

#: The help list each mode installs, and its three rectangles
#: (billhelp.cpp:42-46 and :48-52). They are HIT AREAS and nothing
#: else: decision 38 wants a region's rectangle to be the union of the
#: boxes it names, so each one gets a hidden box and the box IS the
#: rectangle. Note that they are not the same SHAPE in the two modes —
#: select mode's first rectangle covers the science room, change
#: mode's covers the strip of galaxy map left of the panel.
#:
#: Each entry is `(box name, the help rectangle)`. The BOX is what a
#: region resolves against; where something is drawn in that strip the
#: box is the drawn thing and not the hit area — which is why select
#: mode's first box is the science room at x 0..160 and its help
#: rectangle reaches 163. Change mode draws nothing beside the panel,
#: so there the box IS the rectangle.
HELP_RECTS = {
    "select": (254, (("science_room", (0, 0, 163, NATIVE_H - 1)),
                     ("top_band", (163, 0, NATIVE_W - 1, 25)),
                     ("bottom_band", (163, 449, NATIVE_W - 1, NATIVE_H - 1)))),
    "change": (255, (("left_band", (0, 0, 80, NATIVE_H - 1)),
                     ("right_band", (557, 0, NATIVE_W - 1, NATIVE_H - 1)),
                     ("top_band", (80, 0, 557, 25)))),
}


class Geometry:
    """One mode's rectangles, all of them `origin + constant`.

    Built once per screen and handed to the drawing and to the hit
    test, so the two cannot end up on different numbers (decision 5).
    """

    def __init__(self, mode):
        from core import researchlist          # circular at import time
        assert mode in ORIGIN, f"no such research mode: {mode!r}"
        self.mode = mode
        self.select = mode == "select"
        self.origin = ORIGIN[mode]
        self.entry_pos = (researchlist.ENTRY_POS_SELECT if self.select
                          else researchlist.ENTRY_POS_CHANGE)
        self._rl = researchlist
        s = self.origin
        self.panel_rect = (s + FILL_DX1, FILL_DY1, s + FILL_DX2, FILL_DY2)
        self.help_id, bands = HELP_RECTS[mode]
        #: `{box name: the help rectangle it stands for}`, in the
        #: original's own order — the walk stops at the first hit, so
        #: order is load-bearing (decision 38).
        self.bands = dict(bands)
        # THE TITLE IS AN HD EXTENSION and the only chosen rectangle in
        # this module: the original's headline is part of the TECHSEL
        # art and is not a string tech.cpp prints, so there is nothing
        # to transcribe. It is chosen inside the TOP band, which is
        # where the art carries that headline and where a right click
        # opens this mode's help. The band is the only strip with
        # nothing in it — below it the radios start at y 30 and the
        # entry blocks at y 48.
        top = self.bands["top_band"]
        self.title_rect = (s + 8, 3, top[2] - 8, 23)
        # Select mode only: the science room animation, an OMISSION.
        # Its box is what is DRAWN there, x 0..160, and not help 254's
        # 163 — the help rectangle is a hit area and the animation is
        # the thing.
        self.science_room_rect = ((0, 0, s - 1, NATIVE_H - 1)
                                  if self.select else None)
        self.exit_button_origin = (None if self.select
                                   else (s + EXIT_BUTTON_DX, EXIT_BUTTON_Y))

    def entry_block_rect(self, index):
        """Entry `index`'s block rectangle (tech.cpp:225-231).

        The eight exist whether or not the category offers anything,
        which is what `researchlist.expected_fields` validates against.
        """
        x, y = self.entry_pos[index]
        return (x + self._rl.BLOCK_DX1, y + self._rl.BLOCK_DY1,
                x + self._rl.BLOCK_DX2, y + self._rl.BLOCK_DY2)

    def box_native(self):
        """`{box name: native rect}` — what `seat()` needs.

        A box named here and not in `boxes.json` (or the other way
        round) is a mismatch the screen refuses to seat, because a box
        with no rectangle draws at (0, 0) and looks like a layout bug
        rather than a missing entry.
        """
        out = {"panel": self.panel_rect, "title": self.title_rect}
        out.update(self.bands)
        if self.science_room_rect is not None:
            out["science_room"] = self.science_room_rect
        out.update({f"entry_{i}": self.entry_block_rect(i)
                    for i in range(8)})
        return out


def _scale(layout):
    """The one conversion, so nothing lands on two different scales."""
    ref_w, ref_h = layout.ref_w, layout.ref_h
    scale = min(ref_w / NATIVE_W, ref_h / NATIVE_H)
    return (scale, (ref_w - NATIVE_W * scale) / 2.0,
            (ref_h - NATIVE_H * scale) / 2.0)


def to_hd(native_rect, layout):
    """A 640x480 rect as an HD `(x, y, w, h)` in reference space.

    The picture is the largest 4:3 area that fits and is centred,
    exactly as the fallback view places the game's own framebuffer
    (`OriginalView.placement`) — which is what makes an HD screenshot
    line up with the native one beside it.

    Inclusive native rectangles in, half-open HD rect out: the native
    `(x1, y1, x2, y2)` covers x2 and y2, so the width is x2 - x1 + 1.
    """
    scale, off_x, off_y = _scale(layout)
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
    scale, off_x, off_y = _scale(layout)
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


def seat(boxes, layout, box_native):
    """Give every box its rectangle from `box_native`, and lay it out.

    `derived` is set for the same reason `colonyplates.seat` sets it:
    `Box.to_dict` omits the rect of a derived box, so the F5 editor
    cannot write a copy of a number that lives here — and the copy it
    would write is the one that goes stale.

    Returns the names it could not seat, so the caller can refuse
    rather than draw a screen with boxes at the origin.
    """
    unseated = []
    for box in boxes:
        native = box_native.get(box.name)
        if native is None:
            unseated.append(box.name)
            continue
        box.ref_rect = to_hd(native, layout)
        box.derived = True
        box.update_layout(layout)
    return unseated
