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


def ring(surface, orbit, s, cx, cy, hole=None):
    """One orbit's ellipse, antialiased, with `hole` (x, y, r) kept clear."""
    rx, ry = radii(orbit, s)
    k = SUPERSAMPLE
    w, h = int(2 * rx + 6), int(2 * ry + 6)
    big = pygame.Surface((w * k, h * k), pygame.SRCALPHA)
    side = max(1, int(round(RING_WIDTH * s * k)))
    core = max(1, int(round(s * k)))
    half = (side - core) // 2
    pygame.draw.ellipse(big, RING_SIDE + (255,), pygame.Rect(
        3 * k - half, 3 * k - half, int(2 * rx * k) + 2 * half,
        int(2 * ry * k) + 2 * half), side)
    pygame.draw.ellipse(big, RING + (255,), pygame.Rect(
        3 * k, 3 * k, int(2 * rx * k), int(2 * ry * k)), core)
    if hole is not None:
        hx, hy, hr = hole
        pygame.draw.circle(big, (0, 0, 0, 0),
                           (int((hx - cx + w / 2) * k), int((hy - cy + h / 2) * k)),
                           int(hr * k))
    small = pygame.transform.smoothscale(big, (w, h))
    surface.blit(small, (int(cx - w / 2), int(cy - h / 2)))


def belt(surface, orbit, s, cx, cy, seed):
    """DEVIATION `belt_drawn`: the belt's dots, the same on every frame."""
    rng = random.Random(seed * 7 + orbit)
    rx, ry = radii(orbit, s)
    dot = max(1, int(round(s)))
    for _ in range(BELT_DOTS[orbit] if 0 <= orbit < len(BELT_DOTS) else 0):
        a = rng.uniform(0.0, 2 * math.pi)
        r = rng.uniform(*BELT_BAND)
        x = cx + math.cos(a) * rx * r
        y = cy + math.sin(a) * ry * r
        # LOOK EXCEPTION picture: an asteroid of the belt, the picture's greys
        surface.fill(rng.choice(BELT_GREYS), (int(x), int(y), dot, dot))


def draw(surface, view, model, draw_planet):
    """Belts, then each planet's ring and the planet itself, back to front.
    `draw_planet(planet, centre, side)` draws the disc and returns its
    hit rect."""
    s, cx, cy = frame(view)
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
                 hole=(px, py, side / 2 + PIERCE * s))
            hits.append((p, draw_planet(p, (int(px), int(py)),
                                        max(4, int(side)))))
        return hits
    finally:
        surface.set_clip(prev)
