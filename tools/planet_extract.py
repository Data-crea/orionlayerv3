#!/usr/bin/env python3
"""Cut the ten planet discs out of Data's sheet, at their true size.

    python tools/planet_extract.py                 # from ~/Downloads/planets.png
    python tools/planet_extract.py --sheet PATH
    python tools/planet_extract.py --check         # measure, write nothing

**THE SHEET IS NOT IN THE REPOSITORY.** It is Data's own artwork, one
1916x821 PNG with ten captioned discs, and what is committed is what
this tool makes of it: ten small RGBA sprites under
`screens/colony_summary/assets/planets/`. The same line `assets/
frame.png` is on — authored artwork is committed, the thing it was cut
from is not, and this file is how the cut is repeated.

**THERE IS NO PIXEL GRID IN THE SHEET, AND THAT IS MEASURED.** The art
reads as chunky pixel art, so the obvious method is "find the block
size, take one sample per block". Three independent measurements say
there are no blocks to find:

  * edge positions modulo b are uniform for every b in 2..8 — at a
    threshold of 6 and at 120, in x and in y;
  * within-block variance rises smoothly with b and has no knee, and
    the best offset beats the worst by 10 % at b=4, which is noise;
  * the distance between consecutive strong gradient peaks decays
    smoothly from 2 px with no preferred spacing, and a Fourier
    transform of the gradient profile finds its strongest period
    between 5.8 and 9.5 px depending on which disc is asked.

So the sheet was painted or resampled without a grid, and "one sample
per block" cannot mean "align to the blocks". It means the other half
of what Data asked for: **POINT SAMPLING, never an average** — one
source pixel per output pixel, so every colour in the result is a
colour that is in the sheet, and no pair of neighbours is blended into
something that is in neither.

`BLOCK = 5` is therefore a choice and not a measurement, and it is
made from the far end: at 5, a disc is 46 to 50 px across and the
sprite with its glow is `SPRITE`, which is exactly the height the
colony list gives a row's icon at 1920x1080 — the project's reference
resolution draws this art at 1:1, and every other size scales from it
by nearest neighbour like a figure (decision 28's marked exception).

WHAT IS MEASURED HERE rather than typed: the ten discs' positions, by
labelling the sheet's bright components; each disc's centre, from the
component's bounding box; and each disc's radius, from the steepest
drop in its own radial luminance profile past r=80, which is the limb
and not an interior contrast. The captions are excluded by construction
— the crop is a square around the disc's centre, and no caption is
within a radius of it.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import BASE_DIR  # noqa: E402

#: Data's sheet. Outside the repository, like a savegame or an LBX.
SHEET = os.path.join(os.path.expanduser("~"), "Downloads", "planets.png")

OUT_DIR = os.path.join("screens", "colony_summary", "assets", "planets")

#: Source px per output px. See the module docstring: a choice, not a
#: measurement, and the reason is `SPRITE`.
BLOCK = 5

#: The sprite, square, every planet the same — a layout cannot place
#: ten icons of ten sizes. 54 px is the row icon's own height at
#: 1920x1080 (`band 58 - 2 * step 2`), so the reference resolution
#: draws these at 1:1.
SPRITE = 54

#: True px of glow kept outside the disc's own limb. The sheet's glow
#: reaches 10 to 35 source px past it; three is what fits inside
#: `SPRITE` for the largest disc, and it is what keeps a planet from
#: ending on a hard edge.
GLOW = 3

#: **THE ORDER IS `PLANET_CLIMATE` AND THAT IS NOT A COINCIDENCE** —
#: orion2_consts.h:362-374, ids 0..9, and the sheet is drawn in that
#: order, top row then bottom. `colonyrows` reads the same ids out of
#: `s_colony.climate` (offset 226), so a row's text and a row's icon
#: cannot disagree about what the planet is.
NAMES = ("toxic", "radiated", "barren", "desert", "tundra",
         "ocean", "swamp", "arid", "terran", "gaia")


def discs(sheet):
    """[(name, cx, cy, r_src)] — measured off the sheet."""
    from scipy import ndimage
    a = np.array(Image.open(sheet).convert("RGB")).astype(float)
    lum = a.sum(axis=2)
    lab, n = ndimage.label(lum > 60)
    found = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        ys, xs = sl
        h, w = ys.stop - ys.start, xs.stop - xs.start
        if h < 120 or w < 120:
            continue
        # ROUND, not merely large: the captions under a disc can label
        # a component of their own, and a line of text is neither.
        if (lab[sl] == i).sum() < 0.5 * np.pi * (min(h, w) / 2.0) ** 2:
            continue
        found.append((xs.start, ys.start, w, h))
    if len(found) != len(NAMES):
        raise SystemExit(
            f"{sheet}: {len(found)} disc-shaped components, "
            f"{len(NAMES)} planets — the sheet is not the one this "
            f"tool was written for")
    # Reading order: top row left to right, then bottom.
    found.sort(key=lambda b: (b[1] // 300, b[0]))
    out = []
    for name, (x, y, w, h) in zip(NAMES, found):
        cx, cy = x + w / 2.0, y + h / 2.0
        ys, xs = np.mgrid[y - 30:y + h + 30, x - 30:x + w + 30]
        d = np.hypot(xs - cx, ys - cy)
        v = lum[y - 30:y + h + 30, x - 30:x + w + 30]
        prof = np.array([v[(d >= r) & (d < r + 1)].mean()
                         if ((d >= r) & (d < r + 1)).any() else 0.0
                         for r in range(int(d.max()))])
        # THE LIMB IS THE STEEPEST DROP PAST r=80. Without that floor
        # two of the ten answer with an interior edge — barren at 6 px
        # and ocean at 15 — because a bright continent against a dark
        # sea drops faster than the limb does.
        r_src = int(np.argmin(np.diff(prof)[80:])) + 81
        out.append((name, cx, cy, r_src, _caption_top(lum, cx, cy, r_src)))
    return out


def _caption_top(lum, cx, cy, r_src):
    """The first row of the caption under a disc, in source px.

    **THE GLOW RING IS TRIMMED TO THIS AND THE CAPTIONS ARE WHY.** The
    crop is a square around the disc's centre and the captions are
    close enough to reach into it: DESERT's own word sits 130 source
    px under its centre, which is 26 true px, and a glow of three past
    a 23.2 px disc reaches 26.2 — so the first cut carried an orange
    fragment of the word DESERT along the bottom of the sprite. A
    caption is text on black and the glow is a halo, and no per-pixel
    rule separates them; the distance does.
    """
    x0, x1 = int(cx - r_src), int(cx + r_src)
    for y in range(int(cy + r_src) + 2, lum.shape[0]):
        if (lum[y, x0:x1] > 90).any():
            return y
    return lum.shape[0]


def sprite(sheet_px, cx, cy, r_src, cap_y):
    """One planet, SPRITE x SPRITE RGBA, point-sampled.

    Alpha is a CIRCLE ON THE TRUE GRID and never a luma key: the dark
    limb of a planet is the planet, and keying on brightness eats it.
    Inside the disc's own radius the sprite is opaque whatever colour
    it is; between there and `GLOW` px further out the sheet's own
    brightness fades it, which is the glow; beyond that it is gone.
    """
    mid = (SPRITE - 1) / 2.0
    r_true = r_src / float(BLOCK)
    # The glow, trimmed to what the cell has room for — see
    # `_caption_top`. Never past the sprite's own edge either.
    r_glow = min(r_true + GLOW, (cap_y - cy) / float(BLOCK) - 1.0, mid)
    out = np.zeros((SPRITE, SPRITE, 4), dtype=np.uint8)
    h, w, _ = sheet_px.shape
    for j in range(SPRITE):
        for i in range(SPRITE):
            sx = int(round(cx + (i - mid) * BLOCK))
            sy = int(round(cy + (j - mid) * BLOCK))
            if not (0 <= sx < w and 0 <= sy < h):
                continue
            rgb = sheet_px[sy, sx]
            d = np.hypot(i - mid, j - mid)
            if d <= r_true:
                alpha = 255
            elif d <= r_glow:
                # The glow's own falloff, taken from the pixel rather
                # than invented: 60 is where the sheet's background
                # reads as black at this sum.
                alpha = int(np.clip((int(rgb.sum()) - 12) / 120.0, 0, 1) * 255)
            else:
                alpha = 0
            out[j, i] = (rgb[0], rgb[1], rgb[2], alpha)
    return Image.fromarray(out, "RGBA")


def main():
    ap = argparse.ArgumentParser(
        description="Cut the ten planet discs out of Data's sheet.")
    ap.add_argument("--sheet", default=SHEET)
    ap.add_argument("--check", action="store_true",
                    help="measure and report, write nothing")
    args = ap.parse_args()
    if not os.path.exists(args.sheet):
        raise SystemExit(
            f"{args.sheet} is not there. It is Data's own sheet and is "
            f"not in the repository; pass --sheet if it lives "
            f"elsewhere.")
    px = np.array(Image.open(args.sheet).convert("RGB"))
    out_dir = os.path.join(BASE_DIR, OUT_DIR)
    if not args.check:
        os.makedirs(out_dir, exist_ok=True)
    print(f"{args.sheet}: {px.shape[1]}x{px.shape[0]}, block {BLOCK}, "
          f"sprite {SPRITE}, glow {GLOW}")
    for name, cx, cy, r_src, cap_y in discs(args.sheet):
        side = SPRITE * BLOCK
        rect = (int(round(cx - side / 2)), int(round(cy - side / 2)),
                side, side)
        r_glow = min(r_src / BLOCK + GLOW, (cap_y - cy) / BLOCK - 1.0,
                     (SPRITE - 1) / 2.0)
        print(f"  {name:9} source rect {rect}  disc r {r_src} src "
              f"= {r_src / BLOCK:.2f} true, mask r {r_glow:.2f} "
              f"(caption at +{cap_y - cy:.0f} src)  -> {SPRITE}x{SPRITE}")
        if args.check:
            continue
        sprite(px, cx, cy, r_src, cap_y).save(
            os.path.join(out_dir, f"{name}.png"))
    if args.check:
        print("Check only, nothing written.")
    else:
        print(f"wrote {len(NAMES)} sprites to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
