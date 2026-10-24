"""A planet as a turning sphere, built from its flat surface map — work
order 331. HD EXTENSION `rotating_planets` (the original has static sprites).

`frame(res, climate, side, seed)` is the picture every place that draws a
planet asks for: a `side` px square, the sphere inside it with its glow
ring, lit from the upper left, at the angle the planet has NOW
(`core.planetspin`). Nothing is stored in the game.

**LIGHT STAYS, THE SURFACE TURNS.** The map has no light in it. The shade,
the darkening to the limb, the atmosphere over the rim and the glow ring
are computed once per (type, side) and are the same for every angle; only
the sampling column moves. A frame is then one bilinear gather and one
multiply-add over the sphere's pixels.

**WHY IT DOES NOT SHIMMER.** The map is first averaged DOWN to about 1.25
map pixels per screen pixel at the sphere's centre (`smoothscale`, a
cached mip per width bucket), never sampled sparsely, and the gather is
bilinear in both axes with the columns wrapping. The limb is dark and its
coverage is anti-aliased analytically, so what is compressed there is not
bright. At sizes above the map it is magnified bilinearly.

**WHEN IT IS REDRAWN.** A frame is made when the angle has moved by half a
screen pixel at the centre and at most `MIN_STEP` seconds after the last
one, and only for a planet that is asked for: a hidden planet costs
nothing (`planetspin.touch` tells `core.drawgate` a frame holds one).

**A TYPE WITHOUT A SPHERE** (no map, or a mod's old-style full picture,
see `mode`) returns None here and the caller draws what it had.
"""
import logging
import math
import os

import numpy as np
import pygame

from core import planetspin

log = logging.getLogger("planets")

MAP_DIR = "assets/shared/planets/"
SURFACE = MAP_DIR + "{}_surface.png"
CLOUDS = MAP_DIR + "{}_clouds.png"
#: Sphere types with a map in the base pack: PLANET_CLIMATE's ten
#: (orion2_consts.h:409-421) and `volcanic`, which the game has no climate
#: for (WO 331, a question to Data) and which is therefore only reachable by
#: name.
MIN_STEP = 1 / 24
#: Pixels of a frame made per call: about 4 ms, so no single draw is long.
SLICE = 40000
#: Map pixels per screen pixel at the centre, and the width buckets of a mip.
OVERSAMPLE = 1.25
BUCKET = 64
CACHE = 32

_dims = {}       # path -> (stamp, native width)
_maps = {}       # (path, stamp, width) -> (rgb+emissive uint8 (h, w, 4))
_geo = {}        # side -> geometry shared by every type
_types = {}      # (name, side, stamps) -> per-type constants
_jobs = {}       # key -> the frame being made
_last = {}       # (name, side, seed) -> (step, surface)


def surface_path(res, name):
    return res.resolve(SURFACE.format(name))


def in_base(root):
    """True for the tree and the base pack, the two places OrionLayer's own
    files live; any other root is a mod's."""
    from core import basepack
    from core.config import BASE_DIR
    return os.path.abspath(root) in (os.path.abspath(BASE_DIR),
                                     os.path.abspath(basepack.base_dir()))


def mod_map(res, name):
    """True when a mod supplies this type's surface map."""
    path = surface_path(res, name)
    return bool(path) and not any(
        os.path.abspath(path).startswith(os.path.abspath(b) + os.sep)
        for b in _base_roots())


def _base_roots():
    from core import basepack
    from core.config import BASE_DIR
    return (BASE_DIR, basepack.base_dir())


def _stamp(path):
    try:
        return os.stat(path).st_mtime_ns
    except OSError:
        return None


def _bucket(side, native_w):
    want = math.ceil(math.pi * side * OVERSAMPLE / BUCKET) * BUCKET
    return int(min(native_w, max(BUCKET, want)))


def _native_width(path):
    """The map's own width, read once from the file's header."""
    stamp = _stamp(path)
    hit = _dims.get(path)
    if hit is None or hit[0] != stamp:
        try:
            hit = (stamp, pygame.image.load(path).get_width())
        except (pygame.error, OSError):
            hit = (stamp, BUCKET)
        _dims[path] = hit
    return hit[1]


def _emissive(rgb):
    """Where the map itself glows: bright and warm (lava, radiated veins)."""
    r = rgb[..., 0].astype(np.float32)
    b = rgb[..., 2].astype(np.float32)
    lit = np.clip((r - 130.0) / 100.0, 0, 1) * np.clip((r - b - 40.0) / 80.0, 0, 1)
    return (lit * 255).astype(np.uint8)


def _mip(path, width, alpha=False):
    """The map as a (h, w, 4) uint8 array at `width` columns: rgb and either
    the emissive mask (a surface) or the cloud alpha (a cloud map)."""
    stamp = _stamp(path)
    key = (path, stamp, width, alpha)
    hit = _maps.get(key)
    if hit is not None:
        return hit
    try:
        img = pygame.image.load(path)
    except (pygame.error, OSError) as err:
        log.warning("planets: %s will not load (%s)", path, err)
        _maps[key] = None
        return None
    w0, h0 = img.get_size()
    if w0 < 8 or h0 < 4:
        log.warning("planets: %s is %dx%d — too small, not used", path, w0, h0)
        _maps[key] = None
        return None
    height = max(2, width // 2)
    if (w0, h0) != (width, height):
        img = pygame.transform.smoothscale(
            img.convert_alpha() if alpha else img.convert(), (width, height))
    rgb = pygame.surfarray.array3d(img).swapaxes(0, 1)
    if alpha:
        extra = pygame.surfarray.array_alpha(img.convert_alpha()).swapaxes(0, 1)
    else:
        extra = _emissive(rgb)
    out = np.dstack([rgb, extra]).astype(np.uint8)
    if len(_maps) > 24:
        _maps.clear()
    _maps[key] = out
    return out


def _geometry(side, width):
    """What depends on the picture's size alone: per pixel of the sphere and
    its ring, the map column and rows to read, the unit normal's parts and
    the sphere's coverage."""
    key = (side, width)
    hit = _geo.get(key)
    if hit is not None:
        return hit
    cfg = planetspin.config()
    radius = side / 2.0 * (1.0 - float(cfg["glow_width"]))
    centre = side / 2.0
    ys, xs = np.mgrid[0:side, 0:side].astype(np.float32)
    dx = (xs + 0.5 - centre) / radius
    dy = (ys + 0.5 - centre) / radius
    rr = np.hypot(dx, dy)
    ring = side / 2.0 / radius                    # the picture's edge, in radii
    keep = rr < ring
    dx, dy, rr = dx[keep], dy[keep], rr[keep]
    # sampling is clamped inside the disc, so the coverage's soft edge reads
    # real map pixels, not the void beyond them
    inside = np.minimum(rr, 1.0 - 1e-4)
    scale = np.where(rr > 0, inside / np.maximum(rr, 1e-6), 1.0)
    nx, ny = dx * scale, dy * scale
    nz = np.sqrt(np.maximum(1.0 - nx * nx - ny * ny, 0.0))
    height = max(2, width // 2)
    lon = np.arctan2(nx, nz)                       # -pi/2 .. pi/2, east right
    lat = np.arcsin(np.clip(ny, -1, 1))            # down is south
    u = (lon / (2 * math.pi) + 0.5) * width
    v = np.clip((lat / math.pi + 0.5) * height - 0.5, 0, height - 1.001)
    v0 = np.floor(v).astype(np.int32)
    geo = {
        "keep": np.flatnonzero(keep.ravel()), "side": side,
        "u": u.astype(np.float32), "v0": v0, "fv": (v - v0).astype(np.float32)[:, None],
        "nx": nx.astype(np.float32), "ny": ny.astype(np.float32),
        "nz": nz.astype(np.float32), "rr": rr.astype(np.float32),
        "radius": radius, "ring": ring,
        # one pixel's coverage by the sphere: 1 inside, 0 beyond, soft across
        "cov": np.clip((1.0 - rr) * radius + 0.5, 0, 1).astype(np.float32),
    }
    if len(_geo) > CACHE:
        _geo.clear()
    _geo[key] = geo
    return geo


def _constants(name, geo, vals, cfg):
    """The light, the limb, the rim and the glow ring: what does not turn."""
    nx, ny, nz, rr = geo["nx"], geo["ny"], geo["nz"], geo["rr"]
    lx, ly, lz = (float(c) for c in vals["light"])
    norm = math.sqrt(lx * lx + ly * ly + lz * lz) or 1.0
    lam = np.clip((nx * lx + ny * ly + nz * lz) / norm, 0.0, 1.0)
    amb = float(cfg["ambient"])
    shade = amb + (1.0 - amb) * lam ** 0.85
    # the limb darkens by the view angle (nz = 1 at the centre, 0 at the edge)
    shade *= 1.0 - float(cfg["limb"]) * (1.0 - nz) ** 1.4
    shade = np.clip(shade * 1.12, 0.0, 1.15)
    glow = np.array(vals["glow"], np.float32)[None, :]
    strength = float(vals["glow_strength"])
    lit = 0.35 + 0.65 * lam
    cov = geo["cov"]
    # the atmosphere seen through the rim, brighter on the lit side
    rim = float(cfg["rim"]) * strength * (1.0 - nz) ** 3 * lit
    # the ring outside: strongest at the limb, gone at the picture's edge
    out = np.clip((rr - 1.0) / max(geo["ring"] - 1.0, 1e-3), 0, 1)
    ring_a = strength * (1.0 - out) ** 2.2 * lit * (rr >= 1.0 - 1.0 / geo["radius"])
    a_s = cov
    alpha = a_s + ring_a * (1.0 - a_s)
    safe = np.maximum(alpha, 1e-4)
    w_sphere = a_s / safe                          # the sphere's share of the pixel
    k = (shade * w_sphere).astype(np.float32)
    base = (glow * (ring_a * (1.0 - a_s) / safe)[:, None]
            + glow * (rim * w_sphere)[:, None])
    return {
        "k": k[:, None], "w": w_sphere.astype(np.float32)[:, None],
        "c": base.astype(np.float32),
        "alpha": np.clip(alpha * 255.0 + 0.5, 0, 255).astype(np.uint8),
        "emis": float(vals["emissive"]),
    }


def _sample(m, u, v0, fv, shift):
    """Bilinear read of the (h, w, 4) map at columns `u + shift`."""
    width = m.shape[1]
    uu = u + shift
    i0f = np.floor(uu)
    fu = (uu - i0f)[:, None]
    i0 = i0f.astype(np.int64) % width
    i1 = (i0 + 1) % width
    top = m[v0, i0] * (1 - fu) + m[v0, i1] * fu
    bot = m[v0 + 1, i0] * (1 - fu) + m[v0 + 1, i1] * fu
    return top * (1 - fv) + bot * fv


class Job:
    """One frame being made, in slices of at most `SLICE` pixels a call, so
    a big sphere (the battle's, at a high zoom) never costs one long frame:
    the picture on screen is the last finished one until the next is done."""

    def __init__(self, res, name, side, seed, climate, t):
        cfg = planetspin.config(res)
        path = surface_path(res, name)
        vals = planetspin.type_values(cfg, name)
        width = _bucket(side, _native_width(path))
        self.map = _mip(path, width)
        self.ok = self.map is not None
        if not self.ok:
            return
        self.side = side
        self.geo = _geometry(side, width)
        ckey = (name, side, width, _stamp(path), repr(vals), repr(cfg))
        consts = _types.get(ckey)
        if consts is None:
            if len(_types) > CACHE:
                _types.clear()
            consts = _types[ckey] = _constants(name, self.geo, vals, cfg)
        self.consts = consts
        ang = planetspin.angle(cfg, name, climate, seed, t)
        self.shift = -ang / (2 * math.pi) * width     # prograde: to the right
        self.cloud = _cloud_map(res, name, width)
        self.cloud_shift = self.shift * float(cfg["cloud_speed"])
        # the frame's own buffer, the type's alpha already in it: slices
        # land in it as they are made, so finishing is one conversion
        if "base" not in consts:
            consts["base"] = np.zeros((side * side, 4), np.uint8)
            consts["base"][self.geo["keep"], 3] = consts["alpha"]
        self.buf = consts["base"].copy()
        self.pos = 0

    def run(self, limit=SLICE):
        """Make the next slice; True when the frame is whole."""
        g, c = self.geo, self.consts
        a, b = self.pos, min(self.pos + limit, len(g["u"]))
        sl = slice(a, b)
        smp = _sample(self.map, g["u"][sl], g["v0"][sl], g["fv"][sl],
                      self.shift)
        rgb, emis = smp[:, :3], smp[:, 3:4] / 255.0
        k = c["k"][sl]
        if c["emis"] > 0:                          # lava keeps its own light
            k = k + (c["w"][sl] - k) * np.clip(emis * c["emis"], 0, 1)
        if self.cloud is not None:
            cl = _sample(self.cloud, g["u"][sl], g["v0"][sl], g["fv"][sl],
                         self.cloud_shift)
            ca = cl[:, 3:4] / 255.0
            rgb = rgb * (1 - ca) + cl[:, :3] * ca
        self.buf[g["keep"][sl], :3] = np.clip(rgb * k + c["c"][sl], 0, 255)
        self.pos = b
        return b >= len(g["u"])

    def surface(self):
        out = pygame.image.frombuffer(self.buf, (self.side,) * 2, "RGBA")
        return out.convert_alpha() if pygame.display.get_surface() \
            else out.copy()


def render(res, name, side, seed=None, climate=0, t=None):
    """The whole sphere at once as an RGBA surface, or None (no map)."""
    job = Job(res, name, side, seed, climate, t)
    if not job.ok:
        return None
    while not job.run(1 << 30):
        pass
    return job.surface()


def _cloud_map(res, name, width):
    """The optional cloud layer: a map with transparency that turns at its
    own pace over the surface. None when the type has none."""
    path = res.resolve(CLOUDS.format(name))
    return _mip(path, width, alpha=True) if path else None


def frame(res, name, side, seed=None, climate=0, t=None):
    """The picture of planet `(climate, seed)` of map `name` NOW, a `side`
    px square, or None (no map). The surface is kept until the angle has
    moved half a pixel at the centre and `MIN_STEP` has passed; a new one is
    made in slices (`Job`) while the old one stays on screen."""
    side = int(side)
    if side < 4 or not surface_path(res, name):
        return None
    cfg = planetspin.config(res)
    planetspin.touch(side, cfg)
    now = planetspin.now() if t is None else t
    key = (name, side, seed, climate)
    step = int(planetspin.angle(cfg, name, climate, seed, now) * side)
    last = _last.get(key)
    job = _jobs.get(key)
    if job is None and (last is None or (
            last[0] != step and abs(now - last[2]) >= MIN_STEP)):
        job = Job(res, name, side, seed, climate, now)
        if not job.ok:
            _last[key] = (step, None, now)
            return None
        job.step, job.at = step, now
        _jobs[key] = job
    if job is not None and (job.run(1 << 30 if last is None else SLICE)):
        if len(_last) > 256:
            _last.clear()
        _last[key] = (job.step, job.surface(), job.at)
        del _jobs[key]
    last = _last.get(key)
    return last[1] if last else None


def reset():
    for d in (_dims, _maps, _geo, _types, _last, _jobs):
        d.clear()
    planetspin.reload()
