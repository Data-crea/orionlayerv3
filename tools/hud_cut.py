#!/usr/bin/env python3
"""Cut the HUD pieces code cannot draw out of Data's HUD (work order 169).

    python tools/hud_cut.py                 # write assets/shared/hud/cut/
    python tools/hud_cut.py --out DIR       # write somewhere else
    python tools/hud_cut.py --sheet         # also a contact sheet

**What is cut, and why it is cut rather than drawn** (decision 71):

- the twelve ICONS — five in the info panel, six in the nav row, the
  TURN triangle. They are pictures (coins, a space station, a bowl of
  food, a microscope): no amount of code draws those.
- the TITLE PLATE with its two wings — the plate's glossy centre, its
  bevel and the orange lamps are painted light, which a flat fill, an
  edge and a glow cannot reproduce. Judged from the artwork; no code
  version was built (169 parked, P5).

Everything else — panels, buttons, the action button, separators — is
drawn in code by `core/hud` from `assets/shared/hud/style.json`.

**DERIVED, UNSCALED, NEVER COMMITTED** (decisions 40 and 58): each piece
is a crop at the HUD's own resolution; the block scales it once where it
is drawn. `tools/setup.py` runs this and git ignores the output, and the
smoke test rebuilds it into a scratch folder and compares bytes — the
licence to call it derived.

**How an icon is lifted off its panel.** The HUD has real alpha, but an
icon sits ON the panel's opaque fill, so its alpha is 255 like the fill
around it. Each icon is un-composited against the panel it sits on: the
background B is the median of a ring just outside the icon's box, and a
pixel P becomes alpha a = min(1, max|P - B| / KEY) with colour
B + (P - B) / a. Drawn back over B that reproduces P exactly; over the
HUD panel's own fill, which is B's colour to within the fill's noise, it
reproduces the artwork. KEY is the difference at which a pixel counts as
all icon: 72 levels, below which the painted glow around each icon starts
to read as a dark square on a lighter panel.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUD = os.path.join(ROOT, "assets", "shared", "hud", "galaxy_hud.png")
OUT = os.path.join(ROOT, "assets", "shared", "hud", "cut")

#: See the module docstring: the difference that counts as opaque icon.
KEY = 72
#: A pixel differing from the ring's median by more than this belongs to
#: the icon when its box is found.
FIND = 34
#: Ring width and pad around the icon's box, in HUD px.
RING = 10
PAD = 16
#: The alpha falls to zero over this many px at the crop's border, so a
#: painted halo cut by the box cannot end in a visible square edge on a
#: ground lighter than the HUD's own.
FEATHER = 14

#: Where to look for each icon, in HUD px (x0, y0, x1, y1), and how it is
#: told from its ground. The info icons are pictures in many colours,
#: some dark (the microscope's base), so an icon pixel is one unlike the
#: panel's measured deep fill; their regions stop short of the panel's
#: right edge line (x 6618) and its inner glow. The nav icons are lit
#: blue glyphs on a button whose fill is a gradient and whose slanted
#: divider crosses the region, so an icon pixel is one BRIGHTER than any
#: divider (luma 110; the dividers peak at 57-86).
DEEP = (3, 12, 28)
ICONS = {
    "treasury": ((5900, 730, 6585, 1190), "unlike"),
    "command": ((5900, 1245, 6585, 1700), "unlike"),
    "food": ((5900, 1750, 6585, 2170), "unlike"),
    "freighters": ((5900, 2220, 6585, 2650), "unlike"),
    "research": ((5900, 2705, 6585, 3215), "unlike"),
    "colonies": ((130, 3372, 520, 3540), "bright"),
    "planets": ((1000, 3372, 1420, 3540), "bright"),
    "fleets": ((1870, 3372, 2330, 3540), "bright"),
    "leaders": ((2800, 3372, 3220, 3540), "bright"),
    "races": ((3720, 3372, 4140, 3540), "bright"),
    "info": ((4620, 3372, 5040, 3540), "bright"),
    "turn": ((5680, 3380, 5960, 3535), "bright"),
}
#: The luma a nav glyph's pixels reach and a divider's do not.
BRIGHT = 110

#: The title plate and its wings: the whole first row of opaque artwork.
TITLE = (960, 0, 5740, 240)


def load(path=HUD):
    return np.asarray(Image.open(path).convert("RGBA")).astype(np.float64)


def _ring_median(a, x0, y0, x1, y1):
    top = a[max(0, y0 - RING):y0, x0:x1, :3].reshape(-1, 3)
    bot = a[y1:y1 + RING, x0:x1, :3].reshape(-1, 3)
    lef = a[y0:y1, max(0, x0 - RING):x0, :3].reshape(-1, 3)
    rig = a[y0:y1, x1:x1 + RING, :3].reshape(-1, 3)
    return np.median(np.concatenate([top, bot, lef, rig]), axis=0)


def find_box(a, region, how):
    """The icon's box inside `region` (see ICONS for `how`)."""
    x0, y0, x1, y1 = region
    crop = a[y0:y1, x0:x1, :3]
    if how == "bright":
        on = (0.299 * crop[..., 0] + 0.587 * crop[..., 1]
              + 0.114 * crop[..., 2]) > BRIGHT
    else:
        on = np.abs(crop - np.array(DEEP)).max(axis=2) > FIND
    rows = np.where(on.sum(axis=1) >= 3)[0]
    cols = np.where(on.sum(axis=0) >= 3)[0]
    assert len(rows) and len(cols), f"no icon found in {region}"
    return (x0 + int(cols.min()) - PAD, y0 + int(rows.min()) - PAD,
            x0 + int(cols.max()) + 1 + PAD, y0 + int(rows.max()) + 1 + PAD)


def lift(a, box, how):
    """Un-composite the icon in `box` off its panel (module docstring).

    A lit glyph ("bright") is light added to its ground, so only what is
    BRIGHTER than the ground belongs to it: counting darker pixels too
    turned the painted vignette round the TURN triangle into a dark
    square on any ground lighter than the HUD's. A picture ("unlike")
    has real shadows and keeps both directions."""
    x0, y0, x1, y1 = box
    bg = _ring_median(a, x0, y0, x1, y1)
    p = a[y0:y1, x0:x1, :3]
    d = p - bg
    if how == "bright":
        d = np.maximum(d, 0.0)
    alpha = np.clip(np.abs(d).max(axis=2) / KEY, 0.0, 1.0)
    h, w = alpha.shape
    ry = np.minimum(np.arange(h), np.arange(h)[::-1])[:, None]
    rx = np.minimum(np.arange(w), np.arange(w)[::-1])[None, :]
    alpha = alpha * np.clip(np.minimum(rx, ry) / FEATHER, 0.0, 1.0)
    safe = np.where(alpha > 0, alpha, 1.0)[..., None]
    rgb = np.clip(bg + d / safe, 0, 255)
    out = np.dstack([rgb, alpha * 255.0])
    return np.round(out).astype(np.uint8)


def cut(hud=HUD):
    """name -> (RGBA uint8 array, box in HUD px)."""
    a = load(hud)
    pieces = {}
    for name, (region, how) in ICONS.items():
        box = find_box(a, region, how)
        pieces[f"icon_{name}"] = (lift(a, box, how), box)
    x0, y0, x1, y1 = TITLE
    pieces["title_plate"] = (np.round(a[y0:y1, x0:x1]).astype(np.uint8),
                             TITLE)
    return pieces


def write(out=OUT, hud=HUD):
    os.makedirs(out, exist_ok=True)
    names = []
    for name, (arr, _box) in cut(hud).items():
        Image.fromarray(arr, "RGBA").save(os.path.join(out, name + ".png"),
                                          optimize=False)
        names.append(name)
    return sorted(names)


def sheet(out=OUT):
    tiles = []
    for name in sorted(os.listdir(out)):
        if name.endswith(".png") and not name.startswith("_"):
            im = Image.open(os.path.join(out, name)).convert("RGBA")
            im.thumbnail((360, 200))
            bg = Image.new("RGBA", (380, 220), (3, 12, 28, 255))
            bg.alpha_composite(im, ((380 - im.width) // 2,
                                    (220 - im.height) // 2))
            tiles.append(bg)
    cols = 4
    rows = (len(tiles) + cols - 1) // cols
    s = Image.new("RGBA", (cols * 380, rows * 220), (40, 40, 40, 255))
    for i, t in enumerate(tiles):
        s.paste(t, ((i % cols) * 380, (i // cols) * 220))
    s.save(os.path.join(out, "_contact_sheet.png"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--sheet", action="store_true")
    args = ap.parse_args()
    names = write(args.out)
    if args.sheet:
        sheet(args.out)
    print(f"{len(names)} pieces written to {os.path.abspath(args.out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
