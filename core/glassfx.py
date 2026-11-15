"""The glass behind a popup (Data, 15
November 2026: "a strong glass effect lets everything outside blur, so only
the window stays in focus").

What stands behind a popup is blurred hard and darkened; the popup itself
is drawn sharp over it. One implementation for the research panel (the
dispatcher's overlay), the message boxes, the turn popups, the name boxes
and the galaxy map's own modals (`core.msgbox.dimmed_base`,
`screens/galaxy_map/screen.py`).

A blur costs about 4 ms at 1080p and 17 ms at 4K, so a picture that moves
under a popup (the live map) is blurred again at most every `REFRESH`
seconds; a held picture is blurred once.
"""
import time

import pygame

#: the box size of the blur, px at 1920 wide, and the darkening (0-255)
BLUR = 6
DIM = 110
#: how long a blurred live backdrop is kept (s)
REFRESH = 0.25

_last = [None, 0.0]        # the glass last made for a live backdrop, its time
_over = {}                 # name -> (glass, time), for `over`


def blurred(surface, blur=BLUR):
    """A heavily blurred copy of `surface`; `blur` is the box size in
    pixels at 1920 wide."""
    w, h = surface.get_size()
    f = max(2, int(blur * w / 1920))
    small = pygame.transform.smoothscale(
        surface, (max(1, w // f), max(1, h // f)))
    small = pygame.transform.smoothscale(
        small, (max(1, w // (f * 2)), max(1, h // (f * 2))))
    small = pygame.transform.smoothscale(small, (max(1, w // f),
                                                 max(1, h // f)))
    return pygame.transform.smoothscale(small, (w, h))


def glassed(surface, blur=BLUR, dim=DIM):
    """The glass: a blurred copy of `surface`, darkened by `dim`."""
    out = blurred(surface, blur)
    shade = pygame.Surface(out.get_size(), pygame.SRCALPHA)
    shade.fill((0, 0, 0, dim))
    out.blit(shade, (0, 0))
    return out


def live(base, surface):
    """The glass of a backdrop that is drawn live on `surface` every frame:
    `base` (the last one the caller kept) while it is fresh and the right
    size, else a new one."""
    now = time.monotonic()
    if base is not None and base is _last[0] and \
            base.get_size() == surface.get_size() and \
            now - _last[1] < REFRESH:
        return base
    out = glassed(surface)
    _last[0], _last[1] = out, now
    return out


def over(surface, name):
    """Blur and darken what `surface` holds now, in place, under the name
    `name` (kept `REFRESH` seconds between two blurs)."""
    now = time.monotonic()
    hit = _over.get(name)
    if hit is None or hit[0].get_size() != surface.get_size() or \
            now - hit[1] >= REFRESH:
        hit = _over[name] = (glassed(surface), now)
    surface.blit(hit[0], (0, 0))


def forget(name=None):
    """Drop a kept glass (a popup closed), or all."""
    if name is None:
        _over.clear()
    else:
        _over.pop(name, None)
