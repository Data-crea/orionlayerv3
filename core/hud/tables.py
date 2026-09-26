"""The HUD's table blocks: header band, row, selected row, scroll bar.

Split out of `core/hud/blocks.py` by work order 172 (the line
guideline); `blocks` re-exports every name, so callers are unchanged.
Measured off Data's colony mockup (`mockup_colony` in style.json).
"""
import pygame

from core.hud import glass
from core.hud import style as hudstyle


def _px(ref_len, scale, floor=1.0):
    return max(floor, ref_len * scale)


def separator(surface, x0, x1, y, scale):
    from core.hud import blocks
    blocks.separator(surface, x0, x1, y, scale)



def table_header(surface, rect, scale):
    """The header band of a table, and the line under it."""
    st = hudstyle.get()
    r = pygame.Rect(rect)
    # GLASS since work order 174: the header band is dense glass with
    # its colour over it, not a flat near-black band.
    glass.draw(surface, r, dense=True, shade=st.colour("mockup_colony.header"),
               shade_alpha=float(st.get("glass.header_shade")))
    separator(surface, r.x, r.right, r.bottom - 1, scale)


def table_row(surface, rect, scale, index, selected=False):
    """One table row: striped by LIST index, the selected row filled and
    rimmed as the colony mockup draws it, a thin line under every row."""
    st = hudstyle.get()
    r = pygame.Rect(rect)
    if selected:
        glass.draw(surface, r, dense=True,
                   shade=st.colour("mockup_colony.selected"),
                   shade_alpha=float(st.get("glass.selected_shade")))
        edge = st.colour("mockup_colony.selected_edge")
        w = max(1, round(_px(st.get("panel.edge_width"), scale) * 0.6))
        pygame.draw.rect(surface, edge, r, w,
                         border_radius=max(2, int(4 * scale)))
        return
    key = "mockup_colony.row_a" if index % 2 == 0 else "mockup_colony.row_b"
    glass.draw(surface, r, dense=True, shade=st.colour(key),
               shade_alpha=float(st.get("glass.row_shade")))
    pygame.draw.line(surface, st.colour("mockup_colony.row_line"),
                     (r.x, r.bottom - 1), (r.right - 1, r.bottom - 1))


def table_text_colour(kind="row"):
    """The table's words: "header" or "row" (colony mockup)."""
    return hudstyle.get().colour(f"mockup_colony.text_{kind}")


def scrollbar(surface, rect, scale, first=0, visible=1, total=1):
    """A scroll track and its thumb; the thumb covers visible/total of
    the track, starting at first/total, and is `scrollbar.width_frac`
    of the column wide, centred."""
    st = hudstyle.get()
    r = pygame.Rect(rect)
    tw = max(2, int(r.w * st.get("scrollbar.width_frac")))
    track = pygame.Rect(r.centerx - tw // 2, r.y, tw, r.h)
    rad = tw // 2
    pygame.draw.rect(surface, st.colour("mockup_colony.scroll_track"),
                     track, border_radius=rad)
    total = max(total, 1)
    frac = min(1.0, visible / total)
    th = max(tw, int(r.h * frac))
    ty = r.y + int((r.h - th) * (first / max(1, total - visible))
                   if total > visible else 0)
    pygame.draw.rect(surface, st.colour("mockup_colony.scroll_thumb"),
                     (track.x, ty, tw, th), border_radius=rad)
