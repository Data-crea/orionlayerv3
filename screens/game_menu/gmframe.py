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


def placement(screen, design_body):
    """{frame, opening, body: (x, y, w, h) in reference px, factor} for the
    body box as `boxes.json` has it, or None without a map cutout."""
    cfg = spec(screen)
    cut = _map_cutout(screen)
    if not cfg.get("opening") or cut is None:
        return None
    img_w, img_h = cfg["image_size"]
    ox, oy, ow, oh = cfg["opening"]
    mx, my, mw, mh = cut
    s = mh / img_h
    fx, fy = mx + (mw - img_w * s) / 2, my
    opx, opy, opw, oph = fx + ox * s, fy + oy * s, ow * s, oh * s
    _, _, dw, dh = design_body
    factor = min((opw - 2 * BLEED) / dw, (oph - 2 * BLEED) / dh)
    bw, bh = dw * factor, dh * factor
    return {"frame": (fx, fy, img_w * s, mh),
            "opening": (opx, opy, opw, oph),
            "body": (opx + (opw - bw) / 2, opy + (oph - bh) / 2, bw, bh),
            "factor": factor}


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
    """Fill the opening, then the frame over it. False without artwork."""
    if not spec(screen).get("opening"):
        return False
    frame, opening = rects(screen, body)
    if frame is None:
        return False
    image = _image(screen, frame.size)
    if image is None:
        return False
    surface.blit(screen.help_backdrop(), opening, opening)
    surface.blit(image, frame.topleft)
    return True
