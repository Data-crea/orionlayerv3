"""A Races slot whose leader is not known: a picture and HD's own words.

HD EXTENSION `no_contact_panel`: the original draws the slot's frame with
the words NO CONTACT, an empty bar and greyed missions. HD covers the
WHOLE slot box (`racesgeom.slot_box`, the outer frame: portrait, text, bar,
spies and the mission row) with one picture, 20 % darker, clipped to the
HUD panel's outline with the panel's own edge over it, and writes the words
itself: NO CONTACT (the engine's word, cyan) and one sentence (INVENTION
`no_contact_line`, light grey), right of the picture's emblem.

WHICH PICTURE: the player's mod folder `races/no_contact/<any name>.png`
(`screens/races/assets/nocontact/`), else the Leaders screen's empty-slot
picture (`FALLBACK`, `screens/leaders/assets/pictures/slot_empty_background
.png`: the leaders' emblem and an unknown figure, wherever the player has
that picture). The picture carries NO text. It is covered (scaled until it
fills the box, the overhang cut from the right: `racesleaders.cover`) so
that nothing is stretched. Not in the base pack and not in git.

NONE (no picture, the mod folder off, an unreadable file): None, and the
caller draws the slot as before — never the original's screen (Data's rule
since work order 187).
"""
import glob
import logging
import os
import time

import pygame

log = logging.getLogger("races")

FOLDER = "screens/races/assets/nocontact"
FALLBACK = "screens/leaders/assets/pictures/slot_empty_background.png"
#: INVENTION `no_contact_line`: the sentence under NO CONTACT.
LINE = "No diplomatic contact established."
TITLE_INK = (40, 228, 236)
LINE_INK = (205, 215, 225)
#: The words stand between these shares of the box's width (right of the
#: emblem and the figure), centred between them.
TEXT_SPAN = (0.47, 0.97)
DIM = 204                      # 80 % of 255
LOOK_AGAIN = 1.0
_cache = {}
_fitted = {}
_found = (0.0, None, None)


def _look(roots):
    for root in roots:
        for path in sorted(glob.glob(os.path.join(root, FOLDER, "*.png"))):
            if _load(path) is not None:
                return path
    for root in roots:
        if FALLBACK and _load(os.path.join(root, FALLBACK)) is not None:
            return os.path.join(root, FALLBACK)
    return None


def _load(path):
    try:
        stamp = os.stat(path).st_mtime_ns
    except OSError:
        return None
    hit = _cache.get(path)
    if hit is not None and hit[0] == stamp:
        return hit[1]
    try:
        img = pygame.image.load(path)
        img = img.convert_alpha() if pygame.display.get_surface() else img
    except (pygame.error, OSError) as exc:
        log.warning("no-contact panel: %s unreadable (%s) — the slot is "
                    "drawn as before", path, exc)
        img = None
    _cache[path] = (stamp, img)
    return img


def picture(size, scale=None):
    """The panel scaled to exactly `size` (w, h), or None. With `scale`
    (the screen's) it is clipped to the HUD panel's own outline, as the
    Leaders pictures are (`blocks.panel_polygon`): the caller draws the
    panel's edge over it, so the slot's frame is the one every other
    panel has."""
    global _found
    from core import resources
    roots = tuple(resources.res.roots())
    now = time.monotonic()
    when, seen, path = _found
    if seen != roots or now - when >= LOOK_AGAIN:
        path = _look(roots)
        _found = (now, roots, path)
    if path is None or path not in _cache:
        return None
    size = (max(1, int(size[0])), max(1, int(size[1])))
    key = (path, _cache[path][0], size, scale)
    hit = _fitted.get(key)
    if hit is None:
        if len(_fitted) > 16:
            _fitted.clear()
        from . import racesleaders
        hit = racesleaders.cover(_cache[path][1], size, (0.0, 0.5))
        hit.fill((DIM, DIM, DIM), special_flags=pygame.BLEND_RGB_MULT)
        if scale is not None:
            from core.hud import blocks as hud
            mask = pygame.Surface(size, pygame.SRCALPHA)
            # LOOK EXCEPTION picture: the clip of a picture to the panel's
            # outline, not a fill of its own
            pygame.draw.polygon(mask, (255, 255, 255, 255),
                                hud.panel_polygon(size[0], size[1], scale))
            hit = hit.convert_alpha()
            hit.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        _fitted[key] = hit
    return hit


def draw(surface, screen, rect):
    """The picture over `rect`, the panel's edge over it, the words on it.
    False where there is no picture: the caller draws the slot as before."""
    from core import lang
    from core import nativedraw as nd
    from core.hud import blocks as hud
    pic = picture(rect.size, screen.layout.scale)
    if pic is None:
        return False
    surface.blit(pic, rect.topleft)
    hud.panel(surface, rect, screen.layout.scale, filled=False)
    x0 = rect.x + int(rect.w * TEXT_SPAN[0])
    x1 = rect.x + int(rect.w * TEXT_SPAN[1])
    layout, style = screen.layout, screen.style
    big = int(nd.font_px(layout, "name") * 1.7)
    small = int(nd.font_px(layout, "skill") * 1.15)
    with lang.verbatim():               # the engine's word (WO 408)
        title = style.render_text(screen.words_no_contact, nd.fit(
            style, screen.words_no_contact, x1 - x0, big), TITLE_INK) \
            if screen.words_no_contact else None
    line = style.render_text(LINE, nd.fit(style, LINE, x1 - x0, small),
                             LINE_INK)
    gap = max(2, small // 4)
    block = (title.get_height() + gap if title else 0) + line.get_height()
    y = rect.centery - block // 2
    cx = (x0 + x1) // 2
    if title is not None:
        surface.blit(title, (cx - title.get_width() // 2, y))
        y += title.get_height() + gap
    surface.blit(line, (cx - line.get_width() // 2, y))
    return True
