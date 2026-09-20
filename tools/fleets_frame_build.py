#!/usr/bin/env python3
"""Build the Fleets frame from Data's source art: unlit buttons, 32 holes.

Work order 151. The source under `screens/fleets/assets/_src/` is a
painting, not an asset: it has **no alpha at all**, and two of the seven
buttons are painted in their LIT state. This tool is the only thing that
touches its pixels, and it does exactly two things to them.

**1. THE TWO LIT BUTTONS ARE REBUILT UNLIT** (Data's decision (a) on
work order 151: all seven unlit in the art, HD draws the lit state as it
does today). Support and Combat are narrower than the five unlit ones,
so an unlit face cannot be pasted over them — it is rebuilt from the
Leaders plate by a horizontal 3-slice, 60 px of plate kept at each end
and only the straight middle resampled. 60 is well clear of the 22 px
chamfer measured off the art; the plate's lighting gradient runs along
its length, so "where does the border become uniform" measures nothing
here and the corner size comes from the chamfer instead.

The lit glow does not stop at the plate — it lifts the whole dark band
behind the button (blue-minus-green +10.5 above Support against +4.9
above Leaders) — so the tile that is copied runs the full height of that
band, seam to seam. The MX px left of the Leaders plate are not plain
band either: the button panel's own bevel runs there, and copying it
would draw a bright strip where nothing stands, so the left margin is
mirrored from the clean right one.

**2. THE 32 OPENINGS ARE CUT** — and that is what removes the painted
content the order lists. The stars in the map and the words on the
buttons are not retouched away: they are inside a hole. Each cut follows
the interior's own shape and not its bounding rectangle, because every
opening here has chamfered corners and a rectangular cut would leave a
square hole where the frame has an angled one.

Everything else in the image is left alone, the scroll bar included: it
is painted art with no hole, and `fltgeom.SCROLL_SRC_COLUMN` is the
measurement that puts HD's thumb on it.

Usage:
    python tools/fleets_frame_build.py                  # to a temp file
    python tools/fleets_frame_build.py --out PATH
"""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Data's source art, tracked (decision 42: the derived artwork ships,
#: and here the original does too — it is Data's own, not extracted).
SRC = os.path.join(ROOT, "screens", "fleets", "assets", "_src",
                   "fleets_frame_4k_map165.png")
SRC_SHA256 = ("92f89a8650684de237730248a8b3b977674bbe9886a83bc2a961acd"
              "be498a83d")

#: The four bottom-row plates, x range each, measured from the border
#: profiles at mid height. They share one vertical extent; only the
#: widths differ, which is the whole reason the rebuild is a 3-slice.
PLATE = {"Leaders": (2162, 2512), "Support": (2539, 2844),
         "Combat": (2872, 3180), "Return": (3207, 3580)}
PY0, PY1 = 1796, 1941          # plate top and bottom, all four
IY0, IY1 = 1807, 1931          # interior, i.e. the future hole
LEAD_IX = (2173, 2502)         # the Leaders interior's x range

MX = 13                        # side margin; Support and Combat are 27 apart
MT, MB = 32, 27                # to the band's seams above and below
CORNER = 60                    # plate kept at each end of the 3-slice

#: Dark enough to be an interior. Swept 16..40 on the rebuilt art: the
#: 32 openings do not move anywhere in that range.
DARK = 22
#: The opening detector's own two thresholds, swept 26..34 and 22..30.
SEED_DARK, EDGE = 30, 26
SEED_K = 13
MIN_AREA = 8000

EXPECTED_HOLES = 32


def _openings(lum):
    """Every opening of the frame, as (x, y, w, h), from the dark inside.

    Two steps, because neither alone works on this image:

    1. SEPARATE. Every dark interior joins its neighbours through the
       chassis shadow, so a plain threshold returns the whole 3840x2160
       canvas as one blob. Eroding by a 13x13 structure before labelling
       breaks those connections and leaves one seed per opening.
    2. GROW. The seed is smaller than the opening and dilating it back
       overshoots into the frame, so each edge is walked outward while
       the next line is MOSTLY dark. A majority test rather than a
       single scan line, because the openings still contain the painted
       content: a star is a few px of an 1800 px row and would stop a
       centre-line scan dead.

    Morphological reconstruction belongs between the two and is wrong
    here — propagating the seed inside the original mask floods straight
    back into the joined blob.
    """
    h, w = lum.shape
    seeds = ndimage.binary_erosion(lum <= SEED_DARK,
                                   np.ones((SEED_K, SEED_K), bool))
    lab, _n = ndimage.label(seeds)
    out = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        if int((lab[sl] == i).sum()) < MIN_AREA // 4:
            continue
        ys, xs = sl
        left, right = xs.start, xs.stop - 1
        top, bottom = ys.start, ys.stop - 1
        for _ in range(400):
            moved = False
            if left > 0 and (lum[top:bottom + 1, left - 1] < EDGE).mean() >= .8:
                left -= 1
                moved = True
            if right < w - 1 and (lum[top:bottom + 1, right + 1] < EDGE).mean() >= .8:
                right += 1
                moved = True
            if top > 0 and (lum[top - 1, left:right + 1] < EDGE).mean() >= .8:
                top -= 1
                moved = True
            if bottom < h - 1 and (lum[bottom + 1, left:right + 1] < EDGE).mean() >= .8:
                bottom += 1
                moved = True
            if not moved:
                break
        rect = (left, top, right - left + 1, bottom - top + 1)
        # What the detector also finds and what none of it is: the dark
        # vent slots in the outer chassis at either canvas edge, the
        # painted scroll trough, and one blob that merges through the
        # shadow right of RETURN. The frame's own openings all sit
        # inside the chassis and are wider than they are thin.
        if rect[2] * rect[3] < MIN_AREA or rect[3] < 70:
            continue
        if rect[0] < 150 or rect[0] + rect[2] > 3700:
            continue
        if rect[3] > 3 * rect[2]:
            continue
        # ...and one seed that the erosion does not manage to separate,
        # which grows back out over nearly the whole canvas. No opening
        # of this frame is anywhere near that big: the largest is the
        # map at 1812x1101.
        if rect[2] > 3000 and rect[3] > 1500:
            continue
        out.append(rect)
    return sorted(set(out), key=lambda r: (r[1] // 100, r[0]))


def _unlit(im):
    """Support and Combat rebuilt at their own widths, corners kept."""
    a = np.asarray(im).copy()
    x0, x1 = PLATE["Leaders"]
    tile = a[PY0 - MT:PY1 + 1 + MB, x0 - MX:x1 + 1 + MX].copy()
    tile[:, :MX] = tile[:, -MX:][:, ::-1]

    # Flatten the word "Leaders" out of the interior so it is not
    # carried into the other two slots. ONLY the bright islands the
    # dark interior ENCLOSES are replaced — the letters. A plain
    # rectangle also covers the four chamfer corners, which sit in the
    # interior's bounding box but are frame, not content; doing it that
    # way cut the rebuilt corners square.
    iy0, iy1 = IY0 - (PY0 - MT), IY1 - (PY0 - MT)
    ix0, ix1 = LEAD_IX[0] - (x0 - MX), LEAD_IX[1] - (x0 - MX)
    inner = tile[iy0:iy1 + 1, ix0:ix1 + 1]
    dark = inner.astype(np.float32).mean(axis=2) <= DARK
    islands = ndimage.binary_dilation(
        ndimage.binary_fill_holes(dark) & ~dark, np.ones((5, 5), bool))
    for y in range(inner.shape[0]):
        sel = islands[y]
        if sel.any():
            inner[y][sel] = np.percentile(
                inner[y][~sel], 50, axis=0).astype(np.uint8)

    src = Image.fromarray(tile)
    sw, sh = src.size
    keep = CORNER + MX
    left = src.crop((0, 0, keep, sh))
    right = src.crop((sw - keep, 0, sw, sh))
    middle = src.crop((keep, 0, sw - keep, sh))
    out_im = im.copy()
    for name in ("Support", "Combat"):
        px0, px1 = PLATE[name]
        tw = (px1 - px0 + 1) + 2 * MX
        mid = middle.resize((tw - 2 * keep, sh), Image.LANCZOS)
        piece = Image.new("RGB", (tw, sh))
        piece.paste(left, (0, 0))
        piece.paste(mid, (keep, 0))
        piece.paste(right, (tw - keep, 0))
        out_im.paste(piece, (px0 - MX, PY0 - MT))
    return out_im


def _cut(im, rects):
    """Alpha 0 inside every opening, following its shape."""
    a = np.asarray(im.convert("RGBA")).copy()
    lum = a[:, :, :3].astype(np.float32).mean(axis=2)
    alpha = a[:, :, 3]
    for (x, y, w, h) in rects:
        sub = lum[y:y + h, x:x + w]
        # `binary_fill_holes` closes every bright island the interior
        # still encloses — the map's stars, the buttons' labels. That
        # is what takes the painted content out: it ends up inside the
        # hole rather than being retouched off the art.
        mask = ndimage.binary_fill_holes(sub <= DARK)
        lab, n = ndimage.label(mask)
        comp = lab[h // 2, w // 2]
        if comp == 0:                       # centre sits on an island
            sizes = ndimage.sum(mask, lab, range(1, n + 1))
            comp = int(np.argmax(sizes)) + 1
        alpha[y:y + h, x:x + w][lab == comp] = 0
    # Nothing under a fully transparent pixel. Work order 146 measured
    # this on the v4 frame and it is worth keeping: RGB left under
    # alpha 0 is invisible to a normal blit and appears the moment
    # anything reaches for BLEND_RGB_ADD or a premultiplied copy.
    a[:, :, :3][alpha == 0] = 0
    return Image.fromarray(a)


def build(src=SRC):
    """The finished frame, as an RGBA image. Raises if it is not right."""
    import hashlib
    with open(src, "rb") as fh:
        got = hashlib.sha256(fh.read()).hexdigest()
    if got != SRC_SHA256:
        raise SystemExit(f"{src}: sha256 {got}, expected {SRC_SHA256} — "
                         "the source art changed, so every number in "
                         "this module is a measurement of something else")
    im = Image.open(src).convert("RGB")
    im = _unlit(im)
    lum = np.asarray(im).astype(np.float32).mean(axis=2)
    rects = _openings(lum)
    if len(rects) != EXPECTED_HOLES:
        raise SystemExit(f"{len(rects)} openings found, {EXPECTED_HOLES} "
                         "expected (1 minimap + 3 arrow bar + 1 text "
                         "panel + 20 cells + 7 controls)")
    return _cut(im, rects)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--out", default=os.path.join(
        ROOT, "screens", "fleets", "assets", "frame_built.png"))
    args = ap.parse_args()
    out = build(args.src)
    out.save(args.out, optimize=True)
    print(f"wrote {args.out}  {out.size[0]}x{out.size[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
