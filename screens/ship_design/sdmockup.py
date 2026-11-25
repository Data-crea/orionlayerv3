"""The Ship Designer as Data's mockup draws it — HD EXTENSION
`designer_mockup` (work order 433, Data's mockup of 25 November 2026).

DRAWING ONLY, AT THE ORIGINAL'S OWN POSITIONS: every field, every hit and
every number stays where `sdgeom` puts it, so the engine sees exactly the
clicks it saw before. The mockup's look is added over the same geometry:

  * the hull column in the frame colour (replaces `hull_blue`, Data's choice
    of 2 November 2026): the chosen hull on a bar, a picture of the hull's
    class in front of each word — the class's own first picture
    (`design.cpp:990-1007`: eight pictures a size, `8 * size`), the painted
    ship where the mod folder holds one (`core.shippicture`), else the game's
    sprite
  * a HUD glyph in front of the weapon table's and the specials' headers,
    a faint rule under each row of both
  * a painted scene in the drive panel's and the description panel's right
    part (the player's `popups/design_scene_*.png`, `core.buildicons`)
  * a glyph in front of the three buttons' words

INVENTION `designer_glyphs`: which glyph stands for which column is ours;
the original prints words only. The mockup's per-weapon and per-special
pictures and its pencil on the name are NOT drawn (OMISSION
`designer_row_pictures`: neither the game nor the wire carries a picture of
a weapon or a special, and the HUD has no pencil).
"""
# HD EXTENSION `designer_mockup`: see the docstring.
import pygame

from core import buildicons, palette, shippicture, usermod
from core import nativedraw as nd
from core.hud import art as hudart
from core.hud import blocks as hud
from core.hud import hover as hud_hover
from core.hud import text as hudtext

from . import sdart

#: The glyph in front of each weapon-table header, in `geom.WEAPON_HEADS`
#: order (Weapon Type, Damage, Arc, Cost, Space, Modifications), and of the
#: specials' two (Special System, Description).
WEAPON_GLYPHS = (None, "swords", "range", "coin", "all", "gear")
SPECIAL_GLYPHS = ("star", "list")
BUTTON_GLYPHS = {"clear": "trash", "cancel": "close", "build": "hammer"}

_icons = {}
_scenes = {}


def accent():
    return hudtext.colour("label")


def glyph(screen, key, native_x, native_y, h):
    """A glyph `h` tall ending just left of the word at a native anchor."""
    if key is None:
        return
    ic = hudart.icon(key, h)
    if ic is None:
        return None
    px, py = nd.point(screen.layout, native_x, native_y)
    return ic, (px - ic.get_width() - max(3, h // 5), py)


def blit_glyph(surface, screen, key, native_x, native_y, h):
    got = glyph(screen, key, native_x, native_y, h)
    if got is not None:
        surface.blit(*got)


def _cut(pic, h):
    r = pic.get_bounding_rect(min_alpha=40)
    if not (r.w and r.h):
        return None
    return pygame.transform.smoothscale(
        pic.subsurface(r), (max(1, round(r.w * h / r.h)), h))


def hull_icon(screen, view, size, h):
    """The first picture of a hull class (`8 * size`), `h` tall, or None."""
    if view.colour is None:
        return None
    us = getattr(screen.app, "user_settings", None)
    from core import livery
    # what `shippicture.fitted` keys on too: the livery, the detail, the mod
    # folder and the palette
    key = (size, h, view.colour, id(screen.app),
           livery.from_settings(us, view.colour).key(),
           us.get("painted_detail") if us is not None else None,
           shippicture.usermod_generation(), palette.generation(),
           id(usermod._state["index"]))
    if key in _icons:
        return _icons[key]
    if len(_icons) > 60:
        _icons.clear()
    pic = 8 * size
    made = shippicture.fitted(screen.app, view.colour, pic,
                              pygame.Rect(0, 0, h * 4, h * 2),
                              own=view.colour, size=size)
    got = _cut(made[0], h) if made is not None else None
    if got is None:
        sprite = sdart.load().ship(pic, view.colour)
        got = _cut(sprite, h) if sprite is not None else None
    if got is not None:
        _icons[key] = got
    return got


def bar(surface, rect):
    """The chosen row's bar: a dark accent fill under a lit outline."""
    col = accent()
    # LOOK EXCEPTION marking: the chosen hull's bar in the frame colour's accent (Data's mockup of 25 November 2026)
    fill = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(fill, (*col, 58), fill.get_rect(),
                     border_radius=max(3, rect.h // 5))
    surface.blit(fill, rect.topleft)
    pygame.draw.rect(surface, col, rect, width=2,
                     border_radius=max(3, rect.h // 5))


def hull_row(surface, screen, view, names, size, rect, chosen, offered):
    """One hull row: bar if chosen, its class picture, its word."""
    label = names.part("hulls", size) or ""
    if chosen:
        bar(surface, rect.inflate(-6, -2))
    else:
        state = hud_hover.pointer_state(rect) if offered else "disabled"
        if state != "normal":
            hud.small_button(surface, rect, screen.layout.scale, state)
    # one column for every row: the rows differ by a native pixel or two
    unit = nd.rect(screen.layout, (0, 0, 0, 15)).h
    h = max(10, int(unit * 0.78))
    icon = hull_icon(screen, view, size, h)
    x = rect.x + max(8, unit // 3)
    if icon is not None:
        surface.blit(icon, (x, rect.centery - icon.get_height() // 2))
    x += int(unit * 2.7)
    col = hudtext.colour("title") if chosen else hudtext.colour("value")
    if not offered and not chosen:
        col = tuple(c // 2 for c in col[:3])
    nd.blit_text(surface, screen.style, label, x,
                 rect.centery - int(unit * 0.30), rect.right - x - 6,
                 max(nd.MIN_FONT, int(unit * 0.60)), col[:3])


def rule(surface, screen, native_y, panel):
    """A faint rule across a table's panel at a native y."""
    r = nd.rect(screen.layout, panel)
    y = nd.point(screen.layout, 0, native_y)[1]
    col = tuple(int(c * 0.28) for c in accent())
    # LOOK EXCEPTION marking: the faint rule between two table rows, the accent at a quarter of its light (Data's mockup)
    pygame.draw.line(surface, col, (r.x + 14, y), (r.right - 14, y))


def scene(surface, name, rect, share=0.42):
    """The painted scene `popups/<name>.png` in the right `share` of `rect`,
    fading in from its left edge; True if drawn."""
    pic = buildicons.named(name)
    if pic is None:
        return False
    area = pygame.Rect(rect.right - int(rect.w * share), rect.y + 2,
                       int(rect.w * share) - 2, rect.h - 4)
    key = (name, id(pic), pic.get_size(), area.size,
           id(usermod._state["index"]))
    layer = _scenes.get(key)
    if layer is None:
        if len(_scenes) > 8:
            _scenes.clear()
        k = max(area.w / pic.get_width(), area.h / pic.get_height())
        big = pygame.transform.smoothscale(
            pic, (max(area.w, round(pic.get_width() * k)),
                  max(area.h, round(pic.get_height() * k))))
        layer = pygame.Surface(area.size, pygame.SRCALPHA)
        layer.blit(big, (0, 0), pygame.Rect(
            big.get_width() - area.w, (big.get_height() - area.h) // 2,
            area.w, area.h))
        fade = max(2, int(area.w * 0.55))
        for i in range(fade):
            # LOOK EXCEPTION picture: the painted scene's own fade into its panel, no colour of the HUD's
            layer.fill((255, 255, 255, int(235 * i / fade)),
                       pygame.Rect(i, 0, 1, area.h),
                       special_flags=pygame.BLEND_RGBA_MIN)
        _scenes[key] = layer
    surface.blit(layer, area.topleft)
    return True
