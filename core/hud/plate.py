"""The gold plate: Data's galaxy map frame, its right-hand panel, cut into
corners and edge strips and stretched to any rectangle.

**HD EXTENSION `plate_from_galaxy_frame`** (Data, 20 November 2026; the
audience first, then the colony summary). The picture is
`assets/shared/hud/galaxy_frame.png` (through `core.hud.art`, the mod folder's own wins); the pieces are cut from its panel at (2078, 132)-(2540,
1104) of the 2560 x 1440 file, scaled with the file's width, turned to gold
(luminance -> brown..gold, the alpha kept) and then turned with the player's
frame colour (`core.hud.tint`, Game Settings) like every part of the HUD.
Without the picture `plate` returns False and the caller draws what it drew
before. Only the LOOK; no rectangle, hit or text moves.
"""
import pygame

#: the panel in the 2560-wide file: left, top, right, bottom, corner size
SRC = (2078, 132, 2540, 1104, 72)
#: the hue the pieces are drawn in (degrees); the tint turns from here
GOLD_HUE = 41
FILL = (10, 8, 8)

_state = {"pieces": {}, "key": None, "held": {}}


def _pieces(mode):
    """The cut pieces; `mode` "gold" turns the picture to the plate's gold,
    "hud" keeps it as painted (it is then turned with the frame colour like
    the galaxy map's own frame)."""
    if mode in _state["pieces"]:
        return _state["pieces"][mode]
    out = None
    from core.hud import art
    pic = art.raw(art.GALAXY_FRAME)
    if pic is not None and pic.get_width() >= 640:
        import numpy as np
        k = pic.get_width() / 2560
        x0, y0, x1, y1, c = (round(v * k) for v in SRC)
        if mode == "gold":
            raw = pygame.surfarray.array3d(pic).astype(float) / 255
            lum = np.clip(raw @ np.array([.30, .59, .11]) * 1.6, 0,
                          1)[..., None]
            lo, mid, hi = (np.array(v) for v in ((.10, .06, .03),
                                                 (1., .76, .35),
                                                 (1., .93, .70)))
            rgb = np.where(lum > .7, mid + (hi - mid) * ((lum - .7) / .3),
                           lo + (mid - lo) * lum)
            gold = pygame.Surface(pic.get_size(), pygame.SRCALPHA)
            pygame.surfarray.pixels3d(gold)[:] = (rgb * 255).astype("uint8")
            pygame.surfarray.pixels_alpha(gold)[:] = \
                pygame.surfarray.pixels_alpha(pic)
        else:
            gold = pic
        sub = lambda a, b, w, h: gold.subsurface(  # noqa: E731
            pygame.Rect(a, b, w, h)).copy()
        flip = lambda s_: pygame.transform.flip(s_, False, True)  # noqa: E731
        tl, tr = sub(x0, y0, c, c), sub(x1 - c, y0, c, c)
        top = sub(x0 + c, y0, round(100 * k), c)
        out = dict(tl=tl, tr=tr, bl=flip(tl), br=flip(tr), top=top,
                   bot=flip(top),
                   left=sub(x0, y0 + c + round(170 * k), c, round(90 * k)),
                   right=sub(x1 - c, y0 + c + round(170 * k), c,
                             round(90 * k)))
    _state["pieces"][mode] = out
    return out


def _turned(piece, name, mode="gold"):
    from core.hud import tint
    if tint.is_default():
        return piece
    import numpy as np
    out = piece.copy()
    px = pygame.surfarray.pixels3d(out)
    if mode == "hud":
        # as the galaxy map's frame: the whole picture turns, its orange
        # lamps stay as painted (`core.hud.art._tinted`)
        px[...] = tint.rotate_pixels(px, keep=tint.lamp_mask(px))
        del px
        return out
    delta = float(tint.hue()) - GOLD_HUE if tint.hue() is not None else 0.0
    px[:] = tint.transform_array(np.array(px), delta, tint.sat(),
                                 tint.bright(), False, True)
    del px
    return out


def corner(rect_h, size=None):
    """The corner's size in px: `size` when the caller sets it (a table
    whose content runs near the edge wants a thin rim), else a tenth of the
    height."""
    if size is not None:
        return max(8, min(int(size), rect_h // 3))
    return max(16, min(round(rect_h * 0.1), rect_h // 3, 56))


def inset_rect(rect, size=None):
    """The dark middle of a plate at `rect`: inside the rim, which is
    `inset` px deep (the part a caller may fill or draw into)."""
    i = int(corner(rect.h, size) * .52)
    return rect.inflate(-2 * i, -2 * i)


def plate(surface, rect, fill=FILL, size=None, mode="gold"):
    """Draw the plate at `rect`; False when the picture is missing. With
    `fill=None` only the rim is drawn, over whatever stands there."""
    pcs = _pieces(mode)
    if pcs is None or rect.w < 40 or rect.h < 40:
        return False
    from core.hud import tint
    key = (tint.hue(), tint.sat(), tint.bright())
    if _state["key"] != key:
        _state.update(key=key, held={})
    c = corner(rect.h, size)
    w, h = rect.size
    held = _state["held"]
    ck = (mode, c, w, h, None if fill is None else tuple(fill))
    if ck not in held:
        layer = pygame.Surface(rect.size, pygame.SRCALPHA)
        if fill is not None:
            pygame.draw.rect(layer, tuple(fill[:3]) + (245,),
                             (3, 3, w - 6, h - 6), border_radius=int(c * .45))
        inset = int(c * .52)

        def scaled(n, size):
            return pygame.transform.smoothscale(
                _turned(pcs[n], n, mode), (max(1, size[0]), max(1, size[1])))
        layer.blit(scaled("top", (w - 2 * c, c)), (c, 0))
        layer.blit(scaled("bot", (w - 2 * c, c)), (c, h - c))
        layer.blit(scaled("left", (c, h - 2 * c)), (0, c))
        layer.blit(scaled("right", (c, h - 2 * c)), (w - c, c))
        for n, pos in (("tl", (0, 0)), ("tr", (w - c, 0)), ("bl", (0, h - c)),
                       ("br", (w - c, h - c))):
            layer.blit(scaled(n, (c, c)), pos)
        if fill is not None:
            pygame.draw.rect(layer, tuple(fill[:3]) + (255,),
                             (inset, inset, w - 2 * inset, h - 2 * inset),
                             border_radius=max(2, int(c * .2)))
        if len(held) > 64:
            held.clear()
        held[ck] = layer
    surface.blit(held[ck], rect.topleft)
    return True


def plate_available():
    """True when the galaxy frame picture can be cut (a caller that wears
    the plate's look elsewhere asks first)."""
    return _pieces("hud") is not None
