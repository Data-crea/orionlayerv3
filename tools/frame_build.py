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


def build(master, windows, width, height):
    """The frame plate at `width x height`, no holes cut yet.

    A nine-slice from the master: the four corners lifted whole and
    scaled once, the four edges stretched along their own length
    only, and the interior filled with the strut texture. A corner
    stretched along two axes is the one thing a nine-slice exists to
    avoid, and it is what a plain resize of the master would do.
    """
    dl, dr, dt, db = device_ring(windows, width, height)
    ml, mr, mt, mb = master_ring(master)
    src = master.convert("RGB")
    mw, mh = src.size

    out = tiled(strut_texture(master), width, height)
    inner_w, inner_h = width - dl - dr, height - dt - db
    # corners, lifted whole
    for box, dest, size in (
            ((0, 0, ml, mt), (0, 0), (dl, dt)),
            ((mw - mr, 0, mw, mt), (width - dr, 0), (dr, dt)),
            ((0, mh - mb, ml, mh), (0, height - db), (dl, db)),
            ((mw - mr, mh - mb, mw, mh), (width - dr, height - db), (dr, db))):
        if size[0] > 0 and size[1] > 0:
            out.paste(src.crop(box).resize(size, Image.LANCZOS), dest)
    # edges, stretched along their own length only
    for box, dest, size in (
            ((0, mt, ml, mh - mb), (0, dt), (dl, inner_h)),
            ((mw - mr, mt, mw, mh - mb), (width - dr, dt), (dr, inner_h)),
            ((ml, 0, mw - mr, mt), (dl, 0), (inner_w, dt)),
            ((ml, mh - mb, mw - mr, mh), (dl, height - db), (inner_w, db))):
        if size[0] > 0 and size[1] > 0:
            out.paste(src.crop(box).resize(size, Image.LANCZOS), dest)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--master", default=MASTER)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--reference", default=frame_mask.REFERENCE)
    ap.add_argument("--resolution", action="append")
    args = ap.parse_args()

    data, windows = frame_mask.load_reference(args.reference)
    master = Image.open(args.master)
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
