"""The Races screen's quiet polish — drawn in code, no picture.

HD EXTENSION `races_polish` (work order 422, Data's design list of 22 Nov
2026): the information fields under the treaty field (the spy strip and
the agents' strip) as a very dark blue-black with a barely visible
horizontal gradient and a blue-grey inner line; the BONUSES header band;
and small gold glyphs on the four action buttons and RETURN. All of it
stands where the original's boxes and buttons stand; nothing moves, no
content changes.
"""
import pygame

from core.hud import blocks as hud

#: The information field: left to right, nearly the same blue-black, laid
#: TRANSLUCENT over the shared field (`hud.field`) so the panel's glass
#: still shows through (check 006f) and the field stays the one the
#: original paints there (check 090ea).
FIELD_ALPHA = 120
FIELD_LEFT = (9, 14, 24)
FIELD_RIGHT = (14, 22, 36)
FIELD_LINE = (58, 78, 104, 150)
#: The BONUSES header band and its hairline.
HEADER_FILL = (12, 20, 34, 90)
HEADER_LINE = (176, 140, 70)
#: Glyph gold, dimmed on a disabled button.
GOLD = (214, 172, 84)

_fields = {}


def info_field(surface, rect, scale, inset=0):
    """The shared field with a quiet tint over it: a minimal horizontal
    gradient and a blue-grey line just inside the edge. Cached by size."""
    rect = pygame.Rect(rect)
    if rect.w < 4 or rect.h < 4:
        return
    hud.field(surface, rect, scale)
    # the tint stays `inset` px inside the field: where the field reaches a
    # panel's border, the border is not covered
    rect = rect.inflate(-2 * inset, -2 * inset)
    if rect.w < 4 or rect.h < 4:
        return
    key = (rect.w, rect.h, max(1, int(round(scale))))
    pic = _fields.get(key)
    if pic is None:
        if len(_fields) > 32:
            _fields.clear()
        pic = pygame.Surface(rect.size, pygame.SRCALPHA)
        for x in range(rect.w):
            t = x / max(1, rect.w - 1)
            pic.fill(tuple(round(a + (b - a) * t)
                           for a, b in zip(FIELD_LEFT, FIELD_RIGHT))
                     + (FIELD_ALPHA,), (x, 0, 1, rect.h))
        w = max(1, int(round(scale)))
        # LOOK EXCEPTION picture: the field's inner line is a hairline of the
        # tint, not a panel or a box of its own
        pygame.draw.rect(pic, FIELD_LINE, pic.get_rect().inflate(-2 * w,
                                                                 -2 * w), w)
        _fields[key] = pic
    surface.blit(pic, rect.topleft)


def header(surface, rect, scale):
    """The BONUSES header: a darker band over the panel's top rows with a
    gold hairline under it. `rect` is the band's window rectangle."""
    rect = pygame.Rect(rect)
    band = pygame.Surface(rect.size, pygame.SRCALPHA)
    band.fill(HEADER_FILL)
    surface.blit(band, rect.topleft)
    pygame.draw.line(surface, HEADER_LINE, (rect.x, rect.bottom - 1),
                     (rect.right - 1, rect.bottom - 1),
                     max(1, int(round(scale))))


def glyph(surface, name, rect, disabled=False):
    """A small gold symbol inside `rect` (a square): audience (a figure),
    report (a sheet), war (crossed blades), ignore (a ring with a bar),
    back (an arrow to the left)."""
    rect = pygame.Rect(rect)
    c = tuple(v // 2 for v in GOLD) if disabled else GOLD
    w = max(1, rect.h // 9)
    x, y, s = rect.x, rect.y, min(rect.w, rect.h)
    if name == "audience":
        pygame.draw.circle(surface, c, (x + s // 2, y + s * 3 // 10),
                           max(1, s // 5), w)
        pygame.draw.arc(surface, c, (x + s // 8, y + s // 2, s * 3 // 4,
                                     s * 3 // 4), 0.2, 2.94, w)
    elif name == "report":
        # LOOK EXCEPTION picture: a sheet's outline inside a 16 px symbol
        pygame.draw.rect(surface, c, (x + s // 5, y + s // 12, s * 3 // 5,
                                      s * 5 // 6), w)
        for k in (3, 5, 7):
            yy = y + s * k // 11 + s // 12
            pygame.draw.line(surface, c, (x + s * 3 // 10, yy),
                             (x + s * 7 // 10, yy), max(1, w // 2 + 1))
    elif name == "war":
        pygame.draw.line(surface, c, (x + s // 6, y + s // 6),
                         (x + s * 5 // 6, y + s * 5 // 6), w + 1)
        pygame.draw.line(surface, c, (x + s * 5 // 6, y + s // 6),
                         (x + s // 6, y + s * 5 // 6), w + 1)
    elif name == "ignore":
        pygame.draw.circle(surface, c, (x + s // 2, y + s // 2),
                           s * 5 // 12, w)
        pygame.draw.line(surface, c, (x + s // 4, y + s * 3 // 4),
                         (x + s * 3 // 4, y + s // 4), w)
    elif name == "back":
        mid = y + s // 2
        pygame.draw.line(surface, c, (x + s // 6, mid),
                         (x + s * 5 // 6, mid), w + 1)
        # LOOK EXCEPTION picture: the arrow's head, a symbol not a box
        pygame.draw.polygon(surface, c, [(x + s // 6, mid),
                                         (x + s * 5 // 12, mid - s // 4),
                                         (x + s * 5 // 12, mid + s // 4)])
