"""Select mode's rectangles — one binding of the shared geometry.

Everything here is `core.researchnative`, configured for select mode.
The module exists because a screen folder is where a screen's own
things live (decision 7) and because the names below have callers; the
numbers are in `core/researchnative.py`, once, for both modes.

**THE GEOMETRY IS TRANSCRIBED, NOT DESIGNED** — every rectangle carries
the tech.cpp line it comes from, in the shared module.

Select mode's own two facts, and they are the only ones:

    _g_scrn_x = 161, _g_scrn_y = 0                     (tech.cpp:170)
    x 0..160 is the SCIENCE ROOM animation (`SR_R%x_SC.LBX`, :245-273)
        and is NOT drawn by this build — an OMISSION, marked in
        screen.py and in a check. The help list covers it as part of
        help id 254.

HD EXTENSION: the title's strip is the one CHOSEN rectangle on this
screen. The original's headline is part of the TECHSEL art and is not
a string tech.cpp prints, so there is no native rectangle to
transcribe. Chosen inside the top band — the only strip of the panel
with nothing in it, since the radios start at y 30 and the entry blocks
at y 48. Marked in screen.py and held by a check.
"""
from core.researchnative import (            # noqa: F401  (re-exported)
    NATIVE_H, NATIVE_W, Geometry, from_hd_point, seat, to_hd, to_hd_point,
    window_point, window_rect, window_width)

#: This screen's configuration of the shared geometry.
GEOM = Geometry("select")

PANEL_RECT = GEOM.panel_rect
SCIENCE_ROOM_RECT = GEOM.science_room_rect
TITLE_RECT = GEOM.title_rect
TOP_BAND_RECT = GEOM.bands["top_band"]
BOTTOM_BAND_RECT = GEOM.bands["bottom_band"]
BOX_NATIVE = GEOM.box_native()


def entry_block_rect(index):
    """Entry `index`'s block rectangle (tech.cpp:225-231)."""
    return GEOM.entry_block_rect(index)
