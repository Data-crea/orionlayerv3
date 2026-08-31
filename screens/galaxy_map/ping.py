"""Home-system ping — expanding rings on a keypress.

**This is an INVENTION, and it is marked as one on purpose.** MOO2
has no such effect and could not draw it: the game is palette-indexed
and has no alpha blending, so nothing on its galaxy map can fade
(`v3_fundament.md`, "an effect the original is technically incapable
of"). Every other layer on this screen is a transcription with a
source line; this one is a navigation aid for HD resolutions and
large galaxies, where the home system is one small icon among two
hundred. The numbers below are chosen, not measured, and there is no
orion2re function to check them against.

Because it is an invention it is kept strictly cosmetic and strictly
bounded:

* it touches no game state — the key is consumed here and never
  forwarded to orion2re, so the game does not even see it
* it decays to nothing on its own after a few seconds and cannot be
  left switched on
* it draws inside the map clip like every other layer, so it cannot
  bleed over the frame

Sizes are given in NATIVE pixels and multiplied by `ctx.px`, like
every other sizing decision on this screen, so the ping keeps its
proportion to the star icons at every zoom level instead of being a
fixed HD radius that swallows the map when zoomed in.
"""
import time

import pygame

from core import palette

#: Total lifetime of one ping, seconds. Long enough to find the star
#: after looking away, short enough that it cannot be mistaken for a
#: permanent marker.
PING_SECONDS = 3.0

#: Seconds between two ring launches, and how long one ring lives.
#: The overlap (life > interval) is what makes it read as a repeating
#: pulse rather than as three separate flashes.
RING_INTERVAL = 0.55
RING_LIFE = 1.10

#: Ring radius in NATIVE pixels: the first frame sits just outside a
#: full-size star icon (33 px wide, so 17 px radius) and grows to
#: about two icon widths.
RING_START_NATIVE = 12.0
RING_END_NATIVE = 46.0

#: Ring thickness in native pixels, constant while it expands.
RING_WIDTH_NATIVE = 1.6

#: Peak alpha of a ring at birth, 0..255.
RING_ALPHA = 210

#: Supersampling used to draw one antialiased ring. pygame.draw has
#: no antialiased thick circle, and a hard-edged ring at HD sizes
#: reads as a jagged polygon.
SUPERSAMPLE = 3

#: Radii are cached in steps of this many HD pixels. A ping sweeps
#: through ~100 radii; rounding to a step keeps the cache at a few
#: dozen surfaces, and the visual difference is under one pixel.
RADIUS_STEP = 3

PING_COLOR = palette.col("galaxy_map", "home_ping", (255, 214, 130))


def _ring_surface(radius, width, colour):
    """One antialiased ring, `colour` with per-pixel alpha.

    Drawn at SUPERSAMPLE times the size and scaled down, because
    `pygame.draw.circle` does not antialias and `draw.aacircle` (via
    gfxdraw) cannot do thickness.
    """
    side = max(4, int(radius * 2 + width * 2 + 2))
    big = pygame.Surface((side * SUPERSAMPLE,) * 2, pygame.SRCALPHA)
    pygame.draw.circle(
        big, tuple(colour[:3]) + (255,),
        (side * SUPERSAMPLE // 2, side * SUPERSAMPLE // 2),
        int(radius * SUPERSAMPLE),
        max(1, int(round(width * SUPERSAMPLE))))
    return pygame.transform.smoothscale(big, (side, side))


def _faded(surface, factor):
    """A copy of `surface` with its alpha channel scaled by `factor`.

    Not `set_alpha`: on a per-pixel-alpha surface that is an SDL
    alpha-modulation whose interaction with the existing channel has
    already cost this project a day once (see the pygame notes in
    `v3_fundament.md`). Scaling the channel itself is unambiguous.
    """
    out = surface.copy()
    alpha = pygame.surfarray.pixels_alpha(out)
    alpha[:] = (alpha.astype("uint16") * int(factor * 256) // 256
                ).astype("uint8")
    del alpha                      # unlock the surface before blitting
    return out


class HomePing:
    """Expanding rings over one point, triggered by a keypress.

    Holds no reference to a star: the caller resolves the home system
    per frame and hands in a position, so a ping keeps pointing at the
    right place while the player zooms or the galaxy scrolls.
    """

    def __init__(self):
        self._start = None
        self._rings = {}

    # ── State ────────────────────────────────────────────

    def trigger(self, now=None):
        """(Re)start the ping. A second press restarts it."""
        self._start = time.monotonic() if now is None else now

    def cancel(self):
        self._start = None
        self._rings.clear()

    @property
    def active(self):
        if self._start is None:
            return False
        if not self._running(time.monotonic()):
            self.cancel()
            return False
        return True

    def _running(self, now):
        """Whether the ping is alive at `now`.

        Split out from `active` so a caller (and the smoke test) can
        drive the effect from an injected clock. `active` reads the
        real clock and additionally frees the cache once the ping is
        over, which a pure query must not do.
        """
        if self._start is None:
            return False
        return 0.0 <= now - self._start < PING_SECONDS + RING_LIFE

    def clear_cache(self):
        """Drop cached ring surfaces — radii are in HD pixels, so a
        resolution change invalidates every one of them."""
        self._rings.clear()

    # ── Drawing ──────────────────────────────────────────

    def _ring(self, radius, width):
        key = (int(radius) // RADIUS_STEP, int(width))
        surf = self._rings.get(key)
        if surf is None:
            surf = _ring_surface(key[0] * RADIUS_STEP or 1, width,
                                 PING_COLOR)
            self._rings[key] = surf
        return surf

    def render(self, surface, ctx, pos, now=None):
        """Draw the rings centred on `pos`, an HD (x, y).

        Does nothing when the ping is not running, so the caller can
        put this in the draw order unconditionally.
        """
        if pos is None:
            return
        now = time.monotonic() if now is None else now
        if not self._running(now):
            return
        elapsed = now - self._start
        px = ctx.px
        r0 = RING_START_NATIVE * px
        r1 = RING_END_NATIVE * px
        width = max(1, round(RING_WIDTH_NATIVE * px))
        cx, cy = int(pos[0]), int(pos[1])

        launch = 0.0
        while launch <= PING_SECONDS:
            age = elapsed - launch
            launch += RING_INTERVAL
            if age < 0 or age >= RING_LIFE:
                continue
            phase = age / RING_LIFE
            # Ease out: fast at birth, slow at the edge, so the eye
            # is caught by the start of the ring rather than its end.
            radius = r0 + (r1 - r0) * (1.0 - (1.0 - phase) ** 2)
            fade = (1.0 - phase) ** 1.5
            ring = self._ring(radius, width)
            surface.blit(_faded(ring, fade),
                         (cx - ring.get_width() // 2,
                          cy - ring.get_height() // 2))
