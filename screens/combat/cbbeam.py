"""The original's beams, ported — work order 199 C2 (it retires work order
197's simplified straight bolt and that marking).

TRANSCRIPTION `beam_bolt`: what `BEAMS::Fire_Weapon_` hands to
`Draw_Generic_Beam_` (beams.cpp:2233-2479) for the "Steve stuff" weapons —
mass driver, gauss, laser, particle, fusion, ion pulse, graviton, neutron,
phasor, disrupter, death and crystal ray, plasma cannon — and how
`Draw_Beam2_` (:2566-2636) draws them with `bolt.cpp`'s `Bolt_Line_`,
`Wide_Bolt_Line_` and `Bolt_Segment_` through `line::Plasma_Line_`'s
run-sliced line (line.cpp:568-844), in the weapon's sixteen colours from
`Set_Beam_Colors_` (:2481-2564) and the table of
`Build_Steve_Stuff_Struct_For_Weapon_` (:1848-2062): the head advancing
`duration` px a frame, the bolt `sfx_sprite_id` px long, stopped at a third
of the shield's diameter when the shield holds (fire result bit 0, unless
bit 1 says it pierced), `_max_frames` from the range — doubled step past six
frames. The random numbers are the original's shape (`Random_(n)` is 1..n,
random.cpp:25-36) from HD's own generator, seeded per shot, so a shot
looks the same every frame it is redrawn.

Everything is drawn in NATIVE pixels — one world pixel, as the original
draws into its 640 x 480 page — and scaled with the field by the camera.

DEVIATION `beam_fire_point`: a beam leaves the shooter's CENTRE; the
original starts it at one of the picture's fire points (`FIREPTS`, not on
the wire). The other beams (mauler, dragon and plasma breath, spatial
compressor) take their colours from BEAMS.LBX 0's palette fragments
(`Add_Weapon_Palette_Fragment_`, :1124-1192) — HD draws those as the same
bolt in that fragment's colours (`fragment_colours`).
"""
import random

from .cbbeamfx import (HEAD_WIDE, LONG_LINE, SHIELD_DIAMETERS, TAIL_WIDE,  # noqa: F401
                       colours, fx, get_angle)


# ── geometry: beams.cpp:516-532, 2099-2171 ────────────────────────────
def ship_range(x1, y1, x2, y2):
    return max(abs(x2 - x1), abs(y2 - y1))


def _cdiv(a, b):
    """C's integer division (toward zero)."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def interpolate(x, y, tx, ty, step):
    """`Rob_Interpolate_Line_`: the point `step` px along (Chebyshev)."""
    dx, dy = tx - x, ty - y
    if step < 1:
        return x, y
    if max(abs(dx), abs(dy)) <= step:
        return tx, ty
    if dx == 0:
        return x, y - step if dy <= 0 else y + step
    if dy == 0:
        return (x - step if dx <= 0 else x + step), y
    hx, hy, lx, ly = dx, dy, 0, 0
    cx, cy = dx >> 1, dy >> 1
    for _ in range(64):
        d = max(abs(cx), abs(cy))
        if d == step:
            break
        if d < step:
            lx, ly = cx, cy
            cx += _cdiv(hx - cx, 2)
            cy += _cdiv(hy - cy, 2)
        else:
            hx, hy = cx, cy
            cx += _cdiv(lx - cx, 2)
            cy += _cdiv(ly - cy, 2)
    return x + cx, y + cy


def max_frames(src, dst, f):
    """`_max_frames` of the shot (beams.cpp:2272-2292)."""
    rng = ship_range(*src, *dst)
    eff = min(max(f["length"], 60), rng)
    step = f["step"]
    frames = max(3, (rng + eff) // step)
    if frames > 6:
        step *= 2
    return max(3, (rng + eff) // step), step


def segment(src, dst, f, frame, stop_size=None, skip=0):
    """(bx1, by1, bx2, by2) of the bolt at `frame` (:2294-2368), or None on
    the frame that draws only the muzzle (frame 0) or after the last.
    `skip`: a reflected beam's tail starts that far out — a third of the
    reflection field's diameter (:2388-2395)."""
    n, step = max_frames(src, dst, f)
    if frame >= n or frame == 0:
        return None
    rng = ship_range(*src, *dst)
    head = min(max(0, step * frame), rng)
    tail = min(max(0, head - f["length"]), rng)
    if f["style"] == 2:                  # continuous: the whole way, at once
        head, tail = rng, 0
    tail = min(tail + skip, rng)
    cut = 0
    if stop_size is not None:
        cut = min(SHIELD_DIAMETERS[stop_size] // 3, f["length"] - 1)
    bx2, by2 = interpolate(*src, *dst, head - cut)
    bx1, by1 = interpolate(*src, *dst, tail) if tail else src
    return bx1, by1, bx2, by2


# ── drawing into a buffer of palette offsets: bolt.cpp ────────────────
class Canvas:
    """Native pixels (x, y) -> colour offset 0..15 of the beam's slot."""

    def __init__(self):
        self.px = {}

    def plasma_line(self, x1, y1, x2, y2, cmap):
        """`line::Plasma_Line_` (line.cpp:568-844): drawn top to bottom in
        runs, the colour index advancing one per pixel."""
        if y1 > y2:
            x1, y1, x2, y2 = x2, y2, x1, y1
        dx, xd = (x2 - x1, 1) if x2 >= x1 else (x1 - x2, -1)
        dy = y2 - y1
        idx = [0]
        x, y = x1, y1

        def put(px, py):
            self.px[(px, py)] = cmap[idx[0] & (LONG_LINE - 1)]
            idx[0] += 1
        if dx == 0:
            for k in range(dy + 1):
                put(x, y + k)
            return
        if dy == 0:
            for k in range(dx + 1):
                put(x + k * xd, y)
            return
        if dx == dy:
            for k in range(dx + 1):
                put(x + k * xd, y + k)
            return
        major, minor = (dx, dy) if dx > dy else (dy, dx)
        run = major // minor
        inc = (major % minor) * 2
        err = (major % minor) - minor * 2
        half = run // 2 + 1
        first = half
        if inc == 0:
            if run & 1 == 0:
                first -= 1
            else:
                err += minor
        elif run & 1:
            err += minor
        runs = [first]
        for _ in range(minor - 1):
            err += inc
            r = run
            if err > 0:
                r += 1
                err -= minor * 2
            runs.append(r)
        runs.append(half)
        for r in runs:
            for _ in range(r):
                put(x, y)
                if dx > dy:
                    x += xd
                else:
                    y += 1
            if dx > dy:
                y += 1
            else:
                x += xd

    def segment(self, rnd, x1, y1, x2, y2, base, span, chance, jitter,
                lo, hi, sparkles, phase, tip):
        """`Bolt_Segment_` (bolt.cpp:153-261): a gradient from `base` over
        `span`, jittered, sparkled every 8 px, clamped, the tip lit."""
        ln = max(abs(x2 - x1), abs(y2 - y1)) + 1
        step = (span << 16) // ln
        acc, r = 32000 // ln, 0
        buf = [0] * (ln + 2)
        up = y2 < y1
        for i in range(ln + 1):
            c = (acc >> 16) + r + base
            buf[(ln - i + 1) if up else (i + 1)] = c
            acc += step
            r = (rnd.randint(1, 2 * jitter + 1) - jitter) \
                if rnd.randint(1, 100) < chance else 0
        if up:
            buf[ln], buf[0] = base, base + span - 1
        else:
            buf[0], buf[ln] = base, base + span - 1
        if sparkles:
            for i in range(phase % 8, ln + 2, 8):
                buf[i] += 3
        buf = [min(hi, max(lo, c)) for c in buf]
        if tip:
            fade = 3 // tip
            if up:
                for i in range(6):
                    buf[i + 1] += fade
            elif ln > 5:
                for i in range(6):
                    buf[ln - i - 1] += fade
        buf = [min(c, base + 15) for c in buf]
        self.plasma_line(x1, y1, x2, y2, buf)

    def bolt_line(self, rnd, x1, y1, x2, y2, base, span, chance, jitter,
                  phase, tip, full, sparkles, no_sides, core_hi, core_lo,
                  side_hi, side_lo):
        """`Bolt_Line_` (bolt.cpp:263-353), its caps never asked for here
        (Draw_Beam2_ passes 0)."""
        xo, yo = (1, 0) if abs(y2 - y1) >= abs(x2 - x1) else (0, 1)
        flank = side_hi - side_lo + (3 if tip == 1 else 0)
        hi = span + base - 1
        if not no_sides:
            for s in (-1, 1):
                self.segment(rnd, x1 + s * xo, y1 + s * yo, x2 + s * xo,
                             y2 + s * yo, side_lo + base, flank, chance,
                             jitter // 2, base, hi, sparkles, phase, 0)
        rng_, cb = core_hi - core_lo, core_lo + base
        if not full:
            t = rng_ * 3
            cb += (t + (3 if t < 0 else 0)) >> 2
            rng_ = 0
        self.segment(rnd, x1, y1, x2, y2, cb, rng_, chance, jitter, base, hi,
                     sparkles, phase, tip)

    def wide_bolt_line(self, rnd, x1, y1, x2, y2, base, span, chance, jitter,
                       phase, point_source, tip, full, sparkles, core_hi,
                       core_lo, mid_hi, mid_lo, out_hi, out_lo):
        """`Wide_Bolt_Line_` (bolt.cpp:42-150): two outer and four middle
        strands from the direction's table, then the core."""
        a = get_angle(x2 - x1, y2 - y1)
        d = (((371 - a) % 360) * 2) // 45 * 12
        hi = base + span - 1
        side = jitter // 2

        def strand(k, cbase, crange, tipv):
            if point_source:
                sx, sy = x1, y1
            else:
                sx, sy = TAIL_WIDE[d + k] + x1, TAIL_WIDE[d + k + 1] + y1
            self.segment(rnd, sx, sy, HEAD_WIDE[d + k] + x2,
                         HEAD_WIDE[d + k + 1] + y2, cbase, crange, chance,
                         side, base, hi, sparkles, phase, tipv)
        for k in (8, 10):
            strand(k, base + out_lo, out_hi - out_lo, 0)
        for k in (0, 2, 4, 6):
            strand(k, base + mid_lo, mid_hi - mid_lo, tip)
        cb, cr = base + core_lo, core_hi - core_lo
        if not full:
            cb += cr * 3 // 4
            cr = 0
        self.segment(rnd, x1, y1, x2, y2, cb, cr, chance, jitter, base, hi,
                     sparkles, phase, tip)


def draw_beam2(canvas, rnd, start, end, p1, p2, frame, f):
    """`Draw_Beam2_` (beams.cpp:2566-2636) by the weapon's style."""
    (x1, y1), (x2, y2) = p1, p2
    if (x1, y1) == (x2, y2):
        return
    thick = frame % 2
    style = f["style"]
    if style == 0:
        if frame == 0:
            x1, x2, y1, y2 = x2, x1, y2, y1
            lo, hi = 3, 10
        elif frame == 1:
            lo, hi = 6, 10
        else:
            lo, hi = 3, 12
        canvas.bolt_line(rnd, x1, y1, x2, y2, 0, 12, 30, 3, frame, 1, 1, 0,
                         0, hi, lo, 4, 0)
    elif style == 1:
        canvas.wide_bolt_line(rnd, x1, y1, x2, y2, 0, 12, 50, 3, frame, 1,
                              1 if f["length"] >= 10 else 0, 1, 0, 12, 3,
                              f["bonus"] * 2 + 7, 1, 2, 0)
    elif style == 2:
        dv = thick + 1
        ex = rnd.randint(1, 5) + end[0] - 3
        ey = rnd.randint(1, 5) + end[1] - 3
        canvas.bolt_line(rnd, start[0], start[1], ex, ey, 0, 12, 100, 4,
                         frame * 4, 0, 0, 1, 0, 12 // dv, 8 // dv, 4 // dv, 0)
    else:
        a, b, c = 2 // (thick + 1), 5 // (thick * 2 + 1) + 1, 21 // (thick + 2)
        canvas.wide_bolt_line(rnd, start[0], start[1], end[0], end[1], 0, 16,
                              100, 3, frame * 2, 0, 0, 0, 1, c, c, b, b, a, a)


def shot(src, dst, f, frame, stop_size, seed, skip=0):
    """The bolt's pixels at `frame`: {(x, y): colour offset}, native px.
    A reflected beam (`skip`) also starts its strands at its tail, as the
    original's does (`attacker_x = bx1`, :2421-2424)."""
    seg = segment(src, dst, f, frame, stop_size, skip)
    canvas = Canvas()
    if seg is not None:
        rnd = random.Random(seed * 131 + frame)
        bx1, by1, bx2, by2 = seg
        draw_beam2(canvas, rnd, (bx1, by1) if skip else src, dst, (bx1, by1),
                   (bx2, by2), frame, f)
    return canvas.px


def muzzle_entry(src, dst, stream=0, variant=0):
    """BEAMS.LBX entry of the muzzle burst (`Load_Ship_Burst_`,
    :110-130; `Draw_Ship_Burst_`, :1713-1717): 1 + variant * 32 +
    stream * 16 + the beam's direction (:2246-2250)."""
    a = get_angle(src[0] - dst[0], dst[1] - src[1])
    d = abs(((a // 22) + 8) % 16)
    return 1 + variant * 32 + stream * 16 + d


def fragment_colours(art, fragment):
    """Sixteen colours of BEAMS.LBX 0's palette fragment `fragment`
    (`Add_Weapon_Palette_Fragment_`, :2200-2224), or None."""
    try:
        from core import lbx
        blob = art.blob("beams", 0)
        h = lbx.parse_header(blob)
        pal = lbx.read_palette(blob, h.frame_count) if h.has_palette else {}
    except Exception:
        return None
    first = min(pal) if pal else None
    if first is None:
        return None
    out = [pal.get(first + fragment * 16 + i) for i in range(16)]
    return out if all(out) else None
