"""The GAME menu's frame: one fixed image around the popup body.

Decision 69. `assets/frame.png` is Data's artwork, committed, loaded
through the resource roots (decision 16) and plain-scaled — no 9-slice,
no master, the colony screen's way (decision 55). It replaces the body's
`thin_border` outline and nothing else; the buttons, lists and message
panels keep their skins.

**WHERE IT SITS IS THE BODY BOX, AND THE BODY BOX IS THE ORIGINAL'S.**
The artwork has one octagonal opening, `layout.json` `frame.opening` in
image pixels (the smoke test holds it to `tools/frame_holes.find_holes`).
The image is scaled with ONE factor — aspect kept — so that the opening
covers the body box grown by `BLEED` on every side, and centred on it.
Content is not placed against the frame; the frame is placed around the
content.

**THE OPENING IS TRANSPARENT, SO THE MENU FILLS ITS OWN GROUND** — opaque,
from the shared cockpit texture, and no dimmed backdrop (fundament, "A
trick that works on one screen is not a rule": a palette-indexed engine
cannot dim what is under a popup). The fill is the opening's bounding
box; the chamfers outside the octagon are metal and cover its corners.
"""
import pygame

#: Reference px the opening reaches past the body box on each side, so
#: the frame's anti-aliased rim lands on the fill and not on the body's
#: edge. The same 2 as the cutout screens' bleed.
BLEED = 2


def spec(screen):
    return screen.words.get("frame") or {}


def rects(screen, body):
    """(frame rect, opening rect) in window px around the body rect."""
    cfg = spec(screen)
    img_w, img_h = cfg["image_size"]
    ox, oy, ow, oh = cfg["opening"]
    bleed = BLEED * screen.layout.scale
    want_w, want_h = body.w + 2 * bleed, body.h + 2 * bleed
    s = max(want_w / ow, want_h / oh)
    open_w, open_h = ow * s, oh * s
    open_x = body.centerx - open_w / 2
    open_y = body.centery - open_h / 2
    frame = pygame.Rect(round(open_x - ox * s), round(open_y - oy * s),
                        round(img_w * s), round(img_h * s))
    opening = pygame.Rect(int(open_x), int(open_y),
                          int(open_w + 0.999), int(open_h + 0.999))
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
    image = _image(screen, frame.size)
    if image is None:
        return False
    surface.blit(screen.help_backdrop(), opening, opening)
    surface.blit(image, frame.topleft)
    return True
