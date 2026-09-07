#!/usr/bin/env python3
"""What the main-screen master contains, measured.

Split out of `tools/frame_build.py` on 7 September 2026, when that
file passed 300 code lines (decision 6). The seam is real rather than
a place to cut: everything here answers **"what does
`galaxy_map/assets/frame.png` look like"** — its ring, its material,
its window bevel, its rails, its crossings — and nothing here builds
anything. `frame_build` answers "how is a plate put together", and
imports this.

**EVERYTHING IS FOUND, NOT NAMED.** The strut patch, the bevel hole
and each rail are searched for by a measured property and never by a
coordinate: a coordinate goes stale the day the master is redrawn,
and a search re-derives it. `frame_build.py --profiles` prints every
measurement this module makes.
"""
import os
import sys

import numpy as np
from scipy import ndimage

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

from PIL import Image  # noqa: E402

import frame_mask  # noqa: E402

#: How far a texture patch must stay from any hole, in master pixels,
#: for it to carry no bevel. 12 was measured: the master's moulded
#: edges reach about 10 px in from a hole.
BEVEL_CLEARANCE = 12
#: Side of the square patch the strut texture is sampled from.
PATCH = 64
#: How deep the bevel strip is taken from the master. Its own lit
#: edge measures ONE pixel on every hole that has one, so three is
#: that line plus the two pixels of falloff behind it.
BEVEL_MASTER = 3
#: How far out a per-side luminance profile is measured.
PROFILE = 12


def master_ring(master):
    """The master's own metal border, in its own pixels.

    Measured rather than declared: the same threshold sweep the smoke
    test runs on it, so the tool and the check read one thing.
    """
    alpha = np.array(master.convert("RGBA"))[:, :, 3]
    h, w = alpha.shape
    ys, xs = np.where(alpha < 16)
    return (int(xs.min()), int(w - 1 - xs.max()),
            int(ys.min()), int(h - 1 - ys.max()))


def strut_texture(master, _ring=None, patch=PATCH):
    """The flattest bevel-free patch of the master's metal.

    **SEARCHED, NOT A MAGIC COORDINATE.** The patch has to be metal,
    at least `BEVEL_CLEARANCE` from any hole so it carries no
    moulding, and the FLATTEST such patch — lowest luminance variance
    — because what is wanted is the material and not the ornament.
    A named coordinate would go stale the day the master is redrawn;
    a search re-derives it.

    The first attempt took the master's bottom band, which is the
    widest hole-free run it has and therefore looked like the obvious
    source. It contains the band's own ornamental lines, and tiling
    it printed those lines across the interior every 64 px. Widest is
    not flattest.
    """
    a = np.array(master.convert("RGBA"))
    opaque = a[:, :, 3] >= 128
    lum = a[:, :, :3].mean(axis=2)
    free = ndimage.binary_erosion(
        opaque, np.ones((2 * BEVEL_CLEARANCE + 1,) * 2, bool))
    best, at = None, (0, 0)
    for y in range(0, a.shape[0] - patch, patch // 4):
        for x in range(0, a.shape[1] - patch, patch // 4):
            if not free[y:y + patch, x:x + patch].all():
                continue
            spread = float(lum[y:y + patch, x:x + patch].std())
            if best is None or spread < best:
                best, at = spread, (x, y)
    if best is None:                       # no hole-free patch at all
        return master.convert("RGB").crop((0, 0, patch, patch))
    x, y = at
    return master.convert("RGB").crop((x, y, x + patch, y + patch))


#: How much of its own bounding box a hole must fill to count as
#: RECTANGULAR. The master's eight rectangular holes measure 94.4 to
#: 99.9 %; its one chamfered hole — the header cartouche — measures
#: 91.4 %. 0.94 sits in that gap. See `bevel_source` for why the
#: distinction is load-bearing and `print_profiles` for what it does
#: to a reading.
RECT_FILL = 0.94


def hole_fill(size, x0, x1, y0, y1):
    """What share of its bounding box a hole's own pixels occupy."""
    area = (x1 - x0) * (y1 - y0)
    return float(size) / area if area else 0.0


def bevel_source(master, depth=None):
    """(image, opening) — the master's own light edge around one hole.

    **THE HOLE IS FOUND, NOT NAMED**, the same rule as the strut
    patch. Every hole's edge is measured on all four sides and the
    one whose four sides AGREE best is taken: a bevel copied from a
    hole that is bright on the left and flat on the right would put
    that asymmetry on every window of the screen.

    Measured on 7 September 2026: the master's bevel is **one pixel
    wide** on every hole that has one — a single bright line against
    a plateau of luminance 2 — so `depth` is small by measurement and
    not by taste. The chosen hole and every hole's per-side ridge are
    printed by `--profiles`.

    **AND THE HOLE HAS TO BE RECTANGULAR** (`RECT_FILL`), which was
    implicit until 7 September 2026 and is now a gate. This function
    CROPS A RECTANGLE — `master.crop((x0-d, y0-d, x1+d, y1+d))` — and
    `lay_border` lays that band around a rectangular window, so a
    chamfered source would print its own slanted corners onto every
    window of the screen. The master has exactly one such hole, the
    header cartouche, and it was excluded by accident rather than by
    rule: it scores 0.00 because the measurement cannot see its edge
    (see `print_profiles`), not because the check knew its shape. An
    exclusion that happens to hold is not a rule, and the day a
    chamfered hole measures well is the day it silently wins.
    """
    depth = BEVEL_MASTER if depth is None else depth
    a = np.array(master.convert("RGBA"))
    lum = a[:, :, :3].mean(axis=2)
    holes = a[:, :, 3] < 16
    lab, n = ndimage.label(holes)
    objs = ndimage.find_objects(lab)
    sizes = ndimage.sum(holes, lab, range(1, n + 1))
    h, w = holes.shape
    best = None
    for i, size in enumerate(sizes, 1):
        if size < 1500:
            continue
        sy, sx = objs[i - 1]
        x0, x1, y0, y1 = sx.start, sx.stop, sy.start, sy.stop
        if x0 < PROFILE or y0 < PROFILE or x1 > w - PROFILE or y1 > h - PROFILE:
            continue
        if hole_fill(size, x0, x1, y0, y1) < RECT_FILL:
            continue
        prof = _profiles(lum, x0, x1, y0, y1)
        edge = [_ridge(p) for p in prof.values()]
        if any(wd == 0 for _ht, wd in edge):
            continue
        heights = np.array([ht for ht, _wd in edge])
        score = heights.min() / (1 + heights.std())
        if best is None or score > best[0]:
            best = (score, (x0, y0, x1, y1), prof)
    if best is None:
        raise SystemExit("no hole in the master has a lit edge on all "
                         "four sides — the bevel cannot be sampled")
    x0, y0, x1, y1 = best[1]
    crop = master.convert("RGB").crop(
        (x0 - depth, y0 - depth, x1 + depth, y1 + depth))
    return crop, (depth, depth, crop.width - depth, crop.height - depth), best


def _profiles(lum, x0, x1, y0, y1, depth=None):
    """Per-side luminance walking OUTWARD FROM THE BOUNDING BOX.

    **The anchor is the bounding box, not the hole**, and for a
    rectangular hole those are the same edge. For a chamfered one
    they are not: the header cartouche's bbox starts at y=21 while
    its lit lip sits at y=21..22 in the flanks and y=22 in the middle,
    so the T band (rows 18..20) is three rows of plain metal and the
    ridge reads as absent. Callers must gate on `hole_fill` before
    treating a zero here as a fact about the artwork.

    (Recorded because the first diagnosis was wrong: the cause was
    read as "the chamfered corners put hole pixels into the metal
    band and flatten the average". Masking hole pixels out of the
    band changes not one of the forty numbers `--profiles` prints —
    the bands lie outside the box and contain none. The band is
    simply looking in the wrong place.)
    """
    depth = PROFILE if depth is None else depth
    return {"L": lum[y0 + 2:y1 - 2, x0 - depth:x0][:, ::-1].mean(axis=0),
            "R": lum[y0 + 2:y1 - 2, x1:x1 + depth].mean(axis=0),
            "T": lum[y0 - depth:y0, x0 + 2:x1 - 2][::-1, :].mean(axis=1),
            "B": lum[y1:y1 + depth, x0 + 2:x1 - 2].mean(axis=1)}


def _ridge(p):
    """(mean height, width) of the lit run at the start of `p`."""
    plateau = float(np.median(p[-4:]))
    limit = max(plateau * 2.0, plateau + 8)
    width = 0
    while width < len(p) and p[width] >= limit:
        width += 1
    return float(p[:max(width, 1)].mean()), width


def struts(rects):
    """The metal rectangles between facing windows.

    A pair counts as facing if one starts where the other ends on one
    axis and they overlap by more than a token amount on the other —
    the same test the master's own rails were measured with, so the
    gap a rail is judged against is the gap a rail would fill.
    """
    out = []
    boxes = sorted((name, r) for name, r in rects.items())

    def clear(gap):
        """No window inside the gap — otherwise the two are not
        adjacent and the metal between them is not one strut. Without
        this the header and the sort row 'face' each other across the
        whole screen."""
        gx, gy, gw, gh = gap
        for _n, (x, y, w, h) in boxes:
            if gx < x + w and x < gx + gw and gy < y + h and y < gy + gh:
                return False
        return True

    for i, (_na, A) in enumerate(boxes):
        for _nb, B in boxes[i + 1:]:
            for a, b in ((A, B), (B, A)):
                if b[0] >= a[0] + a[2] and \
                        min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]) > 20:
                    gap = b[0] - (a[0] + a[2])
                    y0 = max(a[1], b[1])
                    y1 = min(a[1] + a[3], b[1] + b[3])
                    box = (a[0] + a[2], y0, gap, y1 - y0)
                    if 0 < gap and clear(box):
                        out.append(box + (True,))
                if b[1] >= a[1] + a[3] and \
                        min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]) > 20:
                    gap = b[1] - (a[1] + a[3])
                    x0 = max(a[0], b[0])
                    x1 = min(a[0] + a[2], b[0] + b[2])
                    box = (x0, a[1] + a[3], x1 - x0, gap)
                    if 0 < gap and clear(box):
                        out.append(box + (False,))
    return out


#: Which of the master's struts each kind of gap gets, by ROLE. The
#: measurement behind every line is `--profiles`; the reference
#: widths are 26.7 / 28.4 / 29.2 / 38.9 and `layout_reference.gaps`
#: holds them rounded DOWN, so a rail is never wider than the strut
#: it came from.
#:
#:   header_list  the master's header|map    a title bar above the
#:                                           main content
#:   list_band    map|slot                   the main content above
#:                                           the row beneath it
#:   band_sort    box|slot                   a PANEL above a button
#:                                           row, which is what this
#:                                           gap is and what map|slot
#:                                           is not
#:   in_row       the slot divider           two elements of one row
#:                                           side by side
RAIL_ROLES = ("header_list", "list_band", "band_sort", "in_row")


def _master_holes(master):
    a = np.array(master.convert("RGBA"))
    holes = a[:, :, 3] < 16
    lab, n = ndimage.label(holes)
    objs = ndimage.find_objects(lab)
    sizes = ndimage.sum(holes, lab, range(1, n + 1))
    out = {}
    for i, size in enumerate(sizes, 1):
        if size < 1500:
            continue
        sy, sx = objs[i - 1]
        out[i] = (sx.start, sy.start, sx.stop - sx.start, sy.stop - sy.start)
    return out, a


def _hole_kind(rect, width):
    """What the master calls this hole. Positional, and that is all a
    frame image can say — the names are only used to pick a strut by
    role, and every pick is printed by `--profiles`."""
    x, y, w, h = rect
    if h < 60 and y < 60:
        return "header"
    if w > width * 0.4:
        return "map"
    if x > width * 0.75 and h > 400:
        return "sidebar"
    if x > width * 0.75:
        return "box"
    return "slot"


def master_rails(master):
    """role -> (strip, vertical), each strip a crop of the master.

    **FOUND, NOT NAMED**, like the strut patch and the bevel hole: the
    master's holes are labelled by position, its struts are measured,
    and the narrowest strut of each ROLE is taken. Narrowest, because
    a rail is laid at the gap's own width and a wider source would be
    squeezed — and squeezing a moulding is inventing one.
    """
    rects, a = _master_holes(master)
    h, w = a.shape[:2]
    kind = {i: _hole_kind(r, w) for i, r in rects.items()}
    src = master.convert("RGB")
    best = {}
    for gx, gy, gw, gh, vertical in struts(rects):
        ends = set()
        for i, (x, y, rw, rh) in rects.items():
            if vertical and (x + rw == gx or x == gx + gw) and \
                    min(y + rh, gy + gh) - max(y, gy) > 20:
                ends.add(kind[i])
            if not vertical and (y + rh == gy or y == gy + gh) and \
                    min(x + rw, gx + gw) - max(x, gx) > 20:
                ends.add(kind[i])
        span = gw if vertical else gh
        if vertical:
            role = "in_row" if ends == {"slot"} else None
        elif ends == {"header", "map"}:
            role = "header_list"
        elif ends == {"map", "slot"}:
            role = "list_band"
        elif ends == {"box", "slot"}:
            role = "band_sort"
        else:
            role = None
        if role and (role not in best or span < best[role][0]):
            best[role] = (span, src.crop((gx, gy, gx + gw, gy + gh)), vertical)
    return {r: (v[1], v[2]) for r, v in best.items()}


def junction_source(master):
    """The master's own crossing: a vertical strut meeting a
    horizontal one, cropped whole.

    **NO SYNTHESISED CORNERS.** Where two rails cross, the pixels come
    from the place the master crosses two of its own — the metal
    between two slot buttons where it meets the strip under the map.
    The other orientation is that same crop MIRRORED, which is still
    only the master's pixels; a corner drawn to fit would not be.
    """
    rects, a = _master_holes(master)
    h, w = a.shape[:2]
    kind = {i: _hole_kind(r, w) for i, r in rects.items()}
    slots = sorted((r for i, r in rects.items() if kind[i] == "slot"))
    above = [r for i, r in rects.items() if kind[i] == "map"]
    if len(slots) < 2 or not above:
        return None
    a0, b0 = slots[0], slots[1]
    x0, x1 = a0[0] + a0[2], b0[0]
    y1 = a0[1]
    y0 = above[0][1] + above[0][3]
    if x1 <= x0 or y1 <= y0:
        return None
    return master.convert("RGB").crop((x0, y0, x1, y1))


def print_profiles(master):
    """Every hole's per-side edge, and the one the bevel comes from.

    The measurement the choice rests on, printable, because "found,
    not named" is only worth anything if the finding can be looked at.
    """
    a = np.array(master.convert("RGBA"))
    lum = a[:, :, :3].mean(axis=2)
    holes = a[:, :, 3] < 16
    lab, n = ndimage.label(holes)
    objs = ndimage.find_objects(lab)
    sizes = ndimage.sum(holes, lab, range(1, n + 1))
    h, w = holes.shape
    print("  per-side edge, measured OUTWARD FROM THE BOUNDING BOX "
          "(see _profiles).")
    print(f"  A hole below {100*RECT_FILL:.0f} % fill is not rectangular "
          f"and this reading cannot see its edge.")
    print(f"{'hole':<26}{'fill':>7}" + "".join(f"{k:>13}" for k in "LRTB")
          + "   agreement")
    for i, size in enumerate(sizes, 1):
        if size < 1500:
            continue
        sy, sx = objs[i - 1]
        x0, x1, y0, y1 = sx.start, sx.stop, sy.start, sy.stop
        if x0 < PROFILE or y0 < PROFILE or x1 > w - PROFILE or y1 > h - PROFILE:
            continue
        edge = {k: _ridge(p)
                for k, p in _profiles(lum, x0, x1, y0, y1).items()}
        heights = np.array([edge[k][0] for k in "LRTB"])
        lit = all(edge[k][1] for k in "LRTB")
        fill = hole_fill(size, x0, x1, y0, y1)
        rect = fill >= RECT_FILL
        score = heights.min() / (1 + heights.std()) if (lit and rect) else 0.0
        # THE ANNOTATION IS ABOUT THE READING, NOT ABOUT THE ARTWORK.
        # "no lit edge" used to be printed for the header cartouche,
        # which has a one-pixel lit lip of 147..222 against metal at
        # 2 on every side — the measurement simply looks three rows
        # too high. A tool may report that it cannot measure something;
        # it may not report the thing as absent.
        if not rect:
            note = "   (not rectangular — this reading cannot see its edge)"
        elif not lit:
            note = "   (a side with no lit edge)"
        else:
            note = ""
        print(f"  ({x0:>4},{y0:>4}) {x1-x0:>4}x{y1-y0:<4}{100*fill:6.1f}%"
              + "".join(f"{edge[k][0]:8.0f}/{edge[k][1]:<4d}" for k in "LRTB")
              + f"  {score:6.2f}" + note)
    _crop, _open, chosen = bevel_source(master)
    print(f"  -> sampled from the hole at "
          f"({chosen[1][0]}, {chosen[1][1]}), score {chosen[0]:.2f}")

