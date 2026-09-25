"""The GAME menu's frame: one fixed image around the popup body.

Decision 69. `assets/frame.png` is Data's artwork, committed, loaded
through the resource roots (decision 16) and plain-scaled — no 9-slice,
no master, the colony screen's way (decision 55). It replaces the body's
`thin_border` outline and nothing else; the buttons, lists and message
panels keep their skins.

**HD DEVIATION — WHERE IT SITS IS THE GALAXY MAP'S OPENING** (Data, work
order 125, superseding the anchor of work order 122). The original has no
frame: `Add_Game_Popup_Fields_` puts its frameless popup at a fixed
(0x90, 0x19), and 122 carried that position over as a share of the map
window, which put this frame's metal across the GAME field above and the
nav bar below. Now the frame is FITTED TO THE MAP CUTOUT: `map_area` of the
galaxy map's `boxes.json` (as `tools/frame_holes.py --write` wrote it, for
the window's resolution list), the image's height equal to the cutout's,
aspect kept, centred on it — nothing outside the cutout, and no extra
inset: the image's own transparent margins (20 image rows at the top, 29 at
the bottom, 34 columns each side) keep the metal about 12 and 18 reference
px clear of the cutout's edges already. The menu follows: the body is the
largest box of the original's 628:850 that fits the opening less `BLEED`,
centred in it, and EVERY box of the overlay is seated by the same move and
ONE factor (`seat`), fonts included (`content_scale`) — the original's
geometry, smaller. `boxes.json` keeps the unscaled design geometry; an F5
save writes a dragged box back through the inverse (`Box.to_file`), so the
file never takes the seated rects.

**THE OPENING IS TRANSPARENT, SO THE MENU FILLS ITS OWN GROUND** — opaque,
from the shared cockpit texture, and no dimmed backdrop (fundament, "A
trick that works on one screen is not a rule": a palette-indexed engine
cannot dim what is under a popup). The fill is the opening's bounding
box; the chamfers outside the octagon are metal and cover its corners.

**HD DEVIATION — the confirmation and the warning are scaled INTO the
opening** (Data, work order 123). In the original both are wider than the
popup — CONFIRM.LBX's box is 310 native px at (161, 117), WARNING.LBX's 331
at (154, 144), against the popup's 279 at (144, 25) — and overhang its right
edge, which over this frame put them across the metal. HD scales each group
by ONE factor, the body's width over the panel's (0.900 and 0.843), rects
and font sizes alike, centres it on the body and keeps its vertical centre
where the original has it; the layout is the original's, smaller. The
factors are applied in `boxes.json` (`layout.json` `_dialog_fit_note`), and
the smoke test holds every dialog to the opening's alpha.
"""
import pygame

from core.hud import blocks as hud

#: Reference px the opening reaches past the body box on each side, so
#: the frame's anti-aliased rim lands on the fill and not on the body's
#: edge. The same 2 as the cutout screens' bleed.
BLEED = 2


def spec(screen):
    return screen.words.get("frame") or {}


def _map_cutout(screen):
    """`map_area` of the galaxy map's boxes.json for this window, reference px."""
    from core.box import load_boxes
    path = screen.app.res.screen_file("galaxy_map", "boxes.json")
    for box in load_boxes(path, screen.app.win_w, screen.app.win_h):
        if box.name == "map_area" and box.ref_rect is not None:
            return box.ref_rect
    return None


#: Reference px kept clear between the popup and the map's free area —
#: what the old frame image's own transparent margins gave (12 to 18),
#: and the panel's glow needs room.
MARGIN = 14


def free_area(screen):
    """The map cutout less the HUD's title plate, reference px: the part
    of the map nothing of the HUD covers (decision 71). The plate hangs
    from the top edge (`core.hud.blocks.title_plate_rect`), so only a
    cutout that reaches under it loses its top band."""
    cut = _map_cutout(screen)
    if cut is None:
        return None
    from core.hud import blocks as hud
    plate, _text = hud.title_plate_rect(0, 0, 1.0)
    mx, my, mw, mh = cut
    top = max(my, plate.bottom)
    return (mx, top, mw, my + mh - top)


def placement(screen, design_body):
    """{frame, opening, body: (x, y, w, h) in reference px, factor} for the
    body box as `boxes.json` has it, or None without a map cutout.

    **SINCE DECISION 71 THERE IS NO FRAME IMAGE TO FIT** (work order 169):
    the body is the HUD popup block, and it is the largest box of the
    design body's own aspect (the original's 628:850) that fits the map's
    free area less `MARGIN` and `BLEED`, centred in it. `frame` and
    `opening` are kept as keys, both the body plus `BLEED`, so every
    reader of the placement still finds the rect it asks for."""
    area = free_area(screen)
    if area is None:
        return None
    ax, ay, aw, ah = area
    ax, ay, aw, ah = ax + MARGIN, ay + MARGIN, aw - 2 * MARGIN, ah - 2 * MARGIN
    _, _, dw, dh = design_body
    factor = min((aw - 2 * BLEED) / dw, (ah - 2 * BLEED) / dh)
    bw, bh = dw * factor, dh * factor
    bx, by = ax + (aw - bw) / 2, ay + (ah - bh) / 2
    opening = (bx - BLEED, by - BLEED, bw + 2 * BLEED, bh + 2 * BLEED)
    return {"frame": opening, "opening": opening,
            "body": (bx, by, bw, bh), "factor": factor}


def seat(screen):
    """Move and scale every box of the overlay into the placement; the
    file's rects stay the design geometry (`Box.to_file` inverts)."""
    body = next((b for b in screen.boxes if b.name == "body"), None)
    screen.content_scale = 1.0
    screen.frame_place = None
    if body is None or body.ref_rect is None:
        return
    place = placement(screen, body.ref_rect)
    if place is None:
        return
    dx, dy = body.ref_rect[0], body.ref_rect[1]
    nx, ny = place["body"][0], place["body"][1]
    f = place["factor"]

    def forward(r):
        x, y, w, h = r
        return (nx + (x - dx) * f, ny + (y - dy) * f, w * f, h * f)

    def inverse(r):
        x, y, w, h = r
        return [round(dx + (x - nx) / f), round(dy + (y - ny) / f),
                round(w / f), round(h / f)]

    for box in screen.boxes:
        if box.ref_rect is not None:
            box.ref_rect = forward(box.ref_rect)
            box.to_file = inverse
    screen.content_scale = f
    screen.frame_place = place


def rects(screen, body=None):
    """(frame rect, opening rect) in window px, from the seated placement."""
    place = getattr(screen, "frame_place", None)
    if place is None:
        return None, None
    lay = screen.layout
    fx, fy, fw, fh = place["frame"]
    ox, oy, ow, oh = place["opening"]
    frame = pygame.Rect(round(fx * lay.scale + lay.offset_x),
                        round(fy * lay.scale + lay.offset_y),
                        round(fw * lay.scale), round(fh * lay.scale))
    x0 = ox * lay.scale + lay.offset_x
    y0 = oy * lay.scale + lay.offset_y
    opening = pygame.Rect(int(x0), int(y0), int(ow * lay.scale + 0.999),
                          int(oh * lay.scale + 0.999))
    return frame, opening


def _image(screen, size):
    cache = getattr(screen, "_frame_cache", None)
    if cache is None or cache[0] != size:
        cache = screen._frame_cache = (size, None)
        path = screen.asset_path("assets", spec(screen).get("image",
                                                            "frame.png"))
        if path:
            src = pygame.image.load(path).convert_alpha()
            cache = screen._frame_cache = (
                size, pygame.transform.smoothscale(src, size))
    return cache[1]


def draw(screen, surface, body):
    """The popup block over the opening — decision 71: the GAME menu and
    every dialog in it wear the HUD popup. False without a placement."""
    frame, opening = rects(screen, body)
    if frame is None:
        return False
    hud.popup(surface, opening, screen.layout.scale)
    return True
