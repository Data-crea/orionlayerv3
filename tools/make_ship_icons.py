"""Generate the galaxy map ship icons — four size steps per kind.

    python tools/make_ship_icons.py [--out DIR] [--src DIR] [--sheet]

orion2re keeps FOUR pre-rendered ship sprites per player colour and
per monster type and swaps between them by zoom level; it never
scales one artwork (SHIPS::Get_Ship_Icon_Pict_Seg_, BUFFER0.LBX
205 + colour*4 + (3 - zoom) for players, 241 + (type - 9)*4 + zoom
for monsters). This script produces the same four-file structure so
the renderer can swap rather than scale.

WHERE THIS DEVIATES FROM tools/make_star_icons.py — and why.

The star steps are drawn individually because the spread there is
33 px down to 17 px, a factor of two: detail that reads at 33 px
turns to mush at 17. Ship icons run 13 px to 10 px, a spread of
23 %. Four separately drawn steps would be indistinguishable, so the
steps here are rendered from ONE master per kind. That is a
deliberate, documented departure, not an oversight.

The structure is still four files, so replacing any single step with
hand-drawn artwork needs no code change at all — drop a new 2.png in
and the renderer picks it up.

Input:  assets/ships/_src/<kind>.png   HD master, RGBA, trimmed or not
Output: assets/ships/<kind>/0.png .. 3.png

The player master must be GREYSCALE. It is tinted to the eight MOO2
player colours at runtime (screens/galaxy_map/ships.py), exactly as
core/banner.py tints the banner cloth — colouring it here would mean
eight files per step instead of one.

Every export is EXPORT_SCALE times its native footprint, so the
sprite still has headroom at 4K (13 px x px, and px is about 5 there)
and the renderer only ever scales down.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import zoomtables as zt  # noqa: E402

#: Exported pixels per native pixel. 8 keeps step 0 at 104 px wide,
#: comfortably above the ~65 px it occupies on a 4K map.
EXPORT_SCALE = 8

#: Alpha below this is cleared. The masters are upscaled pixel art
#: with a soft halo; left in, the halo becomes a grey box once the
#: sprite is composited over the star field.
ALPHA_FLOOR = 12

#: Kinds and where their footprint comes from. "player" uses the ship
#: table, everything else the per-type monster table.
KINDS = ("player", "guardian", "amoeba", "crystal", "dragon", "eel",
         "hydra", "antaran")

SRC_REL = os.path.join("screens", "galaxy_map", "assets", "ships", "_src")
OUT_REL = os.path.join("screens", "galaxy_map", "assets", "ships")


def native_dim(kind, step):
    if kind == "player":
        return zt.ship_icon_dimension(step)
    return zt.monster_icon_dimension(kind, step)


def trim(img):
    """Crop to the visible content so the footprint means something.

    An untrimmed master carries a transparent margin, and the renderer
    fits the sprite into a native-pixel box: with the margin included
    the visible ship would come out a third too small and sit off
    centre. Cheapest possible source of a calibration bug.
    """
    a = np.array(img)
    mask = a[..., 3] > ALPHA_FLOOR
    if not mask.any():
        return img
    ys, xs = np.where(mask)
    return img.crop((int(xs.min()), int(ys.min()),
                     int(xs.max()) + 1, int(ys.max()) + 1))


def clean_alpha(img):
    a = np.array(img).astype(np.int16)
    faint = a[..., 3] <= ALPHA_FLOOR
    a[faint, 3] = 0
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def desaturate(img):
    """Force RGB to luma, alpha untouched.

    The master is greyscale to within a couple of levels, but LANCZOS
    ringing at the hard pixel-art edges pushes single channels apart by
    up to ~20. Tinting multiplies by a colour, so a stray green pixel
    survives as a stray green pixel. Cheaper to guarantee it here than
    to explain it later.
    """
    a = np.array(img).astype(np.float32)
    luma = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2])
    a[..., 0] = a[..., 1] = a[..., 2] = luma
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def render_step(master, kind, step):
    """One size step, exported at EXPORT_SCALE x its native footprint.

    Aspect ratio of the artwork is preserved; it is the renderer, not
    this script, that decides how the sprite sits inside the native
    box (see ships.py FIT_MODES). Fitting here would bake one choice
    into the asset and make the layout.json switch a lie.
    """
    nw, _nh = native_dim(kind, step)
    target_w = max(8, nw * EXPORT_SCALE)
    ratio = master.height / master.width
    target_h = max(8, int(round(target_w * ratio)))
    out = master.resize((target_w, target_h), Image.LANCZOS)
    out = clean_alpha(out)
    if kind == "player":
        out = desaturate(out)
    return out


def is_greyscale(img):
    a = np.array(img)
    vis = a[..., 3] > ALPHA_FLOOR
    if not vis.any():
        return True
    rgb = a[..., :3][vis].astype(int)
    return int((rgb.max(1) - rgb.min(1)).max()) <= 16


def contact_sheet(rendered, path):
    cell = 140
    pad = 10
    kinds = sorted(rendered)
    steps = zt.icon_step_count()
    sheet = Image.new("RGBA",
                      (pad + steps * (cell + pad),
                       pad + len(kinds) * (cell + pad)), (18, 18, 22, 255))
    for row, kind in enumerate(kinds):
        for step, img in enumerate(rendered[kind]):
            f = min(cell / img.width, cell / img.height, 1.0)
            scaled = img.resize((max(1, int(img.width * f)),
                                 max(1, int(img.height * f))), Image.LANCZOS)
            x = pad + step * (cell + pad) + (cell - scaled.width) // 2
            y = pad + row * (cell + pad) + (cell - scaled.height) // 2
            sheet.alpha_composite(scaled, (x, y))
    sheet.save(path)
    return path


def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default=os.path.join(base, SRC_REL))
    ap.add_argument("--out", default=os.path.join(base, OUT_REL))
    ap.add_argument("--sheet", action="store_true",
                    help="also write _contact_sheet.png next to --out")
    args = ap.parse_args()

    rendered = {}
    missing = []
    for kind in KINDS:
        src = os.path.join(args.src, f"{kind}.png")
        if not os.path.exists(src):
            missing.append(kind)
            continue
        master = trim(Image.open(src).convert("RGBA"))

        if kind == "player" and not is_greyscale(master):
            print(f"  WARNING: {kind}.png is not greyscale — runtime "
                  f"tinting will multiply on top of its own colour")

        out_dir = os.path.join(args.out, kind)
        os.makedirs(out_dir, exist_ok=True)
        steps = []
        for step in range(zt.icon_step_count()):
            img = render_step(master, kind, step)
            img.save(os.path.join(out_dir, f"{step}.png"))
            steps.append(img)
        rendered[kind] = steps
        nw, nh = native_dim(kind, 0)
        print(f"  {kind:9s} master {master.width}x{master.height} "
              f"-> 4 steps, native {nw}x{nh} at zoom 0, "
              f"export {steps[0].width}x{steps[0].height}")

    if missing:
        print("\n  no master, not generated: " + ", ".join(missing))
        print("  the renderer falls back to the player sprite for these.")

    if args.sheet and rendered:
        path = contact_sheet(rendered,
                             os.path.join(args.out, "_contact_sheet.png"))
        print(f"\n  contact sheet: {path}")

    return 0 if rendered else 1


if __name__ == "__main__":
    sys.exit(main())
