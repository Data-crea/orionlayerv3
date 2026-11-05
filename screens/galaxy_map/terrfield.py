"""Territories, the computing half: who reaches where on the galaxy map.

HD EXTENSION `territory_view` (Data's mockups of 4 November 2026): every
empire gets a visible reach round its stars, drawn as a glass area with a
border, and a nebula takes the colour of the empire it lies in. The
original draws none of this, so nothing here is a transcription; what it
reads — the star's owner, the player's colour and race name — are the
fields the star names are already coloured by.

**WHY A FIELD, NOT A CIRCLE OR A HULL.** Every owned star adds a bump of
influence round itself (`R`, in parsecs); an empire's territory is where
the sum of its bumps passes a threshold. That one rule gives, without a
case of its own for any of them:

  * a rounded blob round a connected group of stars, bridging gaps that
    are shorter than about the radius — the mockups' shape;
  * a separate island for a colony that is not connected — one founded
    across the map through a wormhole, or taken from an enemy deep in
    his space. Nothing joins it to the home blob, and nothing has to:
    the islands are simply where the sum is high;
  * a territory that grows and shrinks by itself when a system is lost
    or won, because it is recomputed from the owners and from nothing
    else (no stored border, no state to go stale).

**OVERLAP IS ALLOWED AND SHOWN.** Two empires' fields may both pass the
threshold in the same place — a contested zone. The fill there is the mix
of both colours (weighted by each field's strength) and both borders are
drawn, so a war front reads as two edges crossing. The alternative, a
hard partition at the line where the fields are equal, hides that two
empires reach a system; the mockup with the overlapping nebula shows the
mixed zone Data wants.

**WHAT IT KNOWS.** Only owners the player knows (`renderer.star_label`'s
rule, the one the star names follow): an unvisited system of an empire not
met has no territory, so the map never says what the game does not.

Pure numpy and no pygame; `terrdraw` puts it on the screen.
"""
import numpy as np

#: The world's parsec: `GEO::Parsecs_Between_Stars_` divides the squared
#: distance by 900 (geo.cpp:73-100; `distance.py`).
PARSEC = 30.0
#: How far an owned star reaches, in parsecs, before the sum of bumps is
#: asked. A lone star's territory is a disc of about 0.7 of this.
RADIUS_PC = 4.0
#: Where the sum of bumps counts as inside. A single star's centre is 1.0.
THRESHOLD = 0.25
#: The grid's cell in world units: ~2 px on screen at the widest view of a
#: 1080p window, fine enough for a smooth edge and cheap on a 1518 x 1200
#: galaxy (about 500 x 400 cells).
CELL = 3.0
#: How far inside the edge the glass stays strong, in field units: the
#: border is the strongest, the inside a third of it (Data: "außenränder
#: kräftiger als innen").
EDGE_FALL = 0.10
INNER = 0.35
#: The colour's own brightness deep inside, against 1.0 at the border.
DEEP = 0.55
#: The edge of the cover ramps over this much field, so a bilinear scale of
#: the grid shows no steps.
RAMP = 0.05


def radius_world():
    return RADIUS_PC * PARSEC


class Empire:
    """One player's known stars: `colour` is the player's colour index
    (0..7, the one star names and ships use), `name` the race name."""

    def __init__(self, player, colour, name, points):
        self.player = player
        self.colour = colour
        self.name = name
        self.points = points            # [(x, y)] in world units


def empires(stars, players, player_num, omniscient, label_of):
    """The empires with at least one star the player knows the owner of,
    in player order. `label_of(star)` is `renderer.star_label` bound to
    the player: a star whose name is shown is a star whose owner is."""
    by_player = {}
    for s in stars:
        owner = s.owner
        if not (0 <= owner < len(players)):
            continue
        if not label_of(s):
            continue
        by_player.setdefault(owner, []).append((float(s.x), float(s.y)))
    out = []
    for owner in sorted(by_player):
        p = players[owner]
        colour = getattr(p, "color", None)
        if colour is None:
            continue
        name = (getattr(p, "race_name", "") or "").strip()
        out.append(Empire(owner, int(colour), name, by_player[owner]))
    return out


def smoothstep(lo, hi, v):
    t = np.clip((v - lo) / (hi - lo), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def field(points, x0, y0, w, h, cell=CELL, radius=None):
    """The summed influence of `points` on a w x h grid whose (0, 0) cell
    is at world (x0, y0). Each bump is (1 - (d/R)^2)^2 inside R, 0 beyond
    — compact, so a star only touches the cells near it."""
    radius = radius or radius_world()
    f = np.zeros((h, w), np.float32)
    r_cells = int(radius / cell) + 1
    for (px, py) in points:
        ci = int(round((px - x0) / cell))
        cj = int(round((py - y0) / cell))
        i0, i1 = max(0, ci - r_cells), min(w, ci + r_cells + 1)
        j0, j1 = max(0, cj - r_cells), min(h, cj + r_cells + 1)
        if i0 >= i1 or j0 >= j1:
            continue
        xs = x0 + np.arange(i0, i1, dtype=np.float32) * cell - px
        ys = y0 + np.arange(j0, j1, dtype=np.float32) * cell - py
        d2 = (ys[:, None] ** 2 + xs[None, :] ** 2) / (radius * radius)
        bump = np.where(d2 < 1.0, (1.0 - d2) ** 2, 0.0)
        f[j0:j1, i0:i1] += bump.astype(np.float32)
    return f


class Territory:
    """The territories of one state: what to blit and what to outline.

    `fill` is an (h, w, 4) uint8 array, straight alpha at FULL opacity —
    the player's opacity slider is applied when it is drawn, so moving it
    costs nothing. `tint` is (h, w, 3) float colours and `cover` (h, w)
    in 0..1 for the nebulas. `loops[colour index]` are the borders as
    closed point arrays in world units. `key` says what it was built from.
    """

    def __init__(self, key, x0, y0, fill, tint, cover, loops, names):
        self.key = key
        self.x0, self.y0 = x0, y0
        self.fill = fill
        self.tint = tint
        self.cover = cover
        self.loops = loops
        self.names = names
        self.h, self.w = cover.shape


def state_key(emps, colours):
    return (tuple((e.player, e.colour, tuple(e.points)) for e in emps),
            tuple(tuple(c[:3]) for c in colours))


def build(emps, colours, cell=CELL):
    """The territories of `emps`, `colours[i]` the RGB of colour index i.
    None when nobody holds a known star."""
    if not emps:
        return None
    radius = radius_world()
    pts = [p for e in emps for p in e.points]
    pad = radius + 2 * cell
    x0 = min(p[0] for p in pts) - pad
    y0 = min(p[1] for p in pts) - pad
    w = int((max(p[0] for p in pts) + pad - x0) / cell) + 2
    h = int((max(p[1] for p in pts) + pad - y0) / cell) + 2

    acc = np.zeros((h, w, 3), np.float64)       # sum of colour * weight
    wsum = np.zeros((h, w), np.float64)
    alpha_rest = np.ones((h, w), np.float64)    # product of (1 - a_o)
    cover_rest = np.ones((h, w), np.float64)
    loops = {}
    for e in emps:
        f = field(e.points, x0, y0, w, h, cell, radius)
        cover = smoothstep(THRESHOLD - RAMP, THRESHOLD + RAMP, f)
        # strongest at the border, a third of it deep inside
        edge = np.exp(-np.maximum(f - THRESHOLD, 0.0) / EDGE_FALL)
        a = cover * (INNER + (1.0 - INNER) * edge)
        col = np.asarray(colours[e.colour % len(colours)][:3], np.float64)
        weight = f.astype(np.float64) ** 2          # defined past the edge
        # the inside is also DARKER, not only fainter: a bright colour
        # laid over the picture lifts what a star name stands on, and the
        # names must keep their contrast (006d, 3.4:1 on the background)
        shade = DEEP + (1.0 - DEEP) * edge
        acc += (weight * shade)[..., None] * col
        wsum += weight
        alpha_rest *= 1.0 - a
        cover_rest *= 1.0 - cover
        loops.setdefault(e.colour, []).extend(
            contours(f, THRESHOLD, x0, y0, cell))
    rgb = acc / np.maximum(wsum, 1e-9)[..., None]   # weights carry the shade
    fill = np.zeros((h, w, 4), np.uint8)
    fill[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    fill[..., 3] = np.clip((1.0 - alpha_rest) * 255.0 + 0.5, 0, 255
                           ).astype(np.uint8)
    names = {e.colour: e.name for e in emps}
    return Territory(state_key(emps, colours), x0, y0, fill,
                     rgb.astype(np.float32),
                     (1.0 - cover_rest).astype(np.float32), loops, names)


# ── Marching squares ─────────────────────────────────────

#: Per case (bit 1 = a: (i, j), 2 = b: (i+1, j), 4 = c: (i+1, j+1),
#: 8 = d: (i, j+1)), the pairs of cell edges a border runs between:
#: B bottom a-b, R right b-c, T top d-c, L left a-d. 5 and 10 are the
#: saddles, resolved by the cell's centre in `_segments`.
_CASES = {1: (("L", "B"),), 2: (("B", "R"),), 3: (("L", "R"),),
          4: (("R", "T"),), 6: (("B", "T"),), 7: (("L", "T"),),
          8: (("L", "T"),), 9: (("B", "T"),), 11: (("R", "T"),),
          12: (("L", "R"),), 13: (("B", "R"),), 14: (("L", "B"),)}


def _edge_id(edge, i, j):
    """A cell edge by the grid edge it is, shared by both cells."""
    if edge == "B":
        return ("h", i, j)
    if edge == "T":
        return ("h", i, j + 1)
    if edge == "L":
        return ("v", i, j)
    return ("v", i + 1, j)


def _segments(f, level):
    """[(edge id, edge id)] of the border through every mixed cell."""
    inside = f > level
    a, b = inside[:-1, :-1], inside[:-1, 1:]
    d, c = inside[1:, :-1], inside[1:, 1:]
    case = (a.astype(np.uint8) | (b.astype(np.uint8) << 1)
            | (c.astype(np.uint8) << 2) | (d.astype(np.uint8) << 3))
    out = []
    for j, i in zip(*np.nonzero((case > 0) & (case < 15))):
        k = int(case[j, i])
        if k in (5, 10):
            centre = (f[j, i] + f[j, i + 1] + f[j + 1, i] + f[j + 1, i + 1]
                      ) / 4.0 > level
            if (k == 5) == centre:
                pairs = (("L", "T"), ("B", "R"))
            else:
                pairs = (("L", "B"), ("R", "T"))
        else:
            pairs = _CASES[k]
        for e0, e1 in pairs:
            out.append((_edge_id(e0, i, j), _edge_id(e1, i, j)))
    return out


def _chain(segments):
    """Edge-id pairs joined into runs; every border here is closed (the
    grid's rim is outside every bump), so each run ends where it began."""
    nbr = {}
    for p, q in segments:
        nbr.setdefault(p, []).append(q)
        nbr.setdefault(q, []).append(p)
    seen, runs = set(), []
    for start in nbr:
        if start in seen:
            continue
        run, cur, prev = [start], start, None
        seen.add(start)
        while True:
            nxt = [n for n in nbr[cur] if n != prev and n not in seen]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            seen.add(cur)
            run.append(cur)
        if len(run) > 3:
            runs.append(run)
    return runs


def _point(eid, f, level, x0, y0, cell):
    kind, i, j = eid
    if kind == "h":
        fa, fb = f[j, i], f[j, i + 1]
        t = (level - fa) / (fb - fa) if fb != fa else 0.5
        return x0 + (i + t) * cell, y0 + j * cell
    fa, fb = f[j, i], f[j + 1, i]
    t = (level - fa) / (fb - fa) if fb != fa else 0.5
    return x0 + i * cell, y0 + (j + t) * cell


def chaikin(pts):
    """One corner-cutting pass on a closed loop: the grid's 3-unit steps
    leave visible corners at a close zoom."""
    nxt = np.roll(pts, -1, axis=0)
    out = np.empty((len(pts) * 2, 2), pts.dtype)
    out[0::2] = pts * 0.75 + nxt * 0.25
    out[1::2] = pts * 0.25 + nxt * 0.75
    return out


def contours(f, level, x0, y0, cell=CELL):
    """The closed borders of the region where `f` passes `level`, as
    (n, 2) float arrays of world points — one per island or hole."""
    out = []
    for run in _chain(_segments(f, level)):
        pts = np.array([_point(e, f, level, x0, y0, cell) for e in run],
                       np.float64)
        out.append(chaikin(pts))
    return out
