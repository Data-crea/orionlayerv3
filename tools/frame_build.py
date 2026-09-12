#!/usr/bin/env python3
"""Build the colony screen's frame from the main-screen master.

    python tools/frame_build.py
    python tools/frame_build.py --resolution 1920x1080 --out /tmp/f

**THE FRAME IS BUILT, NOT RENDERED.** Six image-tool renders were
measured on 6 September 2026 (`~/Bilder/rahmen/manifest.md`) and none
was usable: five had near-white metal 30 degrees off the master's hue
and no interior windows at all, and the sixth was the right frame at
2.0163 — 13.4 % wider than 16:9 — letterboxed into a 16:9 canvas,
88 px short of what a crop to 16:9 needs. So the metal comes from the
master this screen has to sit beside, and the geometry comes from
`layout_reference.json`, and nothing is invented in between.

What is taken from `screens/galaxy_map/assets/frame.png`:

  the four ring bands   its own metal border, 129 / 145 / 21 / 86 in
                        its pixels, scaled per side to the ring the
                        reference file declares
  the four corners      lifted whole, so a corner is never stretched
                        along two axes at once
  the strut texture     a patch of its bottom band — the widest run
                        of metal in the master that no hole touches,
                        so it carries no bevel

**STRUTS ARE PLAIN, AND THAT IS THE INSTRUCTION.** The interior metal
between windows is the texture and nothing else: no bevel, no
highlight, no attempt to imitate the master's moulded edges. Whether
it needs any is a judgement to make on the picture, and the picture
is the point of this tool.

**AND THE ALPHA IS STILL THE MASK'S.** The windows are cut by
`frame_cut.cut`, from `layout_reference.json` — never from the
artwork's own dark pixels. See that module for why.

**GENERATED, NEVER COMMITTED** (decision 40). Every input is in the
tree, so regenerating reproduces it byte for byte.

Requires: Pillow, numpy.
"""
import argparse
import os
import sys

import numpy as np
from scipy import ndimage

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is missing. Run: pip install pillow --break-system-packages")

import frame_cut  # noqa: E402
import frame_holes  # noqa: E402
import frame_mask  # noqa: E402
from frame_master import (  # noqa: E402
    RAIL_ROLES, bevel_source, junction_source, master_rails,
    master_ring, print_profiles, strut_texture, struts)

MASTER = os.path.join(frame_mask.ROOT, "screens", "galaxy_map", "assets",
                      "frame.png")
DEFAULT_OUT = os.path.join(frame_mask.ROOT, "screens", "colony_summary",
                           "assets", "frames")
#: How far a texture patch must stay from any hole, in master pixels,
#: for it to carry no bevel. 12 was measured: the master's moulded
#: edges reach about 10 px in from a hole.
BEVEL_CLEARANCE = 12


#: Side of the square patch the strut texture is sampled from.
PATCH = 64
#: How deep the bevel strip is taken from the master, and how wide it
#: is laid in reference px. The master's own lit edge measures ONE
#: pixel on every hole that has one (see `bevel_source`), so three is
#: that line plus the two pixels of falloff behind it, and no more.
BEVEL_MASTER = 3
BEVEL_REF = 3
#: How far out a per-side luminance profile is measured.
PROFILE = 12


def tiled(patch, width, height):
    out = Image.new("RGB", (width, height))
    for y in range(0, height, patch.height):
        for x in range(0, width, patch.width):
            out.paste(patch, (x, y))
    return out


def device_ring(windows, width, height):
    """The ring in device px, taken from the WINDOWS themselves.

    Not `round(ring * scale)`. The ring is by definition the metal
    outside the outermost holes, and the holes are placed by
    `Layout.rect`'s truncation — so at 2560x1440 a rounded ring ended
    one pixel inside its own first hole and the built frame measured
    106 where the table says 107. Deriving it from the rectangles the
    holes are actually cut from makes the two agree by construction
    rather than by two roundings happening to match.
    """
    _image, rects = frame_mask.render(windows, width, height)
    xs = [r[0] for r in rects.values()]
    ys = [r[1] for r in rects.values()]
    rx = [r[0] + r[2] for r in rects.values()]
    by = [r[1] + r[3] for r in rects.values()]
    return min(xs), width - max(rx), min(ys), height - max(by)


def lay_border(dst, src, src_open, dst_open, dst_band):
    """Lay `src`'s border around `dst_open`, nine-slice.

    **ONE FUNCTION FOR THE RING AND FOR EVERY WINDOW'S BEVEL**, which
    is not a coincidence worth being clever about: both are "take the
    band a source image puts around a rectangular opening and put it
    around another rectangle". The ring's opening is the master's own
    inner area; a bevel's opening is one of the master's holes. Two
    implementations of this would be the second copy, and the second
    copy is where a difference gets in.

    The corners are lifted whole and scaled ONCE; the edges stretch
    along their own length only. A corner stretched along two axes is
    the one thing a nine-slice exists to avoid, and it is what a
    plain resize would do.

    `src_open` and `dst_open` are (x0, y0, x1, y1); `dst_band` is
    (left, right, top, bottom) in destination pixels.
    """
    sx0, sy0, sx1, sy1 = src_open
    dx0, dy0, dx1, dy1 = dst_open
    dl, dr, dt, db = dst_band
    sw, sh = src.size
    for box, dest, size in (
            # corners
            ((sx0 - (sx0), 0, sx0, sy0), (dx0 - dl, dy0 - dt), (dl, dt)),
            ((sx1, 0, sw, sy0), (dx1, dy0 - dt), (dr, dt)),
            ((0, sy1, sx0, sh), (dx0 - dl, dy1), (dl, db)),
            ((sx1, sy1, sw, sh), (dx1, dy1), (dr, db)),
            # edges
            ((0, sy0, sx0, sy1), (dx0 - dl, dy0), (dl, dy1 - dy0)),
            ((sx1, sy0, sw, sy1), (dx1, dy0), (dr, dy1 - dy0)),
            ((sx0, 0, sx1, sy0), (dx0, dy0 - dt), (dx1 - dx0, dt)),
            ((sx0, sy1, sx1, sh), (dx0, dy1), (dx1 - dx0, db))):
        if size[0] > 0 and size[1] > 0 and dest[0] >= 0 and dest[1] >= 0:
            dst.paste(src.crop(box).resize(size, Image.LANCZOS), dest)


def lay_rail(dst, strip, rect, vertical, cap=None):
    """Three-slice a rail along `rect`: end cap, stretch, end cap.

    **A SECOND IMPLEMENTATION, AND THIS IS THE REASON.** `lay_border`
    lays four corners and four edges around an opening; a rail has
    two ends and a middle and no corners at all. Forcing it through
    the border would mean synthesising two corners the source does
    not contain, which is the one thing "no invented pixels" rules
    out. The end/stretch logic is the same idea and the third copy of
    it is the one to extract.

    The strip is scaled ACROSS its width to the gap and sliced ALONG
    its length, so the moulding keeps its profile and only the plain
    run in the middle is stretched.
    """
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return
    if vertical:
        strip = strip.resize((w, max(4, strip.height)), Image.LANCZOS)
        length, run = h, strip.height
    else:
        strip = strip.resize((max(4, strip.width), h), Image.LANCZOS)
        length, run = w, strip.width
    cap = max(1, min(cap or run // 3, run // 2, length // 2))
    if vertical:
        dst.paste(strip.crop((0, 0, w, cap)), (x, y))
        dst.paste(strip.crop((0, run - cap, w, run)), (x, y + h - cap))
        mid = strip.crop((0, cap, w, run - cap))
        if h - 2 * cap > 0:
            dst.paste(mid.resize((w, h - 2 * cap), Image.LANCZOS),
                      (x, y + cap))
    else:
        dst.paste(strip.crop((0, 0, cap, h)), (x, y))
        dst.paste(strip.crop((run - cap, 0, run, h)), (x + w - cap, y))
        mid = strip.crop((cap, 0, run - cap, h))
        if w - 2 * cap > 0:
            dst.paste(mid.resize((w - 2 * cap, h), Image.LANCZOS),
                      (x + cap, y))


def _facing(rects, gx, gy, gw, gh, vertical):
    """The names of the two windows a gap lies between."""
    out = set()
    for name, (x, y, w, h) in rects.items():
        if vertical and (x + w == gx or x == gx + gw) and \
                min(y + h, gy + gh) - max(y, gy) > 20:
            out.add(name)
        if not vertical and (y + h == gy or y == gy + gh) and \
                min(x + w, gx + gw) - max(x, gx) > 20:
            out.add(name)
    return out


#: The windows of the bottom row, by their `layout_reference.json`
#: names — seven sort slots and RETURN. Taken from `frame_holes` so
#: the row's membership is stated once; `return_button` is that file's
#: spelling, which `frame_holes.BOX_NAME` maps to the box called
#: `return`.
#:
#: IT WAS `{"sort_bar", "return_button"}` UNTIL 12 September 2026, and
#: the failure of leaving it would have been quiet: a gap whose
#: windows it does not recognise falls through to `list_band`, so the
#: whole band-to-sort seam would have been laid with the wrong strut
#: and nothing would have failed — the rail would simply have been the
#: master's map|slot divider instead of its box|slot one.
SORT_ROW = {"return_button"} | set(frame_holes.SORT_BOX_KEYS)


def gap_role(names, vertical):
    """Which rail a colony gap gets, from the windows it separates."""
    if vertical:
        return "in_row"
    if "header" in names:
        return "header_list"
    if names & SORT_ROW:
        return "band_sort"
    return "list_band"


def build(master, windows, width, height):
    """The frame plate at `width x height`, no holes cut yet.

    The strut texture, then the ring, then every window's bevel —
    all three through `lay_border` except the texture, which is a
    tile.
    """
    dl, dr, dt, db = device_ring(windows, width, height)
    ml, mr, mt, mb = master_ring(master)
    src = master.convert("RGB")
    mw, mh = src.size

    out = tiled(strut_texture(master), width, height)
    lay_border(out, src, (ml, mt, mw - mr, mh - mb),
               (dl, dt, width - dr, height - db), (dl, dr, dt, db))

    scale = min(width / frame_mask.REF_W, height / frame_mask.REF_H)
    band = max(1, round(BEVEL_REF * scale))
    _image, rects = frame_mask.render(windows, width, height)

    # RAILS FIRST, JUNCTIONS OVER THEM, BEVELS LAST. Every gap gets
    # the master's strut for its ROLE (see RAIL_ROLES), laid at the
    # gap's own width — layout_reference.gaps was set to those widths
    # in Stage A3, so nothing is squeezed either way.
    rails = master_rails(master)
    junction = junction_source(master)
    laid = []
    for x, y, gw, gh, vertical in struts(rects):
        names = _facing(rects, x, y, gw, gh, vertical)
        strip_v = rails.get(gap_role(names, vertical))
        if strip_v is None:
            continue
        lay_rail(out, strip_v[0], (x, y, gw, gh), vertical)
        laid.append((x, y, gw, gh, vertical))
    # THE CROSSINGS. Where a vertical rail meets a horizontal one the
    # two overwrite each other's ends; the master's own crossing goes
    # back over the corner, mirrored when the vertical arm comes from
    # the other side. Only the master's pixels, never a drawn corner.
    if junction is not None:
        for vx, vy, vw, vh, vv in laid:
            if not vv:
                continue
            for hx, hy, hw, hh, hv in laid:
                if hv or min(vx + vw, hx + hw) - max(vx, hx) <= 0:
                    continue
                if abs(vy - (hy + hh)) <= 1:          # rail from below
                    out.paste(junction.resize((vw, hh), Image.LANCZOS),
                              (vx, hy))
                elif abs((vy + vh) - hy) <= 1:        # rail from above
                    out.paste(junction.transpose(Image.FLIP_TOP_BOTTOM)
                              .resize((vw, hh), Image.LANCZOS), (vx, hy))

    bsrc, bopen, _chosen = bevel_source(master)
    for _name, (x, y, w, h) in sorted(rects.items()):
        lay_border(out, bsrc, bopen, (x, y, x + w, y + h),
                   (band, band, band, band))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--master", default=MASTER)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--reference", default=frame_mask.REFERENCE)
    ap.add_argument("--resolution", action="append")
    ap.add_argument("--profiles", action="store_true",
                    help="print every master hole's per-side edge profile "
                         "and which one the bevel is sampled from")
    args = ap.parse_args()

    data, windows = frame_mask.load_reference(args.reference)
    master = Image.open(args.master)
    if args.profiles:
        print_profiles(master)
    os.makedirs(args.out, exist_ok=True)
    for spec in args.resolution or data["_resolutions"]:
        width, height = (int(v) for v in spec.lower().split("x"))
        plate = build(master, windows, width, height)
        cut, rects = frame_cut.cut(plate, windows, width, height)
        path = os.path.join(args.out, f"frame_{width}x{height}.png")
        cut.save(path)
        native = master.width >= width
        print(f"{spec}: {len(rects)} holes, master {master.width} px wide "
              f"-> {'downscale' if native else 'UPSCALED INTERIM'} "
              f"x{width / master.width:.3f} -> {path}")
    print("Generated: none of this is committed (.gitignore, decision 40).")


if __name__ == "__main__":
    main()
