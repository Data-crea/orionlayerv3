#!/usr/bin/env python3
"""Cut the colony output panel's six row icons out of Data's sheets.

    python tools/make_output_icons.py
    python tools/make_output_icons.py --out DIR   # write somewhere else
    python tools/make_output_icons.py --probe     # list components only

Writes `screens/colony_summary/assets/output/`:

    food.png  industry.png  research.png  bc.png
    morale_normal.png  morale_low.png

**THE SOURCES ARE AI-GENERATED.** Data made the three sheets with
ChatGPT on 13 September 2026 — `symbols.png` (coin, corn, pickaxe,
test tube, in that order), `normal_moral.png` and `low_moral.png` —
and they live under `screens/colony_summary/assets/_src/output/`.
**LICENCE:** they are the project's own artwork, not extracted from
anybody's Master of Orion 2, so they are ours to ship. That is the
same line `assets/frame.png` and the planet discs are on: the input is
committed (`.gitignore` keeps `_src/`), and what this tool makes of it
is DERIVED — ignored and rebuilt by `tools/setup.py` (decision 40),
with a smoke check that regenerating reproduces the files byte for
byte, which is the only licence to call them derived.

**WHAT THE ICONS ARE, AND ARE NOT** — decision 56. Row LABELS beside
the words FOOD, INDUSTRY, RESEARCH, BC and MORALE, marked DEVIATION
in `layout.json` under `output._deviation_note`. The shapes are
redrawings of the original's own unit sprites (COLONY2.LBX 0-3) and
morale masks (0x10 / 0x11), but the original only ever COUNTS with
them and never puts one beside a word.

**THE BACKGROUND, BY DATA'S RULE.** The sheets have no alpha and no
single background colour: every channel of the black is 0 or 1 and
all eight combinations occur, so an exact key leaves speckle and a
tolerance would eat the icons' own black. So: background is what has
every channel <= 1 AND is connected to the sheet's border (4-connected,
so a diagonal cannot leak into an enclosed area). Everything else is
icon, which keeps the masks' black eyes and mouths. Inside each
icon's rect only the LARGEST 8-connected component is kept — eleven
specks of 1 to 27 px, none brighter than 2, sit on the sheets and are
not part of anything.

**NO DARK FRINGE.** The art was anti-aliased against black, so its
outermost pixels are the icon's colour already multiplied towards
black: the median brightest channel climbs over the first 2 to 4 px
from the background (3 -> 7 -> 38 -> 91 on the coin, 4 -> 26 -> 32 on
the green mask) and then levels out. Keying those as opaque leaves a
dark halo on a light panel; keying them as transparent and leaving
their RGB behind shows the rest wherever a draw path ignores alpha
(`BLEND_RGB_ADD` — fundament section 4). So within `RIM` px of the
background the pixel is un-multiplied: alpha is its brightest channel
over the brightness of the icon just inside the rim, and its colour
is divided back up by that alpha. Deeper than `RIM` everything is
opaque whatever its colour, and every transparent pixel's RGB is
blanked to 0.

**ONE LANCZOS DOWNSCALE, THEN NOTHING SMOOTHS AGAIN.** The sheets look
like pixel art and have no grid (the planet sheet's measurement, same
generator), so there is no block to sample. Data's decision: resample
ONCE, with Lanczos, from the trimmed source to the master size, in
PREMULTIPLIED alpha so the transparent black cannot bleed into an
edge colour; the renderer scales the master by nearest neighbour from
there, like the figures and the planets. The master size is
`output.icon_size` in `layout.json` — ours, with its source beside it
("An asset is not a measurement") — read here, never typed twice.

**ONE FOOTPRINT FOR ALL SIX.** Each icon is fitted by its longer edge
into an `icon_size` square and centred. The two morale masks come on
canvases of different size and aspect (1254x1254 and 1374x1145), and
a state change must neither move nor resize the icon on screen, so
the tool REFUSES TO WRITE ANYTHING if the two masks' outputs differ
in size or either fails to fill the square on its long edge — the
same shape of guard as `make_black_hole_master.py`'s axis check.
"""
import argparse
import hashlib
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "screens", "colony_summary", "assets",
                       "_src", "output")
OUT_DIR = os.path.join(ROOT, "screens", "colony_summary", "assets",
                       "output")
LAYOUT = os.path.join(ROOT, "screens", "colony_summary", "layout.json")

#: The sheets this tool was measured against. A replaced sheet is
#: refused rather than cut at rectangles that describe another one —
#: re-run with --probe and edit ICONS.
SOURCE_SHA256 = {
    "symbols.png":
        "a37a81cddf33b4230383b4fc5219f31d081244301e758b9c4cb925d77473a0c3",
    "normal_moral.png":
        "9441ae254a32087973debc8f78c13e5aeb0d78e84dffafe1fe38e3b267ed354c",
    "low_moral.png":
        "5bc347f5c49614f99b15e0e7839ddd5899084f97ee90fbcb302e9b7b5c7b616d",
}

#: (output name, sheet, (x0, y0, x1, y1)) — each icon's bounding box
#: plus 1 px, read off the connected components once (13 September
#: 2026, `--probe`). The names are Data's assignment of the cut.
ICONS = [
    ("bc",            "symbols.png",      (101, 215, 486, 597)),
    ("food",          "symbols.png",      (555, 129, 990, 670)),
    ("industry",      "symbols.png",      (1072, 188, 1506, 670)),
    ("research",      "symbols.png",      (1616, 199, 1779, 672)),
    ("morale_normal", "normal_moral.png", (203, 155, 1052, 1115)),
    ("morale_low",    "low_moral.png",    (303, 171, 1070, 1015)),
]

MORALE = ("morale_normal", "morale_low")

#: Brightest channel at or below this is background colour — the
#: sheets' black is dithered 0/1 and nothing brighter (Data's rule).
BACKGROUND_MAX = 1

#: Width of the anti-aliased rim that is un-multiplied, in source px.
#: Measured: the ramp is over by 2 to 4 px on all six.
RIM = 3

#: How far inside the rim the reference brightness is taken from.
REFERENCE_DEPTH = 3


def icon_size():
    with open(LAYOUT, encoding="utf-8") as fh:
        size = json.load(fh)["output"].get("icon_size")
    if not isinstance(size, int) or size <= 0:
        sys.exit(f"layout.json output.icon_size is {size!r}; the master "
                 f"size lives there and nowhere else")
    return size


def load_sheet(name):
    path = os.path.join(SRC_DIR, name)
    if not os.path.exists(path):
        sys.exit(f"sheet not found: {path}")
    with open(path, "rb") as fh:
        got = hashlib.sha256(fh.read()).hexdigest()
    if got != SOURCE_SHA256[name]:
        sys.exit(f"{name} has sha256 {got[:16]}…, ICONS was measured on "
                 f"{SOURCE_SHA256[name][:16]}… — run --probe and update "
                 f"ICONS and SOURCE_SHA256 together")
    return np.asarray(Image.open(path).convert("RGB")).astype(np.float64)


def background(rgb):
    """Dark pixels connected to the sheet's border, 4-connected."""
    dark = rgb.max(axis=2) <= BACKGROUND_MAX
    lab, _ = ndimage.label(dark)
    border = np.unique(np.concatenate(
        [lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    return np.isin(lab, border[border != 0])


def cut(rgb, bg, rect):
    """One icon as a float RGBA array, trimmed to its content."""
    x0, y0, x1, y1 = rect
    part = rgb[y0:y1, x0:x1]
    lab, n = ndimage.label(~bg[y0:y1, x0:x1], structure=np.ones((3, 3)))
    if n == 0:
        sys.exit(f"nothing but background inside {rect}")
    sizes = ndimage.sum(np.ones(lab.shape), lab, range(1, n + 1))
    body = lab == (int(np.argmax(sizes)) + 1)

    bright = part.max(axis=2)
    depth = ndimage.distance_transform_edt(body)
    rim = body & (depth <= RIM)
    band = body & (depth > RIM) & (depth <= RIM + REFERENCE_DEPTH)
    reach = 2 * (RIM + REFERENCE_DEPTH) + 1
    reference = ndimage.grey_dilation(np.where(band, bright, 0),
                                      size=(reach, reach))
    # A feature thinner than the rim has no inside to ask; it is
    # referenced to its own brightest neighbour instead.
    thin = ndimage.grey_dilation(np.where(body, bright, 0),
                                 size=(reach, reach))
    reference = np.where(reference > 0, reference, thin)

    alpha = body.astype(np.float64)
    safe = np.maximum(reference, 1.0)
    alpha[rim] = np.clip(bright[rim] / safe[rim], 0.0, 1.0)
    colour = part.copy()
    lift = rim & (alpha > 0)
    colour[lift] = np.clip(part[lift] / alpha[lift][:, None], 0, 255)
    colour[alpha == 0] = 0

    ys, xs = np.nonzero(alpha > 0)
    sl = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
    return np.dstack([colour[sl], alpha[sl] * 255.0])


def master(rgba, size):
    """Fit by the longer edge into a size x size canvas, centred."""
    h, w = rgba.shape[:2]
    im = Image.fromarray(np.rint(rgba).astype(np.uint8), "RGBA")
    scale = size / max(w, h)
    fw, fh = max(1, round(w * scale)), max(1, round(h * scale))
    # PREMULTIPLIED, so the transparent pixels' black cannot be
    # averaged into the edge colours by the filter's support.
    small = im.convert("RGBa").resize((fw, fh), Image.LANCZOS)
    small = np.array(small.convert("RGBA"))
    small[small[:, :, 3] == 0, :3] = 0
    canvas = np.zeros((size, size, 4), dtype=np.uint8)
    ox, oy = (size - fw) // 2, (size - fh) // 2
    canvas[oy:oy + fh, ox:ox + fw] = small
    return Image.fromarray(canvas, "RGBA"), (fw, fh)


def probe():
    for name in SOURCE_SHA256:
        rgb = load_sheet(name)
        fg = ndimage.binary_dilation(rgb.max(axis=2) > BACKGROUND_MAX,
                                     structure=np.ones((3, 3)))
        lab, n = ndimage.label(fg, structure=np.ones((3, 3)))
        print(f"{name}: {n} components")
        for sl in ndimage.find_objects(lab):
            y, x = sl
            print(f"  ({x.start}, {y.start}, {x.stop}, {y.stop})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT_DIR)
    ap.add_argument("--probe", action="store_true",
                    help="print each sheet's components, write nothing")
    args = ap.parse_args()
    if args.probe:
        probe()
        return 0

    size = icon_size()
    sheets = {}
    built = {}
    for name, sheet, rect in ICONS:
        if sheet not in sheets:
            rgb = load_sheet(sheet)
            sheets[sheet] = (rgb, background(rgb))
        rgb, bg = sheets[sheet]
        built[name] = master(cut(rgb, bg, rect), size)

    # THE GUARD: nothing is written unless a morale change keeps the
    # icon where it was and as big as it was.
    fits = {n: built[n][1] for n in MORALE}
    images = {n: built[n][0].size for n in MORALE}
    if len(set(images.values())) != 1 or any(
            max(f) != size for f in fits.values()):
        sys.exit(f"REFUSED: the two morale masks do not share one "
                 f"footprint — canvases {images}, content {fits}, "
                 f"icon_size {size}. Nothing was written.")

    os.makedirs(args.out, exist_ok=True)
    for name, _sheet, _rect in ICONS:
        image, fitted = built[name]
        path = os.path.join(args.out, f"{name}.png")
        image.save(path)
        print(f"  {name:<14} {fitted[0]:>3}x{fitted[1]:<3} in "
              f"{size}x{size} -> {os.path.relpath(path, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
