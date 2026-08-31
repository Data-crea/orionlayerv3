"""Background point stars for the galaxy map.

The original draws a dense field of single-pixel stars behind the
map (see the reference screenshot and `doc/starfield_measurement.md`).
The HD background image carries the gas clouds but no points, so the
map reads as empty next to the original.

Everything in here is a transcription of numbers measured off a
native screenshot, not a taste decision:

* density   1 grey point star per 33 native pixels of map area
* tiers     twenty discrete grey levels, 90 % of them at or below 44
* colour    neutral grey with a constant +8 on blue
* motion    none

That last one is the reason this looks calm at a density of 3 %
of all pixels: almost the entire field sits between 6 % and 17 % of
full white. Brightness, not count, is what makes a star field noisy.

**No twinkle, ever.** MOO2 draws palette-indexed into a static
backdrop; it cannot fade or animate a background pixel. Anything
moving here would be an invention (see `v3_fundament.md`, "an effect
the original is technically incapable of").

Additive compositing, like the nebulas: the original paints these
values over black, so a value *is* the light the star contributes.
Adding it reproduces the same weight over a lit background, where a
flat blit would punch dark holes into the gas clouds and an alpha
blit would wash the whole layer.

The field is built once into a cached surface and reused; rebuilding
5,000 stamps per frame would cost more than the rest of the screen
together. Positions are drawn from a seeded RNG in normalised
coordinates, so an F9 resolution change rescales the same sky
instead of shuffling a new one.
"""
import math
import random

import pygame

# ── Measured constants (doc/starfield_measurement.md) ────

#: Map click area in native coordinates, field 23 of the Galaxy Map
#: field list: (22, 22)-(527, 421). The density below is per native
#: pixel of exactly this rect, so it is independent of the HD
#: resolution the map box happens to have.
NATIVE_MAP_W, NATIVE_MAP_H = 505, 399

#: One grey point star per this many native pixels. MEASURED on two
#: independent nebula-free crops of the reference screenshot, which
#: agreed at 33.3 and 32.4; over the whole map rect, nebula-covered
#: area included, the same count gives 37.4. Take 33 and treat 37 as
#: the far end of the bracket.
DENSITY_NATIVE = 33.0

#: Grey level -> how many stars carried it, counted on the reference
#: screenshot. MEASURED, and deliberately kept as raw counts rather
#: than normalised weights so the sample size stays visible. Values
#: are multiples of 4 because they come out of a 6-bit VGA palette.
STAR_TIERS = (
    (16, 1566), (24, 1599), (36, 217), (44, 1210), (52, 5),
    (60, 114), (72, 88), (80, 81), (88, 87), (96, 65),
    (108, 11), (116, 7), (124, 23), (132, 9), (136, 5),
    (144, 6), (152, 9), (156, 1), (164, 5), (172, 2),
)

#: Blue channel offset. Every grey star measured came out as
#: (v, v, v + 8) — the ramp itself is tinted, not the stars.
BLUE_BIAS = 8

#: Supersampling for the dot stamps. A star wider than one HD pixel
#: has to be drawn round and soft, or the field turns into a grid of
#: squares the moment the map box is larger than 640x480.
STAMP_SUPERSAMPLE = 4

DEFAULTS = {
    "enabled": True,
    "seed": 20260829,
    #: Deviation knob. 1.0 is the measured count (~6,100 stars over
    #: the whole map area). Raising it trades the original's coarse
    #: grain for a finer dust; it is a deviation and should be
    #: recorded as one if it ships above 1.0.
    "count_scale": 1.0,
    #: Dot diameter in NATIVE pixels. 1.0 means one star covers
    #: exactly what it covers in the original, upscaled — a faithful
    #: but chunky 5 px blob on an ultrawide.
    "dot_native": 1.0,
    #: Multiplier on the measured tiers. Below 1.0 the field sinks
    #: into the background image; above 1.0 it starts to compete
    #: with the real stars, which is the failure mode to avoid.
    "brightness": 1.0,
    #: Low-frequency density modulation, 0..1. The reference field is
    #: measurably clumped (cell-to-cell spread is four times what
    #: uniform noise gives), but that sample is contaminated by the
    #: nebulas, so the transcription stops at "not uniform" and the
    #: default stays 0.0. Turning it on is a design decision.
    "clumping": 0.0,
    "clump_cells": 8,
}


def _tier_table(brightness):
    """(colour, cumulative_weight) pairs for weighted picking."""
    table = []
    total = 0
    for value, count in STAR_TIERS:
        total += count
        v = max(0, min(255, int(round(value * brightness))))
        b = max(0, min(255, int(round((value + BLUE_BIAS) * brightness))))
        table.append(((v, v, b), total))
    return table, total


def _pick(table, total, roll):
    target = roll * total
    for colour, cumulative in table:
        if target <= cumulative:
            return colour
    return table[-1][0]


def _stamp(diameter, colour):
    """One star, drawn round and antialiased, on black.

    Black matters: the layer is composited with BLEND_RGB_ADD, which
    ignores alpha entirely, so the stamp's own background has to be
    the additive identity rather than a transparent colour.
    """
    if diameter <= 1.4:
        surf = pygame.Surface((1, 1))
        surf.fill(colour)
        return surf
    size = max(2, int(math.ceil(diameter)))
    ss = STAMP_SUPERSAMPLE
    big = pygame.Surface((size * ss, size * ss))
    big.fill((0, 0, 0))
    pygame.draw.circle(big, colour,
                       (size * ss // 2, size * ss // 2),
                       max(1, int(round(diameter * ss / 2.0))))
    return pygame.transform.smoothscale(big, (size, size))


class StarfieldLayer:
    """Cached point-star field for the map box.

    Mirrors `renderer.WormholeLayer`: a key decides whether the
    cached surface is still valid, and `render` is the only entry
    point the screen needs.
    """

    def __init__(self, config=None):
        self._cfg = dict(DEFAULTS)
        self._key = None
        self._layer = None
        self._count = 0
        if config:
            self.configure(config)

    def configure(self, config):
        """Apply a config dict; unknown keys are ignored."""
        for key in DEFAULTS:
            if key in config:
                self._cfg[key] = config[key]
        self.clear()

    @property
    def enabled(self):
        return bool(self._cfg.get("enabled", True))

    def set_enabled(self, flag):
        """Switch the field on or off without touching the cache.

        `enabled` is deliberately kept out of the cache key below, so
        toggling it in the editor costs nothing — the built surface
        survives being hidden and comes back instantly.
        """
        self._cfg["enabled"] = bool(flag)
        return self._cfg["enabled"]

    def toggle(self):
        return self.set_enabled(not self.enabled)

    @property
    def star_count(self):
        """Stars in the current layer — for diagnostics and tests."""
        return self._count

    def clear(self):
        self._key = None
        self._layer = None
        self._count = 0

    # ── generation ──────────────────────────────────────

    def _clump_weight(self, grid, cells, u, v):
        """Bilinear sample of the coarse density grid at (u, v)."""
        fx = u * (cells - 1)
        fy = v * (cells - 1)
        x0, y0 = int(fx), int(fy)
        x1, y1 = min(x0 + 1, cells - 1), min(y0 + 1, cells - 1)
        tx, ty = fx - x0, fy - y0
        top = grid[y0][x0] * (1 - tx) + grid[y0][x1] * tx
        bot = grid[y1][x0] * (1 - tx) + grid[y1][x1] * tx
        return top * (1 - ty) + bot * ty

    def _build(self, width, height, native_px):
        cfg = self._cfg
        layer = pygame.Surface((width, height))
        layer.fill((0, 0, 0))

        native_area = NATIVE_MAP_W * NATIVE_MAP_H
        count = int(native_area / DENSITY_NATIVE * float(cfg["count_scale"]))
        diameter = max(1.0, float(cfg["dot_native"]) * native_px)

        table, total = _tier_table(float(cfg["brightness"]))
        stamps = {}
        rng = random.Random(cfg["seed"])

        clumping = max(0.0, min(1.0, float(cfg["clumping"])))
        cells = max(2, int(cfg["clump_cells"]))
        grid = [[rng.random() for _ in range(cells)] for _ in range(cells)]

        placed = 0
        attempts = 0
        limit = count * 8
        while placed < count and attempts < limit:
            attempts += 1
            u, v = rng.random(), rng.random()
            if clumping > 0.0:
                weight = (1.0 - clumping
                          + 2.0 * clumping
                          * self._clump_weight(grid, cells, u, v))
                if rng.random() > weight:
                    continue
            colour = _pick(table, total, rng.random())
            stamp = stamps.get(colour)
            if stamp is None:
                stamp = _stamp(diameter, colour)
                stamps[colour] = stamp
            x = int(u * width) - stamp.get_width() // 2
            y = int(v * height) - stamp.get_height() // 2
            layer.blit(stamp, (x, y), special_flags=pygame.BLEND_RGB_ADD)
            placed += 1

        self._layer = layer
        self._count = placed

    # ── drawing ─────────────────────────────────────────

    def render(self, surface, box, native_px=None):
        """Add the field to `surface` inside `box` = (x, y, w, h).

        `native_px` is HD pixels per native pixel — `MapContext.px`.
        It only sizes the dots; the count comes from the native map
        area and is therefore the same at every HD resolution.
        """
        if not self._cfg.get("enabled", True):
            return
        x, y, w, h = (int(v) for v in box)
        if w <= 0 or h <= 0:
            return
        if native_px is None or native_px <= 0:
            native_px = w / float(NATIVE_MAP_W)

        key = (w, h, round(float(native_px), 3),
               tuple(sorted((k, str(v)) for k, v in self._cfg.items()
                            if k != "enabled")))
        if key != self._key:
            self._key = key
            self._build(w, h, float(native_px))
        if self._layer is not None:
            surface.blit(self._layer, (x, y),
                         special_flags=pygame.BLEND_RGB_ADD)
