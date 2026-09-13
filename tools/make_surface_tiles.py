#!/usr/bin/env python3
"""Cut the ten planet surface pictures out of Data's sheet.

    python tools/make_surface_tiles.py
    python tools/make_surface_tiles.py --out DIR     # write elsewhere
    python tools/make_surface_tiles.py --sheet PATH  # another sheet

Writes `screens/colony_summary/assets/surfaces/<climate>.png`, one per
`PLANET_CLIMATE` (orion2_consts.h:362-373), named by the same lowercase
enum names `colonyplanets.NAMES` holds — one home for the names, read
from there, so a disc and a surface for one climate cannot be spelt
two ways.

**THE SOURCE IS AI-GENERATED.** Data made `planet_surfaces.png` with
ChatGPT on 13 September 2026 (brief 97): a 2172x724 sheet of ten
captioned cards in two rows of five, labelled Toxic, Radiated, Barren,
Desert, Tundra / Ocean, Swamp, Arid, Terran, Gaia — which is the
enum's own order, checked against the source and not assumed.
**LICENCE:** project artwork with no copyright claim, not extracted
from anybody's Master of Orion 2. The sheet is committed as input under
`assets/_src/surfaces/`; what this tool makes of it is DERIVED —
ignored, rebuilt by `tools/setup.py` (decision 40), and a smoke check
regenerates it and compares bytes.

**WHAT IS CUT, MEASURED.** Each card is a thin grey frame on a flat
dark field (about (1, 8, 15), noise 3-4) with the title above the
picture and the caption below it. The picture carries its own 3 px
outline — dark, bright, dark — and one anti-aliased row or column
against it. Median edge profiles across all ten cards put the first
FULL picture pixel at x = 13 + 434 * column and the last at
x = 423 + 434 * column, so 411 wide on every card; rows at y 124..334
(211 high) on the top row and y 430..643 (214 high) on the bottom.
The two rows genuinely differ by three pixels on the sheet. Flood fill
from the sheet border finds the cards and not the pictures: Barren's
sky and Swamp's left edge are close to black and read as field to any
brightness threshold, which is why the rule is the edges and not a
mask.

**NO SCALING HERE.** The tile is written at sheet resolution, a plain
crop saved as PNG, so a rebuild is byte-identical and no Pillow
resampling version can move a byte. The image box scales it where it
is drawn; at 1080p and 1440p that is an upscale from 411 px, which
Data accepted for his look (brief 97, decision 4).
"""
import argparse
import hashlib
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from screens.colony_summary.colonyplanets import NAMES  # noqa: E402

SHEET = os.path.join(ROOT, "screens", "colony_summary", "assets", "_src",
                     "surfaces", "planet_surfaces.png")
OUT_DIR = os.path.join(ROOT, "screens", "colony_summary", "assets",
                       "surfaces")

#: The sheet the rule below was measured on. A replaced sheet is
#: refused rather than cut at edges that describe another one.
SHEET_SHA256 = ("0092f48571ff247d74af7d718c797f1055489a549ca561a17811f01c"
                "7e5612de")

#: First full picture column of card 0, and the card pitch.
X0, PITCH, WIDTH = 13, 434, 411
#: (first full row, height) per row of cards, top then bottom.
ROWS = ((124, 211), (430, 214))
COLUMNS = 5


def tile_rects():
    """{climate name: (x, y, w, h)} in the enum's order."""
    out = {}
    for i, name in enumerate(NAMES):
        row, col = divmod(i, COLUMNS)
        y, h = ROWS[row]
        out[name] = (X0 + PITCH * col, y, WIDTH, h)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", default=SHEET)
    ap.add_argument("--out", default=OUT_DIR)
    args = ap.parse_args()
    if not os.path.exists(args.sheet):
        sys.exit(f"sheet not found: {args.sheet}")
    with open(args.sheet, "rb") as fh:
        got = hashlib.sha256(fh.read()).hexdigest()
    if got != SHEET_SHA256:
        sys.exit(f"{args.sheet} has sha256 {got[:16]}…, the tile rule was "
                 f"measured on {SHEET_SHA256[:16]}… — re-measure the edges "
                 f"and update X0, PITCH, WIDTH and ROWS with the hash")
    assert len(NAMES) == COLUMNS * len(ROWS), NAMES
    sheet = Image.open(args.sheet).convert("RGB")
    os.makedirs(args.out, exist_ok=True)
    for name, (x, y, w, h) in tile_rects().items():
        path = os.path.join(args.out, f"{name}.png")
        sheet.crop((x, y, x + w, y + h)).save(path)
        print(f"  {name:<9} ({x}, {y}, {w}, {h}) -> "
              f"{os.path.relpath(path, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
