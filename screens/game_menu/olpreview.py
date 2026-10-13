"""The live preview on the APPEARANCE tab — work order 251.

Data: "Hier würde ich auch die Live-Vorschau mit dem Planeten und dem
Nebel platzieren." His picture of a window onto space (the planet, its
moon, the nebula) is the ground; over it stand the HUD's own blocks — a
panel with a heading, a field, a chosen field and a small button — drawn
by `core.hud` exactly as every screen draws them. So whatever the tab's
rows set shows here at once: the frame colour and tone on the edges, the
glass (the nebula through the panel, or the opaque fill), the box fill and
its tone. Nothing here colours a pixel itself but the picture.

THE PICTURE is in the base pack (decision 95,
`assets/shared/hud/settings_preview.png`), resolved through the resource
roots like every picture, so a mod may replace it. Data's picture carries
a painted metal frame; only its opening is shown (`OPENING`), and the
HUD's own outline goes round it in the frame colour. Absent, the preview
draws the blocks on the window's own ground (decision 38).
"""
import pygame

from core import resources
from core.hud import blocks as hud
from core.hud import text as hudtext

PICTURE = "assets/shared/hud/settings_preview.png"
#: The painted frame's opening in Data's picture (2051 x 767), read off
#: the picture by eye on 13 October 2026 and checked by its crop: inside
#: the metal and clear of the corner lamps. A convention about this one
#: picture, not a measurement of the game (P611): a replacement without a
#: frame is shown from this box too.
OPENING = (165, 115, 1870, 612)

_cache = {}


def _picture(size):
    """The opening, scaled to cover `size` (cropped to its aspect), once
    per size."""
    if size in _cache:
        return _cache[size]
    path = resources.res.resolve(PICTURE)
    img = None
    if path:
        src = pygame.image.load(path)
        x0, y0, x1, y1 = OPENING
        if src.get_width() >= x1 and src.get_height() >= y1:
            src = src.subsurface(pygame.Rect(x0, y0, x1 - x0, y1 - y0))
        w, h = size
        k = max(w / src.get_width(), h / src.get_height())
        big = pygame.transform.smoothscale(
            src, (max(w, int(src.get_width() * k)),
                  max(h, int(src.get_height() * k))))
        img = big.subsurface(pygame.Rect((big.get_width() - w) // 2,
                                         (big.get_height() - h) // 2, w,
                                         h)).copy()
    _cache.clear()
    _cache[size] = img
    return img


def render(screen, surface, rect):
    scale = screen.layout.scale
    img = _picture(rect.size)
    if img is not None:
        surface.blit(img, rect.topleft)
    hud.outline(surface, rect, scale)
    # THE SAMPLE SEES THE PREVIEW'S PICTURE: drawn over it, and the glass
    # shows what is drawn under a box (work order 253; 252 had to hand it
    # the picture while the glass saw only the screen's background).
    _sample(screen, surface, rect, scale)


def _sample(screen, surface, rect, scale):
    # the sample panel over the nebula's side, where glass shows most
    words = screen.words.get("words", {}).get("orionlayer_window", {})
    pw, ph = int(rect.w * 0.40), int(rect.h * 0.78)
    panel = pygame.Rect(rect.right - pw - rect.h // 10,
                        rect.y + (rect.h - ph) // 2, pw, ph)
    hud.panel(surface, panel, scale)
    inner = hud.panel_inner(panel, scale).inflate(-panel.w // 12,
                                                   -panel.h // 10)
    lh = inner.h // 4
    size = max(8, int(lh * 0.55))
    head = hudtext.render(screen.style, words.get("sample_title",
                                                  "Panel").upper(),
                          "title", lh)
    hudtext.blit(surface, head, pygame.Rect(inner.x, inner.y, inner.w, lh),
                 align="left")
    gap = max(2, lh // 8)
    f1 = pygame.Rect(inner.x, inner.y + lh + gap, inner.w, lh - gap)
    f2 = pygame.Rect(inner.x, f1.bottom + gap, inner.w, lh - gap)
    hud.field(surface, f1, scale)
    hud.field(surface, f2, scale, on=True)
    col = hudtext.colour("button")
    for r, key, default in ((f1, "sample_field", "Field"),
                            (f2, "sample_selected", "Selected")):
        s = screen.style.render_text(words.get(key, default), size, col)
        hudtext.blit(surface, s, r.inflate(-r.h // 2, 0), align="left")
    b = pygame.Rect(inner.x, f2.bottom + gap * 2, inner.w // 2,
                    inner.bottom - f2.bottom - gap * 2)
    hud.small_button(surface, b, scale, "normal",
                     words.get("sample_button", "Button"), screen.style)
