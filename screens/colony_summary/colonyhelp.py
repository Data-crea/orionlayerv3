"""The colony summary's own right-click help region kinds — brief 98.

The walk, the popup and the swallow are the shared ones
(`core/screenhelp.py`, `core/helppopup.py`); the regions are
`screens/colony_summary/help.json`, transcribed from
`ERICHELP::_colony_summary_screen_help_list` (erichelp.cpp:65). What
lives here is only the geometry the shared `box` / `screen` kinds
cannot name — the same seam New Game's `slot` and the galaxy map's
`title` use (`ScreenBase.help_extra_rect`). Its own module rather than
the end of `screen.py`, which decision 6 holds under 300 code lines.

`column` is one list column AND its heading plate: the original's
column rectangles run from y 1 to 343, heading included, and HD draws
the heading in the separate `header` cutout, so the region is the
`col_<key>` box unioned with that column's plate from
`colonyheader.plate_rects` — the plate the heading is drawn on
(decision 5).

`scroll` is the up arrow, the track or the down arrow, from
`colonyscroll.arrows` / `track`, the rects the scroll column draws and
clicks with.

Anything else — `no_counterpart`, help 520's Buy column, which is not
a column in HD — resolves to nothing.
"""
import pygame

from . import colonyheader, colonyscroll, colonytrack


def extra_rect(screen, spec):
    """Screen rect for a colony-only region kind, or None."""
    key = spec.get("column")
    if key:
        box = screen.box_rect(f"col_{key}")
        if not box:
            return None
        rect = pygame.Rect(*screen.layout.rect(box))
        header = screen.box_rect("header")
        if header:
            area, cfg, _scale, _n = screen._list_view()
            for plate_key, plate in colonyheader.plate_rects(
                    screen.layout.rect(header),
                    colonytrack.columns(area, cfg), screen.layout.scale):
                if plate_key == key:
                    rect = rect.union(plate)
        return rect
    where = spec.get("scroll")
    if where:
        area, cfg, scale, _n = screen._list_view()
        if where == "track":
            return colonyscroll.track(area, cfg, scale)
        up, down = colonyscroll.arrows(area, cfg, scale)
        return {"up": up, "down": down}.get(where)
    return None
