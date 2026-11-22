"""Cut the Reference page's icons out of the player's two icon sheets — WO 423.

    python tools/reference_icons_install.py <strategy_sheet.png> <hud_sheet.png> [mockup.png]

Data's mockup ("Futuristic Space Reference Interface") puts a gold icon in
front of every row of the Info screen's Reference page, the fourteen
categories and the how-to topics. The icons come from two sheets of gold
symbols: "Golden Sci-Fi Strategy Icon Grid" (8 x 5, an opaque brown ground
with a vignette) and "Golden Sci-Fi HUD Icon Grid" (8 x 4, transparent with
a dark halo). Each symbol is cut out of its cell by what is NOT the ground:
the ground's level is modelled (a blur of the pixels that are not a symbol,
iterated, so the vignette and the brown gradient go), what differs from it is
the symbol, its holes are filled and the edge softened; the HUD sheet is
first laid over black, as its halo asks. Symbols are kept as they are in
colour, trimmed, and written to
`<mod folder>/files/screens/info/assets/icons/<name>.png`, where the Info
screen's Reference page (`screens/info/inforef`) reads them.
Marking: HD EXTENSION `reference_icons`. A symbol that is not found is not
written and its rows go without.

With the mockup as a third argument the two wide pictures under the lists
are cut from it as well (`art_technology.png`, the planet system;
`art_guide.png`, the ship's wireframe; HD EXTENSION `reference_pictures`):
the picture's window inside the mockup's frame, its edge feathered so no box
shows on the panel. The windows are fractions of the mockup (1672 x 941).

The cells are fractions of the sheet (so a sheet of another size works); the
names are those `inforef.ICON_FILES` asks for.
"""
import os
import sys

# Cutting pictures needs no window and no sound: never open one in the
# player's session (the check of the live runs holds every tool to this).
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
from scipy import ndimage as ndi  # noqa: E402

from core import usermod  # noqa: E402
from screens.info import inforef  # noqa: E402

REL = inforef.ICON_REL
#: sheet -> (columns, rows, threshold); the symbol's cell is `(row, column)`
SHEETS = {"strategy": (8, 5, 38), "hud": (8, 4, 30)}
#: name -> (sheet, row, column): the symbol's place on its sheet
CELLS = {
    # Strategy sheet
    "plus": ("strategy", 0, 0), "move": ("strategy", 0, 1),
    "people": ("strategy", 0, 2), "crown": ("strategy", 0, 3),
    "planet": ("strategy", 0, 4), "swords": ("strategy", 0, 5),
    "flask": ("strategy", 0, 6), "crosshair": ("strategy", 0, 7),
    "star": ("strategy", 1, 0), "coins": ("strategy", 1, 2),
    "gear": ("strategy", 1, 3), "shield": ("strategy", 1, 4),
    "skull": ("strategy", 1, 5), "wrench": ("strategy", 1, 6),
    "question": ("strategy", 2, 0), "flag": ("strategy", 2, 1),
    "galaxy": ("strategy", 2, 2), "laurel": ("strategy", 2, 4),
    "burst": ("strategy", 2, 5), "comet": ("strategy", 2, 6),
    "document": ("strategy", 3, 0), "spaceship": ("strategy", 4, 1),
    "ringed_planet": ("strategy", 4, 4), "meteor": ("strategy", 4, 0),
    # HUD sheet
    "ring_target": ("hud", 0, 6), "explosion": ("hud", 2, 3),
    "rocket": ("hud", 2, 5), "factory": ("hud", 2, 6),
    "building": ("hud", 3, 0), "plant": ("hud", 3, 1), "lock": ("hud", 3, 2),
}
assert set(CELLS) == set(inforef.ICON_NAMES), "tool and screen disagree"


def ground(rgb, thr, iters=4, sigma=22):
    """The sheet's own ground level: a blur of what is not a symbol, taken
    again with every pass's symbols left out."""
    v = rgb.max(axis=2)
    weight = np.ones_like(v)
    level = v
    for _ in range(iters):
        level = (ndi.gaussian_filter(v * weight, sigma)
                 / np.maximum(ndi.gaussian_filter(weight, sigma), 1e-3))
        shape = ndi.binary_dilation(np.abs(v - level) > thr, iterations=6)
        weight = (~shape).astype(np.float32)
    return level


def cut_sheet(rgb, cols, rows, thr, min_area=120):
    """`{(row, column): RGBA image}` — every symbol, trimmed."""
    height, width = rgb.shape[:2]
    shape = np.abs(rgb.max(axis=2) - ground(rgb, thr)) > thr
    shape = ndi.binary_fill_holes(ndi.binary_closing(shape, iterations=2))
    label, count = ndi.label(shape)
    ids = range(1, count + 1)
    sizes = ndi.sum(shape, label, ids)
    centres = ndi.center_of_mass(shape, label, ids)
    cell_w, cell_h = width / cols, height / rows
    groups = {}
    for i in range(count):            # a symbol may be several parts (the
        if sizes[i] < min_area:       # dot of a question mark, a moon)
            continue
        cy, cx = centres[i]
        groups.setdefault((int(cy // cell_h), int(cx // cell_w)),
                          []).append(i + 1)
    out = {}
    for key, parts in groups.items():
        keep = np.isin(label, parts)
        alpha = ndi.gaussian_filter(keep.astype(np.float32), 0.7)
        ys, xs = np.where(keep)
        box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
        rgba = np.dstack([rgb, alpha * 255]).astype(np.uint8)
        out[key] = Image.fromarray(rgba).crop(box)
    return out


def load_sheet(path, name):
    cols, rows, thr = SHEETS[name]
    image = np.asarray(Image.open(path).convert("RGBA")).astype(np.float32)
    rgb = image[..., :3] * image[..., 3:] / 255.0 if name == "hud" \
        else image[..., :3]
    return cut_sheet(rgb, cols, rows, thr)


#: name -> window in the mockup as fractions (left, top, right, bottom),
#: measured inside its frame lines
ART_WINDOWS = {"art_technology": (448 / 1672, 640 / 941, 1022 / 1672, 820 / 941),
               "art_guide": (1064 / 1672, 640 / 941, 1636 / 1672, 820 / 941)}
FEATHER = 10
#: the ground's level and the level from which a pixel is fully there
FLOOR, FULL = 14, 60


def cut_art(mockup):
    """`{name: RGBA image}` — the mockup's two wide pictures, edge feathered."""
    image = Image.open(mockup).convert("RGB")
    width, height = image.size
    out = {}
    for name, (x0, y0, x1, y1) in ART_WINDOWS.items():
        part = image.crop((round(x0 * width), round(y0 * height),
                           round(x1 * width), round(y1 * height)))
        w, h = part.size
        ramp = lambda n: np.clip(np.minimum(np.arange(n), np.arange(n)[::-1])
                                 / FEATHER, 0, 1)
        rgb = np.asarray(part).astype(np.float32)
        # light over dark, as the audience's icons: the picture's own dark
        # ground goes (it is not the panel's dark, and showed as a box); the
        # edge is feathered besides
        peak = rgb.max(axis=2)
        light = np.clip((peak - FLOOR) * 255.0 / (FULL - FLOOR), 0, 255)
        alpha = np.outer(ramp(h), ramp(w)) * light
        rgba = np.dstack([rgb, alpha]).astype(np.uint8)
        out[name] = Image.fromarray(rgba)
    return out


def install(strategy, hud, mockup=None):
    cuts = {"strategy": load_sheet(strategy, "strategy"),
            "hud": load_sheet(hud, "hud")}
    folder = os.path.join(usermod.mod_dir(), usermod.FILES,
                          *REL.split("/"))
    os.makedirs(folder, exist_ok=True)
    missing = []
    for name, (sheet, row, col) in sorted(CELLS.items()):
        image = cuts[sheet].get((row, col))
        if image is None:
            missing.append(name)
            continue
        target = os.path.join(folder, name + ".png")
        image.save(target)
        print(f"{name}: {image.size} -> {target}")
    for name, image in (cut_art(mockup) if mockup else {}).items():
        target = os.path.join(folder, name + ".png")
        image.save(target)
        print(f"{name}: {image.size} -> {target}")
    if missing:
        print("NOT FOUND on the sheets (rows go without):",
              ", ".join(missing))


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        raise SystemExit(__doc__)
    install(*sys.argv[1:])
