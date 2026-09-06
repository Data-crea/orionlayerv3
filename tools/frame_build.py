#!/usr/bin/env python3
"""Build the colony screen's frame from the main-screen master.

    python tools/frame_build.py
    python tools/frame_build.py --resolution 1920x1080 --out /tmp/f

**THE FRAME IS BUILT, NOT RENDERED.** Six image-tool renders were
measured on 6 September 2026 (`~/Bilder/rahmen/manifest.md`) and none
was usable: five had near-white metal 30 degrees off the master's hue
and no interior windows at all, and the sixth was the right frame at
2.0163 — 13.4 % wider than 16:9 — letterboxed into a 16:9 canvas,
88 px short of what a crop to 16:9 needs. So the metal comes from the
master this screen has to sit beside, and the geometry comes from
`layout_reference.json`, and nothing is invented in between.

What is taken from `screens/galaxy_map/assets/frame.png`:

  the four ring bands   its own metal border, 129 / 145 / 21 / 86 in
                        its pixels, scaled per side to the ring the
                        reference file declares
  the four corners      lifted whole, so a corner is never stretched
                        along two axes at once
  the strut texture     a patch of its bottom band — the widest run
                        of metal in the master that no hole touches,
                        so it carries no bevel

**STRUTS ARE PLAIN, AND THAT IS THE INSTRUCTION.** The interior metal
between windows is the texture and nothing else: no bevel, no
highlight, no attempt to imitate the master's moulded edges. Whether
it needs any is a judgement to make on the picture, and the picture
is the point of this tool.

**AND THE ALPHA IS STILL THE MASK'S.** The windows are cut by
`frame_cut.cut`, from `layout_reference.json` — never from the
artwork's own dark pixels. See that module for why.

**GENERATED, NEVER COMMITTED** (decision 40). Every input is in the
tree, so regenerating reproduces it byte for byte.

Requires: Pillow, numpy.
"""
import argparse
import os
import sys

import numpy as np
from scipy import ndimage

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is missing. Run: pip install pillow --break-system-packages")

import frame_cut  # noqa: E402
import frame_mask  # noqa: E402

MASTER = os.path.join(frame_mask.ROOT, "screens", "galaxy_map", "assets",
                      "frame.png")
DEFAULT_OUT = os.path.join(frame_mask.ROOT, "screens", "colony_summary",
                           "assets", "frames")
#: How far a texture patch must stay from any hole, in master pixels,
#: for it to carry no bevel. 12 was measured: the master's moulded
#: edges reach about 10 px in from a hole.
BEVEL_CLEARANCE = 12


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


#: Side of the square patch the strut texture is sampled from.
PATCH = 64
#: How deep the bevel strip is taken from the master, and how wide it
#: is laid in reference px. The master's own lit edge measures ONE
#: pixel on every hole that has one (see `bevel_source`), so three is
#: that line plus the two pixels of falloff behind it, and no more.
BEVEL_MASTER = 3
BEVEL_REF = 3
#: How far out a per-side luminance profile is measured.
PROFILE = 12


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


def tiled(patch, width, height):
    out = Image.new("RGB", (width, height))
    for y in range(0, height, patch.height):
        for x in range(0, width, patch.width):
            out.paste(patch, (x, y))
    return out


def device_ring(windows, width, height):
    """The ring in device px, taken from the WINDOWS themselves.

    Not `round(ring * scale)`. The ring is by definition the metal
    outside the outermost holes, and the holes are placed by
    `Layout.rect`'s truncation — so at 2560x1440 a rounded ring ended
    one pixel inside its own first hole and the built frame measured
    106 where the table says 107. Deriving it from the rectangles the
    holes are actually cut from makes the two agree by construction
    rather than by two roundings happening to match.
    """
    _image, rects = frame_mask.render(windows, width, height)
    xs = [r[0] for r in rects.values()]
    ys = [r[1] for r in rects.values()]
    rx = [r[0] + r[2] for r in rects.values()]
    by = [r[1] + r[3] for r in rects.values()]
    return min(xs), width - max(rx), min(ys), height - max(by)


def lay_border(dst, src, src_open, dst_open, dst_band):
    """Lay `src`'s border around `dst_open`, nine-slice.

    **ONE FUNCTION FOR THE RING AND FOR EVERY WINDOW'S BEVEL**, which
    is not a coincidence worth being clever about: both are "take the
    band a source image puts around a rectangular opening and put it
    around another rectangle". The ring's opening is the master's own
    inner area; a bevel's opening is one of the master's holes. Two
    implementations of this would be the second copy, and the second
    copy is where a difference gets in.

    The corners are lifted whole and scaled ONCE; the edges stretch
    along their own length only. A corner stretched along two axes is
    the one thing a nine-slice exists to avoid, and it is what a
    plain resize would do.

    `src_open` and `dst_open` are (x0, y0, x1, y1); `dst_band` is
    (left, right, top, bottom) in destination pixels.
    """
    sx0, sy0, sx1, sy1 = src_open
    dx0, dy0, dx1, dy1 = dst_open
    dl, dr, dt, db = dst_band
    sw, sh = src.size
    for box, dest, size in (
            # corners
            ((sx0 - (sx0), 0, sx0, sy0), (dx0 - dl, dy0 - dt), (dl, dt)),
            ((sx1, 0, sw, sy0), (dx1, dy0 - dt), (dr, dt)),
            ((0, sy1, sx0, sh), (dx0 - dl, dy1), (dl, db)),
            ((sx1, sy1, sw, sh), (dx1, dy1), (dr, db)),
            # edges
            ((0, sy0, sx0, sy1), (dx0 - dl, dy0), (dl, dy1 - dy0)),
            ((sx1, sy0, sw, sy1), (dx1, dy0), (dr, dy1 - dy0)),
            ((sx0, 0, sx1, sy0), (dx0, dy0 - dt), (dx1 - dx0, dt)),
            ((sx0, sy1, sx1, sh), (dx0, dy1), (dx1 - dx0, db))):
        if size[0] > 0 and size[1] > 0 and dest[0] >= 0 and dest[1] >= 0:
            dst.paste(src.crop(box).resize(size, Image.LANCZOS), dest)


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


def build(master, windows, width, height):
    """The frame plate at `width x height`, no holes cut yet.

    The strut texture, then the ring, then every window's bevel —
    all three through `lay_border` except the texture, which is a
    tile.
    """
    dl, dr, dt, db = device_ring(windows, width, height)
    ml, mr, mt, mb = master_ring(master)
    src = master.convert("RGB")
    mw, mh = src.size

    out = tiled(strut_texture(master), width, height)
    lay_border(out, src, (ml, mt, mw - mr, mh - mb),
               (dl, dt, width - dr, height - db), (dl, dr, dt, db))

    scale = min(width / frame_mask.REF_W, height / frame_mask.REF_H)
    band = max(1, round(BEVEL_REF * scale))
    bsrc, bopen, _chosen = bevel_source(master)
    _image, rects = frame_mask.render(windows, width, height)
    for _name, (x, y, w, h) in sorted(rects.items()):
        lay_border(out, bsrc, bopen, (x, y, x + w, y + h),
                   (band, band, band, band))
    return out


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
    print(f"{'hole':<26}" + "".join(f"{k:>13}" for k in "LRTB")
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
        score = heights.min() / (1 + heights.std()) if lit else 0.0
        print(f"  ({x0:>4},{y0:>4}) {x1-x0:>4}x{y1-y0:<4}"
              + "".join(f"{edge[k][0]:8.0f}/{edge[k][1]:<4d}" for k in "LRTB")
              + f"  {score:6.2f}"
              + ("" if lit else "   (a side with no lit edge)"))
    _crop, _open, chosen = bevel_source(master)
    print(f"  -> sampled from the hole at "
          f"({chosen[1][0]}, {chosen[1][1]}), score {chosen[0]:.2f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--master", default=MASTER)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--reference", default=frame_mask.REFERENCE)
    ap.add_argument("--resolution", action="append")
    ap.add_argument("--profiles", action="store_true",
                    help="print every master hole's per-side edge profile "
                         "and which one the bevel is sampled from")
    args = ap.parse_args()

    data, windows = frame_mask.load_reference(args.reference)
    master = Image.open(args.master)
    if args.profiles:
        print_profiles(master)
    os.makedirs(args.out, exist_ok=True)
    for spec in args.resolution or data["_resolutions"]:
        width, height = (int(v) for v in spec.lower().split("x"))
        plate = build(master, windows, width, height)
        cut, rects = frame_cut.cut(plate, windows, width, height)
        path = os.path.join(args.out, f"frame_{width}x{height}.png")
        cut.save(path)
        native = master.width >= width
        print(f"{spec}: {len(rects)} holes, master {master.width} px wide "
              f"-> {'downscale' if native else 'UPSCALED INTERIM'} "
              f"x{width / master.width:.3f} -> {path}")
    print("Generated: none of this is committed (.gitignore, decision 40).")


if __name__ == "__main__":
    main()
