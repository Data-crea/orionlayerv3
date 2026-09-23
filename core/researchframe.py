"""The research panel's outer frame — the Fleets art, nine-sliced.

Work order 166 part B, Data's decision: the research panel gets the
Fleets screen's own inner frame — the one around the scanner map, with
the orange lamps in its four corners — around its content box, in both
modes. This supersedes "frame and artwork come later" for these two
screens only.

**DEVIATION, marked.** The original draws TECHSEL.LBX picture 14
(change) / 0 (select) there, so there IS a frame in that place and
this is a different picture in it — which is a deviation and not an
extension (decision 61's vocabulary: an extension is something the
original does not do at all). `outer_frame` in both screens' `MARKED`,
and a smoke check holds it.

**THE CORNERS SCALE, THEY DO NOT STRETCH**, and that is why this is
not one of the two nine-slicers the tree already has:

    `core/nineslice.NineSlice`  keeps corners at the SOURCE's pixel
                                size, whatever the window is — a 140 px
                                lamp at 1080p and at 4K alike
    `core/frame.FrameRenderer`  scales each corner by target/source PER
                                AXIS, so a target whose aspect differs
                                from the source's stretches them — and
                                this panel is square where the cut is
                                1.62:1

What is wanted is neither: one factor from the WINDOW, so a lamp is
round at every resolution and 1:1 with the artwork at the size the
artwork was drawn for. That is had by SCALING THE SOURCE ONCE and
nine-slicing the result — so `NineSlice` still does the slicing and
there is no third implementation of it here, only a third rule about
its corners.

**THE FACTOR.** `screens/fleets/assets/frame.png` is 3840x2160, which
is the 1920x1080 reference at 2x, so the cut is at reference scale 0.5.
One reference pixel of frame is therefore half a source pixel, and the
window scale multiplies from there: at 1080p a corner is 70 px and at
3840x2160 it is 140 — the source's own, unscaled.
"""
import logging
import os

import pygame

from core import nineslice

log = logging.getLogger("researchframe")

#: Where `tools/make_research_frame.py` writes the cut. DERIVED: the
#: input is committed, this is not, and a smoke check rebuilds it in
#: memory and compares byte for byte (decision 49's surviving half).
ASSET = os.path.join("frames", "research_panel.png")

#: The source's own numbers, from the cutting tool. Imported rather
#: than repeated would be better still, but the tool imports pygame and
#: writes files; these two are asserted equal to it by a smoke check.
CORNER = 140
RAIL = 23

#: `screens/fleets/assets/frame.png` is the 1920x1080 reference at 2x.
#: One reference pixel of this artwork is half a source pixel.
REFERENCE_SCALE = 0.5


class ResearchFrame:
    """The cut, nine-sliced, cached per (scale, size)."""

    def __init__(self, res):
        self.image = None
        path = res.shared(ASSET) if res is not None else None
        if path and os.path.exists(path):
            self.image = pygame.image.load(path).convert_alpha()
        else:
            # ABSENT IS A STATE, not an error (decision 38): a clone
            # that has not run `tools/setup.py` has no cut, and the
            # panel draws without a frame and says so once.
            log.info("research frame absent (%s) — run "
                     "`python tools/setup.py`", ASSET)
        self._slices = {}
        self._cache = {}

    @property
    def available(self):
        return self.image is not None

    def _sliced(self, scale):
        key = round(scale, 4)
        got = self._slices.get(key)
        if got is None:
            w = max(3, int(self.image.get_width() * scale))
            h = max(3, int(self.image.get_height() * scale))
            corner = max(1, int(CORNER * scale))
            # The corner must leave a rail to stretch, or the slice is
            # not a nine-slice any more.
            corner = min(corner, (w - 1) // 2, (h - 1) // 2)
            got = nineslice.NineSlice(
                pygame.transform.smoothscale(self.image, (w, h)),
                corner, corner, corner, corner)
            self._slices[key] = got
        return got

    def rail(self, scale):
        """The plain rail's thickness at this scale, in window pixels.

        What a caller adds around a box so the frame's OPENING lands on
        the box rather than over it.
        """
        return max(1, int(round(RAIL * scale)))

    def corner(self, scale):
        """The corner's size at this scale, in window pixels."""
        return max(1, int(CORNER * scale))

    def around(self, box, scale):
        """The frame's rect for a content box: the box plus the rail."""
        r = self.rail(scale)
        return pygame.Rect(box[0] - r, box[1] - r,
                           box[2] + 2 * r, box[3] + 2 * r)

    def render(self, surface, box, scale):
        """Draw the frame around `box`. Returns its rect, or None.

        `box` is (x, y, w, h) in WINDOW pixels — the panel's content
        box — and `scale` is the window scale, `Layout.scale`.
        """
        if not self.available:
            return None
        scale = REFERENCE_SCALE * scale
        rect = self.around(box, scale)
        key = (rect.width, rect.height, round(scale, 4))
        got = self._cache.get(key)
        if got is None:
            got = self._sliced(scale).render(rect.width, rect.height)
            self._cache[key] = got
        surface.blit(got, rect.topleft)
        return rect

    def clear_cache(self):
        self._slices.clear()
        self._cache.clear()


def for_app(app):
    """The one `ResearchFrame` an App has, built on first use.

    ONE CONSTRUCTION SITE, which is the shape `core/hestrings.for_app`
    established when `HStrings` turned out to be built at four sites
    with three lifetimes (decision D17, work order 159). Both research
    screens wear the same cut; a second instance would be a second
    scaled copy of a 1537x950 image per screen.
    """
    got = getattr(app, "research_frame", None)
    if got is None:
        got = ResearchFrame(getattr(app, "res", None))
        app.research_frame = got
    return got
