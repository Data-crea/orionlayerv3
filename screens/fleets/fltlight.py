"""The inset map lights the star of the fleet the grid shows.

HD EXTENSION `fleet_star_light` (Data's request: switching between fleets
in the Fleets screen, the star on the minimap should at least light up so
the player sees where the fleet stands). The original marks nothing: the
grid's fleet is found by reading the stacks' pictures (flt1.cpp:342-353
only names it in the strip). Cosmetic and bounded, like the galaxy map's
home ping (`screens/galaxy_map/ping.py`): it touches no game state, sends
nothing and ends on its own a few seconds after the last change.

WHICH FLEET: the one the grid shows, `FLTS`'s `ship_idx[0]`. A change of
that head ship (PREV / NEXT FLEET, F1 / F2, a new list on entry) starts
the light.

WHERE: a fleet at a star (`location` below 10000, ship.py) lights that
star's dot, a fleet on its way lights its small ship icon, found by the
same stack rule the strip uses (`core.shipstacks.stack_ships`). Nothing is
lit when neither is found.
"""
import time

import pygame

from core import palette
from core.structs import ship as ship_struct

#: Seconds the light lives after a change, and the pulse period inside it.
LIGHT_SECONDS = 2.4
PULSE_SECONDS = 0.8

#: Ring radii in the inset's NATIVE pixels (the star sprite is 5 px).
RADIUS_MIN_NATIVE = 3.0
RADIUS_MAX_NATIVE = 13.0
WIDTH_NATIVE = 1.4

#: Offset from a small ship icon's origin to its middle, native px.
ICON_MIDDLE = 3

SUPERSAMPLE = 3

COLOUR = palette.col("galaxy_map", "home_ping", (255, 214, 130))

_rings = {}


def key_of(block):
    """What identifies the grid's fleet, or None without one."""
    ships = (block or {}).get("ship_idx") or []
    if (block or {}).get("stack", -1) < 0 or not ships:
        return None
    return (int(block.get("stack", -1)), int(ships[0]))


def point(game_state, block, stars, box_origin):
    """The fleet's place as native pixels inside the inset box, or None.

    `stars` is `colonyfacts.galaxy_inset_stars` for this box, `box_origin`
    the box's native (x, y) — the icons' coordinates are in screen space.
    """
    key = key_of(block)
    if key is None:
        return None
    raws = getattr(game_state, "ships_raw", None) or []
    if not 0 <= key[1] < len(raws):
        return None
    head = ship_struct.parse(raws[key[1]])
    loc = int(head.location)
    if 0 <= loc < len(stars) and loc < ship_struct.LOCATION_MOVING_OFFSET:
        return float(stars[loc][0]), float(stars[loc][1])
    from core import shipstacks
    for icon in getattr(game_state, "ship_icons", None) or []:
        if int(icon.x) < 0 or int(icon.y) < 0:
            continue
        members = shipstacks.stack_ships(game_state, icon)
        if members and key[1] in members:
            return (float(icon.x - box_origin[0] + ICON_MIDDLE),
                    float(icon.y - box_origin[1] + ICON_MIDDLE))
    return None


def _ring(radius, width):
    """One antialiased ring with per-pixel alpha, cached by size."""
    key = (int(radius), int(width))
    ring = _rings.get(key)
    if ring is None:
        side = max(4, int(radius * 2 + width * 2 + 2))
        big = pygame.Surface((side * SUPERSAMPLE,) * 2, pygame.SRCALPHA)
        pygame.draw.circle(big, tuple(COLOUR[:3]) + (255,),
                           (side * SUPERSAMPLE // 2,) * 2,
                           int(radius * SUPERSAMPLE),
                           max(1, int(width * SUPERSAMPLE)))
        ring = pygame.transform.smoothscale(big, (side, side))
        _rings[key] = ring
    return ring


class Light:
    """The running light: restarts when the grid's fleet changes."""

    def __init__(self):
        self._key = None
        self._start = None

    def clear(self):
        """On entry: the next fleet seen counts as a change."""
        self._key = None
        self._start = None

    def follow(self, block, now=None):
        """Start the light when the grid shows another fleet."""
        key = key_of(block)
        if key != self._key:
            self._key = key
            self._start = (time.monotonic() if now is None else now) \
                if key is not None else None

    def alive(self, now=None):
        now = time.monotonic() if now is None else now
        return self._start is not None and \
            0.0 <= now - self._start < LIGHT_SECONDS

    def level(self, now=None):
        """0..1 brightness at `now` (a pulse that fades out), 0 when off."""
        if not self.alive(now):
            return 0.0
        elapsed = (time.monotonic() if now is None else now) - self._start
        beat = (elapsed % PULSE_SECONDS) / PULSE_SECONDS
        return (1.0 - beat) * (1.0 - elapsed / LIGHT_SECONDS)

    def draw(self, surface, at, px, now=None):
        """Rings around the HD point `at`; `px` is HD pixels per native."""
        if at is None or not self.alive(now):
            return
        now = time.monotonic() if now is None else now
        elapsed = now - self._start
        beat = (elapsed % PULSE_SECONDS) / PULSE_SECONDS
        fade = (1.0 - beat) * (1.0 - elapsed / LIGHT_SECONDS)
        radius = (RADIUS_MIN_NATIVE + (RADIUS_MAX_NATIVE - RADIUS_MIN_NATIVE)
                  * (1.0 - (1.0 - beat) ** 2)) * px
        ring = _ring(radius, max(1, round(WIDTH_NATIVE * px))).copy()
        ring.fill((255, 255, 255, int(255 * max(0.0, min(1.0, fade)))),
                  special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(ring, (int(at[0]) - ring.get_width() // 2,
                            int(at[1]) - ring.get_height() // 2))
        # a steady core, so a still frame of the light is findable too
        core = max(2, int(round(2.2 * px)))
        glow = pygame.Surface((core * 2, core * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, tuple(COLOUR[:3]) + (int(200 * fade) + 40,),
                           (core, core), core)
        surface.blit(glow, (int(at[0]) - core, int(at[1]) - core))
