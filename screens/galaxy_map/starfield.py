"""Background point stars for the galaxy map.

The original draws a dense field of single-pixel stars behind the
map (see the reference screenshot and `dev:doc/starfield_measurement.md`).
The HD background image carries the gas clouds but no points, so the
map reads as empty next to the original.

The field itself is GENERATED, not the original's picture: the counts
and grey levels are measured off a native screenshot, the layout is a
seeded RNG. What it transcribes is listed beside each number:

* density   1 grey point star per 33 native pixels of map area (MEASURED)
* tiers     twenty discrete grey levels, 90 % of them at or below 44
            (MEASURED)
* colour    neutral grey with a constant +8 on blue (MEASURED)
* motion    the parallax, TRANSCRIPTION `parallax`: the original draws
            three STARBG.LBX layers, entries 0, 1 and 2, each a 640 x 480
            tile drawn four times so it wraps (Draw_Paralax_,
            mainscr.cpp:650-680), and moves them by 1x, 2x and 4x the
            map's scroll in world units (Get_New_Paralax_XYs_,
            mainscr.cpp:2012-2059), back to 0 when the map stands at its
            widest scale (Get_Map_Scale_, harold.cpp:1170-1178). HD splits
            its own field into the same three layers by the original's
            shares (LAYER_SHARES) and moves them the same way, with the
            DEVIATION `parallax_from_view` written at `parallax_offsets`.
            Nothing moves while the map stands still.

That last one is the reason this looks calm at a density of 3 %
of all pixels: almost the entire field sits between 6 % and 17 % of
full white. Brightness, not count, is what makes a star field noisy.

**No twinkle, ever.** MOO2 draws palette-indexed into a static
backdrop; it cannot fade or animate a background pixel. Anything
moving here other than the parallax would be an invention (see `dev:doc/v3_fundament.md`, "an effect
the original is technically incapable of").

Additive compositing, like the nebulas: the original paints these
values over black, so a value *is* the light the star contributes.
Adding it reproduces the same weight over a lit background, where a
flat blit would punch dark holes into the gas clouds and an alpha
blit would wash the whole layer.

The field is built once into a cached surface and reused; rebuilding
5,000 stamps per frame would cost more than the rest of the screen
together. Positions are drawn from a seeded RNG in normalised
coordinates, so an F7 window-size change rescales the same sky
instead of shuffling a new one.
"""
import math
import random

import pygame

# ── Measured constants (dev:doc/starfield_measurement.md) ────

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

#: The parallax layers: (speed, share of the stars). Speed is the
#: multiplier on the map's scroll, 1 / 2 / 4 for STARBG entries 0 / 1 / 2
#: (mainscr.cpp:2024-2026, :2039-2041). The shares are MEASURED off the
#: player's STARBG.LBX entries 0-2 with core/lbx.py (work order 310): lit
#: pixels 20401 / 1796 / 59 of 640 x 480 each, the far layer all palette
#: indices 2-8 and 35, the mid and near layers 7-21 and 34 and 10-13.
#: The far layer is the dim one, so HD puts its tiers at or below grey
#: 44 there (89.9 % of the measured stars against the original's 91.7 %)
#: and splits the brighter rest between mid and near as 1796 : 59.
PARALLAX_SPEEDS = (1, 2, 4)
LAYER_SHARES = (20401, 1796, 59)
FAR_TIER_MAX = 44

#: The original's tile, native px (mainscr.cpp:662-678, :2045-2056).
PARALLAX_TILE = (640, 480)

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
        # LOOK EXCEPTION picture: the star field's own stars
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
        self._layers = []
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
        self._layers = []
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
        """Three layers, each a tile the window's size that wraps: a stamp
        crossing an edge is stamped again on the opposite side, so a layer
        drawn at any offset (`render`) shows no seam."""
        cfg = self._cfg
        layers = []
        for _ in PARALLAX_SPEEDS:
            layer = pygame.Surface((width, height))
            layer.fill((0, 0, 0))
            layers.append(layer)

        native_area = NATIVE_MAP_W * NATIVE_MAP_H
        count = int(native_area / DENSITY_NATIVE * float(cfg["count_scale"]))
        diameter = max(1.0, float(cfg["dot_native"]) * native_px)

        table, total = _tier_table(float(cfg["brightness"]))
        far_max = FAR_TIER_MAX * float(cfg["brightness"])
        mid, near = LAYER_SHARES[1], LAYER_SHARES[2]
        stamps = {}
        rng = random.Random(cfg["seed"])
        # A second stream picks mid or near, so the first one — positions
        # and greys — is the same sky as before the split.
        pick_layer = random.Random(cfg["seed"] + 1)

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
            if colour[0] <= far_max:
                depth = 0
            else:
                depth = 1 if pick_layer.random() * (mid + near) < mid else 2
            sw, sh = stamp.get_size()
            x = int(u * width) - sw // 2
            y = int(v * height) - sh // 2
            for dx in ((0, -width) if x + sw > width else (0, width)
                       if x < 0 else (0,)):
                for dy in ((0, -height) if y + sh > height else
                           (0, height) if y < 0 else (0,)):
                    layers[depth].blit(stamp, (x + dx, y + dy),
                                       special_flags=pygame.BLEND_RGB_ADD)
            placed += 1

        self._layers = layers
        self._layer = layers[0]
        self._count = placed

    # ── drawing ─────────────────────────────────────────

    def render(self, surface, box, native_px=None, offsets=None):
        """Add the field to `surface` inside `box` = (x, y, w, h).

        `native_px` is HD pixels per native pixel — `MapContext.px`.
        It only sizes the dots; the count comes from the native map
        area and is therefore the same at every HD resolution.
        `offsets` is one (dx, dy) in HD px per layer (`parallax_offsets`);
        None stands every layer at 0.
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
        if not self._layers:
            return
        offsets = offsets or ((0, 0),) * len(self._layers)
        clip = surface.get_clip()
        surface.set_clip(pygame.Rect(x, y, w, h).clip(clip))
        # Draw_Paralax_ draws each tile four times, at (x, y), (x - 640, y),
        # (x - 640, y - 480) and (x, y - 480), the offset kept in [0, 640)
        # x [0, 480) (mainscr.cpp:662-678, :2045-2056): the same here with
        # the window as the tile.
        for layer, (dx, dy) in zip(self._layers, offsets):
            ox, oy = int(round(dx)) % w, int(round(dy)) % h
            for tx in (ox, ox - w):
                for ty in (oy, oy - h):
                    if tx > -w and ty > -h:
                        surface.blit(layer, (x + tx, y + ty),
                                     special_flags=pygame.BLEND_RGB_ADD)
        surface.set_clip(clip)


def parallax_offsets(ctx):
    """Each layer's offset in HD px for the map context `ctx`, or None.

    TRANSCRIPTION `parallax`: the layers move by 1x, 2x and 4x the map's
    scroll in WORLD units, not screen pixels (Get_New_Paralax_XYs_,
    mainscr.cpp:2012-2059: `(target - _cur_map_x) / scale` with scale 1,
    or the step count of a smooth scroll, mainscr.cpp:2634), so one world
    unit of scroll moves the far layer one native pixel at every zoom —
    pushed to HD px by `ctx.px`. At the map's widest scale they stand at
    0 (Get_Map_Scale_, harold.cpp:1170-1178).

    DEVIATION `parallax_from_view`: the original ADDS each scroll step's
    size, `-abs(dx)` through `sign_x` (mainscr.cpp:2020-2027, v2
    mainscr.cpp:2242-2249 the same), so its layers drift right and down
    whichever way the map scrolls, and a view's sky depends on the path
    that led to it. HD reads the offset off the view's own origin,
    -k x map_x, so the layers move against the scroll — the original's
    direction for a scroll left or up — and the same view always shows
    the same sky; HD's view moves continuously, where an added absolute
    value would make a held drag shake the sky. The tile is the window,
    not 640 x 480 native px, because HD's field is generated to the
    window (a 640-px tile would repeat inside a 1920-px window).

    A ZOOM moves the layers too, by the same -k x map_x: HD's wheel zoom
    at the pointer moves map_x, so the sky slides with it. The original
    does not hold its layers on a zoom either, but jumps them: a zoom-out
    calls Get_New_Paralax_XYs_ with `_cur_map_x - old_x` as the TARGET
    (mainscr_main.cpp:838), a step of the old origin's size, and leaving
    the engine's zoom mode sets all six to 0x16 (:853-854); only a scroll
    (mainscr.cpp:2521, :2634) moves them by the scroll. Neither jump has a
    meaning HD's continuous zoom could carry, so HD keeps one rule, the
    view's origin, part of this deviation.
    """
    if ctx is None:
        return None
    view = getattr(ctx, "view", None)
    state = getattr(view, "state", None)
    if state is None:
        return None
    scale = getattr(ctx, "map_scale", 0) or 0
    top = getattr(ctx, "max_map_scale", 0) or 0
    if top and scale >= top:
        return None
    mx = float(getattr(state, "map_x", 0) or 0)
    my = float(getattr(state, "map_y", 0) or 0)
    px = float(getattr(ctx, "px", 1.0) or 1.0)
    return tuple((-k * mx * px, -k * my * px) for k in PARALLAX_SPEEDS)
