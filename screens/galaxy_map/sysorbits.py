"""The system window's orbits — work order 223 (Data's decision 4: "the
orbits the original draws are missing").

What the original draws when a star is clicked (sys.cpp:546-576,
:451-544; geo.cpp:5-13, :245-279), and what HD draws for it:

  TRANSCRIPTION  the frame: the view is the original window's view, the
                 322 x 183 native px inside BUFFER0.LBX 0x49 (12..333,
                 46..228 of the window, the picture drawn one px down,
                 sys.cpp:326), with the rings' centre at (162, 91) in it
                 (`boxmodel.ORBIT_CENTRE` less the view's corner). HD maps
                 that view into its own `system_view` box, one scale both
                 ways, centred. Until work order 230 HD fitted only the
                 ring pictures (288 x 154) and cut a planet on the fifth
                 orbit at the view's edge, which the original's view holds.
  TRANSCRIPTION  the rings: one ellipse per orbit that holds a planet or a
                 gas giant, half-axes `_orbit_consts[orbit + 1] / 10`
                 (geo.cpp:252-254); an empty orbit draws nothing. Drawn in
                 code at the window's size as the pictures draw them (0x4D-
                 0x51, measured, work order 230): a line three native px
                 wide — its core FONTS.LBX 1's 0x3E (40, 52, 88), its sides
                 the darker 0x3C / 0x3D blues (`RING_SIDE`, their mean)
                 — the pictures' own ellipses, not the pictures. (Until
                 work order 230 one native px of the core alone.)
  TRANSCRIPTION  pierced: each ring keeps 2 native px clear round its own
                 planet (two `Outline_Bitmap_` passes masked out of the ring,
                 sys.cpp:509-515), and the planets are drawn back to front
                 by their height (`qsort_sys_disp_`, sys.cpp:316-320).
  TRANSCRIPTION  the planet's place: the engine's own, read off its planet
                 field; its size `_rot_plan_dim` (harold.cpp:1491-1502),
                 a gas giant at the HUGE size (sys.cpp:116-118).
  DEVIATION      `belt_drawn`: an asteroid belt (BUFFER0.LBX 0x5B, frame =
                 orbit, sys.cpp:553-557) is drawn in code from the picture's
                 measured make-up — grey dots, as many as the frame has, in
                 a band of +-5 % round the orbit's ellipse — not the
                 picture, which is not extracted.
  TRANSCRIPTION  `belt_hit`: a belt has no planet field; the original
                 finds it through the window's grid field, by the orbit
                 nearest the pointer (`Get_Orbit_From_X_Y_`, geo.cpp:305-
                 351; mainscr.cpp:2119-2163) — `belt_point` does the same
                 sum on HD's pointer, and the click goes out as the native
                 point the engine scans itself (work order 310; v2 the
                 same, mainscr.cpp:2343-2380, geo.cpp:303).
  TRANSCRIPTION  what turns: in the original only the planets spin
                 (`_ship_frame % frame_count`); where a planet stands is
                 fixed for the turn (the stardate picks it, geo.cpp:246).
                 HD's planets are its discs, as before.
"""
import math
import random

import pygame

#: `_orbit_consts` (geo.cpp:5-13); orbit k uses entry k + 1.
ORBIT_CONSTS = ((225, 118), (464, 242), (704, 372), (949, 502),
                (1199, 632), (1423, 751), (1650, 873))
#: The original window's view in native px, and the rings' centre in it.
VIEW = (322, 183)
VIEW_CENTRE = (162, 91)
#: The rings' core, FONTS.LBX 1 index 0x3E, and its sides: the pictures'
#: 0x3B-0x3D share the other two of the three px (343 / 301 / 413 px on
#: ring 0x4F), drawn as their mean (24, 28, 64).
RING = (40, 52, 88)
RING_SIDE = (24, 28, 64)
RING_WIDTH = 3
#: `_rot_plan_dim` by planet size; a gas giant is drawn HUGE.
PLANET_DIM = (0x13, 0x14, 0x16, 0x16, 0x18)
HUGE = 4
PIERCE = 2
#: BUFFER0.LBX 0x5B, per frame (= orbit): the dots it holds, measured.
BELT_DOTS = (449, 853, 856, 1181, 1332)
BELT_GREYS = ((36, 36, 40), (44, 44, 52), (72, 72, 80))
BELT_BAND = (0.94, 1.05)
SUPERSAMPLE = 3
#: `angle::sin_table` (angle.cpp:136-226): sin of 0..89 degrees * 65536.
SIN_TABLE = tuple(int(round(math.sin(math.radians(d)) * 65536))
                  for d in range(90))


def _sin(angle, magnitude):
    """`angle::Sin` (angle.cpp:288-336) for magnitude >= 0."""
    a = angle % 360

    def t(i):
        return (SIN_TABLE[i] * magnitude + 0x8000) >> 16
    if a < 90:
        return t(a)
    if a == 90:
        return magnitude
    if a < 180:
        return t(180 - a)
    if a < 270:
        return -t(a - 180)
    return -magnitude if a == 270 else -t(360 - a)


def _div(a, b):
    """C's integer division, truncating towards zero."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


#: `angle::_atan_lookup_table` (angle.cpp:5-14).
ATAN_TABLE = (
    0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 4, 5, 5, 6, 6, 7,
    7, 8, 8, 8, 9, 9, 10, 10, 11, 11, 11, 12, 12, 13, 13, 14,
    14, 14, 15, 15, 16, 16, 16, 17, 17, 18, 18, 18, 19, 19, 20, 20,
    20, 21, 21, 22, 22, 22, 23, 23, 24, 24, 24, 25, 25, 25, 26, 26,
    26, 27, 27, 27, 28, 28, 29, 29, 29, 30, 30, 30, 31, 31, 31, 32,
    32, 32, 32, 33, 33, 33, 34, 34, 34, 35, 35, 35, 36, 36, 36, 36,
    37, 37, 37, 38, 38, 38, 38, 39, 39, 39, 39, 40, 40, 40, 40, 41,
    41, 41, 41, 42, 42, 42, 42, 43, 43, 43, 43, 44, 44, 44, 44, 45)


def _angle(dx, dy):
    """TRANSCRIPTION `angle::Get_Angle_` (angle.cpp:28-81)."""
    if dx == 0:
        return 270 if dy < 0 else (90 if dy > 0 else 0)
    if dy == 0:
        return 180 if dx < 0 else 0
    if dx < 0:
        nx, ny, base = ((-dx, -dy, 180) if dy < 0 else (dy, -dx, 90))
    else:
        nx, ny, base = ((dx, dy, 0) if dy > 0 else (-dy, dx, 270))
    if ny == nx:
        a = 45
    elif ny > nx:
        a = 90 - ATAN_TABLE[(nx << 7) // ny]
    else:
        a = ATAN_TABLE[(ny << 7) // nx]
    a += base
    return 0 if a == 360 else a


def orbit_from_xy(x, y):
    """TRANSCRIPTION `GEO::Get_Orbit_From_X_Y_` (geo.cpp:305-351): the
    orbit 0..4 whose ellipse lies nearest (x, y) — native px, the hit
    centre LESS the pointer, as the window's scan passes them
    (mainscr.cpp:2128, :2149) — or -1 (the centre itself, or nearest the
    rings inside orbit 0 or outside orbit 4)."""
    if x == 0 and y == 0:
        return -1
    best, best_d = -1, None
    for i, (rx, ry) in enumerate(ORBIT_CONSTS):
        a = _angle(ry * x, rx * -y)
        c = _sin(a + 90, rx)
        c = _div(c + 10, 10) if c + 5 >= 0 else _div(c, 10)
        s = _sin(a, ry)
        s = _div(s, 10) if s - 5 >= 0 else _div(s - 10, 10)
        d = (c - x) ** 2 + (s + y) ** 2
        if best_d is None or d < best_d:
            best, best_d = i, d
    return best - 1 if 0 < best < 6 else -1


#: The window's scan centre, off the window's corner (mainscr.cpp:2122-
#: 2123: `_system_display_base_x + 171`, `+ 134`) — three native px up and
#: left of the rings' drawn centre (sys.cpp:1830-1834: the grid field's
#: corner + 0xA1, + 0x5A); the original's own offset, kept.
SCAN_CENTRE = (171, 134)
DRAWN_CENTRE = (0xA1, 0x5A)


def belt_point(model, pointer):
    """TRANSCRIPTION `belt_hit` — the system window's grid scan
    (`Scan_System_Display_Fields_` part 4, mainscr.cpp:2119-2163): the
    pointer as the native point it stands for in the window — the rings'
    drawn centre off the grid field's corner plus the pointer's offset
    from HD's drawn centre at HD's scale (the frame `draw` drew in) — and
    the first asteroid belt of the star, in its planet list's order, on
    the orbit `orbit_from_xy` names from the scan centre. (native point,
    belt) or None: only inside the grid field (sys.cpp:1922-1931), where
    the original's click lands."""
    at, grid, corner = (model.get("frame"), model.get("grid"),
                        model.get("corner"))
    if at is None or grid is None or corner is None:
        return None
    s, cx, cy = at
    if s <= 0:
        return None
    nx = grid[0] + DRAWN_CENTRE[0] + int(round((pointer[0] - cx) / s))
    ny = grid[1] + DRAWN_CENTRE[1] + int(round((pointer[1] - cy) / s))
    if not (grid[0] <= nx <= grid[2] and grid[1] <= ny <= grid[3]):
        return None
    orbit = orbit_from_xy(corner[0] + SCAN_CENTRE[0] - nx,
                          corner[1] + SCAN_CENTRE[1] - ny)
    if orbit < 0:
        return None
    belt = next((b for b in model.get("asteroids", ())
                 if b["orbit"] == orbit), None)
    return None if belt is None else ((nx, ny), belt)


def orbit_place(star, orbit, stardate):
    """TRANSCRIPTION `GEO::Get_Orbit_Display_X_Y` (geo.cpp:244-283): a
    planet's place off the orbit centre in native px, from the star, the
    orbit and the stardate alone — for a window that has no engine field
    to read it off (the Leaders screen's system display)."""
    angle = _div((int(star) * 7 + int(stardate)) * 5311,
                 int(orbit) * 100 + int(star) + 150) % 360
    rx, ry = ORBIT_CONSTS[int(orbit) + 1]
    x = _sin(angle + 90, rx) + 5
    y = _sin(angle, ry) - 5
    return (_div(x + 5 if x >= 0 else x - 5, 10),
            -_div(y + 5 if y >= 0 else y - 5, 10))


def frame(view):
    """(scale, centre x, centre y): the original's view fitted into `view`,
    the rings' centre where it stands in it."""
    s = min(view.w / VIEW[0], view.h / VIEW[1])
    x0 = view.x + (view.w - VIEW[0] * s) / 2.0
    y0 = view.y + (view.h - VIEW[1] * s) / 2.0
    return s, x0 + VIEW_CENTRE[0] * s, y0 + VIEW_CENTRE[1] * s


def radii(orbit, s):
    rx, ry = ORBIT_CONSTS[orbit + 1]
    return rx / 10.0 * s, ry / 10.0 * s


def planet_dim(planet):
    return PLANET_DIM[HUGE if planet.get("type") == 2 else
                      max(0, min(HUGE, int(planet.get("size", 0))))]


def place(planet, s, cx, cy):
    """The planet's centre in the window, from the engine's own place."""
    ax, ay = planet.get("at", (0, 0))
    return cx + ax * s, cy + ay * s


#: Made once, drawn every frame (audit pass 3, measured: 5-20 ms a ring at the
#: sizes of a 1080p window, up to 1332 dots a belt). Both caches are keyed on
#: EVERY value that goes into the picture — the integers handed to pygame, not
#: the floats they came from — so a cached picture is the one the same call
#: would have drawn; a bounded dict, cleared when full.
_RINGS, _BELTS, _CACHE_MAX = {}, {}, 96
#: ... and by memory as well: a ring is up to 8 MB at 4K, so the count alone
#: says nothing. Each cache is cleared when its pictures pass this many bytes.
_CACHE_BYTES = 48 * 1024 * 1024
_held = {"rings": 0, "belts": 0}


def _remember(cache, name, key, value, picture):
    """Keep `value` under `key`; start the cache over when it is full by
    count or by the bytes of its pictures."""
    size = picture.get_width() * picture.get_height() * 4 if picture else 0
    if len(cache) >= _CACHE_MAX or _held[name] + size > _CACHE_BYTES:
        cache.clear()
        _held[name] = 0
    cache[key] = value
    _held[name] += size


def _ring_picture(orbit, s, hole_at, core_rgb, core_a, side_rgb):
    """The ring's antialiased picture (w x h) and its size. `hole_at`
    is (x, y, r) in the supersampled picture's own pixels, or None."""
    rx, ry = radii(orbit, s)
    k = SUPERSAMPLE
    w, h = int(2 * rx + 6), int(2 * ry + 6)
    side = max(1, int(round(RING_WIDTH * s * k)))
    core = max(1, int(round(s * k)))
    key = (w, h, int(2 * rx * k), int(2 * ry * k), side, core,
           core_rgb, core_a, None if side_rgb is None else tuple(side_rgb),
           hole_at(w, h) if callable(hole_at) else hole_at)
    hit = _RINGS.get(key)
    if hit is not None:
        return hit, w, h
    big = pygame.Surface((w * k, h * k), pygame.SRCALPHA)
    half = (side - core) // 2
    if side_rgb is not None:
        pygame.draw.ellipse(big, tuple(side_rgb) + (255,), pygame.Rect(
            3 * k - half, 3 * k - half, int(2 * rx * k) + 2 * half,
            int(2 * ry * k) + 2 * half), side)
    pygame.draw.ellipse(big, core_rgb + (core_a,), pygame.Rect(
        3 * k, 3 * k, int(2 * rx * k), int(2 * ry * k)), core)
    if key[-1] is not None:
        hx, hy, hr = key[-1]
        pygame.draw.circle(big, (0, 0, 0, 0), (hx, hy), hr)
    small = pygame.transform.smoothscale(big, (w, h))
    _remember(_RINGS, "rings", key, small, small)
    return small, w, h


def ring(surface, orbit, s, cx, cy, hole=None, colours=None):
    """One orbit's ellipse, antialiased, with `hole` (x, y, r) kept clear;
    `colours` (core, side) in place of the original's; side None draws
    the core alone; a core with a fourth value is drawn at that alpha."""
    core_rgb, side_rgb = colours or (RING, RING_SIDE)
    core_a = core_rgb[3] if len(core_rgb) > 3 else 255
    core_rgb = tuple(core_rgb[:3])
    k = SUPERSAMPLE
    # the hole's integers are what pygame is handed, as before
    at = None if hole is None else (lambda w, h: (
        int((hole[0] - cx + w / 2) * k), int((hole[1] - cy + h / 2) * k),
        int(hole[2] * k)))
    small, w, h = _ring_picture(orbit, s, at, core_rgb, core_a, side_rgb)
    surface.blit(small, (int(cx - w / 2), int(cy - h / 2)))


def belt(surface, orbit, s, cx, cy, seed):
    """DEVIATION `belt_drawn`: the belt's dots, the same on every frame."""
    key = (seed, orbit, s, cx, cy)
    hit = _BELTS.get(key)
    if hit is None:
        rng = random.Random(seed * 7 + orbit)
        rx, ry = radii(orbit, s)
        dot = max(1, int(round(s)))
        dots = []
        for _ in range(BELT_DOTS[orbit] if 0 <= orbit < len(BELT_DOTS) else 0):
            a = rng.uniform(0.0, 2 * math.pi)
            r = rng.uniform(*BELT_BAND)
            x = cx + math.cos(a) * rx * r
            y = cy + math.sin(a) * ry * r
            # LOOK EXCEPTION picture: an asteroid of the belt, the
            # picture's greys
            dots.append((rng.choice(BELT_GREYS), int(x), int(y)))
        if dots:
            left = min(d[1] for d in dots)
            top = min(d[2] for d in dots)
            pic = pygame.Surface(
                (max(d[1] for d in dots) + dot - left,
                 max(d[2] for d in dots) + dot - top), pygame.SRCALPHA)
            for colour, x, y in dots:     # in order: a later dot covers
                pic.fill(tuple(colour)[:3] + (255,),
                         (x - left, y - top, dot, dot))
            hit = (pic, left, top)
        else:
            hit = (None, 0, 0)
        _remember(_BELTS, "belts", key, hit, hit[0])
    if hit[0] is not None:
        surface.blit(hit[0], (hit[1], hit[2]))


def draw(surface, view, model, draw_planet, at=None, colours=None):
    """Belts, then each planet's ring and the planet itself, back to front.
    `draw_planet(planet, centre, side)` draws the disc and returns its
    hit rect. `at` (scale, centre x, centre y) in place of `frame(view)`,
    `colours` the rings' (core, side)."""
    s, cx, cy = at or frame(view)
    # the frame the window was drawn in: the belts' hit test reads it
    # (`belt_point`), so a click finds the belt where it was drawn
    model["frame"] = (s, cx, cy)
    prev = surface.get_clip()
    surface.set_clip(view)
    try:
        for orbit in model.get("belts", ()):
            if 0 <= orbit < len(BELT_DOTS):
                belt(surface, orbit, s, cx, cy, model.get("star", 0))
        hits = []
        for p in sorted(model.get("planets", ()),
                        key=lambda q: q.get("at", (0, 0))[1]):
            px, py = place(p, s, cx, cy)
            side = planet_dim(p) * s
            ring(surface, int(p["orbit"]), s, cx, cy,
                 hole=(px, py, side / 2 + PIERCE * s), colours=colours)
            hits.append((p, draw_planet(p, (int(px), int(py)),
                                        max(4, int(side)))))
        return hits
    finally:
        surface.set_clip(prev)
