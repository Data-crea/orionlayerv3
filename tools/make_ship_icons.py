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

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import basepack, zoomtables as zt  # noqa: E402
from core.shipcut import (KINDS, PANEL_FILE, SRC_REL, OUT_REL,  # noqa: E402
                          is_greyscale, native_dim, render_panel,
                          render_step, trim)

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
    ap.add_argument("--src", default=basepack.source(SRC_REL, base))
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
        if kind != "player":
            render_panel(master).save(os.path.join(out_dir, PANEL_FILE))
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
