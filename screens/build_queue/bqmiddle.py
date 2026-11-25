"""The middle panel and the buttons as the mockup draws them — HD EXTENSION
`build_summary_mockup` (work order 432, Data's mockup of 25 November 2026).

The summary's name in a large type over a rule with the numbers under it,
each behind its small picture; the painted scene under a help text; the
queue's heading; a glyph in front of each button's word. The glyphs are the
HUD's (`core.hud.art`) and turn with the frame colour (172's rule); the scene
is the player's picture (`core.buildicons`) and without it the large box is as
it was.

INVENTION `queue_heading`: the words CONSTRUCTION QUEUE are ours; the
original prints nothing over the queue's seven rows.
"""
# HD EXTENSION `build_summary_mockup`: see the docstring.
import pygame

from core import buildicons
from core.hud import art as hudart
from core import nativedraw as nd
from core.hestrings import printf
from core.hud import text as hudtext

from . import bqcolour as col
from . import bqwire as w

#: Shares of the window's height.
TITLE, LINE, PITCH = 0.030, 0.0185, 0.034
E_COST, E_MAINT, E_TIME, E_TURNS = 242, 367, 211, 544
#: The HUD glyphs in front of the summary's numbers and on the buttons (they
#: turn with the frame colour, as every glyph does).
ICONS = {E_COST: "coin", E_MAINT: "coin", E_TIME: "gear", E_TURNS: "play"}
BUTTONS = {"cancel": "close", "ok": "check", "refit": "wrench",
           "design": "all", "repeat": "relocate", "auto": "gear"}


def summary(surface, screen, view, state, names, product):
    """The selected product's name and numbers, in the summary box."""
    height = surface.get_height()
    box = nd.rect(screen.layout, w.SUMMARY_BOX)
    pad = max(6, int(box.h * 0.05))
    name, _st = names.product(product, state)
    size = max(nd.MIN_FONT, int(height * TITLE))
    nd.blit_text(surface, screen.style, name, box.x + pad, box.y + pad,
                 box.w - 2 * pad, size, col.TITLE)
    y = box.y + pad + int(size * 1.45)
    # LOOK EXCEPTION marking: the thin rule under the product's name, the old summary's rule (HD EXTENSION build_summary_mockup)
    pygame.draw.line(surface, col.RULE, (box.x + pad, y),
                     (box.right - pad, y))
    e = view.entry(product)
    if e is None:
        return
    lines = [(E_COST, e["cost"])]
    if e["maintenance"] >= 0:
        lines.append((E_MAINT, e["maintenance"]))
    lines.append((E_TIME, e["time"]))
    turns = screen.turns_left(state, view, product)
    if turns is not None:
        lines.append((E_TURNS, turns))
    pitch = int(height * PITCH)
    line = max(nd.MIN_FONT, int(height * LINE))
    accent = hudtext.colour("label")
    y += int(pitch * 0.3)
    for eid, value in lines:
        fmt = screen.e(eid)
        if not fmt:
            continue
        x = box.x + pad
        icon = hudart.icon(ICONS[eid], int(pitch * 0.8))
        if icon is not None:
            surface.blit(icon, (x, y + (pitch - icon.get_height()) // 2))
            x += int(pitch * 1.25)
        nd.blit_text(surface, screen.style, printf(fmt, value), x,
                     y + (pitch - line) // 2 - 2, box.right - pad - x, line,
                     col.INFO)
        y += pitch


_scenes = {}


def scene(surface, screen, box):
    """The painted scene under a help text: the lower part of the large box,
    covered and faded into the box at its top. True if drawn."""
    pic = buildicons.art()
    if pic is None:
        return False
    area = pygame.Rect(box.x + 2, box.y + int(box.h * 0.38), box.w - 4,
                       box.h - int(box.h * 0.38) - 2)
    key = (id(pic), area.size)
    layer = _scenes.get(key)
    if layer is None:
        _scenes.clear()
        k = max(area.w / pic.get_width(), area.h / pic.get_height())
        big = pygame.transform.smoothscale(
            pic, (max(area.w, round(pic.get_width() * k)),
                  max(area.h, round(pic.get_height() * k))))
        cut = pygame.Rect((big.get_width() - area.w) // 2,
                          (big.get_height() - area.h) // 2, area.w, area.h)
        layer = pygame.Surface(area.size, pygame.SRCALPHA)
        layer.blit(big, (0, 0), cut)
        fade = max(2, area.h // 4)
        for i in range(fade):
            # LOOK EXCEPTION picture: the painted scene's own fade into the large box, no colour of the HUD's
            layer.fill((255, 255, 255, int(255 * i / fade)),
                       pygame.Rect(0, i, area.w, 1),
                       special_flags=pygame.BLEND_RGBA_MIN)
        _scenes[key] = layer
    surface.blit(layer, area.topleft)
    return True


def queue_heading(surface, screen, view, queue_row):
    """CONSTRUCTION QUEUE between the large box and the first row."""
    height = surface.get_height()
    desc = nd.rect(screen.layout, w.DESCRIPTION_BOX)
    first = nd.rect(screen.layout, queue_row(view, 0))
    room = first.top - desc.bottom
    if room < 12:
        return
    size = max(nd.MIN_FONT, min(int(height * 0.021), int(room * 0.55)))
    cx = (first.left + first.right) // 2
    word = screen.word("queue")
    nd.blit_text(surface, screen.style, word, cx, desc.bottom + room // 2
                 - size // 2, first.w, size, col.VALUE, align="center")
    accent = hudtext.colour("label")
    y = first.top - max(3, room // 8)
    # LOOK EXCEPTION marking: the rule under the queue's heading in the frame colour's accent (HD EXTENSION build_summary_mockup)
    pygame.draw.line(surface, tuple(int(c * 0.6) for c in accent),
                     (first.left + 4, y), (first.right - 4, y))
