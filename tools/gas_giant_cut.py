#!/usr/bin/env python3
"""Cut the gas giant out of Data's picture, at the size 4K draws it.

    python tools/gas_giant_cut.py                  # from ~/Downloads
    python tools/gas_giant_cut.py --sheet PATH
    python tools/gas_giant_cut.py --check          # measure, write nothing

Work order 236. Writes `screens/galaxy_map/assets/gas_giant.png`, which is
committed; the picture it is cut from is not (the line `planet_extract.py`
draws: authored artwork is committed, the thing it was cut from is not,
and this file is how the cut is repeated). The source is Data's
"Crimson Eye of the Gas Giant.png", delivered on 11 October 2026, 1254 x
1254 RGBA, refused by sha256 if it is another file.

**THE SIZE, MEASURED, NOT CHOSEN.** HD draws a system window's planet on
a square of `_rot_plan_dim[size]` native px (`sysorbits.PLANET_DIM`), a
gas giant at the HUGE size (sys.cpp:116-118): 24 native px, at 3840x2160
24 x 4.083 = 98 device px since the window grew (work order 284, the
"system_*" boxes x 1.45; 24 x 2.832 = 67 before) — the largest any
supported window draws it (nothing above 4K, Data). So the canvas is
`CANVAS` = 98 and 4K draws the master 1:1; every smaller window scales it down. In that square the
original's gas giant is exactly as large as its largest huge planet —
BUFFER0.LBX 0x5C + 50 and terran-huge 0x5C + 44 are both 26 px across on
the same 31 x 31 canvas, in every one of the 40 frames — so the disc is
cut as large as HD's largest huge disc stands in its square: terran,
50 of 54 px (`colonyplanets`, measured), 91 of 98. A smoke check holds
both numbers against the layout and the discs.

**THE CUT, MEASURED.** The picture is a disc on transparency, clean
outside (no alpha above 1 beyond 590 px from the centre) but not opaque
inside (alpha 247-253) and slightly oval (568-581 px by direction). So
the disc's edge is found on 720 rays (alpha crossing 128), a circle fitted
to it, and the cut is that centre with the SMALLEST edge radius less one
pixel — inside the soft edge in every direction, at most 15 source px
lost at the widest (1.3 %, under one output pixel). The colours are
the source's, downsampled with Lanczos; the alpha is not the source's
but the circle's own coverage at the output size (4 x 4 samples a
pixel), so the disc is opaque and its rim antialiased.
"""
import argparse
import hashlib
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.expanduser("~/Downloads/Crimson Eye of the Gas Giant.png")
SOURCE_SHA256 = \
    "67af89ec6a2880d04e7990ef7190ae88d85a714763286c29d2de0c74fdec01fe"
sys.path.insert(0, ROOT)
from core import basepack  # noqa: E402
#: Into the base pack since work order 241: the repository holds no picture.
OUT = os.path.join(basepack.base_dir(), "screens", "galaxy_map", "assets",
                   "gas_giant.png")
#: The square a gas giant is drawn on at 3840x2160 (module docstring).
CANVAS = 98
#: The disc's diameter in it: terran-huge's 50 of 54, of 98.
DISC = 91
RAYS = 720
SUPERSAMPLE = 4


def fit_disc(alpha):
    """(cx, cy, r): the fitted centre, the smallest edge radius less 1."""
    h, w = alpha.shape
    ys, xs = np.nonzero(alpha >= 128)
    cx0, cy0 = xs.mean(), ys.mean()
    pts = []
    for t in np.linspace(0, 2 * np.pi, RAYS, endpoint=False):
        edge = None
        for k in range(int(min(w, h) / 2) + 40, 0, -1):
            x, y = int(cx0 + k * np.cos(t)), int(cy0 + k * np.sin(t))
            if 0 <= x < w and 0 <= y < h and alpha[y, x] >= 128:
                edge = (cx0 + k * np.cos(t), cy0 + k * np.sin(t))
                break
        if edge is not None:
            pts.append(edge)
    p = np.array(pts)
    # algebraic circle fit: x^2 + y^2 + D x + E y + F = 0
    a = np.c_[p[:, 0], p[:, 1], np.ones(len(p))]
    b = -(p[:, 0] ** 2 + p[:, 1] ** 2)
    d, e, _f = np.linalg.lstsq(a, b, rcond=None)[0]
    cx, cy = -d / 2, -e / 2
    r = np.hypot(p[:, 0] - cx, p[:, 1] - cy)
    return cx, cy, float(r.min() - 1), (float(r.min()), float(r.max()))


def coverage(size, diameter, n=SUPERSAMPLE):
    """The circle's coverage of each output pixel, 0..255."""
    c = (np.arange(size * n) + 0.5) / n - size / 2.0
    inside = (c[None, :] ** 2 + c[:, None] ** 2) <= (diameter / 2.0) ** 2
    return (inside.reshape(size, n, size, n).mean(axis=(1, 3)) * 255
            ).round().astype(np.uint8)


def cut(path):
    src = Image.open(path).convert("RGBA")
    cx, cy, r, spread = fit_disc(np.asarray(src)[..., 3])
    half = r * CANVAS / DISC
    box = (cx - half, cy - half, cx + half, cy + half)
    rgb = src.convert("RGB").resize((CANVAS, CANVAS), Image.LANCZOS, box=box)
    out = rgb.convert("RGBA")
    out.putalpha(Image.fromarray(coverage(CANVAS, DISC)))
    return out, (cx, cy, r, spread)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sheet", default=SOURCE)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if not os.path.exists(a.sheet):
        print(f"no picture at {a.sheet}")
        return 1
    digest = hashlib.sha256(open(a.sheet, "rb").read()).hexdigest()
    if digest != SOURCE_SHA256:
        print(f"{a.sheet} is not the picture of 11 October 2026 "
              f"(sha256 {digest[:16]}..., wanted {SOURCE_SHA256[:16]}...)")
        return 1
    img, (cx, cy, r, spread) = cut(a.sheet)
    print(f"disc: centre ({cx:.1f}, {cy:.1f}), edge radius "
          f"{spread[0]:.1f}..{spread[1]:.1f}, cut at {r:.1f}; "
          f"{CANVAS} x {CANVAS}, disc {DISC}")
    if a.check:
        return 0
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    img.save(a.out, optimize=True)
    print(f"written {os.path.relpath(a.out, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
