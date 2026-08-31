#!/usr/bin/env python3
"""Cut the galaxy map sidebar icons out of the source sheet.

The sheet (assets/icons/_source_sheet.png) holds five painted icons
on a transparent background. This tool crops each one, trims it to
its own alpha bounding box and writes a square-free PNG scaled to
ICON_MAX px on the longer edge:

    treasury.png    stack of coins
    command.png     starbase with escorts
    food.png        bowl of produce
    freighters.png  freighter convoy over a planet
    research.png    microscope

The source rects below were read off the sheet's connected alpha
components once; they are kept literal so a re-run is deterministic
and does not depend on scipy. If the sheet is ever replaced, print
new rects with --probe and edit REGIONS.

Usage:
    python tools/make_sidebar_icons.py
    python tools/make_sidebar_icons.py --probe
    python tools/make_sidebar_icons.py --sheet other_sheet.png --max 640
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_DIR = os.path.join(BASE, "screens", "galaxy_map", "assets", "icons")
DEFAULT_SHEET = os.path.join(ICON_DIR, "_source_sheet.png")

#: Longest edge of a written icon. The sidebar box is 255 reference
#: pixels wide, so even at 4K an icon is drawn well below this — the
#: headroom is for larger master resolutions, not for the current UI.
ICON_MAX = 512

#: Alpha below this counts as background when trimming.
ALPHA_FLOOR = 16

#: name -> (x0, y0, x1, y1) on the source sheet.
REGIONS = {
    "treasury":   (10, 95, 520, 490),
    "command":    (600, 5, 1058, 545),
    "research":   (1090, 32, 1528, 512),
    "food":       (10, 508, 640, 997),
    "freighters": (700, 546, 1524, 1004),
}


def load_sheet(path):
    if not os.path.exists(path):
        sys.exit(f"sheet not found: {path}")
    im = Image.open(path)
    if im.mode != "RGBA":
        sys.exit(f"sheet must be RGBA (has alpha), got {im.mode}")
    return im


def trim(im):
    """Crop to the alpha bounding box."""
    alpha = np.asarray(im)[:, :, 3]
    ys, xs = np.nonzero(alpha > ALPHA_FLOOR)
    if len(xs) == 0:
        return im
    return im.crop((int(xs.min()), int(ys.min()),
                    int(xs.max()) + 1, int(ys.max()) + 1))


def fit(im, longest):
    w, h = im.size
    if max(w, h) <= longest:
        return im
    scale = longest / max(w, h)
    return im.resize((max(1, round(w * scale)), max(1, round(h * scale))),
                     Image.LANCZOS)


def probe(im):
    """Print the alpha components of the sheet, largest first.

    Only needed when the sheet is replaced — the numbers go into
    REGIONS by hand so the normal run stays dependency-free.
    """
    try:
        from scipy import ndimage
    except ImportError:
        sys.exit("--probe needs scipy")
    mask = np.asarray(im)[:, :, 3] > ALPHA_FLOOR
    mask = ndimage.binary_closing(mask, np.ones((9, 9)))
    lab, n = ndimage.label(mask)
    found = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        area = int((lab == i).sum())
        if area > 2000:
            found.append((area, sl[1].start, sl[0].start,
                          sl[1].stop, sl[0].stop))
    for area, x0, y0, x1, y1 in sorted(found, reverse=True):
        print(f"  area {area:>7}  ({x0}, {y0}, {x1}, {y1})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", default=DEFAULT_SHEET)
    ap.add_argument("--out", default=ICON_DIR)
    ap.add_argument("--max", type=int, default=ICON_MAX)
    ap.add_argument("--probe", action="store_true",
                    help="print alpha components instead of writing")
    args = ap.parse_args()

    sheet = load_sheet(args.sheet)
    print(f"sheet {args.sheet} {sheet.size[0]}x{sheet.size[1]}")
    if args.probe:
        probe(sheet)
        return

    os.makedirs(args.out, exist_ok=True)
    for name, rect in REGIONS.items():
        icon = fit(trim(sheet.crop(rect)), args.max)
        path = os.path.join(args.out, f"{name}.png")
        icon.save(path)
        print(f"  {name:<11} {icon.size[0]:>4}x{icon.size[1]:<4} -> {path}")


if __name__ == "__main__":
    main()
